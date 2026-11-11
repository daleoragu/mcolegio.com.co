/* Recortar y girar imágenes en el editor de documentos.
 * Se marca con el mouse o el dedo el pedazo que se quiere (se mueve arrastrando y se agranda por las esquinas).
 * El servidor recorta siempre desde la imagen original (que se guarda), así se puede volver a recortar o restaurar.
 *
 *   window.MMImg.recortar({id, url, recorte}, alListo)   recorte: {x, y, w, h, giro, url_origen} o null
 *      alListo({id, url, recorte}) con la imagen nueva
 */
(function () {
    'use strict';
    var CFG = window.MM || {};
    var modal, lienzo, marco, sel, info, img = null, giro = 0, r = { x: 0, y: 0, w: 1, h: 1 }, proporcion = 0, actual = null, alListoCb = null;

    function el(tag, attrs, hijos) {
        var e = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (k) {
            if (k === 'text') e.textContent = attrs[k];
            else if (k === 'html') e.innerHTML = attrs[k];
            else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), attrs[k]);
            else e.setAttribute(k, attrs[k]);
        });
        (hijos || []).forEach(function (h) { if (h) e.appendChild(h); });
        return e;
    }

    // --- Dibujar la imagen (girada) en el lienzo ---
    function pintar() {
        if (!img) return;
        var giradaW = giro % 180 ? img.naturalHeight : img.naturalWidth, giradaH = giro % 180 ? img.naturalWidth : img.naturalHeight;
        var maxW = Math.min(marco.parentNode.clientWidth || 700, 760), maxH = window.innerHeight * 0.58;
        var esc = Math.min(maxW / giradaW, maxH / giradaH, 1);
        lienzo.width = Math.round(giradaW * esc); lienzo.height = Math.round(giradaH * esc);
        var c = lienzo.getContext('2d');
        c.save();
        c.translate(lienzo.width / 2, lienzo.height / 2);
        c.rotate(giro * Math.PI / 180);
        var w = img.naturalWidth * esc, h = img.naturalHeight * esc;
        c.drawImage(img, -w / 2, -h / 2, w, h);
        c.restore();
        marco.style.width = lienzo.width + 'px'; marco.style.height = lienzo.height + 'px';
        ponerSel();
    }
    function ponerSel() {
        sel.style.left = (r.x * 100) + '%'; sel.style.top = (r.y * 100) + '%';
        sel.style.width = (r.w * 100) + '%'; sel.style.height = (r.h * 100) + '%';
        if (img) {
            var gw = giro % 180 ? img.naturalHeight : img.naturalWidth, gh = giro % 180 ? img.naturalWidth : img.naturalHeight;
            info.textContent = Math.round(r.w * gw) + ' × ' + Math.round(r.h * gh) + ' px';
        }
    }
    function acotar() {
        r.w = Math.max(.03, Math.min(1, r.w)); r.h = Math.max(.03, Math.min(1, r.h));
        r.x = Math.max(0, Math.min(1 - r.w, r.x)); r.y = Math.max(0, Math.min(1 - r.h, r.y));
    }
    function conProporcion(ancla) {
        if (!proporcion || !lienzo.width) return;
        // proporción en píxeles → en fracciones del lienzo
        var p = proporcion * lienzo.height / lienzo.width;
        if (r.w / r.h > p) r.w = r.h * p; else r.h = r.w / p;
        if (r.w > 1) { r.w = 1; r.h = r.w / p; }
        if (r.h > 1) { r.h = 1; r.w = r.h * p; }
        if (ancla === 'centro') { r.x = Math.max(0, (1 - r.w) / 2); r.y = Math.max(0, (1 - r.h) / 2); }
    }

    // --- Arrastrar: mover, agrandar por una esquina o marcar uno nuevo ---
    var arrastre = null;
    function punto(ev) {
        var b = marco.getBoundingClientRect();
        return [(ev.clientX - b.left) / b.width, (ev.clientY - b.top) / b.height];
    }
    function empezar(ev) {
        ev.preventDefault();
        var p = punto(ev), esquina = ev.target.getAttribute && ev.target.getAttribute('data-esquina');
        if (esquina) arrastre = { modo: 'esquina', esquina: esquina, ini: p, r0: Object.assign({}, r) };
        else if (ev.target === sel) arrastre = { modo: 'mover', ini: p, r0: Object.assign({}, r) };
        else { arrastre = { modo: 'nuevo', ini: p }; r = { x: p[0], y: p[1], w: .03, h: .03 }; }
        marco.setPointerCapture(ev.pointerId);
    }
    function mover(ev) {
        if (!arrastre) return;
        var p = punto(ev), dx = p[0] - arrastre.ini[0], dy = p[1] - arrastre.ini[1], r0 = arrastre.r0;
        if (arrastre.modo === 'mover') { r.x = r0.x + dx; r.y = r0.y + dy; }
        else if (arrastre.modo === 'nuevo') {
            r = { x: Math.min(p[0], arrastre.ini[0]), y: Math.min(p[1], arrastre.ini[1]), w: Math.abs(dx), h: Math.abs(dy) };
            conProporcion();
        } else {
            var e = arrastre.esquina, x1 = r0.x + r0.w, y1 = r0.y + r0.h, nx = r0.x, ny = r0.y;
            if (e.indexOf('o') >= 0) nx = Math.min(x1 - .03, r0.x + dx); else x1 = Math.max(r0.x + .03, x1 + dx);
            if (e.indexOf('n') >= 0) ny = Math.min(y1 - .03, r0.y + dy); else y1 = Math.max(r0.y + .03, y1 + dy);
            r = { x: nx, y: ny, w: x1 - nx, h: y1 - ny };
            if (proporcion) {
                var w0 = r.w; conProporcion();
                if (e.indexOf('o') >= 0) r.x += w0 - r.w;
                if (e.indexOf('n') >= 0) r.y = y1 - r.h;
            }
        }
        acotar(); ponerSel();
    }
    function soltar() { arrastre = null; }

    function preparar() {
        if (modal) return;
        modal = document.getElementById('mm-recorte-modal');
        marco = document.getElementById('rc-marco'); lienzo = document.getElementById('rc-lienzo'); info = document.getElementById('rc-info');
        sel = el('div', { class: 'rc-sel', title: 'Arrastre para mover' });
        ['no', 'ne', 'so', 'se'].forEach(function (e) { sel.appendChild(el('span', { class: 'rc-esq rc-' + e, 'data-esquina': e })); });
        marco.appendChild(sel);
        marco.addEventListener('pointerdown', empezar);
        marco.addEventListener('pointermove', mover);
        marco.addEventListener('pointerup', soltar);
        marco.addEventListener('pointercancel', soltar);
        document.getElementById('rc-izq').addEventListener('click', function () { girar(-90); });
        document.getElementById('rc-der').addEventListener('click', function () { girar(90); });
        document.getElementById('rc-todo').addEventListener('click', function () { r = { x: 0, y: 0, w: 1, h: 1 }; conProporcion('centro'); ponerSel(); });
        document.getElementById('rc-proporcion').addEventListener('change', function () {
            proporcion = +this.value || 0; conProporcion('centro'); acotar(); ponerSel();
        });
        document.getElementById('rc-aplicar').addEventListener('click', function () { enviar(false); });
        document.getElementById('rc-restaurar').addEventListener('click', function () {
            if (confirm('¿Volver a la imagen original, sin recorte?')) enviar(true);
        });
        window.addEventListener('resize', function () { if (modal.classList.contains('show')) pintar(); });
    }
    function girar(g) {
        // al girar, el recorte se reinicia (es otra forma)
        giro = (giro + g + 360) % 360; r = { x: 0, y: 0, w: 1, h: 1 }; conProporcion('centro'); pintar();
    }
    function enviar(restaurar) {
        var b = document.getElementById('rc-aplicar'), aviso = document.getElementById('rc-aviso');
        b.disabled = true; aviso.textContent = 'Recortando…';
        fetch('/materiales/imagen/' + actual.id + '/recortar/', {
            method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf },
            body: JSON.stringify({ x: r.x, y: r.y, w: r.w, h: r.h, giro: giro, restaurar: !!restaurar })
        }).then(function (x) { return x.json(); }).then(function (j) {
            b.disabled = false;
            if (!j.ok) { aviso.textContent = j.error || 'No se pudo recortar.'; return; }
            aviso.textContent = '';
            window.bootstrap.Modal.getOrCreateInstance(modal).hide();
            if (alListoCb) alListoCb(j);
        }).catch(function () { b.disabled = false; aviso.textContent = 'Sin conexión: no se recortó.'; });
    }
    function recortar(imagen, alListo) {
        preparar();
        actual = imagen; alListoCb = alListo;
        var rec = imagen.recorte;
        giro = rec ? (rec.giro || 0) : 0;
        r = rec ? { x: rec.x, y: rec.y, w: rec.w, h: rec.h } : { x: .05, y: .05, w: .9, h: .9 };
        proporcion = 0; document.getElementById('rc-proporcion').value = '0';
        document.getElementById('rc-restaurar').classList.toggle('d-none', !rec);
        document.getElementById('rc-aviso').textContent = 'Cargando la imagen…';
        img = new Image();
        img.onload = function () { document.getElementById('rc-aviso').textContent = ''; pintar(); };
        img.onerror = function () { document.getElementById('rc-aviso').textContent = 'No se pudo cargar la imagen.'; };
        img.src = rec && rec.url_origen ? rec.url_origen : imagen.url;
        window.bootstrap.Modal.getOrCreateInstance(modal).show();
        modal.addEventListener('shown.bs.modal', function una() { modal.removeEventListener('shown.bs.modal', una); pintar(); });
    }
    window.MMImg = { recortar: recortar };
})();
