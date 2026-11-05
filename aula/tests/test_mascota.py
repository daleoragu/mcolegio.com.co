"""Mascota académica: se cuida respondiendo preguntas; las necesidades bajan con las horas."""
from datetime import timedelta

from django.utils import timezone

from aula import mascota as MA
from aula.models import Aula, MascotaAula
from notas.tests.base import ColegioDePrueba

PREGUNTAS = """1. ¿2 + 2?
A) 3
*B) 4
2. ¿3 + 3?
*A) 6
B) 7
"""


class Mascota(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def setUp(self):
        self.ana = self.estudiantes[0]
        self.profe = self.cliente(self.u_docente)
        self.profe.get(f'/aula/asignacion/{self.asig.id}/')
        self.aula = Aula.objects.get(asignacion=self.asig)
        self.base = f'/aula/{self.aula.pk}/mascota'
        self.yo = self.cliente(self.ana.user)

    def adoptar(self):
        self.yo.post(f'{self.base}/', {'especie': 'gato', 'nombre': 'Michi'})
        return MascotaAula.objects.get(estudiante=self.ana)

    def correcta(self, m):
        m.refresh_from_db()
        return m.pendiente['correcta']

    def test_adoptar(self):
        r = self.yo.get(f'{self.base}/')
        self.assertContains(r, 'Adopte su mascota')
        m = self.adoptar()
        self.assertEqual((m.especie, m.nombre), ('gato', 'Michi'))
        r = self.yo.get(f'{self.base}/')
        self.assertContains(r, 'MICHI')
        self.assertContains(r, 'aula/mascota.js')

    def test_pedir_no_manda_la_correcta_y_responder_llena(self):
        m = self.adoptar()
        MascotaAula.objects.filter(pk=m.pk).update(hambre=20)
        j = self.yo.post(f'{self.base}/pedir/', {'accion': 'comer'}).json()
        self.assertTrue(j['ok'])
        self.assertNotIn('correcta', j['pregunta'])
        self.assertNotIn('correcta', str(j['pregunta']['opciones']))
        j = self.yo.post(f'{self.base}/responder/', {'opcion': self.correcta(m)}).json()
        self.assertTrue(j['bien'])
        self.assertGreaterEqual(j['estado']['hambre'], 53)
        # La misma respuesta no se puede repetir para llenarla otra vez
        j = self.yo.post(f'{self.base}/responder/', {'opcion': 0}).json()
        self.assertFalse(j['ok'])

    def test_respuesta_mala_no_llena_y_dice_la_correcta(self):
        m = self.adoptar()
        MascotaAula.objects.filter(pk=m.pk).update(higiene=10)
        self.yo.post(f'{self.base}/pedir/', {'accion': 'banar'})
        buena = self.correcta(m)
        j = self.yo.post(f'{self.base}/responder/', {'opcion': (buena + 1) % 2}).json()
        self.assertFalse(j['bien'])
        self.assertEqual(j['correcta'], buena)
        self.assertLessEqual(j['estado']['higiene'], 10)

    def test_si_esta_llena_no_pregunta(self):
        m = self.adoptar()
        MascotaAula.objects.filter(pk=m.pk).update(hambre=99)
        j = self.yo.post(f'{self.base}/pedir/', {'accion': 'comer'}).json()
        self.assertFalse(j['ok'])
        self.assertIn('no tiene hambre', j['mensaje'])

    def test_bajan_con_el_tiempo_se_desmaya_y_se_reanima(self):
        m = self.adoptar()
        hace = timezone.now() - timedelta(days=3)
        MascotaAula.objects.filter(pk=m.pk).update(nacida=hace, actualizada=timezone.now() - timedelta(hours=10))
        m.refresh_from_db()
        MA.actualizar(m)
        self.assertEqual(MA.dias_vivo(m), 3)
        self.assertEqual(m.mejor_racha, 3)
        self.assertAlmostEqual(m.hambre, 40, delta=1)          # 80 - 4 × 10 h
        # Dos días sin atenderla: se desmaya y la racha vuelve a cero
        MascotaAula.objects.filter(pk=m.pk).update(actualizada=timezone.now() - timedelta(hours=40))
        m.refresh_from_db()
        MA.actualizar(m)
        self.assertTrue(m.debil)
        self.assertEqual(MA.dias_vivo(m), 0)
        self.assertEqual(m.mejor_racha, 3)
        j = self.yo.post(f'{self.base}/pedir/', {'accion': 'comer'}).json()
        self.assertIn('desmayada', j['mensaje'])
        for _ in range(3):
            self.yo.post(f'{self.base}/pedir/', {'accion': 'reanimar'})
            j = self.yo.post(f'{self.base}/responder/', {'opcion': self.correcta(m)}).json()
        self.assertFalse(j['estado']['debil'])
        self.assertIn('despertó', j['mensaje'])
        self.assertEqual(j['estado']['hambre'], 50)

    def test_usa_las_preguntas_del_docente(self):
        r = self.profe.post(f'{self.base}/', {'preguntas': PREGUNTAS})
        self.aula.refresh_from_db()
        self.assertEqual(len(self.aula.preguntas_mascota), 2)
        m = self.adoptar()
        MascotaAula.objects.filter(pk=m.pk).update(sueno=10)
        j = self.yo.post(f'{self.base}/pedir/', {'accion': 'dormir'}).json()
        self.assertIn(j['pregunta']['texto'], ['¿2 + 2?', '¿3 + 3?'])

    def test_el_docente_ve_las_mascotas(self):
        self.adoptar()
        r = self.profe.get(f'{self.base}/')
        self.assertContains(r, 'Mascotas de la clase (1)')
        self.assertContains(r, 'Michi')

    def test_en_el_menu_de_juegos(self):
        self.assertContains(self.yo.get(f'/aula/{self.aula.pk}/gamificacion/'), 'MI MASCOTA')
