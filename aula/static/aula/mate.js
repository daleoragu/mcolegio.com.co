/* Fórmulas con formato profesional (KaTeX) en las preguntas.
 *
 * Las preguntas se escriben en texto normal ("¿Cuánto es 3/4 + 1/2?", "Factorice: x² − 49", "√(x − 1)",
 * "f(x) = 5x^3"). Mate encuentra los tramos que son matemáticas y los dibuja con KaTeX: fracciones apiladas,
 * potencias, raíces, ×, ÷, ≤, π y variables en cursiva. El resto del texto queda igual.
 * También se puede escribir LaTeX directo entre $…$ (por ejemplo $\frac{a}{b}$).
 *
 *   Mate.render(elemento)      ← dibuja las fórmulas del texto del elemento (se puede llamar varias veces)
 *   Mate.plano(texto)          ← quita el LaTeX ($\frac{3}{4}$ → 3/4) para dibujar en los juegos (lienzo)
 *   elementos con class="mate" se dibujan solos al cargar la página
 */
(function () {
    'use strict';
    if (window.Mate) return;
    const SUP = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁺': '+', '⁻': '-', 'ⁿ': 'n'};
    const FUNCIONES = ['sen', 'cos', 'tan', 'log', 'ln', 'lím', 'lim', 'mcm', 'mcd', 'máx', 'mín'];
    // Lo que puede ir dentro de una fórmula
    const CARACTER = /[0-9a-zA-Z()\[\]+\-−×÷·=^/√∛π.,<>≤≥≠≈∞°′″%²³¹⁰⁴⁵⁶⁷⁸⁹⁺⁻ⁿ |∠△∈∉∪∩⊂⊆∅ℕℤℚℝ±]/;
    const OPERADOR = /[+\-−×÷·=^/√∛≤≥<>≠≈²³⁴ⁿ±]/;

    function esc(t) { return t.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])); }

    const LETRAS_ES = /[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+/g;
    // ¿Puede ir dentro de una fórmula esta palabra? (números, letras sueltas como variables, f(x), 3x², 10^4, √(x−1),
    // operadores y funciones conocidas). Las palabras del idioma (dos letras o más) no.
    function palabraMate(p) {
        if (!p) return false;
        if (!/^[0-9a-zA-Z()\[\]+\-−×÷·=^/√∛π.,<>≤≥≠≈∞°′%²³¹⁰⁴⁵⁶⁷⁸⁹⁺⁻ⁿ|∠△∈∉∪∩⊂⊆∅ℕℤℚℝ±:;]+$/.test(p)) return false;
        const letras = p.match(LETRAS_ES) || [];
        return letras.every(l => l.length === 1 || FUNCIONES.includes(l.toLowerCase()));
    }
    // «y», «o», «a», «e» sueltas entre dos cosas que no son operadores: es una palabra de unión, no una variable
    function esUnion(p, ant, sig) {
        return /^(y|o|e|a)$/.test(p) && !OPERADOR.test((ant || '').slice(-1)) && !OPERADOR.test((sig || '').slice(0, 1));
    }

    /* Parte el texto en tramos: {t: texto} · {m: fórmula en texto plano} · {latex: LaTeX escrito entre $…$} */
    function tramos(texto) {
        const out = [];
        // LaTeX directo entre $…$ (solo si de verdad es LaTeX: lleva \ ^ _ o {, para no confundir precios como $2.000)
        String(texto).split(/(\$[^$]*[\\^_{][^$]*\$)/).forEach(p => {
            if (/^\$[^$]*[\\^_{][^$]*\$$/.test(p)) out.push({latex: p.slice(1, -1)});
            else buscar(p, out);
        });
        return out;
    }
    function buscar(texto, out) {
        const piezas = texto.split(/(\s+)/);          // palabras y espacios, en orden
        let run = [], txt = '';
        const soltarTexto = () => { if (txt) { out.push({t: txt}); txt = ''; } };
        const cerrarRun = () => {
            if (!run.length) return;
            // espacios del final del tramo vuelven al texto
            let fin = '';
            while (run.length && /^\s+$/.test(run[run.length - 1])) fin = run.pop() + fin;
            let f = run.join(''), antes = '', despues = '';
            // paréntesis que no cierran dentro del tramo: son del texto, no de la fórmula
            const abre = () => (f.match(/\(/g) || []).length, cierra = () => (f.match(/\)/g) || []).length;
            while (f.endsWith(')') && cierra() > abre()) { despues = ')' + despues; f = f.slice(0, -1); }
            while (f.startsWith('(') && abre() > cierra()) { antes += '('; f = f.slice(1); }
            if (f && esFormula(f)) { txt += antes; soltarTexto(); out.push({m: f}); txt += despues; } else txt += antes + f + despues;
            txt += fin; run = [];
        };
        piezas.forEach((pz, k) => {
            if (/^\s+$/.test(pz) || pz === '') { if (run.length) run.push(pz); else txt += pz; return; }
            // puntuación pegada a la palabra: ¿ ( al comienzo, ? . , ; : ) al final (si no es de la fórmula)
            const m = pz.match(/^([¿¡"«]*)(.*?)([?!.,;:"»]*)$/);
            let ini = m[1], nucleo = m[2], fin = m[3];
            const ant = piezas[k - 2], sig = piezas[k + 2];
            if (nucleo && palabraMate(nucleo) && !esUnion(nucleo, ant, sig)) {
                if (ini) { cerrarRun(); txt += ini; }
                run.push(nucleo);
                if (fin) { cerrarRun(); txt += fin; }
            } else {
                cerrarRun(); txt += pz;
            }
        });
        cerrarRun(); soltarTexto();
    }
    function esFormula(s) {
        if (!/[0-9a-zA-Zπ∞]/.test(s)) return false;
        if (/\d{1,2}\/\d{1,2}\/\d{2,4}/.test(s)) return false;           // fecha
        if (/^[0-9.,]+$/.test(s)) return false;                         // un número solo se queda como texto
        // una letra sola («A», «x») se queda como texto: puede ser una palabra («¿A qué…?»); 2x, 3a sí son fórmula
        return OPERADOR.test(s) || /[πℝℕℤℚ∞√]/.test(s) || /\b(sen|cos|tan|log|ln)\b/i.test(s) || /[a-zA-Z]\(/.test(s) || /^-?[0-9.,]+[a-zA-Z]$/.test(s);
    }

    /* Texto plano → LaTeX */
    function aLatex(s) {
        let t = s.replace(/−/g, '-');
        // superíndices unicode → ^{…}
        t = t.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ]+/g, m => '^{' + [...m].map(c => SUP[c]).join('') + '}');
        // raíces: √(…), √n, ∛(…)
        t = t.replace(/√\(([^()]*)\)/g, '\\sqrt{$1}').replace(/√([0-9a-zA-Z.,]+)/g, '\\sqrt{$1}');
        t = t.replace(/∛\(([^()]*)\)/g, '\\sqrt[3]{$1}').replace(/∛([0-9a-zA-Z.,]+)/g, '\\sqrt[3]{$1}');
        // potencias: a^b, a^(b), a^-1
        t = t.replace(/\^\(([^()]*)\)/g, '^{$1}').replace(/\^(-?[0-9a-zA-Z.,]+)/g, '^{$1}');
        // fracciones: a/b con a y b números, letras, potencias o grupos entre paréntesis
        const OPER = '(\\([^()]*\\)|\\\\sqrt\\{[^{}]*\\}|-?[0-9]+(?:[.,][0-9]+)?(?:[a-zA-Z](?![a-zA-Z]))?(?:\\^\\{[^{}]*\\})?|[a-zA-Z](?![a-zA-Z])(?:\\^\\{[^{}]*\\})?)';
        const reFr = new RegExp(OPER + '\\s*/\\s*' + OPER, 'g');
        let antes;
        do { antes = t; t = t.replace(reFr, (m, a, b) => `\\dfrac{${quitarParen(a)}}{${quitarParen(b)}}`); } while (t !== antes);
        t = t.replace(/×/g, '\\times ').replace(/÷/g, '\\div ').replace(/·/g, '\\cdot ').replace(/≤/g, '\\le ').replace(/≥/g, '\\ge ')
             .replace(/≠/g, '\\ne ').replace(/≈/g, '\\approx ').replace(/±/g, '\\pm ').replace(/π/g, '\\pi ').replace(/∞/g, '\\infty ')
             .replace(/°/g, '^{\\circ}').replace(/%/g, '\\%').replace(/∠/g, '\\angle ').replace(/△/g, '\\triangle ')
             .replace(/∈/g, '\\in ').replace(/∉/g, '\\notin ').replace(/∪/g, '\\cup ').replace(/∩/g, '\\cap ').replace(/⊂/g, '\\subset ')
             .replace(/⊆/g, '\\subseteq ').replace(/∅/g, '\\emptyset ').replace(/ℝ/g, '\\mathbb{R}').replace(/ℕ/g, '\\mathbb{N}')
             .replace(/ℤ/g, '\\mathbb{Z}').replace(/ℚ/g, '\\mathbb{Q}').replace(/′/g, "'");
        t = t.replace(/\b(sen|cos|tan|log|ln|lím|lim|mcm|mcd)\b/g, m => ({sen: '\\operatorname{sen}', cos: '\\cos', tan: '\\tan', log: '\\log', ln: '\\ln',
            'lím': '\\lim', lim: '\\lim', mcm: '\\operatorname{mcm}', mcd: '\\operatorname{mcd}'}[m]));
        t = t.replace(/(\d),(\d)/g, '$1{,}$2');       // coma decimal sin espacio
        // unidades en letra recta (no son variables): 18 m², 3 km
        t = t.replace(/(\d)\s*(mm|cm|km|m|kg|g|s|h)(?![a-zA-Z])(\^\{[0-9]\})?/g, (x, d, u, e) => `${d}\\,\\text{${u}}${e || ''}`);
        // paréntesis que crecen con lo que encierran
        t = t.replace(/\(([^()]*\\dfrac[^()]*)\)/g, '\\left($1\\right)');
        return t;
    }
    function quitarParen(a) { return /^\([^()]*\)$/.test(a) ? a.slice(1, -1) : a; }

    function html(texto) {
        if (!window.katex) return esc(String(texto));
        return tramos(texto).map(tz => {
            if (tz.t !== undefined) return esc(tz.t);
            const latex = tz.latex !== undefined ? tz.latex : aLatex(tz.m);
            try { return katex.renderToString(latex, {throwOnError: true, strict: false, output: 'html'}); }
            catch (e) { return esc(tz.latex !== undefined ? '$' + tz.latex + '$' : tz.m); }
        }).join('');
    }

    function render(el) {
        if (!el) return;
        const fuente = el.dataset.mateTexto !== undefined ? el.dataset.mateTexto : el.textContent;
        el.dataset.mateTexto = fuente;
        el.innerHTML = html(fuente);
    }

    /* LaTeX → texto plano (para los juegos que dibujan en un lienzo) */
    function plano(texto) {
        return String(texto).replace(/\$([^$]+)\$/g, (m, l) => l
            .replace(/\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}/g, '$1/$2').replace(/\\sqrt\{([^{}]*)\}/g, '√($1)')
            .replace(/\^\{2\}/g, '²').replace(/\^\{3\}/g, '³').replace(/\^\{([^{}]*)\}/g, '^$1')
            .replace(/\\times/g, '×').replace(/\\div/g, '÷').replace(/\\cdot/g, '·').replace(/\\le/g, '≤').replace(/\\ge/g, '≥')
            .replace(/\\pi/g, 'π').replace(/\\infty/g, '∞').replace(/\\pm/g, '±').replace(/\\left|\\right/g, '')
            .replace(/\\[a-zA-Z]+/g, '').replace(/[{}]/g, '').replace(/\s+/g, ' ').trim());
    }

    function todos(raiz) { (raiz || document).querySelectorAll('.mate').forEach(render); }
    window.Mate = {render, html, plano, todos, aLatex, tramos};
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => todos()); else todos();
})();
