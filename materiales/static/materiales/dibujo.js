/* Dibujo a mano alzada para el editor de materiales (las mismas herramientas de la pizarra digital).
 *   window.MMDibujo.abrir(actual, alGuardar)
 *     actual: null (dibujo nuevo), {id, dibujo} (editar un dibujo) o {base: idImagen} (dibujar encima de una imagen)
 *     alGuardar(j): j = {id, url, dibujo} de la imagen PNG guardada en la nube del docente.
 * Los trazos se guardan aparte para poder volver a editarlos (borrar uno, cambiar el fondo…). */
(function () {
    'use strict';
    var CFG = (window.MM || {}).dibujo || {};
    var COLORES = ['#111827', '#2563eb', '#dc2626', '#16a34a', '#ea580c', '#7c3aed', '#facc15', '#ffffff'];
    var GROSORES = [3, 6, 12];
    var FONDOS = [['blanco', 'Blanco'], ['cuadros', 'Cuadriculado'], ['rayas', 'Rayado'], ['puntos', 'Puntos'], ['transparente', 'Sin fondo']];
    var FORMAS = { horizontal: [1200, 800], cuadrado: [1000, 1000], vertical: [800, 1100], ancho: [1400, 500] };
    var HERR = [['lapiz', 'fa-pen', 'Lápiz'], ['resaltar', 'fa-highlighter', 'Resaltador'], ['linea', 'fa-minus', 'Línea'],
                ['flecha', 'fa-arrow-right-long', 'Flecha'], ['rect', 'fa-square', 'Rectángulo'], ['elipse', 'fa-circle', 'Círculo u óvalo'],
                ['texto', 'fa-font', 'Texto'], ['borrar', 'fa-eraser', 'Borrador (quita el trazo que toque)']];

    var modal, lienzo, ctx, est = null, alGuardarCb = null;
    function el(tag, at, hijos) {
        var e = document.createElement(tag);
        Object.keys(at || {}).forEach(function (k) {
            if (k === 'text') e.textContent = at[k]; else if (k === 'html') e.innerHTML = at[k];
            else if (k === 'onclick') e.addEventListener('click', at[k]); else e.setAttribute(k, at[k]);
        });
        (hijos || []).forEach(function (h) { if (h) e.appendChild(h); });
        return e;
    }
    function armar() {
        if (modal) return;
        var barra = el('div', { class: 'mmd-barra' });
        var grupoH = el('div', { class: 'btn-group btn-group-sm flex-wrap', role: 'group', 'aria-label': 'Herramientas' });
        HERR.forEach(function (h) {
            grupoH.appendChild(el('button', { type: 'button', class: 'btn btn-outline-dark', 'data-h': h[0], title: h[2], 'aria-label': h[2],
                html: '<i class="fas ' + h[1] + '"></i>', onclick: function () { est.h = h[0]; pintarBarra(); } }));
        });
        var grupoC = el('div', { class: 'mmd-colores', role: 'group', 'aria-label': 'Color' });
        COLORES.forEach(function (c) {
            grupoC.appendChild(el('button', { type: 'button', class: 'mmd-color', 'data-c': c, title: c, 'aria-label': 'Color ' + c, style: 'background:' + c,
                onclick: function () { est.c = c; pintarBarra(); } }));
        });
        var otro = el('input', { type: 'color', class: 'mmd-otro', title: 'Otro color', 'aria-label': 'Otro color' });
        otro.addEventListener('input', function () { est.c = otro.value; pintarBarra(); });
        grupoC.appendChild(otro);
        var grupoG = el('div', { class: 'btn-group btn-group-sm', role: 'group', 'aria-label': 'Grosor' });
        GROSORES.forEach(function (g, i) {
            grupoG.appendChild(el('button', { type: 'button', class: 'btn btn-outline-secondary', 'data-g': g, title: ['Fino', 'Medio', 'Grueso'][i],
                html: '<span class="mmd-punto" style="width:' + (g + 3) + 'px;height:' + (g + 3) + 'px"></span>', onclick: function () { est.g = g; pintarBarra(); } }));
        });
        var relleno = el('input', { type: 'checkbox', class: 'form-check-input', id: 'mmd-relleno' });
        relleno.addEventListener('change', function () { est.relleno = relleno.checked; });
        var fondo = el('select', { class: 'form-select form-select-sm', id: 'mmd-fondo', 'aria-label': 'Fondo', style: 'width:auto' });
        FONDOS.forEach(function (f) { fondo.appendChild(el('option', { value: f[0], text: f[1] })); });
        fondo.addEventListener('change', function () { est.fondo = fondo.value; dibujar(); });
        var forma = el('select', { class: 'form-select form-select-sm', id: 'mmd-forma', 'aria-label': 'Forma del lienzo', style: 'width:auto' });
        [['horizontal', 'Horizontal'], ['cuadrado', 'Cuadrado'], ['vertical', 'Vertical'], ['ancho', 'Franja ancha']].forEach(function (f) {
            forma.appendChild(el('option', { value: f[0], text: f[1] }));
        });
        forma.addEventListener('change', function () { var m = FORMAS[forma.value]; est.ancho = m[0]; est.alto = m[1]; ajustar(); });
        barra.appendChild(grupoH);
        barra.appendChild(grupoC);
        barra.appendChild(grupoG);
        barra.appendChild(el('div', { class: 'form-check form-check-inline m-0', title: 'Rectángulos y círculos rellenos' }, [relleno,
            el('label', { class: 'form-check-label small', for: 'mmd-relleno', text: 'Relleno' })]));
        barra.appendChild(el('div', { class: 'btn-group btn-group-sm', role: 'group', 'aria-label': 'Deshacer' }, [
            el('button', { type: 'button', class: 'btn btn-outline-secondary', id: 'mmd-deshacer', title: 'Deshacer (Ctrl+Z)', 'aria-label': 'Deshacer', html: '<i class="fas fa-rotate-left"></i>', onclick: deshacer }),
            el('button', { type: 'button', class: 'btn btn-outline-secondary', id: 'mmd-rehacer', title: 'Rehacer (Ctrl+Y)', 'aria-label': 'Rehacer', html: '<i class="fas fa-rotate-right"></i>', onclick: rehacer }),
            el('button', { type: 'button', class: 'btn btn-outline-danger', title: 'Borrar todo', 'aria-label': 'Borrar todo', html: '<i class="fas fa-trash-can"></i>',
                onclick: function () { if (est.trazos.length && confirm('¿Borrar todo el dibujo?')) { est.hist.push(est.trazos.slice()); est.trazos = []; est.rehacer = []; dibujar(); } } })]));
        barra.appendChild(fondo);
        barra.appendChild(forma);

        lienzo = el('canvas', { class: 'mmd-lienzo', 'aria-label': 'Lienzo para dibujar' });
        ctx = lienzo.getContext('2d');
        var guardar = el('button', { type: 'button', class: 'btn btn-primary', id: 'mmd-guardar', html: '<i class="fas fa-check me-1"></i>Poner en el documento', onclick: guardarDibujo });
        modal = el('div', { class: 'modal fade', id: 'mm-dibujo-modal', tabindex: '-1', 'aria-hidden': 'true', 'aria-labelledby': 'mmd-titulo' }, [
            el('div', { class: 'modal-dialog modal-xl modal-fullscreen-lg-down' }, [el('div', { class: 'modal-content' }, [
                el('div', { class: 'modal-header py-2' }, [
                    el('h5', { class: 'modal-title', id: 'mmd-titulo', html: '<i class="fas fa-pen-nib me-2 text-primary"></i>Dibujo a mano alzada' }),
                    el('button', { type: 'button', class: 'btn-close', 'data-bs-dismiss': 'modal', 'aria-label': 'Cerrar' })]),
                el('div', { class: 'modal-body p-2' }, [barra, el('div', { class: 'mmd-marco', id: 'mmd-marco' }, [lienzo]),
                    el('div', { class: 'small text-muted mt-1', text: 'Dibuje con el ratón, el dedo o el lápiz de la tableta. El borrador quita el trazo completo que toque. Con «Texto», toque donde quiere escribir.' })]),
                el('div', { class: 'modal-footer py-2' }, [el('span', { class: 'small text-danger me-auto', id: 'mmd-error' }),
                    el('button', { type: 'button', class: 'btn btn-outline-secondary', 'data-bs-dismiss': 'modal', text: 'Cancelar' }), guardar])])])]);
        document.body.appendChild(modal);
        var css = el('style', { text:
            '.mmd-barra{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px}' +
            '.mmd-colores{display:flex;gap:4px;align-items:center}' +
            '.mmd-color{width:24px;height:24px;border-radius:50%;border:2px solid #cbd5e1;padding:0}' +
            '.mmd-color.activo{outline:3px solid #0d6efd;outline-offset:1px}' +
            '.mmd-otro{width:28px;height:28px;padding:0;border:0;background:none}' +
            '.mmd-punto{display:inline-block;border-radius:50%;background:currentColor;vertical-align:middle}' +
            '.mmd-marco{background:#e2e8f0;border-radius:8px;padding:10px;display:flex;justify-content:center;align-items:center;min-height:300px}' +
            '.mmd-lienzo{background:#fff;box-shadow:0 4px 16px rgba(15,23,42,.18);touch-action:none;cursor:crosshair;max-width:100%}' +
            '.mmd-lienzo.transparente{background:repeating-conic-gradient(#f1f5f9 0 25%,#fff 0 50%) 0 0/20px 20px}' });
        document.head.appendChild(css);

        lienzo.addEventListener('pointerdown', abajo);
        lienzo.addEventListener('pointermove', mover);
        lienzo.addEventListener('pointerup', arriba);
        lienzo.addEventListener('pointercancel', arriba);
        modal.addEventListener('keydown', function (ev) {
            if (!(ev.ctrlKey || ev.metaKey)) return;
            var k = ev.key.toLowerCase();
            if (k === 'z' && !ev.shiftKey) { ev.preventDefault(); deshacer(); }
            else if (k === 'y' || (k === 'z' && ev.shiftKey)) { ev.preventDefault(); rehacer(); }
        });
        modal.addEventListener('shown.bs.modal', ajustar);
        window.addEventListener('resize', function () { if (modal.classList.contains('show')) ajustar(); });
    }
    function pintarBarra() {
        Array.prototype.forEach.call(modal.querySelectorAll('[data-h]'), function (b) { b.classList.toggle('active', b.getAttribute('data-h') === est.h); });
        Array.prototype.forEach.call(modal.querySelectorAll('[data-c]'), function (b) { b.classList.toggle('activo', b.getAttribute('data-c') === est.c); });
        Array.prototype.forEach.call(modal.querySelectorAll('[data-g]'), function (b) { b.classList.toggle('active', +b.getAttribute('data-g') === est.g); });
        document.getElementById('mmd-deshacer').disabled = !est.hist.length;
        document.getElementById('mmd-rehacer').disabled = !est.rehacer.length;
        lienzo.style.cursor = est.h === 'texto' ? 'text' : est.h === 'borrar' ? 'cell' : 'crosshair';
    }
    // El lienzo tiene un tamaño fijo «lógico» (ancho × alto) y en pantalla se achica para caber
    function ajustar() {
        var dpr = Math.min(2, window.devicePixelRatio || 1), marco = document.getElementById('mmd-marco');
        var libreW = Math.max(200, marco.clientWidth - 20), libreH = Math.max(240, window.innerHeight - 260);
        var esc = Math.min(libreW / est.ancho, libreH / est.alto, 1);
        lienzo.style.width = Math.round(est.ancho * esc) + 'px'; lienzo.style.height = Math.round(est.alto * esc) + 'px';
        lienzo.width = Math.round(est.ancho * esc * dpr); lienzo.height = Math.round(est.alto * esc * dpr);
        est.esc = esc * dpr;
        lienzo.classList.toggle('transparente', est.fondo === 'transparente');
        dibujar();
    }
    function punto(ev) {
        var r = lienzo.getBoundingClientRect();
        return [Math.round((ev.clientX - r.left) / r.width * est.ancho * 10) / 10, Math.round((ev.clientY - r.top) / r.height * est.alto * 10) / 10];
    }
    var actual = null;
    function abajo(ev) {
        if (!est || ev.button > 0) return;
        ev.preventDefault();
        var p = punto(ev);
        if (est.h === 'texto') {
            var t = prompt('Texto para poner en el dibujo:');
            if (t && t.trim()) agregar({ h: 'texto', c: est.c, g: est.g, p: [p], texto: t.trim().slice(0, 300) });
            return;
        }
        lienzo.setPointerCapture(ev.pointerId);
        if (est.h === 'borrar') { actual = { borrar: true }; est.hist.push(est.trazos.slice()); est.rehacer = []; borrarEn(p); return; }
        actual = { h: est.h, c: est.c, g: est.g, p: [p, p.slice()] };
        if (est.relleno && (est.h === 'rect' || est.h === 'elipse')) actual.relleno = true;
        if (est.h === 'lapiz' || est.h === 'resaltar') actual.p = [p];
    }
    function mover(ev) {
        if (!actual) return;
        var p = punto(ev);
        if (actual.borrar) { borrarEn(p); return; }
        if (actual.h === 'lapiz' || actual.h === 'resaltar') {
            var u = actual.p[actual.p.length - 1];
            if (Math.abs(u[0] - p[0]) + Math.abs(u[1] - p[1]) < 1.5) return;
            actual.p.push(p);
        } else {
            if (ev.shiftKey && actual.h !== 'elipse' && actual.h !== 'rect') {          // líneas rectas a 0°, 45° o 90°
                var a = actual.p[0], dx = p[0] - a[0], dy = p[1] - a[1], ang = Math.round(Math.atan2(dy, dx) / (Math.PI / 4)) * Math.PI / 4, d = Math.hypot(dx, dy);
                p = [Math.round((a[0] + d * Math.cos(ang)) * 10) / 10, Math.round((a[1] + d * Math.sin(ang)) * 10) / 10];
            }
            actual.p[1] = p;
        }
        dibujar();
    }
    function arriba() {
        if (!actual) return;
        var t = actual; actual = null;
        if (t.borrar) { if (est.hist.length && est.hist[est.hist.length - 1].length === est.trazos.length) est.hist.pop(); pintarBarra(); return; }
        if (t.p.length === 1) t.p.push([t.p[0][0] + .1, t.p[0][1] + .1]);   // un toque deja un punto
        agregar(t);
    }
    function agregar(t) { est.hist.push(est.trazos.slice()); est.rehacer = []; est.trazos.push(t); dibujar(); pintarBarra(); }
    function deshacer() { if (!est.hist.length) return; est.rehacer.push(est.trazos); est.trazos = est.hist.pop(); dibujar(); pintarBarra(); }
    function rehacer() { if (!est.rehacer.length) return; est.hist.push(est.trazos); est.trazos = est.rehacer.pop(); dibujar(); pintarBarra(); }
    function distSeg(p, a, b) {
        var dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy, t = l ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l)) : 0;
        return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
    }
    function toca(t, p) {
        var r = 10 + (t.g || 3);
        if (t.h === 'texto') { var tam = tamTexto(t), w = t.texto.length * tam * .55; return p[0] >= t.p[0][0] - 4 && p[0] <= t.p[0][0] + w && p[1] >= t.p[0][1] - tam && p[1] <= t.p[0][1] + tam * .3; }
        if (t.h === 'rect' || t.h === 'elipse') {
            var a = t.p[0], b = t.p[1], x0 = Math.min(a[0], b[0]) - r, x1 = Math.max(a[0], b[0]) + r, y0 = Math.min(a[1], b[1]) - r, y1 = Math.max(a[1], b[1]) + r;
            if (p[0] < x0 || p[0] > x1 || p[1] < y0 || p[1] > y1) return false;
            if (t.relleno) return true;
            return p[0] < x0 + 2 * r || p[0] > x1 - 2 * r || p[1] < y0 + 2 * r || p[1] > y1 - 2 * r;
        }
        for (var i = 1; i < t.p.length; i++) if (distSeg(p, t.p[i - 1], t.p[i]) <= r) return true;
        return t.p.length === 1 && Math.hypot(p[0] - t.p[0][0], p[1] - t.p[0][1]) <= r;
    }
    function borrarEn(p) {
        var antes = est.trazos.length;
        est.trazos = est.trazos.filter(function (t) { return !toca(t, p); });
        if (est.trazos.length !== antes) dibujar();
    }
    function tamTexto(t) { return 14 + (t.g || 3) * 3; }

    // ------------------------------------------------------------ Dibujar (en pantalla o para exportar)
    function fondoEn(c, W, H, fondo) {
        if (fondo === 'transparente') { c.clearRect(0, 0, W, H); return; }
        c.fillStyle = '#ffffff'; c.fillRect(0, 0, W, H);
        var paso = 40;
        if (fondo === 'cuadros') {
            c.strokeStyle = '#cbd5e1'; c.lineWidth = 1; c.beginPath();
            for (var x = paso; x < W; x += paso) { c.moveTo(x, 0); c.lineTo(x, H); }
            for (var y = paso; y < H; y += paso) { c.moveTo(0, y); c.lineTo(W, y); }
            c.stroke();
        } else if (fondo === 'rayas') {
            c.strokeStyle = '#bfdbfe'; c.lineWidth = 1.2; c.beginPath();
            for (var y2 = paso * 1.2; y2 < H; y2 += paso * 1.2) { c.moveTo(0, y2); c.lineTo(W, y2); }
            c.stroke();
        } else if (fondo === 'puntos') {
            c.fillStyle = '#94a3b8';
            for (var x3 = paso; x3 < W; x3 += paso) for (var y3 = paso; y3 < H; y3 += paso) { c.beginPath(); c.arc(x3, y3, 2, 0, 2 * Math.PI); c.fill(); }
        }
    }
    function trazo(c, t) {
        var p = t.p;
        c.save();
        c.strokeStyle = t.c; c.fillStyle = t.c; c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = t.g;
        if (t.h === 'resaltar') { c.globalAlpha = .35; c.lineWidth = t.g * 3; c.lineCap = 'butt'; }
        if (t.h === 'lapiz' || t.h === 'resaltar') {
            c.beginPath(); c.moveTo(p[0][0], p[0][1]);
            if (p.length < 3) { for (var i = 1; i < p.length; i++) c.lineTo(p[i][0], p[i][1]); }
            else {
                // trazo suave: curvas entre los puntos medios
                for (var j = 1; j < p.length - 1; j++) c.quadraticCurveTo(p[j][0], p[j][1], (p[j][0] + p[j + 1][0]) / 2, (p[j][1] + p[j + 1][1]) / 2);
                c.lineTo(p[p.length - 1][0], p[p.length - 1][1]);
            }
            c.stroke();
        } else if (t.h === 'linea' || t.h === 'flecha') {
            var a = p[0], b = p[1];
            c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke();
            if (t.h === 'flecha') {
                var ang = Math.atan2(b[1] - a[1], b[0] - a[0]), L = 10 + t.g * 2.5;
                c.beginPath(); c.moveTo(b[0], b[1]);
                c.lineTo(b[0] - L * Math.cos(ang - .45), b[1] - L * Math.sin(ang - .45));
                c.lineTo(b[0] - L * Math.cos(ang + .45), b[1] - L * Math.sin(ang + .45));
                c.closePath(); c.fill();
            }
        } else if (t.h === 'rect') {
            var x = Math.min(p[0][0], p[1][0]), y = Math.min(p[0][1], p[1][1]), w = Math.abs(p[1][0] - p[0][0]), h = Math.abs(p[1][1] - p[0][1]);
            if (t.relleno) { c.globalAlpha = .9; c.fillRect(x, y, w, h); } else c.strokeRect(x, y, w, h);
        } else if (t.h === 'elipse') {
            c.beginPath();
            c.ellipse((p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2, Math.abs(p[1][0] - p[0][0]) / 2 || .1, Math.abs(p[1][1] - p[0][1]) / 2 || .1, 0, 0, 2 * Math.PI);
            if (t.relleno) { c.globalAlpha = .9; c.fill(); } else c.stroke();
        } else if (t.h === 'texto') {
            c.font = 'bold ' + tamTexto(t) + 'px Arial, sans-serif'; c.textBaseline = 'alphabetic';
            c.fillText(t.texto, p[0][0], p[0][1]);
        }
        c.restore();
    }
    function escena(c, W, H, esc) {
        c.save(); c.setTransform(esc, 0, 0, esc, 0, 0);
        fondoEn(c, W, H, est.fondo);
        if (est.baseImg) {
            var iw = est.baseImg.naturalWidth, ih = est.baseImg.naturalHeight, k = Math.min(W / iw, H / ih);
            c.drawImage(est.baseImg, (W - iw * k) / 2, (H - ih * k) / 2, iw * k, ih * k);
        }
        est.trazos.forEach(function (t) { trazo(c, t); });
        if (actual && !actual.borrar) trazo(c, actual);
        c.restore();
    }
    function dibujar() { if (est) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, lienzo.width, lienzo.height); escena(ctx, est.ancho, est.alto, est.esc); } }

    function guardarDibujo() {
        var err = document.getElementById('mmd-error');
        if (!est.trazos.length && !est.baseImg) { err.textContent = 'Dibuje algo primero.'; return; }
        // Se exporta a 1,5× el tamaño lógico (sin pasar de 3000 px) para que se vea nítido al imprimir
        var k = Math.min(1.5, 3000 / Math.max(est.ancho, est.alto));
        var c = document.createElement('canvas');
        c.width = Math.round(est.ancho * k); c.height = Math.round(est.alto * k);
        escena(c.getContext('2d'), est.ancho, est.alto, k);
        var png;
        try { png = c.toDataURL('image/png'); } catch (e) { err.textContent = 'No se pudo usar la imagen de fondo para el dibujo.'; return; }
        var btn = document.getElementById('mmd-guardar');
        btn.disabled = true; err.textContent = '';
        fetch(CFG.guardar, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.MM.csrf },
            body: JSON.stringify({ png: png, imagen: est.id, dibujo: { trazos: est.trazos, fondo: est.fondo, ancho: est.ancho, alto: est.alto, base: est.base } }) })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                btn.disabled = false;
                if (!j.ok) { err.textContent = j.error || 'No se pudo guardar el dibujo.'; return; }
                window.bootstrap.Modal.getOrCreateInstance(modal).hide();
                if (alGuardarCb) alGuardarCb(j);
            })
            .catch(function () { btn.disabled = false; err.textContent = 'Sin conexión: el dibujo no se guardó.'; });
    }

    function abrir(previo, alGuardar) {
        armar();
        alGuardarCb = alGuardar;
        var d = previo && previo.dibujo ? previo.dibujo : null;
        est = { h: 'lapiz', c: COLORES[0], g: GROSORES[0], relleno: false, hist: [], rehacer: [], esc: 1,
                id: d ? previo.id : null, trazos: d ? JSON.parse(JSON.stringify(d.trazos || [])) : [],
                fondo: d ? d.fondo || 'blanco' : 'blanco', ancho: d ? d.ancho : FORMAS.horizontal[0], alto: d ? d.alto : FORMAS.horizontal[1],
                base: d ? d.base : (previo && previo.base) || null, baseImg: null };
        if (est.base && !d) est.fondo = 'blanco';
        document.getElementById('mmd-fondo').value = est.fondo;
        document.getElementById('mmd-relleno').checked = false;
        var forma = document.getElementById('mmd-forma');
        forma.value = Object.keys(FORMAS).filter(function (k) { return FORMAS[k][0] === est.ancho && FORMAS[k][1] === est.alto; })[0] || 'horizontal';
        forma.disabled = !!est.base;
        document.getElementById('mmd-error').textContent = '';
        document.getElementById('mmd-titulo').innerHTML = '<i class="fas fa-pen-nib me-2 text-primary"></i>' + (est.base ? 'Dibujar encima de la imagen' : d ? 'Editar el dibujo' : 'Dibujo a mano alzada');
        pintarBarra();
        if (est.base) {
            var img = new Image();
            img.onload = function () {
                est.baseImg = img;
                if (!d) {          // el lienzo toma la forma de la imagen
                    var r = img.naturalHeight / img.naturalWidth;
                    est.ancho = 1200; est.alto = Math.max(200, Math.min(3000, Math.round(1200 * r)));
                    if (est.alto > 1400) { est.alto = 1400; est.ancho = Math.max(200, Math.round(1400 / r)); }
                }
                ajustar();
            };
            img.onerror = function () { document.getElementById('mmd-error').textContent = 'No cargó la imagen de fondo.'; };
            img.src = (CFG.imagen || '/materiales/imagen/0/').replace('/0/', '/' + est.base + '/');
        }
        window.bootstrap.Modal.getOrCreateInstance(modal).show();
    }
    window.MMDibujo = { abrir: abrir };
})();
