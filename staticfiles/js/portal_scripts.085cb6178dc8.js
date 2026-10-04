/**
 * portal_scripts.js
 * Este script maneja toda la carga de contenido dinámico para el portal público.
 * Versión actualizada para usar atributos 'data-action' y restaurar la funcionalidad del directorio.
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // --- Selectores de Elementos del DOM ---
    const defaultContentContainer = document.getElementById('defaultMainContent');
    const dynamicContentContainer = document.getElementById('dynamicMainContent');
    const dynamicContentBody = dynamicContentContainer.querySelector('.card-body');

    // --- Plantillas HTML ---
    const loadingSpinner = `<div class="text-center w-100 py-5"><div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-3 fw-bold">Cargando contenido...</p></div>`;
    const errorAlert = (message) => `<div class="alert alert-danger text-center">${message}</div>`;
    
    // --- Funciones de Gestión de Vistas ---
    function showDefaultView(content) {
        defaultContentContainer.innerHTML = content;
        defaultContentContainer.classList.remove('d-none');
        dynamicContentContainer.classList.add('d-none');
        dynamicContentBody.innerHTML = '';
    }

    function showDynamicView(content) {
        defaultContentContainer.classList.add('d-none');
        dynamicContentContainer.classList.remove('d-none');
        dynamicContentBody.innerHTML = content;
    }

    // --- Funciones de Carga de Datos (Asíncronas) ---
    async function fetchAndShow(url) {
        showDynamicView(loadingSpinner);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Error de red: ${response.statusText}`);
            const htmlContent = await response.text();
            showDynamicView(htmlContent);
        } catch (error) {
            showDynamicView(errorAlert('No se pudo cargar el contenido solicitado.'));
            console.error(`Error al obtener de ${url}:`, error);
        }
    }
    
    async function fetchAndShowJSON(url, renderFunction) {
        const showView = renderFunction.name === 'renderCarrusel' ? showDefaultView : showDynamicView;
        showView(loadingSpinner);
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Error de red: ${response.statusText}`);
            const data = await response.json();
            renderFunction(data);
        } catch (error) {
            const errorMessage = 'No se pudo cargar el contenido solicitado.';
            showView(errorAlert(errorMessage));
            console.error(`Error al obtener JSON de ${url}:`, error);
        }
    }

    // --- Funciones de Renderizado ---
    function renderCarrusel(imagenes) {
        if (!imagenes || imagenes.length === 0) {
            showDefaultView('<div class="text-center p-5 bg-light rounded"><h3>Bienvenido al Portal</h3></div>');
            return;
        }
        const indicatorsHTML = imagenes.map((img, index) => `<button type="button" data-bs-target="#portalCarousel" data-bs-slide-to="${index}" class="${index === 0 ? 'active' : ''}"></button>`).join('');
        const itemsHTML = imagenes.map((img, index) => `
            <div class="carousel-item ${index === 0 ? 'active' : ''}">
                <img src="${img.url_imagen}" class="d-block w-100" alt="${img.titulo}" style="max-height: 550px; object-fit: cover; border-radius: 10px;">
                <div class="carousel-caption d-none d-md-block bg-dark bg-opacity-50 p-3 rounded">
                    <h5>${img.titulo}</h5>
                    <p>${img.subtitulo}</p>
                </div>
            </div>`).join('');
        const carruselHTML = `
            <div id="portalCarousel" class="carousel slide mb-5 shadow-lg" data-bs-ride="carousel">
                <div class="carousel-indicators">${indicatorsHTML}</div>
                <div class="carousel-inner">${itemsHTML}</div>
                <button class="carousel-control-prev" type="button" data-bs-target="#portalCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon"></span></button>
                <button class="carousel-control-next" type="button" data-bs-target="#portalCarousel" data-bs-slide="next"><span class="carousel-control-next-icon"></span></button>
            </div>`;
        showDefaultView(carruselHTML);
    }

    function renderNoticias(noticias) {
        let noticiasHTML;
        if (noticias.length === 0) {
            noticiasHTML = '<div class="card"><div class="card-body text-center text-muted">No hay noticias publicadas.</div></div>';
        } else {
            noticiasHTML = noticias.map(noticia => {
                const imagenHTML = noticia.url_imagen ? `<img src="${noticia.url_imagen}" class="card-img-top" alt="${noticia.titulo}" style="max-height: 250px; object-fit: cover;">` : '';
                return `
                    <div class="card mb-4 shadow-sm">
                        ${imagenHTML}
                        <div class="card-body">
                            <h4 class="card-title">${noticia.titulo}</h4>
                            <p class="card-text"><small class="text-muted">Publicado por ${noticia.autor} el ${noticia.fecha}</small></p>
                            <p class="card-text">${noticia.resumen}</p>
                            <button class="btn btn-primary noticia-link" data-pk="${noticia.pk}">Leer más...</button>
                        </div>
                    </div>`;
            }).join('');
        }
        const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Últimas Noticias</h2> ${noticiasHTML}`;
        showDynamicView(finalHTML);
    }
    
    function renderDocumentos(documentos) {
        let documentosHTML;
        if (documentos.length === 0) {
            documentosHTML = '<p class="text-center text-muted">No hay documentos disponibles.</p>';
        } else {
            documentosHTML = '<div class="list-group">' + documentos.map(doc => 
                `<a href="${doc.url_archivo}" class="list-group-item list-group-item-action" target="_blank" rel="noopener noreferrer">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1"><i class="fas fa-file-download me-2"></i>${doc.titulo}</h5>
                        <small>${doc.fecha}</small>
                    </div>
                    <p class="mb-1 small">${doc.descripcion || 'Clic para descargar'}</p>
                </a>`
            ).join('') + '</div>';
        }
        const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Documentos Públicos</h2> ${documentosHTML}`;
        showDynamicView(finalHTML);
    }

    // --- INICIO: FUNCIÓN RESTAURADA PARA EL DIRECTORIO DOCENTE ---
    function renderDirectorio(docentes) {
        let htmlContent;
        if (!docentes || docentes.length === 0) {
            htmlContent = '<p class="text-center text-muted">No hay información de docentes disponible.</p>';
        } else {
            const rows = docentes.map(docente => `
                <tr>
                    <td>${docente.nombre_completo}</td>
                    <td>${docente.direccion_grupo}</td>
                    <td>${docente.asignaturas}</td>
                </tr>
            `).join('');

            htmlContent = `
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>Nombre Completo</th>
                                <th>Director de Grupo</th>
                                <th>Asignaturas que Orienta</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>
            `;
        }
        const finalHTML = `<h2 class="card-title mb-4 border-bottom pb-3">Directorio Docente</h2> ${htmlContent}`;
        showDynamicView(finalHTML);
    }
    // --- FIN: FUNCIÓN RESTAURADA ---

    // --- Objeto de Acciones ---
    const actions = {
        'inicio': () => fetchAndShowJSON(DJANGO_URLS.carrusel, renderCarrusel),
        'noticias': () => fetchAndShowJSON(DJANGO_URLS.noticias, renderNoticias),
        'historia': () => fetchAndShow(DJANGO_URLS.historia),
        'mision': () => fetchAndShow(DJANGO_URLS.mision),
        'modelo': () => fetchAndShow(DJANGO_URLS.modelo),
        'directorio': () => fetchAndShowJSON(DJANGO_URLS.directorio, renderDirectorio), // <-- CORREGIDO
        'galeria': () => fetchAndShow(DJANGO_URLS.galeria),
        'documentos': () => fetchAndShowJSON(DJANGO_URLS.documentos, renderDocumentos),
        'recursos': () => fetchAndShow(DJANGO_URLS.recursos),
        'redes': () => fetchAndShow(DJANGO_URLS.redes),
    };

    // --- Detector de Eventos Principal (Delegado) ---
    document.body.addEventListener('click', function(e) {
        const actionTarget = e.target.closest('[data-action]');
        const noticiaLink = e.target.closest('.noticia-link');
        const volverBtn = e.target.closest('.volver-noticias-btn');

        if (actionTarget) {
            e.preventDefault();
            const action = actionTarget.dataset.action;
            if (actions[action]) {
                actions[action]();
                const navbar = document.querySelector('.navbar-collapse.show');
                if (navbar) {
                    new bootstrap.Collapse(navbar).hide();
                }
            }
        } else if (noticiaLink) {
            e.preventDefault();
            const pk = noticiaLink.dataset.pk;
            const url = DJANGO_URLS.noticia_detalle.replace('0', pk);
            fetchAndShow(url);
        } else if (volverBtn) {
            e.preventDefault();
            fetchAndShowJSON(DJANGO_URLS.noticias, renderNoticias);
        }
    });

    // --- Carga Inicial ---
    if (actions.inicio) {
        actions.inicio();
    }
});
