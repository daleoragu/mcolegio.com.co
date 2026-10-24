# -*- coding: utf-8 -*-
"""Circulares: publicar a quien corresponde, leer, confirmar y ver quién falta."""
import os
from unittest import mock

from notas.models import Curso, FichaEstudiante, Notificacion
from notas.tests.base import ColegioDePrueba

from . import logica
from .models import Circular, Lectura

VARIABLES_WA = {'WHATSAPP_TOKEN': 'x', 'WHATSAPP_PHONE_ID': '123', 'WHATSAPP_PLANTILLA': 'aviso'}


class Circulares(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.otro = Curso.objects.create(colegio=cls.a, nombre='701', grado=7)
        cls.dani = cls.crear_estudiante('dani', curso=cls.otro)
        FichaEstudiante.objects.create(estudiante=cls.estudiantes[0], celular_madre='3001234567')

    def _publicar(self, **datos):
        base = {'titulo': 'Salida pedagógica', 'cuerpo': 'El viernes salimos al museo.', 'para': 'FAMILIAS',
                'pide_confirmacion': 'on', 'accion': 'publicar'}
        base.update(datos)
        return self.cliente(self.rectora).post('/circulares/gestion/nueva/', base)

    def test_publicar_a_todas_las_familias(self):
        self._publicar()
        c = Circular.objects.get()
        self.assertEqual(c.numero, 1)
        self.assertEqual(c.lecturas.count(), 4)            # ana, beto, caro y dani
        self.assertEqual(Notificacion.objects.filter(mensaje__contains='Salida pedagógica').count(), 4)
        self._publicar(titulo='Otra')
        self.assertEqual(Circular.objects.get(titulo='Otra').numero, 2)

    def test_solo_algunos_cursos_y_docentes(self):
        self._publicar(para='CURSOS', cursos=[self.otro.id])
        self.assertEqual(list(Lectura.objects.values_list('usuario__username', flat=True)), ['dani'])
        self._publicar(titulo='Para profes', para='DOCENTES')
        self.assertEqual(list(Circular.objects.get(titulo='Para profes').lecturas.values_list('usuario__username', flat=True)), ['profe'])

    def test_al_personal_le_llega_a_docentes_y_administrativos(self):
        self._publicar(titulo='Reunión de personal', para='PERSONAL')
        quienes = set(Circular.objects.get(titulo='Reunión de personal').lecturas.values_list('usuario__username', flat=True))
        self.assertEqual(quienes, {'profe', 'rectora'})

    def test_cursos_sin_escoger_no_se_publica(self):
        self._publicar(para='CURSOS')
        self.assertFalse(Circular.objects.exists())

    def test_la_familia_abre_y_confirma(self):
        self._publicar()
        c = Circular.objects.get()
        ana = self.cliente(self.estudiantes[0].user)
        self.assertContains(ana.get('/circulares/'), 'Nueva')
        self.assertContains(ana.get(f'/circulares/{c.id}/'), 'El viernes salimos al museo.')
        ana.post(f'/circulares/{c.id}/confirmar/', {'nombre': 'Marta (mamá)'})
        l = Lectura.objects.get(usuario=self.estudiantes[0].user)
        self.assertIsNotNone(l.abierta)
        self.assertEqual(l.quien_confirma, 'Marta (mamá)')
        # Quien no es destinatario no la ve.
        self.assertEqual(self.cliente(self.u_docente).get(f'/circulares/{c.id}/').status_code, 404)

    def test_detalle_muestra_pendientes_con_whatsapp(self):
        self._publicar()
        c = Circular.objects.get()
        r = self.cliente(self.rectora).get(f'/circulares/gestion/{c.id}/')
        self.assertContains(r, 'https://wa.me/573001234567')
        self.assertEqual(r.context['resumen']['total'], 4)

    def test_borrador_no_le_llega_a_nadie(self):
        self._publicar(accion='borrador')
        c = Circular.objects.get()
        self.assertTrue(c.es_borrador)
        self.assertFalse(c.lecturas.exists())
        self.assertEqual(self.cliente(self.u_docente).get('/circulares/gestion/').status_code, 403)

    def test_curso_sin_estudiantes_queda_en_borrador(self):
        vacio = Curso.objects.create(colegio=self.a, nombre='1101', grado=11)
        self._publicar(para='CURSOS', cursos=[vacio.id])
        self.assertTrue(Circular.objects.get().es_borrador)


@mock.patch.object(logica, 'EN_SEGUNDO_PLANO', False)
class CircularesPorWhatsApp(ColegioDePrueba):
    """La casilla de WhatsApp: solo con la línea conectada; un mensaje por familia; reintento de las que faltan."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        FichaEstudiante.objects.create(estudiante=cls.estudiantes[0], celular_madre='3001234567',
                                       celular_acudiente='3109998877')
        FichaEstudiante.objects.create(estudiante=cls.estudiantes[1], celular_padre='3015550000')

    def _publicar(self, **datos):
        base = {'titulo': 'Reunión de padres', 'cuerpo': 'El lunes a las 7.', 'para': 'FAMILIAS',
                'pide_confirmacion': 'on', 'por_whatsapp': 'on', 'accion': 'publicar'}
        base.update(datos)
        return self.cliente(self.rectora).post('/circulares/gestion/nueva/', base)

    def test_sin_linea_no_se_ofrece_ni_se_envia(self):
        os.environ.pop('WHATSAPP_TOKEN', None)
        r = self.cliente(self.rectora).get('/circulares/gestion/nueva/')
        self.assertNotIn('por_whatsapp', r.context['form'].fields)
        with mock.patch('notas.mensajeria.enviar_whatsapp') as mandar:
            self._publicar()
        mandar.assert_not_called()
        self.assertFalse(Circular.objects.get().por_whatsapp)

    def test_un_whatsapp_por_familia_al_primer_celular(self):
        self.a.whatsapp_automatico = True
        self.a.save()
        with mock.patch.dict(os.environ, VARIABLES_WA), \
                mock.patch('notas.mensajeria.enviar_whatsapp', return_value=(True, 'ok')) as mandar:
            self.assertIn('por_whatsapp', self.cliente(self.rectora).get('/circulares/gestion/nueva/').context['form'].fields)
            self._publicar()
        c = Circular.objects.get()
        self.assertTrue(c.por_whatsapp)
        numeros = sorted(llamada.args[1] for llamada in mandar.call_args_list)
        self.assertEqual(numeros, ['573015550000', '573109998877'])      # acudiente antes que mamá; caro sin ficha
        self.assertIn(f'/circulares/{c.id}/', mandar.call_args_list[0].args[2])
        ana = Lectura.objects.get(usuario=self.estudiantes[0].user)
        self.assertIsNotNone(ana.whatsapp_enviado)
        self.assertEqual(ana.whatsapp_detalle, 'Acudiente 3109998877')
        self.assertEqual(Lectura.objects.get(usuario=self.estudiantes[2].user).whatsapp_detalle, 'La ficha no tiene celular')
        self.assertEqual(logica.resumen(c)['whatsapp'], 2)

    def test_reintentar_solo_a_las_que_faltan(self):
        self.a.whatsapp_automatico = True
        self.a.save()
        with mock.patch.dict(os.environ, VARIABLES_WA):
            with mock.patch('notas.mensajeria.enviar_whatsapp', side_effect=[(True, 'ok'), (False, 'WhatsApp respondió 429')]):
                self._publicar()
            c = Circular.objects.get()
            fallo = Lectura.objects.get(whatsapp_detalle__startswith='No salió')
            self.assertIn('429', fallo.whatsapp_detalle)
            r = self.cliente(self.rectora).get(f'/circulares/gestion/{c.id}/')
            self.assertContains(r, 'Enviar a las que faltan')
            with mock.patch('notas.mensajeria.enviar_whatsapp', return_value=(True, 'ok')) as mandar:
                self.cliente(self.rectora).post(f'/circulares/gestion/{c.id}/whatsapp/')
        self.assertEqual(mandar.call_count, 1)                           # solo la que había fallado
        fallo.refresh_from_db()
        self.assertIsNotNone(fallo.whatsapp_enviado)

    def test_se_para_si_fallan_muchos_seguidos(self):
        self.a.whatsapp_automatico = True
        self.a.save()
        with mock.patch.dict(os.environ, VARIABLES_WA), mock.patch.object(logica, 'MAX_FALLOS_SEGUIDOS', 1), \
                mock.patch('notas.mensajeria.enviar_whatsapp', return_value=(False, 'límite')) as mandar:
            self._publicar()
        self.assertEqual(mandar.call_count, 1)
