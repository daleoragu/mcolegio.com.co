# notas/hashers.py
"""Contraseña inicial de las cuentas creadas en bloque (importaciones).

Django guarda cada contraseña con PBKDF2 de 1.000.000 de vueltas: en el servidor
eso cuesta cerca de un segundo por cuenta, y una importación de 500 estudiantes
pasaba el límite de 3 minutos del servidor y se caía sin guardar nada.

La contraseña inicial de esas cuentas es su mismo usuario (la plataforma la
entrega en el archivo de credenciales y pide cambiarla), así que guardarla con
menos vueltas no la hace más fácil de adivinar. Y no queda así: la primera vez
que la persona entra, Django la vuelve a guardar con el método normal (el
primero de PASSWORD_HASHERS), porque este no es el preferido.
"""
from django.contrib.auth.hashers import PBKDF2PasswordHasher, make_password


class PBKDF2InicialHasher(PBKDF2PasswordHasher):
    algorithm = 'pbkdf2_inicial'
    iterations = 20000


def clave_inicial(clave):
    """El hash de una contraseña inicial, rápido de calcular."""
    return make_password(clave, hasher='pbkdf2_inicial')
