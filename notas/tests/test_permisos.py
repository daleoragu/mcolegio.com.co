# notas/tests/test_permisos.py
"""Quién puede qué: superusuario, administrador del colegio y docente."""
from django.contrib.auth.models import Group, User
from django.urls import reverse

from notas.models import AdministradorColegio, Docente

from .base import CLAVE, ColegioDePrueba

PANTALLAS_ADMIN = ['admin_dashboard', 'gestion_cursos', 'gestion_estudiantes', 'gestion_docentes',
                   'panel_control_periodos', 'configuracion_calificaciones', 'promocion_anual',
                   'administradores_colegio', 'personalizacion_portal']


class Roles(ColegioDePrueba):

    def test_rectora_inicia_sesion_en_su_colegio_y_no_en_otro(self):
        r = self.cliente(host='a.localhost').post('/', {'username': 'rectora', 'password': CLAVE})
        self.assertEqual(r.status_code, 302)
        r = self.cliente(host='b.localhost').post('/', {'username': 'rectora', 'password': CLAVE})
        self.assertEqual(r.status_code, 200)          # se queda en el portal: «no pertenece»
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_rectora_administra_su_colegio(self):
        c = self.cliente(self.rectora)
        for nombre in PANTALLAS_ADMIN:
            with self.subTest(pantalla=nombre):
                self.assertEqual(c.get(reverse('notas:' + nombre)).status_code, 200)

    def test_rectora_no_administra_otro_colegio(self):
        c = self.cliente(self.rectora, host='b.localhost')
        for nombre in PANTALLAS_ADMIN:
            with self.subTest(pantalla=nombre):
                self.assertNotEqual(c.get(reverse('notas:' + nombre)).status_code, 200)

    def test_docente_no_entra_a_administracion(self):
        c = self.cliente(self.u_docente)
        for nombre in PANTALLAS_ADMIN:
            with self.subTest(pantalla=nombre):
                self.assertNotEqual(c.get(reverse('notas:' + nombre)).status_code, 200)

    def test_superusuario_entra_a_todos(self):
        for host in ('a.localhost', 'b.localhost'):
            c = self.cliente(self.super, host=host)
            self.assertEqual(c.get(reverse('notas:gestion_cursos')).status_code, 200)

    def test_grupo_viejo_ya_no_da_permisos(self):
        u = User.objects.create_user('viejo', password=CLAVE)
        u.groups.add(Group.objects.create(name='Administradores'))
        Docente.objects.create(colegio=self.b, user=u)
        self.assertNotEqual(self.cliente(u).get(reverse('notas:gestion_cursos')).status_code, 200)


class Suplantacion(ColegioDePrueba):

    def usuario_en_sesion(self, c):
        return User.objects.get(id=c.session['_auth_user_id']).username

    def test_rectora_ve_como_docente_y_vuelve(self):
        c = self.cliente(self.rectora)
        c.post(f'/suplantar/iniciar/{self.u_docente.id}/')
        self.assertEqual(self.usuario_en_sesion(c), 'profe')
        c.get('/suplantar/detener/')
        self.assertEqual(self.usuario_en_sesion(c), 'rectora')

    def test_nadie_suplanta_al_superusuario_ni_a_otro_admin(self):
        otro = User.objects.create_user('coord', password=CLAVE)
        AdministradorColegio.objects.create(user=otro, colegio=self.a)
        c = self.cliente(self.rectora)
        for objetivo in (self.super, otro):
            c.post(f'/suplantar/iniciar/{objetivo.id}/')
            self.assertEqual(self.usuario_en_sesion(c), 'rectora')

    def test_no_se_suplanta_por_enlace(self):
        c = self.cliente(self.rectora)
        self.assertEqual(c.get(f'/suplantar/iniciar/{self.u_docente.id}/').status_code, 405)

    def test_no_se_suplanta_a_alguien_de_otro_colegio(self):
        ajeno = self.crear_estudiante('ajeno', curso=None, colegio=self.b)
        c = self.cliente(self.rectora)
        c.post(f'/suplantar/iniciar/{ajeno.user.id}/')
        self.assertEqual(self.usuario_en_sesion(c), 'rectora')
