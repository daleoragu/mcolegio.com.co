# pruebas/management/commands/recalcular_endpoints.py
"""
Vuelve a apuntar el ENDPOINT de las páginas ya publicadas.

Hace falta cuando se subió un archivo desde el computador local (quedó grabado
"localhost") y después se pasó a producción, o cuando cambia el dominio.

Uso:
    python manage.py recalcular_endpoints --dominio mcolegio.com.co
    python manage.py recalcular_endpoints --dominio mcolegio.com.co --simular
"""
import posixpath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from salon_digital.models import PaginaPublicada
from salon_digital.utils import reescribir_endpoint


def html_del_sitio(base):
    """Recorre la carpeta del sitio y devuelve las rutas de sus .html."""
    encontrados = []
    pendientes = [base]
    while pendientes:
        actual = pendientes.pop()
        try:
            carpetas, archivos = default_storage.listdir(actual)
        except (NotImplementedError, OSError):
            continue
        for nombre in archivos:
            if nombre.lower().endswith(('.html', '.htm')):
                encontrados.append(posixpath.join(actual, nombre))
        pendientes.extend(posixpath.join(actual, c) for c in carpetas)
    return encontrados


class Command(BaseCommand):
    help = 'Reapunta el ENDPOINT de las páginas publicadas al dominio indicado.'

    def add_arguments(self, parser):
        parser.add_argument('--dominio', required=True,
                            help='Dominio público. Ej: mcolegio.com.co')
        parser.add_argument('--usuario', help='Nombre de usuario. Por defecto, todas las cuentas.')
        parser.add_argument('--simular', action='store_true',
                            help='Muestra qué cambiaría, sin tocar nada.')

    def handle(self, *args, **op):
        base = op['dominio'].strip().rstrip('/')
        if not base:
            raise CommandError('Indica un dominio.')

        paginas = PaginaPublicada.objects.filter(captura_resultados=True)
        if op['usuario']:
            paginas = paginas.filter(propietario__slug=op['usuario'])
        if not paginas.exists():
            self.stdout.write(self.style.WARNING('No hay páginas que recojan resultados.'))
            return

        simular = op['simular']
        total_archivos = 0

        host = base if base.startswith(('http://', 'https://')) else 'https://' + base
        host = host.rstrip('/')

        for pagina in paginas.select_related('propietario'):
            endpoint = host + reverse('salon_digital:api_resultados', kwargs={
                'usuario': pagina.propietario.slug, 'slug': pagina.slug})

            if pagina.tipo == 'sitio':
                rutas = html_del_sitio(pagina.base_sitio)
            elif pagina.archivo:
                rutas = [pagina.archivo.name]
            else:
                rutas = []

            cambiados = 0
            for ruta in rutas:
                try:
                    with default_storage.open(ruta, 'rb') as fh:
                        original = fh.read()
                except OSError:
                    self.stdout.write(self.style.WARNING(f'   no se pudo leer {ruta}'))
                    continue

                nuevo, cambio = reescribir_endpoint(original, endpoint, pagina.clave_panel)
                if not cambio:
                    continue
                cambiados += 1
                if simular:
                    continue
                default_storage.delete(ruta)
                default_storage.save(ruta, ContentFile(nuevo.encode('utf-8')))

            total_archivos += cambiados
            if not simular and cambiados:
                PaginaPublicada.objects.filter(pk=pagina.pk).update(endpoint_reescrito=True)

            marca = self.style.SUCCESS('✓') if cambiados else self.style.WARNING('—')
            self.stdout.write(f'{marca} {pagina.titulo}: {cambiados} archivo(s) → {endpoint}')

        verbo = 'se cambiarían' if simular else 'cambiados'
        self.stdout.write(self.style.SUCCESS(f'\n{total_archivos} archivo(s) {verbo}.'))
