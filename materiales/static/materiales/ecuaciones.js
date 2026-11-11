/* Ecuaciones en el editor de documentos.
 *
 * En el documento se guardan dentro del texto como \( LaTeX \). En el editor se ven dibujadas (la imagen la hace
 * el servidor, la misma del PDF y de Word) y un clic sobre una ecuación la abre para cambiarla.
 * La ventana usa el teclado de ecuaciones MathLive (se carga solo la primera vez); si no carga, queda el campo LaTeX.
 *
 *   window.MMEq.aVista(nodo)        \( … \) del texto → ecuaciones dibujadas
 *   window.MMEq.aTexto(nodo, plano) ecuaciones dibujadas → \( … \) (para guardar)
 *   window.MMEq.vista(texto)        un <div> con el texto y sus ecuaciones (para las opciones)
 */
(function () {
    'use strict';
    var CFG = window.MM || {};
    var RE = /\\\(([\s\S]+?)\\\)/g;
    var BASE_ML = 'https://cdn.jsdelivr.net/npm/mathlive@0.108.2/', MATHLIVE = BASE_ML + 'mathlive.min.js';

    function url(tex) { return CFG.ecuacion + '?tex=' + encodeURIComponent(tex); }
    function span(tex) {
        var s = document.createElement('span');
        s.className = 'mm-eqv'; s.contentEditable = 'false'; s.setAttribute('data-tex', tex);
        s.title = 'Clic para cambiar la ecuación';
        var i = new Image(); i.alt = tex; i.src = url(tex);
        i.onerror = function () { s.classList.add('mala'); s.textContent = tex; s.title = 'Esta ecuación no se puede dibujar: clic para corregirla'; };
        s.appendChild(i);
        return s;
    }
    function aVista(raiz) {
        if (!raiz || (raiz.textContent || '').indexOf('\\(') < 0) return false;
        var w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT), nodos = [], n;
        while ((n = w.nextNode())) {
            if (n.nodeValue.indexOf('\\(') >= 0 && !(n.parentNode.closest && n.parentNode.closest('.mm-eqv'))) nodos.push(n);
        }
        var hubo = false;
        nodos.forEach(function (t) {
            var txt = t.nodeValue, frag = document.createDocumentFragment(), i = 0, m;
            RE.lastIndex = 0;
            while ((m = RE.exec(txt))) {
                if (m.index > i) frag.appendChild(document.createTextNode(txt.slice(i, m.index)));
                frag.appendChild(span(m[1].trim()));
                i = RE.lastIndex; hubo = true;
            }
            if (i < txt.length) frag.appendChild(document.createTextNode(txt.slice(i)));
            t.parentNode.replaceChild(frag, t);
        });
        return hubo;
    }
    function aTexto(raiz, plano) {
        var c = raiz.cloneNode(true);
        Array.prototype.forEach.call(c.querySelectorAll('.mm-eqv'), function (s) {
            s.parentNode.replaceChild(document.createTextNode('\\(' + s.getAttribute('data-tex') + '\\)'), s);
        });
        return plano ? c.textContent : c.innerHTML;
    }
    function vista(texto) {
        var d = document.createElement('div'); d.className = 'mm-eq-vista';
        d.textContent = texto || '';
        aVista(d);
        return d;
    }

    // ---------------------------------------------------------------
    // Dónde va la ecuación: el último lugar donde estaba el cursor
    // ---------------------------------------------------------------
    var ultimo = null;           // {el, rango} (texto con formato) o {el, ini, fin} (campo de una línea)
    function dentroDelEditor(n) { return n && n.closest && n.closest('.mm-bloque'); }
    document.addEventListener('selectionchange', function () {
        var a = document.activeElement;
        if (!dentroDelEditor(a)) return;
        if (a.isContentEditable) {
            var s = window.getSelection();
            if (s.rangeCount && a.contains(s.getRangeAt(0).startContainer)) ultimo = { el: a, rango: s.getRangeAt(0).cloneRange() };
        } else if (a.tagName === 'INPUT' && a.type === 'text' || a.tagName === 'TEXTAREA') {
            ultimo = { el: a, ini: a.selectionStart, fin: a.selectionEnd };
        }
    });
    function avisarCambio(el) { el.dispatchEvent(new Event('input', { bubbles: true })); }
    function insertarEn(destino, tex) {
        if (destino.span) {
            if (!tex) { var p = destino.span.closest('[contenteditable="true"]'); destino.span.remove(); if (p) avisarCambio(p); return; }
            var nuevo = span(tex); destino.span.parentNode.replaceChild(nuevo, destino.span);
            avisarCambio(nuevo.closest('[contenteditable="true"]'));
            return;
        }
        if (!tex) return;
        var el = destino.el;
        if (el.isContentEditable) {
            var r = destino.rango;
            if (!r || !el.contains(r.startContainer)) { r = document.createRange(); r.selectNodeContents(el); r.collapse(false); }
            r.deleteContents();
            var s = span(tex), espacio = document.createTextNode(' ');
            r.insertNode(espacio); r.insertNode(s);
            var sel = window.getSelection(), fin = document.createRange();
            fin.setStartAfter(espacio); fin.collapse(true);
            el.focus(); sel.removeAllRanges(); sel.addRange(fin);
            avisarCambio(el);
        } else {
            var token = '\\(' + tex + '\\)', ini = destino.ini == null ? el.value.length : destino.ini, finx = destino.fin == null ? ini : destino.fin;
            el.value = el.value.slice(0, ini) + token + el.value.slice(finx);
            el.focus(); el.setSelectionRange(ini + token.length, ini + token.length);
            avisarCambio(el);
        }
    }

    // ---------------------------------------------------------------
    // La ventana
    // ---------------------------------------------------------------
    var PALETA = [
        ['Básico', [['a/b', '\\frac{#@}{#?}'], ['√', '\\sqrt{#@}'], ['ⁿ√', '\\sqrt[#?]{#@}'], ['xⁿ', '#@^{#?}'], ['xₙ', '#@_{#?}'], ['( )', '\\left(#@\\right)'],
                    ['|x|', '\\left|#@\\right|'], ['×', '\\times'], ['÷', '\\div'], ['·', '\\cdot'], ['±', '\\pm'], ['%', '\\%']]],
        ['Relaciones', [['=', '='], ['≠', '\\neq'], ['<', '<'], ['>', '>'], ['≤', '\\leq'], ['≥', '\\geq'], ['≈', '\\approx'], ['∝', '\\propto']]],
        ['Geometría', [['°', '^{\\circ}'], ['∠', '\\angle'], ['△', '\\triangle'], ['⊥', '\\perp'], ['∥', '\\parallel'], ['≅', '\\cong'], ['∼', '\\sim'],
                       ['AB̄', '\\overline{#@}'], ['AB→', '\\overrightarrow{#@}'], ['π', '\\pi'], ['θ', '\\theta'], ['α', '\\alpha'], ['β', '\\beta']]],
        ['Conjuntos y lógica', [['∈', '\\in'], ['∉', '\\notin'], ['⊂', '\\subset'], ['∪', '\\cup'], ['∩', '\\cap'], ['∅', '\\emptyset'], ['ℕ', '\\mathbb{N}'],
                                ['ℤ', '\\mathbb{Z}'], ['ℚ', '\\mathbb{Q}'], ['ℝ', '\\mathbb{R}'], ['→', '\\rightarrow'], ['⇒', '\\Rightarrow'], ['⇔', '\\Leftrightarrow']]],
        ['Cálculo y estadística', [['∑', '\\sum_{#?}^{#?}#@'], ['∫', '\\int_{#?}^{#?}#@\\,dx'], ['lím', '\\lim_{x\\to #?}#@'], ['∞', '\\infty'], ['Δ', '\\Delta'],
                                   ['x̄', '\\bar{#@}'], ['σ', '\\sigma'], ['sen', '\\mathrm{sen}\\,'], ['cos', '\\cos'], ['tan', '\\tan'], ['log', '\\log'], ['ln', '\\ln']]]
    ];
    var modal = null, campo = null, latex = null, previa = null, destino = null, mathlive = null, esperaPrevia = null;

    function cargarMathLive() {
        if (mathlive) return mathlive;
        mathlive = new Promise(function (ok, no) {
            if (window.customElements && window.customElements.get('math-field')) return ok();
            var s = document.createElement('script'); s.src = MATHLIVE; s.async = true;
            s.onload = function () { ok(); }; s.onerror = no;
            document.head.appendChild(s);
            setTimeout(no, 12000);
        });
        return mathlive;
    }
    function valor() { return (campo && campo.tagName === 'MATH-FIELD' ? campo.value : latex.value).trim(); }
    function verPrevia() {
        clearTimeout(esperaPrevia);
        esperaPrevia = setTimeout(function () {
            var tex = valor();
            previa.innerHTML = '';
            if (!tex) { previa.innerHTML = '<span class="text-muted small">(vacía)</span>'; return; }
            var i = new Image(); i.alt = tex; i.src = url(tex);
            i.onerror = function () { previa.innerHTML = '<span class="text-danger small">Esta ecuación no se puede dibujar todavía. Revise que esté completa (por ejemplo, las fracciones con numerador y denominador). Las matrices no se pueden.</span>'; };
            previa.appendChild(i);
        }, 250);
    }
    function crearPaleta() {
        var p = document.getElementById('mm-eq-paleta');
        PALETA.forEach(function (g) {
            var t = document.createElement('div'); t.className = 'grupo'; t.textContent = g[0]; p.appendChild(t);
            g[1].forEach(function (x) {
                var b = document.createElement('button'); b.type = 'button'; b.textContent = x[0]; b.title = x[1].replace(/#[@?]/g, '□');
                b.addEventListener('mousedown', function (e) { e.preventDefault(); });
                b.addEventListener('click', function () {
                    if (campo.tagName === 'MATH-FIELD') { campo.executeCommand(['insert', x[1], { selectionMode: 'placeholder', focus: true }]); campo.focus(); }
                    else {
                        var t2 = x[1].replace(/#@|#\?/g, ''), a = latex.selectionStart, z = latex.selectionEnd;
                        latex.value = latex.value.slice(0, a) + t2 + latex.value.slice(z);
                        latex.focus(); latex.setSelectionRange(a + t2.length, a + t2.length);
                    }
                    verPrevia();
                });
                p.appendChild(b);
            });
        });
    }
    function preparar() {
        if (modal) return;
        modal = document.getElementById('mm-eq-modal');
        latex = document.getElementById('mm-eq-latex');
        previa = document.getElementById('mm-eq-previa');
        var caja = document.getElementById('mm-eq-campo');
        campo = latex;                                       // hasta que cargue el teclado
        crearPaleta();
        latex.addEventListener('input', function () {
            if (campo.tagName === 'MATH-FIELD' && campo.value !== latex.value) campo.value = latex.value;
            verPrevia();
        });
        cargarMathLive().then(function () {
            if (window.MathfieldElement) {          // cargado a mano: hay que decirle dónde están sus letras
                try { window.MathfieldElement.fontsDirectory = BASE_ML + 'fonts'; window.MathfieldElement.soundsDirectory = null; } catch (e) { /* nada */ }
            }
            var mf = document.createElement('math-field');
            mf.setAttribute('math-virtual-keyboard-policy', 'auto');
            mf.setAttribute('aria-label', 'Ecuación');
            caja.appendChild(mf);
            campo = mf;
            mf.addEventListener('input', function () { latex.value = mf.value; verPrevia(); });
            mf.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); aceptar(); } });
            try { mf.smartFence = true; mf.smartMode = false; } catch (e) { /* versión distinta */ }
            if (destino) { mf.value = latex.value; setTimeout(function () { mf.focus(); }, 50); }
        }).catch(function () {
            latex.closest('details').open = true;
            caja.innerHTML = '<div class="small text-warning">No cargó el teclado de ecuaciones (¿sin internet?). Puede escribirla en LaTeX o con los botones.</div>';
        });
        document.getElementById('mm-eq-insertar').addEventListener('click', aceptar);
        document.getElementById('mm-eq-quitar').addEventListener('click', function () { var d = destino; cerrar(); insertarEn(d, ''); });
        modal.addEventListener('shown.bs.modal', function () { (campo || latex).focus(); });
        modal.addEventListener('hidden.bs.modal', function () { if (window.mathVirtualKeyboard) try { window.mathVirtualKeyboard.hide(); } catch (e) { /* nada */ } });
    }
    function cerrar() { window.bootstrap.Modal.getOrCreateInstance(modal).hide(); }
    function aceptar() {
        var tex = valor().replace(/\\\)/g, ')');
        var d = destino; cerrar();
        if (d) insertarEn(d, tex);
    }
    function abrir(tex, dest) {
        preparar();
        destino = dest;
        latex.value = tex || '';
        if (campo.tagName === 'MATH-FIELD') campo.value = tex || '';
        document.getElementById('mm-eq-insertar').textContent = dest.span ? 'Guardar cambios' : 'Insertar';
        document.getElementById('mm-eq-quitar').classList.toggle('d-none', !dest.span);
        verPrevia();
        window.bootstrap.Modal.getOrCreateInstance(modal).show();
    }
    function abrirNueva() {
        if (!ultimo || !document.body.contains(ultimo.el)) {
            alert('Primero haga clic en el texto, la pregunta, la opción o la celda donde quiere la ecuación.');
            return;
        }
        abrir('', ultimo);
    }

    document.addEventListener('click', function (e) {
        var s = e.target.closest && e.target.closest('.mm-eqv');
        if (s && dentroDelEditor(s)) { e.preventDefault(); abrir(s.getAttribute('data-tex'), { span: s }); }
    });
    document.addEventListener('keydown', function (e) {
        if (e.altKey && (e.key === '=' || e.code === 'Equal') && dentroDelEditor(document.activeElement)) { e.preventDefault(); abrirNueva(); }
    });
    var boton = document.getElementById('mm-ecuacion-btn');
    if (boton) {
        boton.addEventListener('mousedown', function (e) { e.preventDefault(); });
        boton.addEventListener('click', abrirNueva);
    }
    document.documentElement.style.setProperty('--keyboard-zindex', '3000');

    window.MMEq = { aVista: aVista, aTexto: aTexto, vista: vista, span: span };
})();
