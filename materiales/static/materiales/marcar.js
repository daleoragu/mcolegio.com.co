/* Marcar a mano alzada sobre la hoja tal como se imprime (calificar, chulos, equis, encerrar, notas).
 * Esta página se abre dentro del editor (iframe): lee y cambia las marcas del documento del editor
 * (window.parent.MMEditor), que es el que las guarda y las deshace.
 * Cada marca queda pegada al bloque donde empezó; coordenadas en milésimas del ancho del bloque, desde su esquina
 * (las mismas del PDF). Tinta con presión como la pizarra digital (window.MMTinta). */
(function () {
    'use strict';
    var P = window.parent, E = P && P !== window ? P.MMEditor : null, T = window.MMTinta;
    if (!E || !T) return;
    var cuerpo = document.body;
    var COLORES = ['#dc2626', '#16a34a', '#2563eb', '#111827', '#ea580c', '#7c3aed', '#facc15'];
    var GROSORES = [2, 4, 8];
    var HERR = [['lapiz', 'fas fa-pen', 'Lápiz (P)'], ['resaltar', 'fas fa-highlighter', 'Resaltador (H)'], ['linea', 'fas fa-minus', 'Línea (L)'],
                ['flecha', 'fas fa-arrow-right-long', 'Flecha'], ['rect', 'far fa-square', 'Rectángulo'], ['elipse', 'far fa-circle', 'Encerrar en círculo'],
                ['texto', 'fas fa-font', 'Texto o nota (A)'], ['bien', 'fas fa-check', 'Chulo: bien'], ['mal', 'fas fa-xmark', 'Equis: mal'],
                ['medio', 'fas fa-check-double', 'Medio punto'], ['estrella', 'fas fa-star', 'Estrella'],
                ['borrar', 'fas fa-eraser', 'Borrador (B) · también el botón del lápiz o el clic derecho']];
    var SELLOS = { bien: 1, mal: 1, medio: 1, estrella: 1 };
    var st = { h: 'lapiz', c: COLORES[0], g: GROSORES[0], lapizVisto: false };
    function lista() { if (!Array.isArray(E.datos.anotaciones)) E.datos.anotaciones = []; return E.datos.anotaciones; }

    // ------------------------------------------------------------ Lienzo encima de toda la hoja
    var lienzo = document.createElement('canvas');
    lienzo.className = 'mk-lienzo';
    cuerpo.appendChild(lienzo);
    var ctx = lienzo.getContext('2d');
    var css = document.createElement('style');
    css.textContent =
        '.mk-lienzo{position:absolute;left:0;top:0;z-index:20;touch-action:none;cursor:crosshair}' +
        'body.mk-lapiz .mk-lienzo{touch-action:pan-x pan-y pinch-zoom}' +
        '.mk-barra{position:fixed;left:0;right:0;top:0;z-index:50;display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:center;' +
        'background:#fff;border-bottom:1px solid #e2e8f0;box-shadow:0 4px 16px rgba(15,23,42,.14);padding:7px 10px;font:14px system-ui,Arial,sans-serif;line-height:1.2}' +
        '.mk-grupo{display:flex;gap:2px;align-items:center;padding-right:6px;border-right:1px solid #e2e8f0}' +
        '.mk-b{min-width:34px;height:34px;border:1px solid #cbd5e1;background:#fff;border-radius:8px;color:#111827;font-size:15px;cursor:pointer;padding:0 8px}' +
        '.mk-b:hover{background:#f1f5f9}.mk-b.on{background:#111827;color:#fff;border-color:#111827}.mk-b.on i{color:#fff !important}' +
        '.mk-b[data-h=bien] i{color:#16a34a}.mk-b[data-h=mal] i{color:#dc2626}.mk-b[data-h=medio] i{color:#ea580c}.mk-b[data-h=estrella] i{color:#ca8a04}' +
        '.mk-c{width:24px;height:24px;border-radius:50%;border:2px solid #cbd5e1;padding:0;cursor:pointer}.mk-c.on{outline:3px solid #0d6efd;outline-offset:1px}' +
        '.mk-pt{display:inline-block;border-radius:50%;background:currentColor;vertical-align:middle}' +
        '.mk-listo{background:#0d6efd;color:#fff;border-color:#0d6efd;font-weight:600}.mk-listo:hover{background:#0b5ed7}' +
        '.mk-aviso{width:100%;text-align:center;color:#64748b;font-size:12px}' +
        '.mk-sw{display:flex;align-items:center;gap:4px;font-size:13px;color:#334155;cursor:pointer}';
    document.head.appendChild(css);

    function cajas() { return Array.prototype.slice.call(document.querySelectorAll('[data-bid]')); }
    var ORIG = {};
    function origenes() {
        var rc = cuerpo.getBoundingClientRect(), o = {};
        cajas().forEach(function (n) {
            var r = n.getBoundingClientRect();
            o[n.getAttribute('data-bid')] = { x: r.left - rc.left, y: r.top - rc.top, k: (r.width || 700) / 1000 };
        });
        return o;
    }
    function medir() {
        var w = cuerpo.offsetWidth, h = Math.max(cuerpo.scrollHeight, cuerpo.offsetHeight);
        var dpr = Math.min(2, window.devicePixelRatio || 1);
        dpr = Math.min(dpr, 16000 / Math.max(1, h), 16000 / Math.max(1, w));
        lienzo.style.width = w + 'px'; lienzo.style.height = h + 'px';
        var W = Math.round(w * dpr), H = Math.round(h * dpr);
        if (lienzo.width !== W || lienzo.height !== H) { lienzo.width = W; lienzo.height = H; }
        return dpr;
    }

    // ------------------------------------------------------------ Dibujar (lo mismo que sale en el PDF)
    function sello(c, tipo, x, y, tam) {
        c.save(); c.translate(x, y); c.scale(tam / 100, tam / 100); c.lineCap = 'round'; c.lineJoin = 'round';
        if (tipo === 'bien' || tipo === 'medio') {
            c.strokeStyle = tipo === 'bien' ? '#16a34a' : '#ea580c'; c.lineWidth = 14;
            c.beginPath(); c.moveTo(-38, 2); c.lineTo(-12, 28); c.lineTo(40, -30); c.stroke();
            if (tipo === 'medio') { c.lineWidth = 8; c.beginPath(); c.moveTo(-34, 34); c.lineTo(34, -34); c.stroke(); }
        } else if (tipo === 'mal') {
            c.strokeStyle = '#dc2626'; c.lineWidth = 14;
            c.beginPath(); c.moveTo(-30, -30); c.lineTo(30, 30); c.moveTo(30, -30); c.lineTo(-30, 30); c.stroke();
        } else {
            var pts = [0, -46, 13, -15, 46, -14, 20, 7, 29, 40, 0, 21, -29, 40, -20, 7, -46, -14, -13, -15];
            c.beginPath(); c.moveTo(pts[0], pts[1]); for (var i = 2; i < pts.length; i += 2) c.lineTo(pts[i], pts[i + 1]); c.closePath();
            c.fillStyle = '#facc15'; c.fill(); c.strokeStyle = '#ca8a04'; c.lineWidth = 5; c.stroke();
        }
        c.restore();
    }
    function tamSello(g) { return 22 + g * 4; }
    function tamTexto(a) { return 14 + a.g * 3; }
    function marca(c, a) {
        var p = a.p;
        c.save();
        c.strokeStyle = a.c; c.fillStyle = a.c; c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = a.g;
        if (a.h === 'lapiz' && p[0].length > 2) T.tinta(c, a);
        else if (a.h === 'lapiz' || a.h === 'resaltar') {
            if (a.h === 'resaltar') { c.globalAlpha = .35; c.lineWidth = a.g * 3; c.lineCap = 'butt'; }
            c.beginPath(); c.moveTo(p[0][0], p[0][1]);
            for (var i = 1; i < p.length - 1; i++) c.quadraticCurveTo(p[i][0], p[i][1], (p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2);
            c.lineTo(p[p.length - 1][0] + (p.length === 1 ? .1 : 0), p[p.length - 1][1]); c.stroke();
        } else if (a.h === 'linea' || a.h === 'flecha') {
            var A = p[0], B = p[p.length - 1];
            c.beginPath(); c.moveTo(A[0], A[1]); c.lineTo(B[0], B[1]); c.stroke();
            if (a.h === 'flecha') {
                var ang = Math.atan2(B[1] - A[1], B[0] - A[0]), L = 10 + a.g * 2.5;
                c.beginPath(); c.moveTo(B[0], B[1]); c.lineTo(B[0] - L * Math.cos(ang - .45), B[1] - L * Math.sin(ang - .45));
                c.lineTo(B[0] - L * Math.cos(ang + .45), B[1] - L * Math.sin(ang + .45)); c.closePath(); c.fill();
            }
        } else if (a.h === 'rect') {
            c.strokeRect(Math.min(p[0][0], p[1][0]), Math.min(p[0][1], p[1][1]), Math.abs(p[1][0] - p[0][0]), Math.abs(p[1][1] - p[0][1]));
        } else if (a.h === 'elipse') {
            c.beginPath(); c.ellipse((p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2, Math.abs(p[1][0] - p[0][0]) / 2 || .1, Math.abs(p[1][1] - p[0][1]) / 2 || .1, 0, 0, 7); c.stroke();
        } else if (a.h === 'texto') {
            c.font = 'bold ' + tamTexto(a) + 'px Arial, sans-serif'; c.fillText(a.texto, p[0][0], p[0][1]);
        } else if (a.h === 'sello') sello(c, a.s, p[0][0], p[0][1], tamSello(a.g));
        c.restore();
    }
    var actual = null;
    function pintar() {
        var dpr = medir();
        ORIG = origenes();
        ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, lienzo.width, lienzo.height);
        function una(a) { var o = ORIG[a.b]; if (!o) return; ctx.setTransform(dpr * o.k, 0, 0, dpr * o.k, dpr * o.x, dpr * o.y); marca(ctx, a); }
        lista().forEach(una);
        if (actual && actual.a) una(actual.a);
    }
    var cuadro = null;
    function pedir() { if (!cuadro) cuadro = requestAnimationFrame(function () { cuadro = null; pintar(); }); }

    // ------------------------------------------------------------ Puntero → bloque y coordenadas
    function enHoja(ev) { var r = cuerpo.getBoundingClientRect(); return [ev.clientX - r.left, ev.clientY - r.top]; }
    // El bloque donde cae el punto (o el más cercano por arriba)
    function bloqueEn(y) {
        var mejor = null, ids = Object.keys(ORIG);
        ids.forEach(function (id) { var o = ORIG[id]; if (o.y <= y + 2 && (!mejor || o.y > ORIG[mejor].y)) mejor = id; });
        if (!mejor && ids.length) mejor = ids.reduce(function (a, b) { return ORIG[a].y < ORIG[b].y ? a : b; });
        return mejor;
    }
    function aUnidades(q, bid) { var o = ORIG[bid]; return [Math.round((q[0] - o.x) / o.k * 10) / 10, Math.round((q[1] - o.y) / o.k * 10) / 10]; }
    function agregar(a) { lista().push(a); E.cambio(); pintar(); }
    // Borrador: quita la marca completa que toque
    function toca(a, q) {
        var o = ORIG[a.b]; if (!o) return false;
        var x = (q[0] - o.x) / o.k, y = (q[1] - o.y) / o.k, r = a.g * 1.5 + 8, p = a.p;
        if (a.h === 'sello') { var t = tamSello(a.g) / 2; return Math.abs(x - p[0][0]) < t && Math.abs(y - p[0][1]) < t; }
        if (a.h === 'texto') { var tt = tamTexto(a); return x >= p[0][0] - 4 && x <= p[0][0] + a.texto.length * tt * .6 && y >= p[0][1] - tt && y <= p[0][1] + tt * .3; }
        if (a.h === 'rect' || a.h === 'elipse') {
            var x0 = Math.min(p[0][0], p[1][0]), x1 = Math.max(p[0][0], p[1][0]), y0 = Math.min(p[0][1], p[1][1]), y1 = Math.max(p[0][1], p[1][1]);
            return x >= x0 - r && x <= x1 + r && y >= y0 - r && y <= y1 + r && (x < x0 + r || x > x1 - r || y < y0 + r || y > y1 - r);
        }
        for (var i = 0; i < p.length; i++) {
            var A = p[Math.max(0, i - 1)], B = p[i], dx = B[0] - A[0], dy = B[1] - A[1], l = dx * dx + dy * dy;
            var s = l ? Math.max(0, Math.min(1, ((x - A[0]) * dx + (y - A[1]) * dy) / l)) : 0;
            if (Math.hypot(x - (A[0] + s * dx), y - (A[1] + s * dy)) <= r) return true;
        }
        return false;
    }
    function borrarEn(q) {
        var antes = lista().length;
        E.datos.anotaciones = lista().filter(function (a) { return !toca(a, q); });
        if (E.datos.anotaciones.length !== antes) { actual.borro = true; pintar(); }
    }

    lienzo.addEventListener('contextmenu', function (ev) { ev.preventDefault(); });
    lienzo.addEventListener('pointerdown', function (ev) {
        if (ev.pointerType === 'pen' && !st.lapizVisto) {
            st.lapizVisto = true; cuerpo.classList.add('mk-lapiz');
            aviso('✍️ Lápiz detectado: ahora el dedo solo mueve la hoja (la palma no raya).');
        }
        if (ev.pointerType === 'touch' && st.lapizVisto) return;      // el dedo desplaza; el lápiz escribe
        ev.preventDefault();
        ORIG = origenes();
        var q = enHoja(ev), bid = bloqueEn(q[1]);
        if (!bid) { aviso('El documento está vacío: agregue algo para poder marcar encima.'); return; }
        lienzo.setPointerCapture(ev.pointerId);
        if (st.h === 'borrar' || ev.button === 2 || (ev.buttons & 32)) { actual = { borrar: true }; borrarEn(q); return; }
        var u = aUnidades(q, bid), g = st.g;
        if (st.h === 'texto') {
            var t = prompt('Texto o nota para poner aquí (por ejemplo: 4,5 · ¡Muy bien! · Revisa el signo):');
            if (t && t.trim()) agregar({ b: bid, h: 'texto', c: st.c, g: g, p: [u], texto: t.trim().slice(0, 200) });
            return;
        }
        if (SELLOS[st.h]) { agregar({ b: bid, h: 'sello', s: st.h, c: st.c, g: g, p: [u] }); return; }
        var a = { b: bid, h: st.h, c: st.c, g: g, p: [u] };
        if (st.h === 'lapiz') {
            var pr = T.presion(ev, null);
            a.g = g * 1.4; a.p = [[u[0], u[1], pr]];
            actual = { a: a, ult: { sx: ev.clientX, sy: ev.clientY, t: ev.timeStamp, pr: pr, w: u } };
        } else {
            if (st.h !== 'resaltar') a.p = [u, u.slice()];
            actual = { a: a };
        }
        pedir();
    });
    lienzo.addEventListener('pointermove', function (ev) {
        if (!actual) return;
        if (actual.borrar) { borrarEn(enHoja(ev)); return; }
        var a = actual.a, aU = function (e) { return aUnidades(enHoja(e), a.b); };
        if (a.h === 'lapiz') T.sumarPuntos(a, ev, actual.ult, aU);
        else if (a.h === 'resaltar') { var q = aU(ev), u = a.p[a.p.length - 1]; if (Math.abs(q[0] - u[0]) + Math.abs(q[1] - u[1]) >= 1.5) a.p.push(q); }
        else {
            var p = aU(ev);
            if (ev.shiftKey && (a.h === 'linea' || a.h === 'flecha')) {          // rectas a 0°, 45° o 90°
                var o = a.p[0], dx = p[0] - o[0], dy = p[1] - o[1], ang = Math.round(Math.atan2(dy, dx) / (Math.PI / 4)) * Math.PI / 4, d = Math.hypot(dx, dy);
                p = [Math.round((o[0] + d * Math.cos(ang)) * 10) / 10, Math.round((o[1] + d * Math.sin(ang)) * 10) / 10];
            }
            a.p[1] = p;
        }
        pedir();
    });
    function soltar() {
        if (!actual) return;
        var t = actual; actual = null;
        if (t.borrar) { if (t.borro) E.cambio(); return; }
        agregar(t.a);
    }
    lienzo.addEventListener('pointerup', soltar);
    lienzo.addEventListener('pointercancel', soltar);

    // ------------------------------------------------------------ Barra de herramientas
    var barra = document.createElement('div');
    barra.className = 'mk-barra'; barra.setAttribute('role', 'toolbar'); barra.setAttribute('aria-label', 'Marcar a mano sobre la hoja');
    var h = ['<div class="mk-grupo">'];
    HERR.forEach(function (x) { h.push('<button type="button" class="mk-b" data-h="' + x[0] + '" title="' + x[2] + '" aria-label="' + x[2] + '"><i class="' + x[1] + '"></i></button>'); });
    h.push('</div><div class="mk-grupo" role="group" aria-label="Color">');
    COLORES.forEach(function (c) { h.push('<button type="button" class="mk-c" data-c="' + c + '" style="background:' + c + '" aria-label="Color ' + c + '"></button>'); });
    h.push('</div><div class="mk-grupo" role="group" aria-label="Grosor">');
    GROSORES.forEach(function (g, i) { h.push('<button type="button" class="mk-b" data-g="' + g + '" title="' + ['Fino', 'Medio', 'Grueso'][i] + '"><span class="mk-pt" style="width:' + (4 + i * 4) + 'px;height:' + (4 + i * 4) + 'px"></span></button>'); });
    h.push('</div><div class="mk-grupo">' +
           '<button type="button" class="mk-b" data-a="deshacer" title="Deshacer (Ctrl+Z)" aria-label="Deshacer"><i class="fas fa-rotate-left"></i></button>' +
           '<button type="button" class="mk-b" data-a="rehacer" title="Rehacer (Ctrl+Y)" aria-label="Rehacer"><i class="fas fa-rotate-right"></i></button>' +
           '<button type="button" class="mk-b" data-a="limpiar" title="Quitar todas las marcas" aria-label="Quitar todas las marcas"><i class="fas fa-trash-can" style="color:#dc2626"></i></button></div>' +
           '<label class="mk-sw" title="Si se apaga, las marcas solo se ven aquí y no salen en el PDF"><input type="checkbox" id="mk-pdf"> En el PDF</label>' +
           '<button type="button" class="mk-b mk-listo" data-a="listo"><i class="fas fa-check"></i> Listo</button>' +
           '<div class="mk-aviso" id="mk-aviso"></div>');
    barra.innerHTML = h.join('');
    cuerpo.appendChild(barra);
    var avisoT = null, AYUDA = 'Marque donde quiera, como en papel. Las marcas quedan pegadas a cada pregunta y se guardan solas.';
    function aviso(t) {
        var s = document.getElementById('mk-aviso'); s.textContent = t;
        clearTimeout(avisoT); avisoT = setTimeout(function () { s.textContent = AYUDA; }, 4500);
    }
    function pintarBarra() {
        barra.querySelectorAll('[data-h]').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-h') === st.h); });
        barra.querySelectorAll('[data-c]').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-c') === st.c); });
        barra.querySelectorAll('[data-g]').forEach(function (b) { b.classList.toggle('on', +b.getAttribute('data-g') === st.g); });
        document.getElementById('mk-pdf').checked = E.datos.opciones.marcas_pdf !== false;
        lienzo.style.cursor = st.h === 'texto' ? 'text' : st.h === 'borrar' ? 'cell' : SELLOS[st.h] ? 'copy' : 'crosshair';
    }
    function cerrar() { if (P.MMAnotar) P.MMAnotar.cerrar(); }
    barra.addEventListener('click', function (ev) {
        var b = ev.target.closest('button'); if (!b) return;
        if (b.hasAttribute('data-h')) st.h = b.getAttribute('data-h');
        else if (b.hasAttribute('data-c')) { st.c = b.getAttribute('data-c'); if (st.h === 'borrar' || SELLOS[st.h]) st.h = 'lapiz'; }
        else if (b.hasAttribute('data-g')) st.g = +b.getAttribute('data-g');
        else {
            var acc = b.getAttribute('data-a');
            if (acc === 'deshacer') E.deshacer();
            else if (acc === 'rehacer') E.rehacer();
            else if (acc === 'limpiar') { if (lista().length && confirm('¿Quitar todas las marcas de la hoja?')) { E.datos.anotaciones = []; E.cambio(); pintar(); } }
            else if (acc === 'listo') { cerrar(); return; }
        }
        pintarBarra();
    });
    document.getElementById('mk-pdf').addEventListener('change', function () { E.datos.opciones.marcas_pdf = this.checked; E.cambio(); });
    var TECLAS = { p: 'lapiz', h: 'resaltar', l: 'linea', a: 'texto', b: 'borrar' };
    document.addEventListener('keydown', function (ev) {
        var k = ev.key.toLowerCase();
        if (ev.ctrlKey || ev.metaKey) {
            if (k === 'z' && !ev.shiftKey) { ev.preventDefault(); E.deshacer(); }
            else if (k === 'y' || (k === 'z' && ev.shiftKey)) { ev.preventDefault(); E.rehacer(); }
            return;
        }
        if (ev.key === 'Escape') { cerrar(); return; }
        if (TECLAS[k]) { st.h = TECLAS[k]; pintarBarra(); }
    });

    // Deshacer en el editor cambia la lista: se repinta
    P.document.addEventListener('mm-restaurado', pedir);
    window.addEventListener('resize', pedir);
    window.addEventListener('load', pintar);          // cuando ya cargaron las imágenes
    if (window.ResizeObserver) new ResizeObserver(pedir).observe(cuerpo);
    pintarBarra(); aviso(AYUDA); pintar();
})();
