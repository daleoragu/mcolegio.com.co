/* «Descargar informes» por partes: con muchos estudiantes el servidor no alcanzaba a armar todo el ZIP en una sola
 * petición y se cortaba. El navegador pide el plan (qué partes hay: el total, cada grado, cada curso y los
 * estudiantes de a 12), pide cada parte por separado mostrando el avance y al final las une en UN solo ZIP.
 * Si una parte falla, se reintenta; si falla otra vez, se avisa cuál y se entrega lo demás. */
(function () {
    'use strict';
    var form = document.getElementById('pe-descarga');
    if (!form || !window.fetch) return;

    var capa = document.createElement('div');
    capa.className = 'pe-zip-capa';
    capa.hidden = true;
    capa.innerHTML = '<div class="pe-zip-caja" role="dialog" aria-live="polite" aria-label="Armando los informes">' +
        '<div class="fw-bold mb-1"><i class="fas fa-file-zipper me-1"></i> Armando los informes</div>' +
        '<div class="small text-muted mb-2" id="pe-zip-que">Preparando…</div>' +
        '<div class="progress" style="height:12px"><div class="progress-bar progress-bar-striped progress-bar-animated" id="pe-zip-barra" style="width:0%"></div></div>' +
        '<div class="small mt-2" id="pe-zip-cuenta"></div>' +
        '<div class="small text-danger mt-2" id="pe-zip-error"></div>' +
        '<div class="text-end mt-2"><button type="button" class="btn btn-sm btn-outline-secondary" id="pe-zip-cancelar">Cancelar</button></div></div>';
    document.body.appendChild(capa);
    var css = document.createElement('style');
    css.textContent = '.pe-zip-capa{position:fixed;inset:0;z-index:2100;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;padding:16px}' +
        '.pe-zip-capa[hidden]{display:none}.pe-zip-caja{background:#fff;border-radius:14px;padding:18px 20px;width:min(440px,100%);box-shadow:0 20px 50px rgba(0,0,0,.3)}';
    document.head.appendChild(css);
    var $ = function (id) { return document.getElementById(id); };
    var cancelado = false;
    $('pe-zip-cancelar').addEventListener('click', function () { cancelado = true; capa.hidden = true; });

    function cargarJSZip() {
        if (window.JSZip) return Promise.resolve(window.JSZip);
        return new Promise(function (ok, mal) {
            var s = document.createElement('script');
            s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
            s.onload = function () { window.JSZip ? ok(window.JSZip) : mal(); };
            s.onerror = mal;
            document.head.appendChild(s);
        });
    }
    function describir(p) {
        if (p.que === 'general') return 'Informe general';
        if (p.que === 'grados') return 'Informe del grado ' + p.valor;
        if (p.que === 'cursos') return 'Informe del curso ' + p.valor;
        return 'Estudiantes, grupo ' + p.n;
    }
    function pedir(parte, intento) {
        var fd = new FormData(form);
        fd.append('parte', JSON.stringify(parte));
        return fetch(form.action, {method: 'POST', body: fd, credentials: 'same-origin'}).then(function (r) {
            var tipo = r.headers.get('Content-Type') || '';
            if (!r.ok || tipo.indexOf('zip') < 0) throw new Error('HTTP ' + r.status);
            return r.blob();
        }).catch(function (e) {
            if (intento < 1 && !cancelado) return new Promise(function (ok) { setTimeout(ok, 2000); }).then(function () { return pedir(parte, intento + 1); });
            throw e;
        });
    }
    function bajar(blob, nombre) {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = nombre;
        document.body.appendChild(a); a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 4000);
    }

    form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        cancelado = false;
        capa.hidden = false;
        $('pe-zip-que').textContent = 'Preparando…'; $('pe-zip-barra').style.width = '0%'; $('pe-zip-cuenta').textContent = ''; $('pe-zip-error').textContent = '';
        var fd = new FormData(form);
        fd.append('plan', '1');
        var plan, JSZipLib;
        Promise.all([
            fetch(form.action, {method: 'POST', body: fd, credentials: 'same-origin'}).then(function (r) {
                if ((r.headers.get('Content-Type') || '').indexOf('json') < 0) throw new Error('sin plan');
                return r.json();
            }),
            cargarJSZip()
        ]).then(function (res) {
            plan = res[0]; JSZipLib = res[1];
            if (!plan.ok || !plan.partes || !plan.partes.length) throw new Error('sin partes');
            var final = new JSZipLib(), fallidas = [], hechas = 0, total = plan.partes.length, usados = {};
            var cadena = Promise.resolve();
            plan.partes.forEach(function (parte) {
                cadena = cadena.then(function () {
                    if (cancelado) return;
                    $('pe-zip-que').textContent = describir(parte) + '…';
                    $('pe-zip-cuenta').textContent = 'Parte ' + (hechas + 1) + ' de ' + total;
                    return pedir(parte, 0).then(function (blob) {
                        return JSZipLib.loadAsync(blob).then(function (z) {
                            var copias = [];
                            z.forEach(function (ruta, archivo) {
                                if (archivo.dir) return;
                                var destino = ruta, k = 2;
                                while (usados[destino.toLowerCase()]) { destino = ruta.replace(/(\.[^.\/]+)?$/, ' (' + k++ + ')$1'); }
                                usados[destino.toLowerCase()] = true;
                                copias.push(archivo.async('uint8array').then(function (d) { final.file(destino, d, {binary: true}); }));
                            });
                            return Promise.all(copias);
                        });
                    }).catch(function () { fallidas.push(describir(parte)); });
                }).then(function () {
                    hechas++;
                    $('pe-zip-barra').style.width = Math.round(hechas / total * 100) + '%';
                });
            });
            return cadena.then(function () {
                if (cancelado) return;
                if (fallidas.length === total) throw new Error('todas fallaron');
                $('pe-zip-que').textContent = 'Uniendo todo en un solo ZIP…';
                return final.generateAsync({type: 'blob', compression: 'STORE'}).then(function (blob) {
                    bajar(blob, plan.nombre || 'Informes.zip');
                    if (fallidas.length) {
                        $('pe-zip-que').textContent = 'Listo, pero faltaron algunas partes.';
                        $('pe-zip-error').textContent = 'No se pudieron armar: ' + fallidas.join(', ') + '. Vuelva a intentarlo solo con esos estudiantes o cursos.';
                        $('pe-zip-cancelar').textContent = 'Cerrar';
                    } else capa.hidden = true;
                });
            });
        }).catch(function () {
            // Sin la librería o sin el plan (servidor viejo): como antes, todo de una vez
            capa.hidden = true;
            if (!cancelado) HTMLFormElement.prototype.submit.call(form);
        });
    });
})();
