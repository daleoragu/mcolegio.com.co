"""Los archivos privados (aula, chat) deben salir con enlace firmado, aunque settings tenga un dominio propio."""
import os
from unittest import mock

from django.test import SimpleTestCase, override_settings

ENTORNO = {'DO_SPACES_BUCKET_NAME': 'cubeta', 'DO_SPACES_REGION': 'atl1',
           'DO_SPACES_ACCESS_KEY': 'llave', 'DO_SPACES_SECRET_KEY': 'secreto'}


class EnlaceFirmado(SimpleTestCase):

    @override_settings(AWS_S3_CUSTOM_DOMAIN='cubeta.atl1.digitaloceanspaces.com', AWS_LOCATION='media')
    def test_privado_firma_el_enlace(self):
        from aula.almacen import privado
        with mock.patch.dict(os.environ, ENTORNO):
            url = privado().url('chat/2/foto.png')
        self.assertIn('aula/chat/2/foto.png', url)
        self.assertIn('Signature', url)          # X-Amz-Signature (v4) o Signature (v2)
