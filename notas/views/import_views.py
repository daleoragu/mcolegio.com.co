# notas/views/import_views.py
import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db import transaction, IntegrityError
from django.http import HttpResponseNotFound
from django.utils.text import slugify
from unidecode import unidecode
from django.contrib.auth.hashers import make_password

try:
    from openpyxl import load_workbook
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

from ..models.perfiles import Estudiante, Docente, Curso, FichaEstudiante
from ..models.academicos import Materia, AreaConocimiento, PonderacionAreaMateria
from ..permisos import es_admin, es_admin_usuario

def es_superusuario(user):
    return es_admin_usuario(user)

@login_required
@user_passes_test(es_superusuario)
def importacion_vista(request):
    """
    Gestiona la carga y el procesamiento de archivos para la carga masiva de datos,
    asegurando que todos los datos estén asociados con el colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST' and 'archivo_importacion' in request.FILES:
        tipo_importacion = request.POST.get('tipo_importacion')
        archivo = request.FILES['archivo_importacion']

        try:
            with transaction.atomic():
                if tipo_importacion == 'estudiantes':
                    if not EXCEL_SUPPORT:
                        raise Exception("La librería 'openpyxl' es necesaria. Instálela con 'pip install openpyxl'.")
                    if not archivo.name.endswith('.xlsx'):
                        raise Exception("Para importar estudiantes, seleccione un archivo Excel válido (.xlsx).")
                    # Se llama a la versión súper optimizada
                    _procesar_excel_estudiantes_super_optimizado(request, archivo, request.colegio)
                
                elif tipo_importacion == 'materias':
                    if not EXCEL_SUPPORT:
                        raise Exception("La librería 'openpyxl' es necesaria. Instálela con 'pip install openpyxl'.")
                    if not archivo.name.endswith('.xlsx'):
                         raise Exception(f"Para importar materias, seleccione un archivo Excel válido (.xlsx).")
                    _procesar_excel_materias(request, archivo, request.colegio)

                elif tipo_importacion == 'docentes':
                    messages.warning(request, "La importación de docentes aún no está implementada para Excel.")
                    pass
                else:
                    raise Exception("El tipo de importación seleccionado no es válido.")

        except IntegrityError as e:
            messages.error(request, f"Error de integridad: Un dato (como un documento o username) podría ya existir. Detalles: {e}")
        except Exception as e:
            messages.error(request, f"Error durante el proceso: {e}")

        return redirect(request.META.get('HTTP_REFERER', 'notas:admin_dashboard'))

    return redirect('notas:admin_dashboard')

def _procesar_excel_estudiantes_super_optimizado(request, archivo, colegio):
    """
    Lógica SÚPER OPTIMIZADA. Realiza todas las operaciones de base de datos en bloque.
    Este es el enfoque síncrono más rápido posible.
    """
    creados_count, errores_count = 0, 0
    grupo_estudiantes, _ = Group.objects.get_or_create(name="Estudiantes")
    
    wb = load_workbook(archivo, data_only=True)
    sheet = wb.active
    map_tipo_doc = {v.upper(): k for k, v in FichaEstudiante.TIPO_DOCUMENTO_CHOICES}
    map_grupo_sang = {v: k for k, v in FichaEstudiante.GRUPO_SANGUINEO_CHOICES}
    
    # --- PASO 1: Preparar datos de usuario en memoria ---
    usuarios_a_crear = []
    datos_para_pasos_siguientes = []
    existing_usernames = set(User.objects.values_list('username', flat=True))

    for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        if not any(row) or not row[0] or not row[1]:
            continue
        row_data = list(row) + [None] * (20 - len(row))
        nombres, apellidos, _, _, nombre_curso, *_ = row_data

        try:
            primer_nombre = unidecode(str(nombres).split(' ')[0].lower())
            primer_apellido = unidecode(str(apellidos).split(' ')[0].lower())
            username_base = f"{slugify(primer_nombre)}.{slugify(primer_apellido)}"
            username_final = username_base
            counter = 1
            while username_final in existing_usernames:
                username_final = f"{username_base}{counter}"
                counter += 1
            existing_usernames.add(username_final)

            user = User(
                username=username_final, 
                password=make_password(username_final),
                first_name=str(nombres or '').strip().upper(), 
                last_name=str(apellidos or '').strip().upper()
            )
            usuarios_a_crear.append(user)
            datos_para_pasos_siguientes.append({'user_obj': user, 'curso_nombre': nombre_curso, 'data': row_data, 'fila_num': i})

        except Exception as e:
            messages.warning(request, f"Error preparando la fila {i}: {e}")
            errores_count += 1

    # --- PASO 2: Creación masiva de Usuarios ---
    if not usuarios_a_crear:
        messages.warning(request, "No se encontraron nuevos estudiantes para procesar.")
        return
        
    usuarios_creados = User.objects.bulk_create(usuarios_a_crear)
    mapa_usuarios = {u.username: u for u in usuarios_creados}
    grupo_estudiantes.user_set.add(*mapa_usuarios.values())

    # --- PASO 3: Preparar y crear masivamente Estudiantes y Fichas ---
    estudiantes_a_crear = []
    fichas_a_crear = []
    mapa_cursos = {c.nombre: c for c in Curso.objects.filter(colegio=colegio)}

    for datos in datos_para_pasos_siguientes:
        fila_num = datos['fila_num']
        try:
            user_obj = mapa_usuarios.get(datos['user_obj'].username)
            if not user_obj: continue

            curso_obj = mapa_cursos.get(str(datos['curso_nombre']).strip().upper())
            if not curso_obj:
                raise ValueError(f"El curso '{datos['curso_nombre']}' no existe en este colegio.")

            estudiante_obj = Estudiante(user=user_obj, curso=curso_obj, colegio=colegio)
            estudiantes_a_crear.append(estudiante_obj)
            # Guardamos la referencia para el siguiente paso
            datos['estudiante_obj_preparado'] = estudiante_obj

        except Exception as e:
            messages.warning(request, f"Error preparando datos de Estudiante en fila {fila_num}: {e}")
            errores_count += 1
    
    # Creación masiva de Estudiantes
    estudiantes_creados = Estudiante.objects.bulk_create(estudiantes_a_crear)
    mapa_estudiantes = {e.user.username: e for e in estudiantes_creados}

    # Preparación masiva de Fichas
    for datos in datos_para_pasos_siguientes:
        fila_num = datos['fila_num']
        try:
            estudiante_final = mapa_estudiantes.get(datos['user_obj'].username)
            if not estudiante_final: continue

            (_, _, tipo_doc_str, num_doc, _, fecha_nac_str, 
             lugar_nac, eps, grupo_sang_str, enfermedades, nombre_padre, cel_padre,
             nombre_madre, cel_madre, nombre_acud, cel_acud, email_acud, 
             espera_porteria_str, colegio_ant, grado_ant) = datos['data']

            fecha_nacimiento = None
            if isinstance(fecha_nac_str, datetime): fecha_nacimiento = fecha_nac_str.date()
            elif isinstance(fecha_nac_str, str):
                try: fecha_nacimiento = datetime.strptime(fecha_nac_str, '%Y-%m-%d').date()
                except (ValueError, TypeError): fecha_nacimiento = None

            ficha = FichaEstudiante(
                estudiante=estudiante_final,
                tipo_documento=map_tipo_doc.get(str(tipo_doc_str).strip().upper(), 'OT') if tipo_doc_str else 'OT',
                numero_documento=str(num_doc).strip() if num_doc else None,
                fecha_nacimiento=fecha_nacimiento,
                lugar_nacimiento=lugar_nac, eps=eps,
                grupo_sanguineo=map_grupo_sang.get(str(grupo_sang_str).strip(), None) if grupo_sang_str else None,
                enfermedades_alergias=enfermedades, nombre_padre=nombre_padre, celular_padre=cel_padre,
                nombre_madre=nombre_madre, celular_madre=cel_madre, nombre_acudiente=nombre_acud,
                celular_acudiente=cel_acud, email_acudiente=email_acud,
                espera_en_porteria=True if espera_porteria_str and 'SI' in str(espera_porteria_str).upper() else False,
                colegio_anterior=colegio_ant, grado_anterior=grado_ant
            )
            fichas_a_crear.append(ficha)
        except Exception as e:
            messages.warning(request, f"Error preparando Ficha en fila {fila_num}: {e}")
            errores_count += 1

    # Creación masiva de Fichas
    if fichas_a_crear:
        FichaEstudiante.objects.bulk_create(fichas_a_crear)
    
    creados_count = len(fichas_a_crear)
    messages.success(request, f"Proceso de estudiantes completado. Creados: {creados_count}. Errores: {errores_count}.")


def _procesar_excel_materias(request, archivo, colegio):
    """Lógica para procesar el archivo Excel de materias para el colegio actual."""
    creadas, errores, asociaciones_creadas = 0, 0, 0
    wb = load_workbook(archivo, data_only=True)
    sheet = wb.active
    for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        try:
            if not any(row): continue
            nombre_materia, abreviatura, nombre_area = row[:3]
            
            nombre_materia = str(nombre_materia).strip().upper()
            nombre_area = str(nombre_area).strip().upper()

            if not nombre_materia or not nombre_area:
                continue

            materia_obj, materia_fue_creada = Materia.objects.get_or_create(
                nombre=nombre_materia,
                colegio=colegio,
                defaults={'abreviatura': str(abreviatura).strip().upper() if abreviatura else None}
            )
            if materia_fue_creada:
                creadas += 1

            area_obj, _ = AreaConocimiento.objects.get_or_create(nombre=nombre_area, colegio=colegio)

            _, ponderacion_fue_creada = PonderacionAreaMateria.objects.get_or_create(
                area=area_obj,
                materia=materia_obj,
                colegio=colegio,
                defaults={'peso_porcentual': 0.00}
            )
            if ponderacion_fue_creada:
                asociaciones_creadas += 1

        except Exception as e:
            messages.warning(request, f"Error en la fila {i} del Excel de materias: {e}")
            errores += 1
            
    messages.success(request, f"Proceso de materias completado. Materias creadas: {creadas}. Asociaciones a áreas creadas: {asociaciones_creadas}. Errores: {errores}.")

def _procesar_csv_docentes(request, reader, colegio):
    """Lógica para procesar el CSV de docentes para el colegio actual (preservada)."""
    creados, errores = 0, 0
    grupo_docentes, _ = Group.objects.get_or_create(name="Docentes")
    for i, row in enumerate(reader, 2):
        try:
            if not any(row): continue
            nombres, primer_apellido, segundo_apellido, documento, email, *_ = row
            if not documento: raise ValueError("El número de documento es obligatorio.")
            if User.objects.filter(username=documento).exists(): continue
            user = User.objects.create_user(username=documento, password=documento, email=email, first_name=str(nombres or '').upper(), last_name=f"{str(primer_apellido or '').upper()} {str(segundo_apellido or '').upper()}".strip())
            user.groups.add(grupo_docentes)
            Docente.objects.create(user=user, colegio=colegio)
            creados += 1
        except Exception as e:
            messages.warning(request, f"Error en la fila {i} del CSV de docentes: {e}")
            errores += 1
    messages.success(request, f"Proceso de docentes completado. Creados: {creados}. Errores: {errores}.")
