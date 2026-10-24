"""Correo interno: enviar, responder, borradores, destacados, papelera de cada uno y acciones en grupo."""
from notas.models import Mensaje, Notificacion

from .base import ColegioDePrueba


class CorreoInterno(ColegioDePrueba):

    def _enviar(self, de, para, asunto='Reunión', cuerpo='Nos vemos el lunes.'):
        return self.cliente(de).post('/mensajeria/componer/', {'destinatario': para.id, 'asunto': asunto, 'cuerpo': cuerpo})

    def test_enviar_y_leer(self):
        r = self._enviar(self.rectora, self.u_docente)
        self.assertRedirects(r, '/mensajeria/enviados/', fetch_redirect_response=False)
        m = Mensaje.objects.get()
        aviso = Notificacion.objects.get(destinatario=self.u_docente, tipo='MENSAJE')
        self.assertEqual(aviso.url, f'/mensajeria/ver/{m.id}/')              # antes quedaba «#»
        c = self.cliente(self.u_docente)
        r = c.get('/mensajeria/bandeja-entrada/')
        self.assertContains(r, 'Reunión')
        self.assertEqual(r.context['no_leidos'], 1)
        c.get(f'/mensajeria/ver/{m.id}/')
        m.refresh_from_db()
        self.assertTrue(m.leido)
        # Un tercero no lo ve
        self.assertEqual(self.cliente(self.estudiantes[0].user).get(f'/mensajeria/ver/{m.id}/').status_code, 403)
        # Sin texto no se envía
        r = self._enviar(self.rectora, self.u_docente, cuerpo='   ')
        self.assertContains(r, 'Escriba el mensaje.')

    def test_directivos_tambien_reciben(self):
        c = self.cliente(self.u_docente)
        r = c.get('/mensajeria/componer/')
        self.assertIn(self.rectora, list(r.context['form'].fields['destinatario'].queryset))
        self.assertContains(r, 'Rosa Rector (Rector(a))')
        self.assertNotIn(self.u_docente, list(r.context['form'].fields['destinatario'].queryset))

    def test_responder_y_reenviar_citan_bien(self):
        self._enviar(self.rectora, self.u_docente, cuerpo='Línea uno\nLínea dos')
        m = Mensaje.objects.get()
        c = self.cliente(self.u_docente)
        r = c.get(f'/mensajeria/componer/?responder_a={m.id}')
        inicial = r.context['form'].initial
        self.assertEqual(inicial['asunto'], 'Re: Reunión')
        self.assertIn('> Línea uno\n> Línea dos', inicial['cuerpo'])
        self.assertNotIn('\\n', inicial['cuerpo'])                        # antes salía «\n» escrito
        r = c.get(f'/mensajeria/componer/?reenviar={m.id}')
        self.assertEqual(r.context['form'].initial['asunto'], 'RV: Reunión')

    def test_borrador_se_edita_y_se_envia(self):
        c = self.cliente(self.rectora)
        c.post('/mensajeria/componer/', {'destinatario': self.u_docente.id, 'asunto': 'Pendiente', 'cuerpo': '',
                                         'guardar_borrador': '1'})
        b = Mensaje.objects.get()
        self.assertEqual(b.estado, 'BORRADOR')
        self.assertContains(c.get('/mensajeria/borradores/'), 'Pendiente')       # antes esta página fallaba
        self.assertFalse(Mensaje.objects.filter(destinatario=self.u_docente, estado='ENVIADO').exists())
        c.post(f'/mensajeria/borrador/{b.id}/', {'destinatario': self.u_docente.id, 'asunto': 'Pendiente',
                                                 'cuerpo': 'Ya está listo'})
        b.refresh_from_db()
        self.assertEqual((b.estado, Mensaje.objects.count()), ('ENVIADO', 1))      # el mismo, no uno nuevo
        # Descartar otro borrador
        c.post('/mensajeria/componer/', {'destinatario': self.u_docente.id, 'asunto': 'Otro', 'cuerpo': '',
                                         'guardar_borrador': '1'})
        otro = Mensaje.objects.get(asunto='Otro')
        c.post(f'/mensajeria/borrador/{otro.id}/', {'descartar': '1'})
        self.assertFalse(Mensaje.objects.filter(id=otro.id).exists())

    def test_papelera_de_cada_uno(self):
        self._enviar(self.rectora, self.u_docente)
        m = Mensaje.objects.get()
        doc, rec = self.cliente(self.u_docente), self.cliente(self.rectora)
        r = doc.post(f'/mensajeria/borrar/{m.id}/', {'vista_origen': 'bandeja_entrada'})
        self.assertEqual(r.status_code, 302)                                          # antes: dirección rota
        self.assertContains(doc.get('/mensajeria/papelera/'), 'Reunión')
        doc.post(f'/mensajeria/borrar-definitivo/{m.id}/')
        self.assertTrue(Mensaje.objects.filter(id=m.id).exists())                     # la rectora lo sigue teniendo
        self.assertContains(rec.get('/mensajeria/enviados/'), 'Reunión')
        self.assertNotContains(doc.get('/mensajeria/papelera/'), 'Reunión')
        rec.post('/mensajeria/acciones/', {'accion_uno': f'papelera:{m.id}', 'volver': '/mensajeria/enviados/'})
        rec.post('/mensajeria/acciones/', {'vaciar': '1', 'volver': '/mensajeria/papelera/'})
        self.assertFalse(Mensaje.objects.filter(id=m.id).exists())                    # ya nadie lo tiene

    def test_acciones_en_grupo_y_destacados(self):
        for k in range(3):
            self._enviar(self.rectora, self.u_docente, asunto=f'Aviso {k}')
        ids = list(Mensaje.objects.values_list('id', flat=True))
        doc = self.cliente(self.u_docente)
        doc.post('/mensajeria/acciones/', {'accion': 'leido', 'ids': ids[:2]})
        self.assertEqual(doc.get('/mensajeria/bandeja-entrada/').context['no_leidos'], 1)
        doc.post('/mensajeria/acciones/', {'accion': 'destacar', 'ids': [ids[0]]})
        r = doc.get('/mensajeria/destacados/')
        self.assertEqual([f['m'].id for f in r.context['filas']], [ids[0]])
        # La estrella es de cada quien
        self.assertEqual(self.cliente(self.rectora).get('/mensajeria/destacados/').context['filas'], [])
        # Una acción sobre mensajes ajenos no hace nada
        ajeno = self.cliente(self.estudiantes[0].user)
        ajeno.post('/mensajeria/acciones/', {'accion': 'papelera', 'ids': ids})
        self.assertFalse(Mensaje.objects.filter(eliminado_por_destinatario=True).exists())
        # Volver solo a direcciones de la misma página
        r = doc.post('/mensajeria/acciones/', {'accion': 'leido', 'ids': ids, 'volver': 'https://otro.sitio/'})
        self.assertEqual(r['Location'], '/mensajeria/bandeja-entrada/')

    def test_paginas_y_busqueda(self):
        for k in range(30):
            Mensaje.objects.create(colegio=self.a, remitente=self.rectora, destinatario=self.u_docente,
                                   asunto=f'Circular {k}', cuerpo='x')
        doc = self.cliente(self.u_docente)
        r = doc.get('/mensajeria/bandeja-entrada/')
        self.assertEqual(len(r.context['filas']), 25)
        self.assertEqual(len(doc.get('/mensajeria/bandeja-entrada/?pagina=2').context['filas']), 5)
        self.assertEqual(len(doc.get('/mensajeria/bandeja-entrada/?q=Circular 7').context['filas']), 1)
