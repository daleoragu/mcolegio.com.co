# notas/management/commands/admin_colegio.py
"""Da (o quita) la administración de un colegio a un usuario.

Uso:
    python manage.py admin_colegio --listar
    python manage.py admin_colegio rectora colegio-bilingue-san-sebastian --cargo RECTOR
    python manage.py admin_colegio rectora colegio-bilingue-san-sebastian --quitar-superusuario
    python manage.py admin_colegio rectora colegio-bilingue-san-sebastian --quitar

--quitar-superusuario sirve para el rector que hoy es superusuario: queda
como administrador de SU colegio y deja de poder entrar a los demás.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from notas.models import AdministradorColegio, Colegio


class Command(BaseCommand):
    help = 'Da o quita la administración de un colegio a un usuario.'

    def add_arguments(self, parser):
        parser.add_argument('usuario', nargs='?')
        parser.add_argument('colegio', nargs='?', help='slug del colegio (el subdominio)')
        parser.add_argument('--cargo', default='RECTOR', choices=[c for c, _ in AdministradorColegio.CARGOS])
        parser.add_argument('--quitar-superusuario', action='store_true',
                            help='Le quita el superusuario: solo administra su colegio.')
        parser.add_argument('--quitar', action='store_true', help='Le quita la administración de ese colegio.')
        parser.add_argument('--listar', action='store_true', help='Lista superusuarios y administradores.')

    def handle(self, *args, **o):
        if o['listar']:
            self.stdout.write('Superusuarios (entran a todos los colegios):')
            for u in User.objects.filter(is_superuser=True).order_by('username'):
                self.stdout.write(f'  {u.username:20} {u.get_full_name()}')
            self.stdout.write('\nAdministradores de colegio:')
            for a in AdministradorColegio.objects.select_related('user', 'colegio').order_by('colegio__nombre'):
                estado = '' if a.activo else '  (sin acceso)'
                self.stdout.write(f'  {a.user.username:20} {a.get_cargo_display():24} {a.colegio.slug}{estado}')
            return
        if not (o['usuario'] and o['colegio']):
            raise CommandError('Indique el usuario y el slug del colegio, o use --listar.')
        try:
            usuario = User.objects.get(username=o['usuario'])
        except User.DoesNotExist:
            raise CommandError(f'No existe el usuario «{o["usuario"]}».')
        try:
            colegio = Colegio.objects.get(slug=o['colegio'])
        except Colegio.DoesNotExist:
            slugs = ', '.join(Colegio.objects.values_list('slug', flat=True))
            raise CommandError(f'No existe el colegio «{o["colegio"]}». Colegios: {slugs}')

        if o['quitar']:
            n = AdministradorColegio.objects.filter(user=usuario, colegio=colegio).update(activo=False)
            self.stdout.write(self.style.SUCCESS(f'{usuario.username} ya no administra {colegio.slug}.' if n
                                                 else 'No era administrador de ese colegio.'))
            return

        admin, creado = AdministradorColegio.objects.update_or_create(
            user=usuario, colegio=colegio, defaults={'cargo': o['cargo'], 'activo': True})
        self.stdout.write(self.style.SUCCESS(
            f'{usuario.username} administra {colegio.slug} como {admin.get_cargo_display()}.'))
        if o['quitar_superusuario'] and (usuario.is_superuser or usuario.is_staff):
            if User.objects.filter(is_superuser=True).exclude(pk=usuario.pk).count() == 0:
                raise CommandError('Es el único superusuario: no se le quita, quedaría la plataforma sin dueño.')
            usuario.is_superuser = False
            usuario.is_staff = False
            usuario.save(update_fields=['is_superuser', 'is_staff'])
            self.stdout.write(self.style.SUCCESS('Ya no es superusuario: solo entra a su colegio.'))
