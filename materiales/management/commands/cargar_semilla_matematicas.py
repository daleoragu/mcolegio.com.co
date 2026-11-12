"""Igual que cargar_semilla, para Matemáticas (se deja por compatibilidad).

    python manage.py cargar_semilla_matematicas --usuario luis --grados 6 7
"""
from .cargar_semilla import Command as Base


class Command(Base):
    area_fija = 'MAT'
