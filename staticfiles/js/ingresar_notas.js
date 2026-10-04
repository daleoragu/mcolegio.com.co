/**
 * Script for handling the grade entry page with a spreadsheet style.
 * @version 12.0 - Integrada la escala de valoración dinámica para los colores de la nota definitiva.
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
    } catch (e) {
        console.error("Error parsing student JSON:", e);
        return;
    }

    let hayCambiosSinGuardar = false;
    let descripcionesColumnas = { ser: {}, saber: {}, hacer: {} };

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
            if (maxNotas[tipo] === 0) maxNotas[tipo] = 1;
        }

        let headerHtml = `<thead class="table-light"><tr><th rowspan="2" class="text-center align-middle">#</th><th rowspan="2" class="align-middle">Estudiante</th>`;
        for (const tipo of ['ser', 'saber', 'hacer']) {
            headerHtml += `<th colspan="${maxNotas[tipo] + 1}" class="text-center comp-${tipo}">${tipo.toUpperCase()} <button class="btn btn-outline-success btn-sm btn-add-col" data-tipo="${tipo}" title="Añadir columna de nota">+</button><button class="btn btn-outline-danger btn-sm btn-remove-col" data-tipo="${tipo}" title="Quitar última columna">-</button></th>`;
        }
        headerHtml += `<th rowspan="2" class="text-center align-middle">Definitiva</th><th rowspan="2" class="text-center align-middle">Inasistencias</th></tr><tr>`;

        for (const tipo of ['ser', 'saber', 'hacer']) {
            for (let i = 0; i < maxNotas[tipo]; i++) {
                const desc = descripcionesColumnas[tipo][i] || '';
                headerHtml += `<th class="text-center th-nota" data-tipo="${tipo}" data-col-index="${i}" title="Clic para describir esta columna">
                                 <span class="col-title">n${i + 1}</span>
                                 <span class="col-desc">${desc}</span>
                               </th>`;
            }
            headerHtml += `<th class="text-center align-middle prom-header">Prom.</th>`;
        }
        headerHtml += `</tr></thead>`;

        let bodyHtml = `<tbody>`;
        if (estudiantesData.length === 0) {
            const colspan = 4 + maxNotas.ser + maxNotas.saber + maxNotas.hacer;
            bodyHtml += `<tr><td colspan="${colspan}" class="text-center text-muted py-4">No hay estudiantes en este curso.</td></tr>`;
        } else {
            estudiantesData.forEach((estudiante, index) => {
                bodyHtml += `<tr data-estudiante-id="${estudiante.id}"><td class="text-center align-middle">${index + 1}</td><td class="align-middle">${estudiante.nombre_completo}</td>`;
                for (const tipo of ['ser', 'saber', 'hacer']) {
                    for (let i = 0; i < maxNotas[tipo]; i++) {
                        const nota = estudiante.notas[tipo]?.[i]?.valor || '';
                        bodyHtml += `<td><input type="text" class="form-control form-control-sm input-nota" data-tipo="${tipo}" value="${nota}" inputmode="decimal"></td>`;
                    }
                    bodyHtml += `<td class="text-center align-middle fw-bold prom-celda" data-tipo="${tipo}">0.0</td>`;
                }
                bodyHtml += `<td class="text-center align-middle fw-bolder def-celda">0.0</td>
                             <td class="align-middle">
                               <div class="input-group input-group-sm">
                                 <input type="number" class="form-control input-inasistencia" min="0" value="${estudiante.inasistencias || 0}">
                                 <button class="btn btn-outline-secondary sync-inasistencias" type="button" title="Sincronizar faltas automáticas">
                                   <i class="fas fa-sync-alt"></i>
                                 </button>
                               </div>
                             </td></tr>`;
            });
        }
        bodyHtml += `</tbody>`;
        tablaCalificaciones.innerHTML = headerHtml + bodyHtml;
        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(actualizarTodosLosPromedios);
    }

    function actualizarTodosLosPromedios(fila) {
        ['ser', 'saber', 'hacer'].forEach(tipo => {
            const inputs = fila.querySelectorAll(`.input-nota[data-tipo="${tipo}"]`);
            const promCelda = fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`);
            let suma = 0, count = 0;
            inputs.forEach(input => {
                const valor = parseFloat(input.value.replace(',', '.'));
                if (!isNaN(valor) && valor >= 1.0 && valor <= 5.0) {
                    suma += valor;
                    count++;
                }
            });
            promCelda.textContent = count > 0 ? (suma / count).toFixed(1) : '0.0';
        });
        actualizarDefinitiva(fila);
    }

    // --- ======================================================= ---
    // --- FUNCIÓN ACTUALIZADA PARA USAR LA ESCALA DE VALORACIÓN ---
    // --- ======================================================= ---
    function actualizarDefinitiva(fila) {
        const defCelda = fila.querySelector('.def-celda');
        let definitiva = 0;
        
        const pSerInput = document.getElementById('p-ser');
        const pSaberInput = document.getElementById('p-saber');
        const pHacerInput = document.getElementById('p-hacer');

        let porcentajes;

        if (pSerInput && pSaberInput && pHacerInput) {
            porcentajes = {
                ser: (parseFloat(pSerInput.value) || 0) / 100,
                saber: (parseFloat(pSaberInput.value) || 0) / 100,
                hacer: (parseFloat(pHacerInput.value) || 0) / 100,
            };
        } else {
            porcentajes = {
                ser: (parseFloat(asignacionDetailsEl.dataset.pSer) || 0) / 100,
                saber: (parseFloat(asignacionDetailsEl.dataset.pSaber) || 0) / 100,
                hacer: (parseFloat(asignacionDetailsEl.dataset.pHacer) || 0) / 100,
            };
        }

        ['ser', 'saber', 'hacer'].forEach(tipo => {
            const prom = parseFloat(fila.querySelector(`.prom-celda[data-tipo="${tipo}"]`).textContent);
            if (!isNaN(prom)) definitiva += prom * porcentajes[tipo];
        });
        
        defCelda.textContent = definitiva.toFixed(1);
        
        // --- INICIO: LÓGICA DE COLOR DINÁMICA ---
        const notaFinal = parseFloat(defCelda.textContent);
        let claseDesempeno = '';

        if (escalaValoracion && escalaValoracion.length > 0) {
            // Usar la escala personalizada
            const escalaEncontrada = escalaValoracion.find(escala => 
                notaFinal >= parseFloat(escala.valor_minimo) && notaFinal <= parseFloat(escala.valor_maximo)
            );
            if (escalaEncontrada) {
                // Convierte "DESEMPEÑO BAJO" a "desempeno-bajo"
                claseDesempeno = 'desempeno-' + escalaEncontrada.nombre_desempeno.toLowerCase().replace(' ', '-');
            } else {
                claseDesempeno = 'desempeno-default'; // Si no encaja en ningún rango
            }
        } else {
            // Fallback a la lógica antigua si no hay escala configurada
            if (notaFinal < 3.0) claseDesempeno = 'nota-roja';
            else if (notaFinal < 4.0) claseDesempeno = 'nota-amarilla';
            else if (notaFinal < 4.6) claseDesempeno = 'nota-verde';
            else claseDesempeno = 'nota-azul';
        }

        // Limpiar clases anteriores y aplicar la nueva
        defCelda.className = 'text-center align-middle fw-bolder def-celda'; // Resetea a la clase base
        if(claseDesempeno) {
            defCelda.classList.add(claseDesempeno);
        }
        // --- FIN: LÓGICA DE COLOR DINÁMICA ---
    }
    
    function actualizarStatus(estado) {
        if (!statusIndicator) return;
        statusIndicator.className = 'status-indicator';
        const periodoCerrado = document.querySelector('.card-footer .text-warning');
        switch (estado) {
            case 'pending':
                statusIndicator.classList.add('status-pending');
                statusIndicator.title = 'Cambios sin guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado && tablaCalificaciones.dataset.hayIndicadores === 'true') {
                    guardarTodoBtn.disabled = false;
                }
                break;
            case 'saved':
                statusIndicator.classList.add('status-saved');
                statusIndicator.title = 'Cambios guardados';
                hayCambiosSinGuardar = false;
                if (guardarTodoBtn) guardarTodoBtn.disabled = true;
                break;
            case 'error':
                statusIndicator.classList.add('status-error');
                statusIndicator.title = 'Error al guardar';
                hayCambiosSinGuardar = true;
                if (guardarTodoBtn && !periodoCerrado) guardarTodoBtn.disabled = false;
                break;
        }
    }

    // --- EVENT HANDLERS ---
    tablaCalificaciones.addEventListener('input', e => {
        if (e.target.classList.contains('input-nota') || e.target.classList.contains('input-inasistencia')) {
            if (e.target.classList.contains('input-nota')) {
                actualizarTodosLosPromedios(e.target.closest('tr'));
            }
            actualizarStatus('pending');
        }
    });

    const panelPonderacion = document.getElementById('panel-ponderacion');
    if (panelPonderacion) {
        panelPonderacion.addEventListener('input', () => {
             tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
                actualizarDefinitiva(fila);
            });
            actualizarStatus('pending');
        });
    }
    
    tablaCalificaciones.addEventListener('click', async e => {
        const btnAdd = e.target.closest('.btn-add-col');
        const btnRemove = e.target.closest('.btn-remove-col');
        const thNota = e.target.closest('.th-nota');
        const btnSync = e.target.closest('.sync-inasistencias');

        if (btnAdd) {
            const tipo = btnAdd.dataset.tipo;
            if (estudiantesData.length > 0) {
                estudiantesData.forEach(est => {
                    if (!est.notas[tipo]) est.notas[tipo] = [];
                    est.notas[tipo].push({ valor: '', descripcion: '' });
                });
            }
            renderizarTabla();
            actualizarStatus('pending');
        }
        if (btnRemove) {
            const tipo = btnRemove.dataset.tipo;
            estudiantesData.forEach(est => {
                if (est.notas[tipo]?.length > 1) est.notas[tipo].pop();
            });
            const lastIndex = Object.keys(descripcionesColumnas[tipo]).length - 1;
            if (lastIndex >= 0) delete descripcionesColumnas[tipo][lastIndex];
            renderizarTabla();
            actualizarStatus('pending');
        }
        if (thNota) {
            const tipo = thNota.dataset.tipo;
            const colIndex = thNota.dataset.colIndex;
            const descSpan = thNota.querySelector('.col-desc');
            const descActual = descripcionesColumnas[tipo][colIndex] || '';
            const nuevaDesc = prompt(`Descripción para la columna ${thNota.querySelector('.col-title').textContent}:`, descActual);
            if (nuevaDesc !== null) {
                descripcionesColumnas[tipo][colIndex] = nuevaDesc.trim();
                descSpan.textContent = nuevaDesc.trim();
                actualizarStatus('pending');
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
                    actualizarStatus('pending');
                } else {
                    alert('Error al sincronizar: ' + data.message);
                }
            } catch (error) {
                console.error('Error en fetch de inasistencias:', error);
                alert('No se pudo conectar con el servidor para obtener las inasistencias.');
            } finally {
                icon.classList.remove('fa-spin');
                btnSync.disabled = false;
            }
        }
    });

    guardarTodoBtn?.addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';
        
        const payload = {
            asignacion_id: asignacionData.id,
            periodo_id: asignacionData.periodoId,
            estudiantes: [],
            porcentajes: {}
        };
        
        const pSerInput = document.getElementById('p-ser');
        if (pSerInput) {
            payload.porcentajes = {
                ser: document.getElementById('p-ser').value,
                saber: document.getElementById('p-saber').value,
                hacer: document.getElementById('p-hacer').value
            }
        }

        tablaCalificaciones.querySelectorAll('tbody tr[data-estudiante-id]').forEach(fila => {
            const estId = fila.dataset.estudianteId;
            const datosEst = { id: estId, notas: { ser: [], saber: [], hacer: [] }, inasistencias: fila.querySelector('.input-inasistencia').value };
            for (const tipo of ['ser', 'saber', 'hacer']) {
                fila.querySelectorAll(`.input-nota[data-tipo="${tipo}"]`).forEach((input, index) => {
                    const valor = input.value.replace(',', '.').trim();
                    if (valor) {
                        const descripcion = descripcionesColumnas[tipo][index] || `Nota ${index + 1}`;
                        datosEst.notas[tipo].push({ descripcion, valor });
                    }
                });
            }
            payload.estudiantes.push(datosEst);
        });

        try {
            const response = await fetch(asignacionData.guardarUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': asignacionData.csrfToken },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || 'Error del servidor');
            actualizarStatus('saved');
            alert('¡Guardado con éxito!');
        } catch (error) {
            console.error('Error al guardar:', error);
            alert('Error al guardar: ' + error.message);
            actualizarStatus('error');
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save me-2"></i>Guardar Cambios';
        }
    });

    // --- INITIALIZATION ---
    renderizarTabla();
    actualizarStatus('saved');
});
