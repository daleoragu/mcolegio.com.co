"""Región del docente: País → Departamento → Municipio con el código DANE (DIVIPOLA), y la biblioteca por región."""
from django.contrib.auth.models import User
from django.test import Client, TestCase

from . import regiones as R
from .models import Cuenta


class Regiones(TestCase):
    def test_lista_oficial_y_reconocer(self):
        self.assertEqual(len(R.departamentos()), 33)                          # 32 departamentos y Bogotá D.C.
        self.assertEqual(sum(len(R.municipios(c)) for c, _ in R.departamentos()), 1122)
        self.assertEqual(R.etiqueta('73001'), 'Ibagué, Tolima')
        self.assertEqual(R.etiqueta('11001'), 'Bogotá, D.C.')
        self.assertEqual(R.reconocer('ibague'), '73001')
        self.assertEqual(R.reconocer('Líbano, Tolima'), '73411')
        self.assertEqual(R.reconocer('Armenia'), '')                         # hay varias Armenias: no adivina
        self.assertEqual(R.reconocer('Armenia', 'quindio'), '63001')
        self.assertEqual(R.reconocer('Bogota'), '11001')
        self.assertEqual(R.reconocer('Ciudad inventada'), '')

    def datos(self, **extra):
        d = {'username': 'lina', 'email': 'lina@correo.co', 'password1': 'UnaClave.Segura99', 'password2': 'UnaClave.Segura99',
             'nombre_publico': 'Lina Pérez', 'slug': 'linaperez', 'institucion': 'IE Fátima', 'pais': 'Colombia'}
        d.update(extra)
        return d

    def test_inscripcion_con_el_menu(self):
        c = Client(HTTP_HOST='localhost')
        r = c.get('/salon_digital/registro/')
        self.assertContains(r, 'mm-region-dep'); self.assertContains(r, 'id="mm-regiones"')
        self.assertIn(['73001', 'Ibagué'], r.context['regiones_menu']['municipios']['73'])
        # Sin municipio, o con uno de otro departamento: no
        r = c.post('/salon_digital/registro/', self.datos())
        self.assertContains(r, 'Escoja su municipio de la lista')
        self.assertFalse(Cuenta.objects.exists())
        r = c.post('/salon_digital/registro/', self.datos(departamento_dane='05', municipio_dane='73001'))
        self.assertContains(r, 'Ese municipio no es del departamento escogido')
        r = c.post('/salon_digital/registro/', self.datos(departamento_dane='73', municipio_dane='73411'))
        self.assertEqual(r.status_code, 302)
        cu = Cuenta.objects.get()
        self.assertEqual((cu.pais, cu.municipio_dane, cu.municipio, cu.departamento), ('Colombia', '73411', 'Líbano', 'Tolima'))

    def test_otro_pais_y_mi_cuenta(self):
        c = Client(HTTP_HOST='localhost')
        r = c.post('/salon_digital/registro/', self.datos(pais='otro', pais_otro=''))
        self.assertContains(r, 'Escriba su país y su ciudad')
        c.post('/salon_digital/registro/', self.datos(pais='otro', pais_otro='Ecuador, Quito'))
        cu = Cuenta.objects.get()
        self.assertEqual((cu.pais, cu.municipio, cu.municipio_dane), ('Ecuador', 'Quito', ''))
        # En «Mi cuenta» se cambia a Colombia y el inicio deja de pedir el municipio
        r = c.post('/salon_digital/panel/cuenta/', {'nombre_publico': 'Lina Pérez', 'slug': 'linaperez', 'institucion': 'IE Fátima',
                                                   'pais': 'Colombia', 'departamento_dane': '11', 'municipio_dane': '11001'})
        self.assertEqual(r.status_code, 302)
        cu.refresh_from_db()
        self.assertEqual((cu.pais, cu.municipio_dane, cu.departamento), ('Colombia', '11001', 'Bogotá, D.C.'))
        self.assertContains(c.get('/salon_digital/panel/cuenta/'), 'value="11001" selected')

    def test_el_inicio_pide_el_municipio(self):
        u = User.objects.create_user('profe', password='x')
        Cuenta.objects.create(usuario=u, slug='profe', nombre_publico='Profe', estado='verificada', municipio='Ibague')
        c = Client(HTTP_HOST='localhost'); c.force_login(u)
        self.assertContains(c.get('/salon_digital/inicio/'), '¿De qué municipio es?')
        Cuenta.objects.filter(usuario=u).update(municipio_dane='73001')
        self.assertNotContains(c.get('/salon_digital/inicio/'), '¿De qué municipio es?')

    def test_biblioteca_por_region(self):
        from materiales.models import MaterialCompartido
        yo = User.objects.create_user('yo', password='x')
        Cuenta.objects.create(usuario=yo, slug='yo', nombre_publico='Yo', estado='verificada', plan='ilimitado', municipio_dane='73001')
        otro = User.objects.create_user('otro', password='x')
        crear = lambda t, mun, reg=False: MaterialCompartido.objects.create(autor=otro, titulo=t, alcance='comunidad', estado='publicado',
                                                                           municipio_dane=mun, regional=reg, contenido={'bloques': []})
        crear('Fracciones con café del Tolima', '73001', True)
        crear('Guía del Líbano', '73411')
        crear('Taller de Medellín', '05001')
        c = Client(HTTP_HOST='localhost'); c.force_login(yo)
        ver = lambda q: sorted(m.titulo for m in c.get('/materiales/biblioteca/' + q).context['materiales'])
        self.assertEqual(len(ver('')), 3)
        self.assertEqual(ver('?region=municipio'), ['Fracciones con café del Tolima'])
        self.assertEqual(ver('?region=departamento'), ['Fracciones con café del Tolima', 'Guía del Líbano'])
        self.assertEqual(ver('?regional=1'), ['Fracciones con café del Tolima'])
        r = c.get('/materiales/biblioteca/')
        self.assertContains(r, 'De mi municipio (Ibagué, Tolima)'); self.assertContains(r, '📍 Medellín, Antioquia')
