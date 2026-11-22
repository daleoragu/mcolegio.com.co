/* Botón «Marcar a mano» del editor: guarda y abre, a pantalla completa, la hoja tal como se imprime para marcar
 * encima (marcar.js). Las marcas viven en el documento del editor (MMEditor.datos.anotaciones) y salen en el PDF. */
(function () {
    'use strict';
    function arrancar() {
        var E = window.MMEditor, CFG = window.MM || {}, boton = document.getElementById('mm-anotar-btn');
        if (!E || !boton || !CFG.marcar) return;
        if (CFG.soloVer) { boton.hidden = true; return; }
        var capa = null;
        function contar() {
            var n = (E.datos.anotaciones || []).length;
            boton.innerHTML = '<i class="fas fa-pen-fancy me-1"></i>Marcar a mano' + (n ? ' <span class="badge text-bg-danger">' + n + '</span>' : '');
        }
        function abrir() {
            if (capa) return;
            boton.disabled = true;
            // Primero se guarda: la hoja para marcar se arma con lo último del documento
            Promise.resolve(E.guardarYa()).catch(function () {}).then(function () {
                boton.disabled = false;
                capa = document.createElement('div');
                capa.style.cssText = 'position:fixed;inset:0;z-index:1080;background:#cbd5e1';
                var marco = document.createElement('iframe');
                marco.title = 'Marcar a mano sobre la hoja';
                marco.style.cssText = 'border:0;width:100%;height:100%;display:block';
                marco.src = CFG.marcar + '?v=' + Date.now();
                capa.appendChild(marco);
                document.body.appendChild(capa);
                document.documentElement.style.overflow = 'hidden';
                marco.addEventListener('load', function () { try { marco.contentWindow.focus(); } catch (e) { /* nada */ } });
            });
        }
        function cerrar() {
            if (!capa) return;
            capa.remove(); capa = null;
            document.documentElement.style.overflow = '';
            contar();
        }
        boton.addEventListener('click', abrir);
        document.addEventListener('mm-restaurado', contar);
        contar();
        window.MMAnotar = { abrir: abrir, cerrar: cerrar };
    }
    if (window.MMEditor) arrancar(); else document.addEventListener('mm-editor-listo', arrancar);
})();
