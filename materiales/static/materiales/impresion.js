/* Vista previa e impresión de una guía: copias por hoja (1, 2, 4 o folleto), versión con respuestas y cuántas
 * hojas se gastan. Lo usan la ventana del editor y la página «Imprimir» de Mis materiales.
 *
 *   var imp = ImpresionMM({pdf: '/materiales/12/pdf/'}); imp.cargar('2');
 */
(function () {
    'use strict';
    window.ImpresionMM = function (CFG) {
        var $ = function (s) { return document.querySelector(s); };
        var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };
        var pv = { imp: '', blob: null, turno: 0 };
        var AYUDA = {
            '': 'Una guía por hoja, como la ve en el editor.',
            '2': 'Cada hoja lleva 2 copias a media carta. Si la guía tiene varias páginas, imprima a doble cara y corte por la línea punteada.',
            '4': 'Cada hoja lleva 4 copias en un cuarto de hoja. Imprima a doble cara si tiene varias páginas y corte por las líneas.',
            'folleto': 'Imprima a doble cara volteando por el BORDE CORTO, doble las hojas por la mitad y grape en el centro.'
        };
        function urlPrevia(descargar) {
            var q = [];
            if (pv.imp) q.push('impresion=' + pv.imp);
            if ($('#mm-pv-resp') && $('#mm-pv-resp').checked) q.push('respuestas=1');
            if (descargar) q.push('descargar=1');
            return CFG.pdf + (q.length ? '?' + q.join('&') : '');
        }
        function cuentaHojas(paginas, caras) {
            var est = Math.max(1, parseInt($('#mm-pv-est').value, 10) || 1), por = pv.imp === '2' ? 2 : pv.imp === '4' ? 4 : 1, hojas, copias;
            var porCopia = paginas > 1 ? Math.ceil(paginas / 2) : 1;
            if (pv.imp === 'folleto') { copias = est; hojas = est * Math.ceil(caras / 2); }
            else { copias = Math.ceil(est / por); hojas = copias * porCopia; }
            var normal = est * porCopia, s = function (n, uno, varios) { return n === 1 ? uno : varios; };
            var txt = 'La guía tiene <b>' + paginas + '</b> ' + s(paginas, 'página', 'páginas') + '. ';
            if (pv.imp === 'folleto') txt += 'Imprima <b>' + copias + '</b> folletos: <b>' + hojas + '</b> ' + s(hojas, 'hoja', 'hojas') + ' a doble cara.';
            else txt += 'Imprima <b>' + copias + '</b> ' + s(copias, 'copia', 'copias') + ' de este PDF: <b>' + hojas + '</b> ' + s(hojas, 'hoja', 'hojas') + (paginas > 1 ? ' a doble cara' : '') + '.';
            if (hojas < normal) txt += '<div class="text-success mt-1"><i class="fas fa-leaf me-1"></i>Ahorra ' + (normal - hojas) + ' ' + s(normal - hojas, 'hoja', 'hojas') + ' frente a 1 por hoja.</div>';
            $('#mm-pv-cuenta').innerHTML = txt;
        }
        function cargarPrevia() {
            var mio = ++pv.turno, marco = $('#mm-previa-marco'), url = urlPrevia(false);
            $('#mm-pv-cargando').hidden = false; marco.style.visibility = 'hidden';
            $('#mm-pv-ayuda').textContent = AYUDA[pv.imp];
            $('#mm-pv-descargar').href = urlPrevia(true);
            $('#mm-pv-abrir').href = url;
            $$('.mm-ph button').forEach(function (b) { var on = b.dataset.imp === pv.imp; b.classList.toggle('on', on); b.setAttribute('aria-checked', on ? 'true' : 'false'); });
            fetch(url + (url.indexOf('?') > -1 ? '&' : '?') + 't=' + Date.now(), { credentials: 'same-origin' }).then(function (r) {
                var paginas = parseInt(r.headers.get('X-Paginas'), 10) || 1, caras = parseInt(r.headers.get('X-Caras'), 10) || paginas;
                return r.blob().then(function (b) { return { b: b, paginas: paginas, caras: caras }; });
            }).then(function (d) {
                if (mio !== pv.turno) return;
                if (pv.blob) URL.revokeObjectURL(pv.blob);
                pv.blob = URL.createObjectURL(d.b);
                pv.paginas = d.paginas; pv.caras = d.caras;
                $('#mm-pv-cargando').hidden = true;
                // Los celulares (y algunos navegadores) no muestran PDF dentro de la página: se ofrece abrirlo aparte
                var sinVisor = navigator.pdfViewerEnabled === false;
                $('#mm-pv-sinvisor').hidden = !sinVisor; $('.mm-pv-ver').href = pv.blob;
                marco.hidden = sinVisor;
                if (!sinVisor) { marco.src = pv.blob; marco.style.visibility = 'visible'; }
                cuentaHojas(d.paginas, d.caras);
            }).catch(function () { $('#mm-pv-cargando').textContent = 'No se pudo armar el PDF. Intente de nuevo.'; });
        }

        $$('.mm-ph button').forEach(function (b) { b.addEventListener('click', function () { pv.imp = b.dataset.imp; cargarPrevia(); }); });
        if ($('#mm-pv-resp')) $('#mm-pv-resp').addEventListener('change', cargarPrevia);
        $('#mm-pv-est').addEventListener('input', function () { if (pv.paginas) cuentaHojas(pv.paginas, pv.caras); });
        return {
            cargar: function (imp) { pv.imp = imp || ''; cargarPrevia(); },
            actual: function () { return pv.imp; }
        };
    };
})();
