"""Cuentas de estudiantes como Khan Academy: el docente escribe los nombres, la plataforma propone contraseñas fáciles,
se imprimen en tarjetas y el estudiante entra tocando su nombre. La contraseña se guarda cifrada."""
from django.contrib.auth.models import User
from django.test import Client, TestCase

from aula.models import Aula
from .models import Cuenta, Grupo, Integrante


class CuentasDeEstudiantes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user('profe', password='x', first_name='David')
        cls.cuenta = Cuenta.objects.create(usuario=cls.u, slug='davidramos', nombre_publico='Prof. David', estado='verificada',
                                           plan='ilimitado')

    def setUp(self):
        self.profe = Client(HTTP_HOST='localhost')
        self.profe.force_login(self.u)
        self.profe.post('/salon_digital/grupos/nuevo/', {'nombre': '7-01', 'activo': 'on'})
        self.grupo = Grupo.objects.get(nombre='7-01')
        self.profe.get(f'/aula/grupo/{self.grupo.pk}/')
        self.aula = Aula.objects.get(grupo=self.grupo)
        self.g = f'/salon_digital/grupos/{self.grupo.pk}/'

    def crear(self, filas, permiso=True):
        datos = {'paso': 'crear', 'nombre': [n for n, _ in filas], 'clave': [c for _, c in filas]}
        if permiso:
            datos['permiso'] = 'on'
        return self.profe.post(self.g + 'agregar/', datos)

    def entrar(self, est, integrante, secreto='', recordar=False):
        datos = {'codigo': self.grupo.codigo, 'integrante': integrante.pk, 'pin': secreto}
        if recordar:
            datos['recordar'] = 'on'
        return est.post(f'/aula/{self.aula.pk}/entrar/', datos)

    def test_un_grupo_nuevo_entra_con_contrasena(self):
        self.assertEqual(self.grupo.ingreso, 'clave')

    def test_crear_cuentas_paso_a_paso(self):
        r = self.profe.get(self.g + 'agregar/')
        self.assertContains(r, 'Crear cuentas para sus estudiantes')
        # Paso 1 → 2: nombres escritos y pegados; se proponen contraseñas fáciles
        r = self.profe.post(self.g + 'agregar/', {'paso': 'revisar', 'nombre': ['Rosa Salazar', ''], 'lista': 'Cano Valentina\nRosa Salazar'})
        self.assertContains(r, 'Revise las contraseñas')
        self.assertEqual([f['nombre'] for f in r.context['filas']], ['Rosa Salazar', 'Cano Valentina'])
        self.assertRegex(r.context['filas'][0]['clave'], r'^[a-z]+-\d{3}$')
        # Sin el permiso de los padres o con una contraseña débil, no se crea nada
        r = self.crear([('Rosa Salazar', 'luna-482')], permiso=False)
        self.assertContains(r, 'permiso de los padres')
        r = self.crear([('Rosa Salazar', '1234'), ('Cano Valentina', '12345678')])
        self.assertContains(r, 'al menos 8')
        self.assertContains(r, 'muy común')
        self.assertFalse(Integrante.objects.exists())
        # Se crean: la contraseña queda cifrada y se ve solo ahora, en la lista y en las tarjetas
        r = self.crear([('Rosa Salazar', 'luna-482'), ('Cano Valentina', 'tigre-917')])
        self.assertRedirects(r, self.g + 'cuentas/')
        rosa = Integrante.objects.get(completo='Rosa Salazar')
        self.assertNotIn('luna-482', rosa.clave)
        self.assertTrue(rosa.clave_correcta('luna-482'))
        self.assertContains(self.profe.get(self.g + 'cuentas/'), 'luna-482')
        r = self.profe.get(self.g + 'tarjetas/?recientes=1')
        self.assertContains(r, 'tigre-917')
        self.assertContains(r, 'Mi contraseña')
        # En otra sesión del docente ya no se ven (solo se pueden restablecer)
        otro = Client(HTTP_HOST='localhost')
        otro.force_login(self.u)
        self.assertNotContains(otro.get(self.g + 'cuentas/'), 'luna-482')
        self.assertContains(self.profe.get(self.g), 'Restablecer contraseña')

    def test_entrar_con_contrasena_restablecer_y_cambiarla(self):
        self.crear([('Rosa Salazar', 'luna-482')])
        rosa = Integrante.objects.get()
        est = Client(HTTP_HOST='localhost')
        r = est.get(f'/aula/{self.aula.pk}/entrar/', {'codigo': self.grupo.codigo})
        self.assertContains(r, 'Toque su nombre')
        self.assertContains(r, 'Rosa Salazar')
        r = self.entrar(est, rosa, 'otra-cosa')
        self.assertContains(r, 'Esa contraseña no es')
        r = self.entrar(est, rosa, 'luna-482', recordar=True)
        self.assertRedirects(r, f'/aula/{self.aula.pk}/inicio/')
        self.assertGreater(est.session.get_expiry_age(), 60 * 60 * 24 * 30)          # «Recordarme» la deja abierta
        r = est.get(f'/aula/{self.aula.pk}/inicio/')
        for texto in ('Aprender', 'Practicar', 'Tareas', 'Evaluaciones', 'Muro de la clase', 'Próximas entregas', 'Cambiar mi contraseña'):
            self.assertContains(r, texto)
        self.assertContains(est.get(f'/aula/{self.aula.pk}/trabajo/'), 'Juegos de lógica')
        # El estudiante pone su propia contraseña
        r = est.post(f'/aula/{self.aula.pk}/mi-clave/', {'actual': 'mala', 'nueva': 'mi-perro-99', 'otra': 'mi-perro-99'})
        self.assertContains(r, 'actual no es')
        r = est.post(f'/aula/{self.aula.pk}/mi-clave/', {'actual': 'luna-482', 'nueva': 'mi-perro-99', 'otra': 'mi-perro-99'})
        self.assertRedirects(r, f'/aula/{self.aula.pk}/inicio/')
        rosa.refresh_from_db()
        self.assertTrue(rosa.clave_propia and rosa.clave_correcta('mi-perro-99'))
        # La olvidó: el docente la restablece y la ve una vez
        r = self.profe.post(f"{self.g}estudiante/{rosa.pk}/clave/", {}, follow=True)
        rosa.refresh_from_db()
        self.assertFalse(rosa.clave_correcta('mi-perro-99'))
        nueva = [m.message for m in r.context['messages']][-1].split(': ')[-1]
        self.assertTrue(rosa.clave_correcta(nueva))
        self.assertFalse(rosa.clave_propia)

    def test_sin_contrasena_entra_con_su_pin_y_el_docente_ve_el_aviso(self):
        luis = Integrante.objects.create(grupo=self.grupo, apellidos='Pérez', nombres='Luis')
        self.assertContains(self.profe.get(self.g), 'Darles contraseña ahora')
        est = Client(HTTP_HOST='localhost')
        self.assertContains(self.entrar(est, luis, '0000' if luis.pin_chat != '0000' else '1111'), 'PIN no es')
        self.assertRedirects(self.entrar(est, luis, luis.pin_chat), f'/aula/{self.aula.pk}/inicio/')
        # Contraseñas para los que no tienen
        self.profe.post(self.g + 'claves/')
        luis.refresh_from_db()
        self.assertTrue(luis.clave)
        self.assertContains(self.profe.get(self.g + 'cuentas/'), 'Pérez Luis')

    def test_los_otros_modos_y_el_docente(self):
        rosa = Integrante.objects.create(grupo=self.grupo, apellidos='Salazar', nombres='Rosa')
        Grupo.objects.filter(pk=self.grupo.pk).update(ingreso='nombre')
        est = Client(HTTP_HOST='localhost')
        self.assertRedirects(self.entrar(est, rosa), f'/aula/{self.aula.pk}/inicio/')
        self.assertNotContains(est.get(f'/aula/{self.aula.pk}/inicio/'), 'Cambiar mi contraseña')
        # El docente sigue llegando a su muro de siempre
        self.assertRedirects(self.profe.get(f'/aula/{self.aula.pk}/inicio/'), f'/aula/{self.aula.pk}/')
        self.assertContains(self.profe.get(self.g + 'carta-padres/'), 'Ley 1581')
