/**
 * Script for handling the grade entry page with a spreadsheet style.
 * @version 12.4 - Sincronización robusta con Modal PIAR y window._incData
 */
document.addEventListener('DOMContentLoaded', function () {
    // --- DOM ELEMENTS AND INITIAL DATA ---
    const container = document.querySelector('.container-notas');
    if (!container) return;

    const tablaCalificaciones = document.getElementById('tabla-calificaciones');
    const guardarTodoBtn = document.getElementById('guardarTodoBtn');
    const statusIndicator = document.getElementById('status-indicator');
    const estudiantesDataEl = document.getElementById('estudiantes-data-json');
    const urlInasistenciasEl = document.getElementById('url-get-inasistencias');
    const asignacionDetailsEl = document.getElementById('asignacion-details');
    
    // --- INICIO: LEER DATOS DE LA ESCALA DE VALORACIÓN ---
    const escalaDataEl = document.getElementById('escala-valoracion-json');
    let escalaValoracion = [];
    if (escalaDataEl) {
        try {
            escalaValoracion = JSON.parse(escalaDataEl.textContent.trim() || '[]');
        } catch (e) {
            console.error("Error parsing escala de valoración JSON:", e);
        }
    }

    // --- INICIO: LEER DATOS DE INCLUSIÓN ---
    const inclusionDataEl = document.getElementById('inclusion-data-json');
    let inclusionData = {};
    if (inclusionDataEl) {
        try {
            inclusionData = JSON.parse(inclusionDataEl.textContent.trim() || '{}');
        } catch (e) {
            console.error("Error parsing inclusion JSON:", e);
        }
    }
    // --- FIN: LEER DATOS ---

    if (!tablaCalificaciones || !estudiantesDataEl || !urlInasistenciasEl || !asignacionDetailsEl) {
        console.error("Faltan elementos HTML esenciales para la inicialización del script.");
        return;
    }

    const asignacionData = {
        id: container.dataset.asignacionId,
        periodoId: container.dataset.periodoId,
        csrfToken: container.dataset.csrfToken,
        guardarUrl: container.dataset.guardarUrl,
        inasistenciasUrl: urlInasistenciasEl.dataset.url
    };

    let estudiantesData = [];
    try {
        estudiantesData = JSON.parse(estudiantesDataEl.textContent.trim() || '[]');
        
        // Fusionar los datos de inclusión en el array principal de estudiantes al inicio
        estudiantesData.forEach(est => {
            if (inclusionData[est.id]) {
                est.es_inclusion = inclusionData[est.id].es_inclusion;
                est.observacion_inclusion = inclusionData[est.id].obs || "";
            }
        });
    } catch (e) {
        console.error("Error parsing student JSON:", e);
        return;
    }

    let hayCambiosSinGuardar = false;
    let descripcionesColumnas = { ser: {}, saber: {}, hacer: {} };

    // --- PLAN DE NOTAS: columnas de cada componente, con su nombre ---------
    // Las notas se guardan sin huecos (si falta la nota 2, se guarda [1, 3]).
    // Antes se pintaban por posición y la nota 3 caía en la columna 2. Ahora
    // cada nota va a la columna que tiene su mismo nombre.
    const planNotasEl = document.getElementById('plan-notas-json');
    let planNotas = null;
    if (planNotasEl) {
        try { planNotas = JSON.parse(planNotasEl.textContent.trim() || 'null'); }
        catch (e) { console.error('Error leyendo el plan de notas:', e); }
    }
    function escaparHtml(texto) {
        return String(texto == null ? '' : texto)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    if (planNotas) {
        for (const tipo of ['ser', 'saber', 'hacer']) {
            const columnas = Array.isArray(planNotas[tipo]) ? planNotas[tipo] : [];
            if (!columnas.length) continue;
            columnas.forEach((nombre, i) => { descripcionesColumnas[tipo][i] = nombre; });
            estudiantesData.forEach(est => {
                const guardadas = (est.notas && est.notas[tipo]) || [];
                const ubicadas = columnas.map(nombre => ({ valor: '', descripcion: nombre }));
                const usadas = new Array(columnas.length).fill(false);
                const sinLugar = [];
                guardadas.forEach(nota => {
                    const i = columnas.findIndex((c, k) => !usadas[k] && c === nota.descripcion);
                    if (i >= 0) { ubicadas[i].valor = nota.valor; usadas[i] = true; }
                    else sinLugar.push(nota);
                });
                sinLugar.forEach(nota => {
                    const i = usadas.indexOf(false);
                    if (i >= 0) { ubicadas[i].valor = nota.valor; usadas[i] = true; }
                });
                if (!est.notas) est.notas = { ser: [], saber: [], hacer: [] };
                est.notas[tipo] = ubicadas;
            });
        }
    }

    // --- COMPONENTES QUE SE MUESTRAN ------------------------------------------
    // Solo los que tienen porcentaje (> 0 %). Una materia programada con un
    // solo componente al 100 % muestra solo ese. Si todos están en 0 %
    // (materia informativa), se muestran los tres.
    const TIPOS = ['ser', 'saber', 'hacer'];
    let configMateria = {};
    try {
        const el = document.getElementById('config-materia-json');
        configMateria = JSON.parse((el && el.textContent.trim()) || '{}');
    } catch (e) { configMateria = {}; }

    function porcentajesActuales() {
        const salida = {};
        TIPOS.forEach(tipo => {
            const input = document.getElementById(`p-${tipo}`);
            const dato = asignacionDetailsEl.dataset['p' + tipo.charAt(0).toUpperCase() + tipo.slice(1)];
            salida[tipo] = (parseFloat(input ? input.value : dato) || 0) / 100;
        });
        return salida;
    }
    function tiposVisibles() {
        const p = porcentajesActuales();
        const activos = TIPOS.filter(t => p[t] > 0);
        return activos.length ? activos : TIPOS.slice();
    }
    function etiquetaComponente(tipo) {
        const propia = (configMateria['lbl_' + tipo] || '').trim();
        return (propia || tipo).toUpperCase();
    }
    let tiposPintados = [];

    // Helper para reemplazar los alert() nativos
    function mostrarNotificacion(mensaje, esError = false) {
        const div = document.createElement('div');
        div.className = `alert ${esError ? 'alert-danger' : 'alert-success'} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3 shadow-lg`;
        div.style.zIndex = '9999';
        div.innerHTML = `
            <strong>${esError ? '<i class="fas fa-exclamation-triangle me-2"></i>Error:' : '<i class="fas fa-check-circle me-2"></i>Éxito:'}</strong> ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(div);
        setTimeout(() => { if (div.parentNode) div.parentNode.removeChild(div); }, 4500);
    }

    function sincronizarDatosDesdeDOM() {
        if (!tablaCalificaciones) return;
        
        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
            const estId = fila.dataset.estudianteId;
            const estudiante = estudiantesData.find(e => e.id.toString() === estId.toString());
            
            if (estudiante) {
                // Guardar inasistencias en memoria
                const inasistInput = fila.querySelector('.input-inasistencia');
                if (inasistInput) {
                    estudiante.inasistencias = inasistInput.value;
                }

                // Observación de la asignatura (opcional)
                const obsInput = fila.querySelector('.input-observacion');
                if (obsInput) {
                    estudiante.observacion = obsInput.value;
                }

                // Intentar leer el input oculto de inclusión si existe en la fila (como respaldo)
                const inputInclusion = fila.querySelector('.input-observacion-inclusion');
                if (inputInclusion) {
                    estudiante.observacion_inclusion = inputInclusion.value;
                }

                // Guardar notas digitadas en memoria
                for (const tipo of tiposPintados) {
                    const inputs = fila.querySelectorAll(`.input-nota[data-tipo="${tipo}"]`);
                    
                    if (!estudiante.notas[tipo]) {
                        estudiante.notas[tipo] = [];
                    }
                    
                    inputs.forEach((input, index) => {
                        if (!estudiante.notas[tipo][index]) {
                            estudiante.notas[tipo][index] = { valor: '', descripcion: '' };
                        }
                        estudiante.notas[tipo][index].valor = input.value;
                    });
                    
                    estudiante.notas[tipo].length = inputs.length;
                }
            }
        });
    }

    function renderizarTabla() {
        const hayIndicadores = tablaCalificaciones.dataset.hayIndicadores === 'true';
        if (!hayIndicadores) return;

        const maxNotas = { ser: 0, saber: 0, hacer: 0 };
        estudiantesData.forEach(est => {
            for (const tipo in maxNotas) {
                const notasCount = est.notas[tipo]?.length || 0;
                if (notasCount > maxNotas[tipo]) maxNotas[tipo] = notasCount;
                est.notas[tipo]?.forEach((nota, i) => {
                    if (nota.descripcion && !descripcionesColumnas[tipo][i]) {
                        descripcionesColumnas[tipo][i] = nota.descripcion;
                    }
                });
            }
        });

        for (const tipo in maxNotas) {
            const delPlan = Object.keys(descripcionesColumnas[tipo]).length;
            if (delPlan > maxNotas[tipo]) maxNotas[tipo] = delPlan;
            if (maxNotas[tipo] === 0) maxNotas[tipo] = 1;
        }

        const visibles = tiposVisibles();
        tiposPintados = visibles;
        let headerHtml = `<thead class="table-light"><tr><th rowspan="2" class="text-center align-middle">#</th><th rowspan="2" class="align-middle">Estudiante</th>`;
        for (const tipo of visibles) {
            headerHtml += `<th colspan="${maxNotas[tipo] + 1}" class="text-center comp-${tipo}">${escaparHtml(etiquetaComponente(tipo))} <button class="btn btn-outline-success btn-sm btn-add-col ms-1" data-tipo="${tipo}" title="Añadir columna de nota">+</button><button class="btn btn-outline-danger btn-sm btn-remove-col ms-1" data-tipo="${tipo}" title="Quitar última columna">-</button></th>`;
        }
        headerHtml += `<th rowspan="2" class="text-center align-middle">Definitiva</th><th rowspan="2" class="text-center align-middle">Inasistencias</th><th rowspan="2" class="text-center align-middle th-observacion">Observación<br><span class="small fw-normal text-muted">(opcional)</span></th></tr><tr>`;

        for (const tipo of visibles) {
            for (let i = 0; i < maxNotas[tipo]; i++) {
                const desc = escaparHtml(descripcionesColumnas[tipo][i] || '');
                headerHtml += `<th class="text-center th-nota" data-tipo="${tipo}" data-col-index="${i}" style="cursor: pointer;" title="Clic para describir esta columna">
                                 <span class="col-title text-primary"><i class="fas fa-edit me-1 small"></i>n${i + 1}</span><br>
                                 <span class="col-desc small fw-normal text-muted">${desc}</span>
                               </th>`;
            }
            headerHtml += `<th class="text-center align-middle prom-header">Prom.</th>`;
        }
        headerHtml += `</tr></thead>`;

        let bodyHtml = `<tbody>`;
        if (estudiantesData.length === 0) {
            const colspan = 5 + visibles.reduce((n, t) => n + maxNotas[t] + 1, 0);
            bodyHtml += `<tr><td colspan="${colspan}" class="text-center text-muted py-4">No hay estudiantes en este curso.</td></tr>`;
        } else {
            estudiantesData.forEach((estudiante, index) => {
                // Marcador visual para estudiante de inclusión PIAR
                const badgeInclusion = estudiante.es_inclusion ? ' <span class="badge bg-info text-dark ms-1" title="Estudiante de Inclusión (PIAR)"><i class="fas fa-universal-access"></i></span>' : '';
                
                bodyHtml += `<tr data-estudiante-id="${estudiante.id}">
                                <td class="text-center align-middle">${index + 1}</td>
                                <td class="align-middle fw-bold">
                                    ${estudiante.nombre_completo}${badgeInclusion}
                                    <input type="hidden" class="input-observacion-inclusion" value="${estudiante.observacion_inclusion || ''}">
                                </td>`;
                for (const tipo of visibles) {
                    for (let i = 0; i < maxNotas[tipo]; i++) {
                        const nota = estudiante.notas[tipo]?.[i]?.valor || '';
                        bodyHtml += `<td><input type="text" class="form-control form-control-sm text-center input-nota" data-tipo="${tipo}" value="${nota}" inputmode="decimal"></td>`;
                    }
                    bodyHtml += `<td class="text-center align-middle fw-bold prom-celda" data-tipo="${tipo}">0.0</td>`;
                }
                bodyHtml += `<td class="text-center align-middle fw-bolder def-celda fs-6">0.0</td>
                             <td class="align-middle">
                               <div class="input-group input-group-sm">
                                 <input type="number" class="form-control text-center input-inasistencia" min="0" value="${estudiante.inasistencias || 0}">
                                 <button class="btn btn-outline-secondary sync-inasistencias" type="button" title="Sincronizar faltas automáticas">
                                   <i class="fas fa-sync-alt"></i>
                                 </button>
                               </div>
                             </td>
                             <td class="align-middle td-observacion">
                               <textarea class="form-control form-control-sm input-observacion" rows="2" maxlength="600"
                                         placeholder="Escriba una observación si la necesita…"
                                         title="Opcional. Sale en el boletín debajo de los indicadores de esta asignatura.">${escaparHtml(estudiante.observacion || '')}</textarea>
                             </td></tr>`;
            });
        }
        bodyHtml += `</tbody>`;
        tablaCalificaciones.innerHTML = headerHtml + bodyHtml;
        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(actualizarTodosLosPromedios);
    }

    // --- La escala de valoración que declaró el colegio manda -----------------
    // Sin escala propia se usa la de siempre (1 a 5), la misma que usa el servidor.
    const ESCALA = (escalaValoracion && escalaValoracion.length ? escalaValoracion : [
        { nombre_desempeno: 'BAJO', valor_minimo: 1.0, valor_maximo: 2.9 },
        { nombre_desempeno: 'BÁSICO', valor_minimo: 3.0, valor_maximo: 3.9 },
        { nombre_desempeno: 'ALTO', valor_minimo: 4.0, valor_maximo: 4.5 },
        { nombre_desempeno: 'SUPERIOR', valor_minimo: 4.6, valor_maximo: 5.0 },
    ]).map(e => ({ nombre: e.nombre_desempeno, min: parseFloat(e.valor_minimo), max: parseFloat(e.valor_maximo) }))
      .sort((a, b) => a.min - b.min);
    const NOTA_MIN = Math.min(...ESCALA.map(e => e.min));
    const NOTA_MAX = Math.max(...ESCALA.map(e => e.max));
    // Colores por posición en la escala (el más bajo en rojo, el más alto en azul),
    // así sirven para cualquier nombre de desempeño y cualquier número de niveles.
    const COLORES = [['#dc3545', '#fff'], ['#ffc107', '#212529'], ['#28a745', '#fff'], ['#0d6efd', '#fff']];
    function redondear(x, d) { const f = Math.pow(10, d); return Math.round((x + Number.EPSILON) * f) / f; }
    function nivelDe(nota) {
        // Con la nota a una décima (como se lee), el nivel es el último cuyo mínimo no la supera:
        // así no hay huecos entre 2,9 y 3,0.
        const n = redondear(nota, 1);
        let k = -1;
        ESCALA.forEach((e, i) => { if (n >= e.min) k = i; });
        return k;
    }
    window.rangoNotas = { min: NOTA_MIN, max: NOTA_MAX };

    function actualizarTodosLosPromedios(fila) {
        tiposPintados.forEach(tipo => {
            const inputs = fila.querySelectorAll(`.input-nota[data-tipo="${tipo}"]`);
            const promCelda = fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`);
            let suma = 0, count = 0;
            inputs.forEach(input => {
                const valor = parseFloat(input.value.replace(',', '.'));
                const valida = !isNaN(valor) && valor >= NOTA_MIN && valor <= NOTA_MAX;
                if (valida) { suma += valor; count++; }
                // Lo escrito fuera de la escala no cuenta: se marca para que se note.
                input.classList.toggle('is-invalid', input.value.trim() !== '' && !valida);
                input.title = input.value.trim() !== '' && !valida
                    ? `Fuera de la escala del colegio (${NOTA_MIN} a ${NOTA_MAX}): no cuenta` : '';
            });
            // Igual que el servidor: promedio a 2 decimales; se muestra a 1.
            const prom = count > 0 ? redondear(suma / count, 2) : 0;
            promCelda.dataset.valor = prom;
            promCelda.textContent = prom.toFixed(1);
        });
        actualizarDefinitiva(fila);
    }

    function actualizarDefinitiva(fila) {
        const defCelda = fila.querySelector('.def-celda');
        let definitiva = 0;

        // Misma regla del servidor: promedio de cada componente × su porcentaje.
        const porcentajes = porcentajesActuales();
        tiposPintados.forEach(tipo => {
            const celda = fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`);
            const prom = parseFloat(celda.dataset.valor !== undefined ? celda.dataset.valor : celda.textContent);
            if (!isNaN(prom)) definitiva += prom * porcentajes[tipo];
        });
        definitiva = redondear(definitiva, 2);
        defCelda.textContent = definitiva.toFixed(1);

        defCelda.className = 'text-center align-middle fw-bolder def-celda fs-6';
        defCelda.style.backgroundColor = '';
        defCelda.style.color = '';
        const k = nivelDe(definitiva);
        if (k >= 0) {
            const pos = ESCALA.length > 1 ? Math.round(k * (COLORES.length - 1) / (ESCALA.length - 1)) : COLORES.length - 1;
            defCelda.style.backgroundColor = COLORES[pos][0];
            defCelda.style.color = COLORES[pos][1];
            defCelda.title = ESCALA[k].nombre;
        } else {
            defCelda.classList.add('desempeno-default');
            defCelda.title = '';
        }
    }

    // Exportar actualizarStatus globalmente para que el Modal PIAR lo pueda usar
    window.actualizarStatus = function(estado) {
        if (!statusIndicator) return;
        statusIndicator.className = 'status-indicator badge ms-3 fs-6 p-2';
        const periodoCerrado = document.querySelector('.card-footer .text-warning');
        switch (estado) {
            case 'pending':
                statusIndicator.classList.add('bg-warning', 'text-dark');
                statusIndicator.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Cambios sin guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado && tablaCalificaciones.dataset.hayIndicadores === 'true') {
                    guardarTodoBtn.disabled = false;
                }
                break;
            case 'saved':
                statusIndicator.classList.add('bg-success');
                statusIndicator.innerHTML = '<i class="fas fa-check-circle me-1"></i>Cambios guardados';
                hayCambiosSinGuardar = false;
                if (guardarTodoBtn) guardarTodoBtn.disabled = true;
                break;
            case 'error':
                statusIndicator.classList.add('bg-danger');
                statusIndicator.innerHTML = '<i class="fas fa-times-circle me-1"></i>Error al guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado) guardarTodoBtn.disabled = false;
                break;
        }
    };

    tablaCalificaciones.addEventListener('input', e => {
        if (e.target.classList.contains('input-nota') || e.target.classList.contains('input-inasistencia') || e.target.classList.contains('input-observacion') || e.target.classList.contains('input-observacion-inclusion')) {
            if (e.target.classList.contains('input-nota')) {
                actualizarTodosLosPromedios(e.target.closest('tr'));
            }
            window.actualizarStatus('pending');
        }
    });

    const panelPonderacion = document.getElementById('panel-ponderacion');
    if (panelPonderacion) {
        panelPonderacion.addEventListener('input', () => {
            if (tiposVisibles().join() !== tiposPintados.join()) {
                sincronizarDatosDesdeDOM();
                renderizarTabla();
            } else {
                tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
                    actualizarDefinitiva(fila);
                });
            }
            window.actualizarStatus('pending');
        });
    }
    
    tablaCalificaciones.addEventListener('click', async e => {
        const btnAdd = e.target.closest('.btn-add-col');
        const btnRemove = e.target.closest('.btn-remove-col');
        const thNota = e.target.closest('.th-nota');
        const btnSync = e.target.closest('.sync-inasistencias');

        if (btnAdd) {
            sincronizarDatosDesdeDOM();
            const tipo = btnAdd.dataset.tipo;
            const nueva = tablaCalificaciones.querySelectorAll(`thead .th-nota[data-tipo="${tipo}"]`).length;
            if (!descripcionesColumnas[tipo][nueva]) descripcionesColumnas[tipo][nueva] = `Nota ${nueva + 1}`;
            if (estudiantesData.length > 0) {
                estudiantesData.forEach(est => {
                    if (!est.notas[tipo]) est.notas[tipo] = [];
                    while (est.notas[tipo].length < nueva) est.notas[tipo].push({ valor: '', descripcion: '' });
                    est.notas[tipo].push({ valor: '', descripcion: '' });
                });
            }
            renderizarTabla();
            window.actualizarStatus('pending');
        }
        if (btnRemove) {
            sincronizarDatosDesdeDOM();
            const tipo = btnRemove.dataset.tipo;
            estudiantesData.forEach(est => {
                if (est.notas[tipo]?.length > 1) est.notas[tipo].pop();
            });
            const lastIndex = Object.keys(descripcionesColumnas[tipo]).length - 1;
            if (lastIndex >= 0) delete descripcionesColumnas[tipo][lastIndex];
            renderizarTabla();
            window.actualizarStatus('pending');
        }
        if (thNota) {
            const tipo = thNota.dataset.tipo;
            const colIndex = thNota.dataset.colIndex;
            const descSpan = thNota.querySelector('.col-desc');
            const descActual = descripcionesColumnas[tipo][colIndex] || '';
            const nuevaDesc = prompt(`Escriba el nombre o descripción para esta columna (ej: "Examen Final"):`, descActual);
            if (nuevaDesc !== null) {
                descripcionesColumnas[tipo][colIndex] = nuevaDesc.trim();
                descSpan.textContent = nuevaDesc.trim();
                window.actualizarStatus('pending');
            }
        }
        if (btnSync) {
            const fila = btnSync.closest('tr');
            const estudianteId = fila.dataset.estudianteId;
            const inasistenciaInput = fila.querySelector('.input-inasistencia');
            const icon = btnSync.querySelector('i');
            
            icon.classList.add('fa-spin');
            btnSync.disabled = true;

            const url = `${asignacionData.inasistenciasUrl}?asignacion_id=${asignacionData.id}&periodo_id=${asignacionData.periodoId}&estudiante_id=${estudianteId}`;
            
            try {
                const response = await fetch(url);
                const data = await response.json();
                if (data.status === 'success') {
                    inasistenciaInput.value = data.inasistencias_auto;
                    window.actualizarStatus('pending');
                } else {
                    mostrarNotificacion('Error al sincronizar: ' + data.message, true);
                }
            } catch (error) {
                console.error('Error en fetch de inasistencias:', error);
                mostrarNotificacion('No se pudo conectar con el servidor para obtener las inasistencias.', true);
            } finally {
                icon.classList.remove('fa-spin');
                btnSync.disabled = false;
            }
        }
    });

    // --- GUARDAR: lo usan el botón y el autoguardado -------------------------
    let guardando = false;
    let cambiosDuranteGuardado = false;

    async function guardar(silencioso) {
        if (!guardarTodoBtn) return false;
        if (guardando) { cambiosDuranteGuardado = true; return false; }
        if (!navigator.onLine) {
            mostrarEstadoConexion();
            if (!silencioso) mostrarNotificacion('No hay internet. Los cambios quedaron guardados en este equipo y se subirán al volver la conexión.', true);
            return false;
        }
        guardando = true;
        cambiosDuranteGuardado = false;
        guardarTodoBtn.disabled = true;
        guardarTodoBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
        if (silencioso) mostrarEstado('guardando');

        // Sincronizar todos los inputs visibles de la tabla
        sincronizarDatosDesdeDOM();
        
        const payload = {
            asignacion_id: asignacionData.id,
            periodo_id: asignacionData.periodoId,
            estudiantes: [],
            porcentajes: {},
            plan: {}
        };
        // Las columnas tal como están en pantalla: se guardan como el plan de
        // notas, para que el Excel y la próxima apertura salgan iguales.
        for (const tipo of tiposPintados) {
            const n = tablaCalificaciones.querySelectorAll(`thead .th-nota[data-tipo="${tipo}"]`).length;
            payload.plan[tipo] = Array.from({ length: n }, (_, i) => descripcionesColumnas[tipo][i] || `Nota ${i + 1}`);
        }
        
        const pSerInput = document.getElementById('p-ser');
        if (pSerInput) {
            payload.porcentajes = {
                ser: document.getElementById('p-ser').value,
                saber: document.getElementById('p-saber').value,
                hacer: document.getElementById('p-hacer').value
            }
        }

        estudiantesData.forEach(est => {
            // CORRECCIÓN CLAVE: Buscar forzosamente en `window._incData`
            // ya que el modal de PIAR almacena los cambios recientes allí.
            let obsFinal = est.observacion_inclusion || "";
            if (window._incData && window._incData[est.id]) {
                obsFinal = window._incData[est.id].obs || "";
            }

            const datosEst = {
                id: est.id.toString(),
                notas: { ser: [], saber: [], hacer: [] },
                inasistencias: est.inasistencias || "0",
                observacion: est.observacion || "",
                observacion_inclusion: obsFinal // Enviamos el indicador PIAR actualizado
            };
            
            for (const tipo of ['ser', 'saber', 'hacer']) {
                if (est.notas[tipo]) {
                    est.notas[tipo].forEach((nota, index) => {
                        const valor = (nota.valor || '').replace(',', '.').trim();
                        if (valor) {
                            const descripcion = descripcionesColumnas[tipo][index] || `Nota ${index + 1}`;
                            datosEst.notas[tipo].push({ descripcion, valor });
                        }
                    });
                }
            }
            payload.estudiantes.push(datosEst);
        });

        let ok = false;
        try {
            const response = await fetch(asignacionData.guardarUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': asignacionData.csrfToken },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            
            if (!response.ok) throw new Error(result.message || 'Error del servidor');
            ok = true;
            if (cambiosDuranteGuardado) {
                window.actualizarStatus('pending');      // se digitó algo mientras guardaba
            } else {
                window.actualizarStatus('saved');
                borrarBorrador();
            }
            if (silencioso) mostrarEstado('autoguardado');
            else mostrarNotificacion('Todas las calificaciones y observaciones PIAR fueron guardadas exitosamente.', false);
        } catch (error) {
            console.error('Error al guardar:', error);
            window.actualizarStatus('error');
            if (!navigator.onLine) mostrarEstadoConexion();
            else mostrarNotificacion('Error al guardar: ' + error.message +
                (silencioso ? ' Sus cambios siguen en este equipo; intente con «Guardar Cambios».' : ''), true);
        } finally {
            guardando = false;
            guardarTodoBtn.innerHTML = '<i class="fas fa-save me-2"></i>Guardar Cambios';
            guardarTodoBtn.disabled = !hayCambiosSinGuardar;
            if (cambiosDuranteGuardado) programarAutoguardado();
        }
        return ok;
    }

    guardarTodoBtn?.addEventListener('click', function () {
        clearTimeout(temporizadorAuto);
        guardar(false);
    });

    // --- AUTOGUARDADO Y RESPALDO EN ESTE EQUIPO -------------------------------
    // 1. Cada cambio se copia al navegador (localStorage) al instante: si se va
    //    la luz o el internet, al volver a abrir la planilla se ofrece recuperarlo.
    // 2. A los 20 segundos sin digitar, se guarda solo en la plataforma.
    // 3. Sin internet no se intenta: se avisa y se sube al volver la conexión.
    const SEGUNDOS_AUTOGUARDADO = 20;
    const claveBorrador = `mcolegio-planilla-${asignacionData.id}-${asignacionData.periodoId}`;
    let temporizadorAuto = null;
    let temporizadorBorrador = null;
    const puedeGuardar = !!guardarTodoBtn && tablaCalificaciones.dataset.hayIndicadores === 'true';

    function mostrarEstado(tipo) {
        if (!statusIndicator) return;
        const hora = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
        if (tipo === 'guardando') {
            statusIndicator.className = 'status-indicator badge ms-3 fs-6 p-2 bg-info text-dark';
            statusIndicator.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando…';
        } else if (tipo === 'autoguardado') {
            statusIndicator.innerHTML = `<i class="fas fa-check-circle me-1"></i>Guardado solo · ${hora}`;
        }
    }
    function mostrarEstadoConexion() {
        if (!statusIndicator) return;
        if (!navigator.onLine) {
            statusIndicator.className = 'status-indicator badge ms-3 fs-6 p-2 bg-secondary';
            statusIndicator.innerHTML = '<i class="fas fa-wifi me-1"></i>Sin internet · los cambios quedan en este equipo';
        }
    }
    function programarAutoguardado() {
        if (!puedeGuardar) return;
        clearTimeout(temporizadorAuto);
        temporizadorAuto = setTimeout(() => { if (hayCambiosSinGuardar) guardar(true); }, SEGUNDOS_AUTOGUARDADO * 1000);
    }
    function guardarBorrador() {
        if (!puedeGuardar) return;
        clearTimeout(temporizadorBorrador);
        temporizadorBorrador = setTimeout(() => {
            sincronizarDatosDesdeDOM();
            const borrador = {
                fecha: Date.now(),
                columnas: descripcionesColumnas,
                estudiantes: estudiantesData.map(est => ({
                    id: est.id,
                    inasistencias: est.inasistencias,
                    observacion: est.observacion || '',
                    notas: Object.fromEntries(['ser', 'saber', 'hacer'].map(t =>
                        [t, (est.notas[t] || []).map(n => (n && n.valor) || '')]))
                }))
            };
            try { localStorage.setItem(claveBorrador, JSON.stringify(borrador)); } catch (e) { /* sin espacio o bloqueado */ }
        }, 800);
    }
    function borrarBorrador() {
        clearTimeout(temporizadorBorrador);
        try { localStorage.removeItem(claveBorrador); } catch (e) { /* nada */ }
    }
    function recuperarBorrador(borrador) {
        // Las columnas se emparejan por su nombre: si el plan cambió, cada nota
        // vuelve a la columna que se llama igual.
        for (const tipo of ['ser', 'saber', 'hacer']) {
            const viejas = borrador.columnas?.[tipo] || {};
            const actuales = descripcionesColumnas[tipo];
            borrador.estudiantes.forEach(b => {
                const est = estudiantesData.find(e => String(e.id) === String(b.id));
                if (!est) return;
                if (!est.notas[tipo]) est.notas[tipo] = [];
                (b.notas?.[tipo] || []).forEach((valor, i) => {
                    if (!valor) return;
                    const nombre = viejas[i];
                    let destino = Object.keys(actuales).find(k => actuales[k] === nombre);
                    destino = destino !== undefined ? parseInt(destino, 10) : i;
                    while (est.notas[tipo].length <= destino) est.notas[tipo].push({ valor: '', descripcion: '' });
                    est.notas[tipo][destino].valor = valor;
                });
            });
        }
        borrador.estudiantes.forEach(b => {
            const est = estudiantesData.find(e => String(e.id) === String(b.id));
            if (est && b.inasistencias !== undefined) est.inasistencias = b.inasistencias;
            if (est && b.observacion !== undefined) est.observacion = b.observacion;
        });
        renderizarTabla();
        window.actualizarStatus('pending');
        programarAutoguardado();
    }
    function ofrecerBorrador() {
        if (!puedeGuardar) return;
        let borrador = null;
        try { borrador = JSON.parse(localStorage.getItem(claveBorrador) || 'null'); } catch (e) { borrador = null; }
        if (!borrador || !Array.isArray(borrador.estudiantes)) return;
        const fecha = new Date(borrador.fecha).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
        const aviso = document.createElement('div');
        aviso.className = 'alert alert-warning d-flex flex-wrap align-items-center gap-2 mx-3 mt-3 mb-0';
        aviso.innerHTML = `<div class="me-auto"><i class="fas fa-life-ring me-2"></i>En este equipo quedaron notas sin guardar del <strong>${fecha}</strong>.</div>
            <button type="button" class="btn btn-sm btn-warning" data-accion="recuperar">Recuperarlas</button>
            <button type="button" class="btn btn-sm btn-outline-secondary" data-accion="descartar">Descartarlas</button>`;
        tablaCalificaciones.closest('.card')?.insertBefore(aviso, tablaCalificaciones.closest('.table-responsive'));
        aviso.addEventListener('click', ev => {
            const accion = ev.target.closest('button')?.dataset.accion;
            if (accion === 'recuperar') { recuperarBorrador(borrador); aviso.remove(); }
            if (accion === 'descartar') { borrarBorrador(); aviso.remove(); }
        });
    }

    // Cada cambio: respaldo inmediato y autoguardado a los 20 s.
    const actualizarStatusOriginal = window.actualizarStatus;
    window.actualizarStatus = function (estado) {
        actualizarStatusOriginal(estado);
        if (estado === 'pending') {
            guardarBorrador();
            if (navigator.onLine) programarAutoguardado(); else mostrarEstadoConexion();
        }
        if (estado === 'saved') hayCambiosSinGuardar = false;
    };
    window.addEventListener('offline', mostrarEstadoConexion);
    window.addEventListener('online', () => {
        if (hayCambiosSinGuardar) guardar(true);
        else window.actualizarStatus('saved');
    });
    window.addEventListener('beforeunload', ev => {
        if (hayCambiosSinGuardar) { ev.preventDefault(); ev.returnValue = ''; }
    });

    // --- INITIALIZATION ---
    renderizarTabla();
    window.actualizarStatus('saved');
    ofrecerBorrador();
    
    // Exponer el array de estudiantes a nivel global (útil para debuggear)
    window.estudiantesData = estudiantesData;
});