# notas/tests/base.py
"""Datos de prueba: un colegio pequeño, listo para cada prueba."""
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from notas.models import (AdministradorColegio, AsignacionDocente, Colegio, Curso, Docente, EscalaValoracion,
                          Estudiante, IndicadorLogroPeriodo, Materia, PeriodoAcademico)

CLAVE = 'clave-de-prueba-123'


class ColegioDePrueba(TestCase):
    """Colegio A con rectora, docente, un 601 y Matemáticas (SABER 60 %, HACER 40 %)."""

    @classmethod
    def setUpTestData(cls):
        cls.a = Colegio.objects.create(nombre='Colegio A', slug='a', color_primario='#7B1E3A')
        cls.b = Colegio.objects.create(nombre='Colegio B', slug='b')
        for nombre, mi, ma in [('BAJO', '1.0', '2.9'), ('BÁSICO', '3.0', '3.9'),
                               ('ALTO', '4.0', '4.5'), ('SUPERIOR', '4.6', '5.0')]:
            EscalaValoracion.objects.create(colegio=cls.a, nombre_desempeno=nombre,
                                            valor_minimo=Decimal(mi), valor_maximo=Decimal(ma))
        cls.p1 = PeriodoAcademico.objects.create(colegio=cls.a, nombre='PRIMERO', ano_lectivo=2026,
                                                 fecha_inicio=datetime.date(2026, 2, 1),
                                                 fecha_fin=datetime.date(2026, 4, 1))
        cls.p2 = PeriodoAcademico.objects.create(colegio=cls.a, nombre='SEGUNDO', ano_lectivo=2026,
                                                 fecha_inicio=datetime.date(2026, 4, 2),
                                                 fecha_fin=datetime.date(2026, 6, 1))
        cls.super = User.objects.create_superuser('dueno', 'd@d.co', CLAVE)
        cls.rectora = User.objects.create_user('rectora', password=CLAVE, first_name='Rosa', last_name='Rector')
        AdministradorColegio.objects.create(user=cls.rectora, colegio=cls.a, cargo='RECTOR')
        cls.u_docente = User.objects.create_user('profe', password=CLAVE, first_name='Pedro', last_name='Profe')
        cls.docente = Docente.objects.create(colegio=cls.a, user=cls.u_docente)
        cls.curso = Curso.objects.create(colegio=cls.a, nombre='601', grado=6, subgrupo='1', director_grado=cls.docente)
        cls.materia = Materia.objects.create(colegio=cls.a, nombre='Matemáticas', usar_ponderacion_equitativa=False,
                                             porcentaje_ser=0, porcentaje_saber=60, porcentaje_hacer=40)
        cls.asig = AsignacionDocente.objects.create(colegio=cls.a, docente=cls.docente, materia=cls.materia,
                                                    curso=cls.curso)
        IndicadorLogroPeriodo.objects.create(colegio=cls.a, asignacion=cls.asig, periodo=cls.p1,
                                             descripcion='Resuelve problemas')
        cls.estudiantes = [cls.crear_estudiante(n) for n in ('ana', 'beto', 'caro')]

    @classmethod
    def crear_estudiante(cls, nombre, curso=None, colegio=None):
        u = User.objects.create_user(nombre, password=CLAVE, first_name=nombre.title(), last_name='Prueba')
        return Estudiante.objects.create(colegio=colegio or cls.a, user=u, curso=curso or cls.curso)

    def cliente(self, usuario=None, host='a.localhost'):
        c = Client(HTTP_HOST=host)
        if usuario is not None:
            c.force_login(usuario)
        return c
