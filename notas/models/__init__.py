# notas/models/__init__.py

# Este archivo importa todos los modelos de sus respectivos archivos
# y los hace disponibles para que puedan ser importados desde 'notas.models'.

from .perfiles import (Colegio, Curso, Docente, Estudiante, FichaEstudiante, FichaDocente,
                       HistorialMatricula, AdministradorColegio, Sede)

from .academicos import (
    AreaConocimiento, Materia, PeriodoAcademico, AsignacionDocente,
    Calificacion, NotaDetallada, IndicadorLogroPeriodo, ReporteParcial, Observacion,
    PlanDeMejoramiento, Asistencia, InasistenciasManualesPeriodo, EscalaValoracion, 
    ConfiguracionSistema, PublicacionBoletin, PublicacionBoletinFinal,PonderacionAreaMateria,
    PlanNotas, ComponenteEvaluacion, PonderacionGrado
)
from .comunicaciones import Mensaje, RegistroObservador, Notificacion
from .portal_models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, RecursoEducativo

# La variable __all__ es una buena práctica que define qué nombres
# se exportan cuando se hace 'from .models import *'.
# Se ha corregido una coma faltante.
__all__ = [
    'Colegio', 'Curso', 'Docente', 'Estudiante', 'FichaEstudiante', 'FichaDocente',
    'HistorialMatricula', 'AdministradorColegio', 'Sede',
    'AreaConocimiento', 'Materia', 'PeriodoAcademico', 'AsignacionDocente', 'EscalaValoracion', 
    'Calificacion', 'NotaDetallada', 'IndicadorLogroPeriodo', 'ReporteParcial', 'Observacion',
    'PlanDeMejoramiento', 'Asistencia', 'InasistenciasManualesPeriodo','PonderacionAreaMateria',
    'ConfiguracionSistema', 'PublicacionBoletin', 'PublicacionBoletinFinal', 'PlanNotas', 'ComponenteEvaluacion', 'PonderacionGrado',
    'RecursoEducativo', 'Mensaje', 'RegistroObservador', 'Notificacion',
    'DocumentoPublico', 'FotoGaleria', 'Noticia', 'ImagenCarrusel',
]
