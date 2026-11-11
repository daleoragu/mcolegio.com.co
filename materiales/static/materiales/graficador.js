/* Graficador del editor de documentos: funciones, puntos, segmentos, vectores, polígonos, circunferencias,
 * rectas verticales, áreas y textos sobre el plano cartesiano. La vista previa la dibuja el servidor (la misma
 * imagen que queda en el PDF, en Word y en la ficha). Un clic sobre la gráfica ubica puntos y figuras.
 *
 *   window.MMGraf.abrir(actual, alGuardar)
 *      actual: null (nueva) o {id, grafica}; alGuardar(respuesta) con {id, url, grafica}
 */
(function () {
    'use strict';
    var CFG = (window.MM || {}).grafica;
    if (!CFG) return;
    var CSRF = window.MM.csrf;
    var COLORES = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2', '#111827', '#db2777'];
    var NOMBRES = {
        funcion: 'Función', punto: 'Punto', segmento: 'Segmento', vector: 'Vector', poligono: 'Polígono',
        circulo: 'Circunferencia', vertical: 'Recta x = a', area: 'Área sombreada', texto: 'Texto'
    };
    var EJEMPLOS = {
        'Parábola': { x: [-5, 5], y: [-3, 7], elementos: [{ t: 'funcion', expr: 'x^2 - 2x - 1', nombre: 'f' }, { t: 'punto', x: 1, y: -2, nombre: 'V' }] },
        'Recta y = mx + b': { x: [-6, 6], y: [-4, 6], elementos: [{ t: 'funcion', expr: '2x + 1', nombre: 'y = 2x + 1' }, { t: 'punto', x: 0, y: 1, nombre: 'b' }] },
        'Sistema de ecuaciones': { x: [-6, 6], y: [-4, 6], elementos: [{ t: 'funcion', expr: 'x + 1', nombre: 'r' }, { t: 'funcion', expr: '-x + 3', nombre: 's', color: '#dc2626' }, { t: 'punto', x: 1, y: 2, nombre: 'P', proyecciones: true, color: '#111827' }] },
        'Seno y coseno': { x: ['-2pi', '2pi'], y: [-2, 2], pi: true, elementos: [{ t: 'funcion', expr: 'sen(x)', nombre: 'sen x' }, { t: 'funcion', expr: 'cos(x)', nombre: 'cos x', color: '#dc2626' }] },
        'Triángulo en el plano': { x: [-1, 7], y: [-1, 6], escala_igual: true, forma: 'cuadrada', elementos: [{ t: 'poligono', puntos: [[0, 0], [5, 0], [2, 4]], vertices: 'A, B, C' }] },
        'Área bajo la curva': { x: [-1, 4], y: [-1, 5], elementos: [{ t: 'funcion', expr: 'x^2/2', nombre: 'f' }, { t: 'area', expr: 'x^2/2', desde: '0', hasta: '2', nombre: 'A' }] },
        'Plano vacío': { x: [-6, 6], y: [-6, 6], escala_igual: true, forma: 'cuadrada', elementos: [] }
    };

    var modal, lista, previa, imgPrevia, avisos, herramienta = 'mover', espera = null, pendientes = [], caja = null, alGuardarCb = null, actualId = null;
    var g = null;           // la gráfica que se está armando

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
    function nueva() { return JSON.parse(JSON.stringify(EJEMPLOS['Plano vacío'])); }
    function colorLibre() { return COLORES[g.elementos.length % COLORES.length]; }

    // --- Un campo pequeño que actualiza la gráfica ---
    function campo(obj, clave, ayuda, ancho) {
        var i = el('input', { type: 'text', class: 'form-control form-control-sm', placeholder: ayuda, style: 'width:' + (ancho || '70px') });
        i.value = obj[clave] == null ? '' : obj[clave];
        i.addEventListener('input', function () { obj[clave] = i.value; redibujar(); });
        return i;
    }
    function casilla(obj, clave, texto) {
        var id = 'gr-' + Math.random().toString(36).slice(2, 8);
        var c = el('input', { type: 'checkbox', class: 'form-check-input', id: id });
        c.checked = !!obj[clave];
        c.addEventListener('change', function () { obj[clave] = c.checked; redibujar(); });
        return el('span', { class: 'form-check form-check-inline small m-0' }, [c, el('label', { class: 'form-check-label', for: id, text: texto })]);
    }
    function selector(obj, clave, opciones) {
        var s = el('select', { class: 'form-select form-select-sm', style: 'width:auto' });
        opciones.forEach(function (o) { s.appendChild(el('option', { value: o[0], text: o[1] })); });
        s.value = obj[clave] || opciones[0][0];
        s.addEventListener('change', function () { obj[clave] = s.value; redibujar(); });
        return s;
    }
    function coordenada(obj, clave, nombre) {      // obj[clave] = [x, y]
        obj[clave] = obj[clave] || [0, 0];
        var par = obj[clave];
        return el('span', { class: 'd-inline-flex align-items-center gap-1' }, [el('span', { class: 'small text-muted', text: nombre + ' (' }),
            campo(par, 0, 'x', '52px'), el('span', { text: ',' }), campo(par, 1, 'y', '52px'), el('span', { text: ')' })]);
    }

    function filaElemento(e, k) {
        var color = el('input', { type: 'color', class: 'form-control form-control-color form-control-sm', title: 'Color', value: e.color || COLORES[k % 8] });
        color.addEventListener('input', function () { e.color = color.value; redibujar(); });
        var cab = el('div', { class: 'd-flex align-items-center gap-2 mb-1' }, [
            el('b', { class: 'small', text: NOMBRES[e.t] }), color,
            el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger ms-auto p-0', title: 'Quitar', html: '<i class="far fa-trash-can"></i>',
                onclick: function () { g.elementos.splice(k, 1); pintarLista(); redibujar(); } })]);
        var cuerpo = el('div', { class: 'd-flex flex-wrap gap-1 align-items-center' });
        var nombre = campo(e, 'nombre', 'Nombre', '90px');
        if (e.t === 'funcion') {
            cuerpo.appendChild(el('span', { class: 'small', text: 'y =' }));
            cuerpo.appendChild(campo(e, 'expr', '2x^2 - 3x + 1', '170px'));
            cuerpo.appendChild(nombre);
            cuerpo.appendChild(selector(e, 'estilo', [['solida', '——'], ['guiones', '- - -'], ['puntos', '· · ·']]));
            cuerpo.appendChild(el('span', { class: 'small text-muted', text: 'de' })); cuerpo.appendChild(campo(e, 'desde', 'inicio', '58px'));
            cuerpo.appendChild(el('span', { class: 'small text-muted', text: 'a' })); cuerpo.appendChild(campo(e, 'hasta', 'fin', '58px'));
        } else if (e.t === 'area') {
            cuerpo.appendChild(el('span', { class: 'small', text: 'bajo y =' })); cuerpo.appendChild(campo(e, 'expr', 'x^2', '120px'));
            cuerpo.appendChild(el('span', { class: 'small', text: 'sobre y =' })); cuerpo.appendChild(campo(e, 'expr2', '0 (eje x)', '90px'));
            cuerpo.appendChild(el('span', { class: 'small text-muted', text: 'de x =' })); cuerpo.appendChild(campo(e, 'desde', '0', '52px'));
            cuerpo.appendChild(el('span', { class: 'small text-muted', text: 'a' })); cuerpo.appendChild(campo(e, 'hasta', '2', '52px'));
            cuerpo.appendChild(nombre);
        } else if (e.t === 'punto') {
            cuerpo.appendChild(el('span', { class: 'small', text: '(' })); cuerpo.appendChild(campo(e, 'x', 'x', '52px'));
            cuerpo.appendChild(el('span', { text: ',' })); cuerpo.appendChild(campo(e, 'y', 'y', '52px')); cuerpo.appendChild(el('span', { text: ')' }));
            cuerpo.appendChild(nombre); cuerpo.appendChild(casilla(e, 'proyecciones', 'Líneas a los ejes'));
        } else if (e.t === 'segmento' || e.t === 'vector') {
            cuerpo.appendChild(coordenada(e, 'a', e.t === 'vector' ? 'desde' : 'A')); cuerpo.appendChild(coordenada(e, 'b', e.t === 'vector' ? 'hasta' : 'B'));
            cuerpo.appendChild(nombre);
            cuerpo.appendChild(selector(e, 'estilo', [['solida', '——'], ['guiones', '- - -'], ['puntos', '· · ·']]));
        } else if (e.t === 'poligono') {
            var pts = el('input', { type: 'text', class: 'form-control form-control-sm', style: 'width:230px', placeholder: '(0,0) (4,0) (2,3)' });
            pts.value = (e.puntos || []).map(function (p) { return '(' + p[0] + ', ' + p[1] + ')'; }).join(' ');
            pts.addEventListener('input', function () {
                e.puntos = (pts.value.match(/\(([^()]*)\)/g) || []).map(function (x) { var v = x.slice(1, -1).split(/[;,]/); return [v[0] ? v[0].trim() : 0, v[1] ? v[1].trim() : 0]; });
                redibujar();
            });
            cuerpo.appendChild(el('span', { class: 'small text-muted', text: 'vértices' })); cuerpo.appendChild(pts);
            cuerpo.appendChild(campo(e, 'vertices', 'A, B, C', '80px')); cuerpo.appendChild(casilla(e, 'relleno', 'Relleno'));
        } else if (e.t === 'circulo') {
            cuerpo.appendChild(el('span', { class: 'small', text: 'centro (' })); cuerpo.appendChild(campo(e, 'cx', 'x', '52px'));
            cuerpo.appendChild(el('span', { text: ',' })); cuerpo.appendChild(campo(e, 'cy', 'y', '52px'));
            cuerpo.appendChild(el('span', { class: 'small', text: ') radio' })); cuerpo.appendChild(campo(e, 'r', 'r', '52px'));
            cuerpo.appendChild(nombre); cuerpo.appendChild(casilla(e, 'relleno', 'Relleno'));
        } else if (e.t === 'vertical') {
            cuerpo.appendChild(el('span', { class: 'small', text: 'x =' })); cuerpo.appendChild(campo(e, 'x', '2', '60px'));
            cuerpo.appendChild(nombre); cuerpo.appendChild(selector(e, 'estilo', [['guiones', '- - -'], ['solida', '——'], ['puntos', '· · ·']]));
        } else if (e.t === 'texto') {
            cuerpo.appendChild(campo(e, 'texto', 'Escriba el texto', '170px'));
            cuerpo.appendChild(el('span', { class: 'small text-muted', text: 'en (' })); cuerpo.appendChild(campo(e, 'x', 'x', '52px'));
            cuerpo.appendChild(el('span', { text: ',' })); cuerpo.appendChild(campo(e, 'y', 'y', '52px')); cuerpo.appendChild(el('span', { text: ')' }));
        }
        var err = el('div', { class: 'small text-danger gr-error', 'data-k': k });
        return el('div', { class: 'gr-elem' }, [cab, cuerpo, err]);
    }
    function pintarLista() {
        lista.innerHTML = '';
        if (!g.elementos.length) lista.appendChild(el('div', { class: 'small text-muted p-2', text: 'Agregue una función o un punto con los botones de arriba, o haga clic sobre la gráfica.' }));
        g.elementos.forEach(function (e, k) { lista.appendChild(filaElemento(e, k)); });
    }
    function agregar(t) {
        var e = { t: t, color: colorLibre(), nombre: '' };
        if (t === 'funcion') { e.expr = ''; e.estilo = 'solida'; e.nombre = ['f', 'g', 'h', 'p', 'q'][g.elementos.filter(function (x) { return x.t === 'funcion'; }).length] || ''; }
        if (t === 'area') { e.expr = ''; e.expr2 = ''; e.desde = '0'; e.hasta = '1'; }
        if (t === 'punto') { e.x = 1; e.y = 1; e.nombre = letraLibre(); }
        if (t === 'segmento' || t === 'vector') { e.a = [0, 0]; e.b = [2, 1]; e.estilo = 'solida'; }
        if (t === 'poligono') { e.puntos = [[0, 0], [3, 0], [1, 2]]; e.relleno = true; }
        if (t === 'circulo') { e.cx = 0; e.cy = 0; e.r = 2; }
        if (t === 'vertical') { e.x = 1; e.estilo = 'guiones'; }
        if (t === 'texto') { e.x = 0; e.y = 0; e.texto = ''; }
        g.elementos.push(e);
        pintarLista(); redibujar();
        var campos = lista.querySelectorAll('.gr-elem:last-child input[type=text]');
        if (campos.length) campos[0].focus();
    }
    function letraLibre() {
        var usadas = g.elementos.map(function (e) { return e.nombre; });
        var abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        for (var i = 0; i < abc.length; i++) if (usadas.indexOf(abc[i]) < 0) return abc[i];
        return '';
    }

    // --- La ventana de los ejes ---
    function pintarAjustes() {
        var c = document.getElementById('gr-ajustes');
        c.innerHTML = '';
        g.x = g.x || [-6, 6]; g.y = g.y || [-4, 4];
        c.appendChild(el('div', { class: 'd-flex flex-wrap gap-1 align-items-center small' }, [
            el('span', { text: 'x de' }), campo(g.x, 0, '-6', '58px'), el('span', { text: 'a' }), campo(g.x, 1, '6', '58px'),
            el('span', { class: 'ms-2', text: 'y de' }), campo(g.y, 0, '-4', '58px'), el('span', { text: 'a' }), campo(g.y, 1, '4', '58px'),
            selector(g, 'forma', [['ancha', 'Rectangular'], ['cuadrada', 'Cuadrada'], ['alta', 'Vertical']])]));
        if (g.cuadricula === undefined) g.cuadricula = true;
        if (g.ejes === undefined) g.ejes = true;
        if (g.numeros === undefined) g.numeros = true;
        c.appendChild(el('div', { class: 'd-flex flex-wrap gap-2 mt-1' }, [casilla(g, 'cuadricula', 'Cuadrícula'), casilla(g, 'ejes', 'Ejes'),
            casilla(g, 'numeros', 'Números'), casilla(g, 'escala_igual', 'Misma escala en x y y'), casilla(g, 'pi', 'Eje x en π')]));
    }

    // --- Vista previa (la dibuja el servidor) ---
    function redibujar() {
        clearTimeout(espera);
        espera = setTimeout(function () {
            fetch(CFG.vista, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
                body: JSON.stringify({ grafica: g }) })
                .then(function (r) { return r.json(); })
                .then(function (j) {
                    var url = URL.createObjectURL(new Blob([j.svg], { type: 'image/svg+xml' }));
                    var anterior = imgPrevia.src; imgPrevia.src = url;
                    if (anterior && anterior.indexOf('blob:') === 0) setTimeout(function () { URL.revokeObjectURL(anterior); }, 2000);
                    caja = j.caja; g._limpia = j.grafica;
                    Array.prototype.forEach.call(lista.querySelectorAll('.gr-error'), function (d) { d.textContent = j.errores[d.getAttribute('data-k')] || ''; });
                }).catch(function () { avisos.textContent = 'Sin conexión: no se pudo dibujar.'; });
        }, 300);
    }

    // --- Clic en la gráfica: ubicar puntos, segmentos y polígonos ---
    function aDatos(ev) {
        var r = imgPrevia.getBoundingClientRect(), lim = g._limpia;
        if (!caja || !lim) return null;
        var fx = (ev.clientX - r.left) / r.width, fy = 1 - (ev.clientY - r.top) / r.height;
        if (fx < caja[0] || fx > caja[2] || fy < caja[1] || fy > caja[3]) return null;
        var x = lim.x[0] + (fx - caja[0]) / (caja[2] - caja[0]) * (lim.x[1] - lim.x[0]);
        var y = lim.y[0] + (fy - caja[1]) / (caja[3] - caja[1]) * (lim.y[1] - lim.y[0]);
        var paso = document.getElementById('gr-imantar').checked ? .5 : .01;
        return [Math.round(x / paso) * paso, Math.round(y / paso) * paso].map(function (v) { return +v.toFixed(2); });
    }
    function clicGrafica(ev) {
        var p = aDatos(ev);
        if (!p || herramienta === 'mover') return;
        if (herramienta === 'punto') { g.elementos.push({ t: 'punto', x: p[0], y: p[1], nombre: letraLibre(), color: colorLibre() }); pintarLista(); redibujar(); return; }
        pendientes.push(p);
        var faltan = herramienta === 'poligono' ? 0 : 2;
        avisos.textContent = herramienta === 'poligono' ? 'Vértice ' + pendientes.length + ' (' + p.join(', ') + '). Siga haciendo clic; «Terminar polígono» cuando acabe.' : 'Punto ' + pendientes.length + ' de 2: (' + p.join(', ') + ')';
        if (faltan && pendientes.length >= faltan) {
            g.elementos.push({ t: herramienta, a: pendientes[0], b: pendientes[1], color: colorLibre(), estilo: 'solida', nombre: '' });
            pendientes = []; avisos.textContent = ''; pintarLista(); redibujar();
        }
    }
    function terminarPoligono() {
        if (pendientes.length >= 2) {
            var abc = 'ABCDEFGHIJKLMNOP';
            g.elementos.push({ t: 'poligono', puntos: pendientes, relleno: true, color: colorLibre(), vertices: abc.slice(0, pendientes.length).split('').join(', ') });
            pintarLista(); redibujar();
        }
        pendientes = []; avisos.textContent = '';
    }
    function elegirHerramienta(h) {
        herramienta = h; pendientes = [];
        Array.prototype.forEach.call(modal.querySelectorAll('[data-herr]'), function (b) { b.classList.toggle('active', b.getAttribute('data-herr') === h); });
        document.getElementById('gr-terminar').classList.toggle('d-none', h !== 'poligono');
        imgPrevia.style.cursor = h === 'mover' ? 'default' : 'crosshair';
        avisos.textContent = { punto: 'Haga clic en la gráfica para poner un punto.', segmento: 'Haga clic en los dos extremos del segmento.',
            vector: 'Haga clic en el inicio y luego en la punta del vector.', poligono: 'Haga clic en cada vértice.' }[h] || '';
    }

    function preparar() {
        if (modal) return;
        modal = document.getElementById('mm-graf-modal');
        lista = document.getElementById('gr-lista'); previa = document.getElementById('gr-previa'); avisos = document.getElementById('gr-avisos');
        imgPrevia = el('img', { alt: 'Vista previa de la gráfica', style: 'width:100%;display:block;user-select:none', draggable: 'false' });
        previa.appendChild(imgPrevia);
        imgPrevia.addEventListener('click', clicGrafica);
        Array.prototype.forEach.call(modal.querySelectorAll('[data-agregar]'), function (b) {
            b.addEventListener('click', function () { agregar(b.getAttribute('data-agregar')); });
        });
        Array.prototype.forEach.call(modal.querySelectorAll('[data-herr]'), function (b) {
            b.addEventListener('click', function () { elegirHerramienta(b.getAttribute('data-herr')); });
        });
        document.getElementById('gr-terminar').addEventListener('click', terminarPoligono);
        var ej = document.getElementById('gr-ejemplos');
        Object.keys(EJEMPLOS).forEach(function (n) {
            ej.appendChild(el('li', {}, [el('button', { type: 'button', class: 'dropdown-item small', text: n, onclick: function () {
                if (g.elementos.length && !confirm('¿Cambiar la gráfica por el ejemplo «' + n + '»?')) return;
                g = JSON.parse(JSON.stringify(EJEMPLOS[n])); pintarAjustes(); pintarLista(); redibujar();
            } })]));
        });
        document.getElementById('gr-guardar').addEventListener('click', guardar);
    }
    function guardar() {
        var b = document.getElementById('gr-guardar');
        var copia = JSON.parse(JSON.stringify(g)); delete copia._limpia;
        b.disabled = true;
        fetch(CFG.guardar, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({ grafica: copia, imagen: actualId }) })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                b.disabled = false;
                if (!j.ok) { avisos.textContent = j.error || 'No se pudo guardar.'; return; }
                window.bootstrap.Modal.getOrCreateInstance(modal).hide();
                if (alGuardarCb) alGuardarCb(j);
            }).catch(function () { b.disabled = false; avisos.textContent = 'Sin conexión: no se guardó.'; });
    }
    function abrir(actual, alGuardar) {
        preparar();
        alGuardarCb = alGuardar;
        actualId = actual ? actual.id : null;
        g = actual && actual.grafica ? JSON.parse(JSON.stringify(actual.grafica)) : nueva();
        g.elementos = g.elementos || [];
        document.getElementById('gr-guardar').textContent = actualId ? 'Guardar cambios' : 'Insertar gráfica';
        pintarAjustes(); pintarLista(); elegirHerramienta('mover'); redibujar();
        window.bootstrap.Modal.getOrCreateInstance(modal).show();
    }
    window.MMGraf = { abrir: abrir };
})();
