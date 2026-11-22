/* Editor de materiales: menú «Insertar», vista (edición o diseño de impresión) con zoom y panel de navegación.
 * Usa window.MMEditor (lo deja editor.js): insertar bloques o preguntas, ir a un bloque y el tamaño de la hoja. */
(function () {
    'use strict';
    function arrancar() {
        var E = window.MMEditor;
        if (!E) return;
        var $ = function (s) { return document.querySelector(s); }, $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };
        var hoja = $('#mm-hoja');
        function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }
        function leer(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

        // ------------------------------------------------------------ Insertar
        $$('[data-ins]').forEach(function (b) { b.addEventListener('click', function () { E.bloque(b.getAttribute('data-ins')); }); });
        $$('[data-ins-pregunta]').forEach(function (b) { b.addEventListener('click', function () { E.pregunta(b.getAttribute('data-ins-pregunta')); }); });

        // La barra de la izquierda solo muestra íconos: el nombre va en el globo de ayuda
        $$('#mm-agregar [data-nuevo]').forEach(function (b) { if (!b.title) b.title = (b.textContent || '').trim(); b.setAttribute('aria-label', b.title); });

        // ------------------------------------------------------------ Vista y zoom
        var vista = leer('mm-vista') === 'impresion' ? 'impresion' : 'edicion';
        var zoom = Math.max(40, Math.min(200, parseInt(leer('mm-zoom') || '100', 10) || 100));
        function pintarVista() {
            document.body.classList.toggle('mm-impresion', vista === 'impresion');
            $$('#mm-vista [data-vista]').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-vista') === vista); });
            hoja.style.zoom = zoom / 100;
            $('#mm-zoom').value = zoom; $('#mm-zoom-v').textContent = zoom + '%';
            ubicarNav(); armarNav();
        }
        function ponerZoom(z) { zoom = Math.max(40, Math.min(200, Math.round(z))); guardar('mm-zoom', String(zoom)); pintarVista(); }
        $$('#mm-vista [data-vista]').forEach(function (b) {
            b.addEventListener('click', function () { vista = b.getAttribute('data-vista'); guardar('mm-vista', vista); pintarVista(); });
        });
        $('#mm-zoom').addEventListener('input', function () { ponerZoom(+this.value); });
        $('#mm-zoom-menos').addEventListener('click', function () { ponerZoom(zoom - 10); });
        $('#mm-zoom-mas').addEventListener('click', function () { ponerZoom(zoom + 10); });
        function anchoHoja() { var m = E.papel(); return m[0] * 96 / 25.4; }
        $$('[data-zoom]').forEach(function (b) {
            b.addEventListener('click', function () {
                var q = b.getAttribute('data-zoom'), libre = hoja.parentElement.clientWidth - (document.body.classList.contains('mm-con-nav') ? 300 : 0) - 24;
                if (q === 'ancho') ponerZoom(100 * libre / anchoHoja());
                else if (q === 'pagina') {
                    var m = E.papel(), barra = $('.mm-barra-fija'), alto = window.innerHeight - (barra ? barra.getBoundingClientRect().height : 120) - 40;
                    ponerZoom(Math.min(100 * alto / (m[1] * 96 / 25.4), 100 * libre / anchoHoja()));
                } else ponerZoom(+q);
            });
        });
        // Ctrl + rueda del ratón: zoom de la hoja (no de toda la página)
        hoja.addEventListener('wheel', function (ev) { if (!ev.ctrlKey) return; ev.preventDefault(); ponerZoom(zoom + (ev.deltaY < 0 ? 10 : -10)); }, {passive: false});

        // ------------------------------------------------------------ Panel de navegación
        var nav = $('#mm-nav'), lista = $('#mm-nav-lista');
        function abrirNav(si) {
            nav.hidden = !si; document.body.classList.toggle('mm-con-nav', si);
            $('#mm-nav-switch').checked = si; $('#mm-nav-btn').classList.toggle('active', si);
            guardar('mm-nav', si ? '1' : '0'); ubicarNav(); armarNav();
        }
        $('#mm-nav-btn').addEventListener('click', function () { abrirNav(nav.hidden); });
        $('#mm-nav-switch').addEventListener('change', function () { abrirNav(this.checked); });
        $('#mm-nav-cerrar').addEventListener('click', function () { abrirNav(false); });
        function ubicarNav() {
            var barra = $('.mm-barra-fija'), b = barra ? barra.getBoundingClientRect().bottom : 60;
            document.documentElement.style.setProperty('--mm-nav-top', Math.max(12, b + 8) + 'px');
        }
        window.addEventListener('scroll', ubicarNav, {passive: true});
        window.addEventListener('resize', function () { ubicarNav(); armarNav(); });
        function texto(html, n) {
            var d = document.createElement('div'); d.innerHTML = html || '';
            var t = (d.textContent || '').replace(/\s+/g, ' ').trim();
            return t.length > (n || 70) ? t.slice(0, n || 70) + '…' : t;
        }
        var ICONO = {seccion: 'fa-bookmark', titulo: 'fa-heading', pregunta: 'fa-circle-question', contexto: 'fa-book-open', imagen: 'fa-image',
                     tabla: 'fa-table', recuadro: 'fa-square', grafica: 'fa-chart-line', salto: 'fa-file-circle-plus'};
        function armarNav() {
            if (nav.hidden) return;
            var altoPag = parseFloat(getComputedStyle(hoja).getPropertyValue('--mm-alto')) || 0;
            var arriba = hoja.getBoundingClientRect().top, escala = zoom / 100;
            var preguntas = 0, secciones = 0, pagActual = 0, html = [];
            E.datos.bloques.forEach(function (b) {
                var nodo = document.querySelector('#mm-bloques [data-id="' + b.id + '"]');
                var y = nodo ? (nodo.getBoundingClientRect().top - arriba) / escala : 0;
                var pag = altoPag ? Math.floor(y / altoPag) + 1 : 1;
                var etq = null, clase = '';
                if (b.tipo === 'seccion') { secciones++; etq = b.titulo || 'Sección sin título'; clase = 'n1'; }
                else if (b.tipo === 'titulo') { etq = b.texto || 'Título'; clase = 'n1'; }
                else if (b.tipo === 'pregunta') { preguntas++; etq = preguntas + '. ' + (texto(b.enunciado, 60) || texto(b.texto, 60) || 'Pregunta'); clase = 'n2'; }
                else if (b.tipo === 'contexto') { etq = b.titulo || texto(b.html, 50) || 'Texto para varias preguntas'; clase = 'n2'; }
                else if (b.tipo === 'recuadro') { etq = b.titulo || 'Recuadro'; clase = 'n2'; }
                else if (b.tipo === 'tabla') { etq = 'Tabla'; clase = 'n2'; }
                else if (b.tipo === 'imagen') { etq = b.pie || 'Imagen'; clase = 'n2'; }
                else if (b.tipo === 'salto') { etq = 'Nueva página'; clase = 'n2'; }
                if (etq === null) return;
                if (pag !== pagActual) { pagActual = pag; html.push('<div class="mm-nav-pag">Página ' + pag + '</div>'); }
                var e = document.createElement('span'); e.textContent = etq;
                html.push('<button type="button" class="mm-nav-it ' + clase + '" data-ir="' + b.id + '"><i class="fas ' + (ICONO[b.tipo] || 'fa-paragraph') + '"></i>' + e.outerHTML + '</button>');
            });
            var total = altoPag ? Math.max(1, Math.ceil((hoja.scrollHeight) / altoPag)) : 1;
            $('#mm-nav-resumen').textContent = '≈ ' + total + ' página' + (total === 1 ? '' : 's') + ' · ' + secciones + ' sección(es) · ' + preguntas + ' pregunta(s)';
            lista.innerHTML = html.join('') || '<div class="small text-muted p-2">Agregue secciones, títulos o preguntas y aparecerán aquí para ir a ellas con un toque.</div>';
        }
        lista.addEventListener('click', function (ev) {
            var b = ev.target.closest('[data-ir]'); if (!b) return;
            $$('.mm-nav-it').forEach(function (x) { x.classList.toggle('activo', x === b); });
            E.ir(b.getAttribute('data-ir'));
        });
        // Se rehace cuando cambia el documento (bloques nuevos, títulos escritos, cosas movidas)
        var espera = null;
        new MutationObserver(function () { clearTimeout(espera); espera = setTimeout(armarNav, 400); })
            .observe($('#mm-bloques'), {childList: true, subtree: true, characterData: true});

        if (leer('mm-nav') === '1' && window.innerWidth > 900) abrirNav(true);
        pintarVista();
    }
    if (window.MMEditor) arrancar(); else document.addEventListener('mm-editor-listo', arrancar);
})();
