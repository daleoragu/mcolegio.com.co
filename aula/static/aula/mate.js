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
        t = t.replace(/(\d|\})\s*(mm|cm|km|m|kg|g|s|h)(?![a-zA-Z])(\^\{[0-9]\})?/g, (x, d, u, e) => `${d}\\,\\text{${u}}${e || ''}`);
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

    /* ===================== Fórmulas dibujadas en el lienzo de los juegos =====================
     * Mismo aspecto que KaTeX (usa sus mismas letras): fracciones apiladas, potencias, raíces,
     * paréntesis que crecen y variables en cursiva. Entiende el LaTeX que produce aLatex.
     *   Mate.dibujarLienzo(ctx, texto, x, y, {tam, fuente, color, sombra, alinear, base, ancho})
     *   Mate.partirLienzo(texto, ancho, {tam, fuente})   ← renglones (nunca parte una fórmula)
     *   Mate.tieneFormula(texto)
     */
    const FM = 'KaTeX_Main, "Times New Roman", serif', FI = 'KaTeX_Math, "Times New Roman", serif';
    const ESCALA = 1.45;                  // las fórmulas, un poco más grandes que la letra de píxeles del juego
    const BIN = '+−±×÷·∪∩', REL = '=<>≤≥≠≈∈∉⊂⊆:';
    const SIMB = {times: '×', div: '÷', cdot: '·', le: '≤', leq: '≤', ge: '≥', geq: '≥', ne: '≠', neq: '≠', approx: '≈', pm: '±',
        pi: 'π', infty: '∞', circ: '∘', angle: '∠', triangle: '△', in: '∈', notin: '∉', cup: '∪', cap: '∩', subset: '⊂',
        subseteq: '⊆', emptyset: '∅', alpha: 'α', beta: 'β', gamma: 'γ', theta: 'θ', lambda: 'λ', mu: 'μ', Delta: 'Δ',
        to: '→', rightarrow: '→', cdots: '⋯', ldots: '…', degree: '°', prime: '′', lbrace: '{', rbrace: '}', vert: '|'};
    const FUNC = ['log', 'ln', 'sin', 'cos', 'tan', 'lim', 'max', 'min', 'exp'];
    const ESPACIO = {',': .17, ':': .22, ';': .28, ' ': .25, quad: 1, qquad: 2, '!': -.17};
    let medidor = null;
    function mctx() { if (!medidor) medidor = document.createElement('canvas').getContext('2d'); return medidor; }

    function analizar(s) {
        let i = 0;
        const blancos = () => { while (s[i] === ' ') i++; };
        function crudo() {
            blancos();
            if (s[i] !== '{') return s[i++] || '';
            let n = 0, j = i;
            for (; j < s.length; j++) { if (s[j] === '{') n++; else if (s[j] === '}' && !--n) break; }
            const t = s.slice(i + 1, j); i = j + 1; return t;
        }
        function grupo() {
            blancos();
            if (s[i] === '{') { i++; const l = lista('}'); i++; return {k: 'g', l}; }
            const n = atomo(); return {k: 'g', l: n ? [n] : []};
        }
        function delim() {
            blancos();
            if (s[i] === '\\') { const m = /^\\([a-zA-Z]+|.)/.exec(s.slice(i)); i += m[0].length; return SIMB[m[1]] || (m[1] === '|' ? '‖' : m[1]); }
            const c = s[i++] || ''; return c === '.' ? '' : c;
        }
        function lista(fin) {
            const l = [];
            while (i < s.length && s[i] !== fin) {
                if (fin === 'R' && s.startsWith('\\right', i)) break;
                const c = s[i];
                if (c === '^' || c === '_') {
                    i++; const e = grupo(), b = l.pop() || {k: 't', s: '', f: FM};
                    if (b.k === 'exp' && !b[c]) { b[c] = e; l.push(b); } else l.push({k: 'exp', b, [c]: e});
                    continue;
                }
                const n = atomo(); if (n) l.push(n);
            }
            return l;
        }
        function sim(c) {
            if (c === '-') c = '−'; else if (c === '*') c = '×';
            const clase = BIN.includes(c) ? 'bin' : REL.includes(c) ? 'rel' : /[(\[{]/.test(c) ? 'abre' : '';
            return {k: 't', s: c, f: /[a-zA-Zαβγθλμπ]/.test(c) ? FI : FM, clase};
        }
        function atomo() {
            const c = s[i];
            if (c === ' ') { i++; return null; }
            if (c === '{') { i++; const l = lista('}'); i++; return {k: 'g', l}; }
            if (c === '}') { i++; return null; }
            if (c === '\\') {
                const m = /^\\([a-zA-Z]+|.)/.exec(s.slice(i)); i += m[0].length; const cmd = m[1];
                if (cmd === 'frac' || cmd === 'dfrac' || cmd === 'tfrac') return {k: 'frac', a: grupo(), b: grupo()};
                if (cmd === 'sqrt') {
                    let n = null; blancos();
                    if (s[i] === '[') { const j = s.indexOf(']', i); n = {k: 'g', l: analizar(s.slice(i + 1, j))}; i = j + 1; }
                    return {k: 'raiz', n, a: grupo()};
                }
                if (cmd === 'left') { const a = delim(), l = lista('R'); if (s.startsWith('\\right', i)) i += 6; return {k: 'del', a, b: delim(), l}; }
                if (cmd === 'right') return null;
                if (['text', 'textrm', 'mathrm', 'operatorname', 'textbf', 'mathbf'].includes(cmd)) return {k: 't', s: crudo(), f: FM, op: cmd === 'operatorname'};
                if (cmd === 'mathbb') { const t = crudo(); return {k: 't', s: {R: 'ℝ', N: 'ℕ', Z: 'ℤ', Q: 'ℚ', C: 'ℂ'}[t] || t, f: FM}; }
                if (FUNC.includes(cmd)) return {k: 't', s: cmd === 'sin' ? 'sen' : cmd === 'lim' ? 'lím' : cmd, f: FM, op: true};
                if (ESPACIO[cmd] !== undefined) return {k: 'sp', w: ESPACIO[cmd]};
                if (SIMB[cmd]) return sim(SIMB[cmd]);
                if (cmd.length === 1) return sim(cmd);
                return {k: 't', s: cmd, f: FM};
            }
            i++;
            return sim(c);
        }
        return lista(null);
    }

    // Caja = {w, a (sube), d (baja), dib(ctx, x, yBase)}
    function cajaTexto(t, f, s) {
        const c = mctx(); c.font = `${s}px ${f}`;
        const m = c.measureText(t);
        const a = Math.max(m.actualBoundingBoxAscent || 0, .45 * s), d = Math.max(m.actualBoundingBoxDescent || 0, 0);
        const w = m.width + (f === FI ? .06 * s : 0);
        return {w, a, d, dib(ctx, x, y) { ctx.font = `${s}px ${f}`; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; ctx.fillText(t, x, y); }};
    }
    function cajaLista(l, s) {
        const piezas = []; let w = 0, a = .45 * s, d = 0, prev = null;
        l.forEach(n => {
            const b = caja(n, s);
            let lado = 0;          // espacio a cada lado de + − = ≤ … (un − al comienzo o tras otro operador es signo: sin espacio)
            if (n.clase === 'bin') lado = (!prev || ['bin', 'rel', 'abre'].includes(prev.clase)) ? 0 : .22;
            else if (n.clase === 'rel') lado = .28;
            if (prev && prev.op && n.k !== 'sp') w += .17 * s;
            w += lado * s; piezas.push({b, x: w}); w += b.w + lado * s;
            a = Math.max(a, b.a); d = Math.max(d, b.d); prev = n;
        });
        return {w, a, d, dib(ctx, x, y) { piezas.forEach(p => p.b.dib(ctx, x + p.x, y)); }};
    }
    function caja(n, s) {
        switch (n.k) {
        case 't': return cajaTexto(n.s, n.f, s);
        case 'sp': return {w: n.w * s, a: 0, d: 0, dib() {}};
        case 'g': return cajaLista(n.l, s);
        case 'frac': {
            const sz = Math.max(s * .86, 6), A = cajaLista(n.a.l, sz), B = cajaLista(n.b.l, sz);
            const eje = .26 * s, gr = Math.max(1, .055 * s), hueco = .14 * s, w = Math.max(A.w, B.w) + .24 * s;
            const yA = -(eje + gr / 2 + hueco + A.d), yB = -eje + gr / 2 + hueco + B.a;
            return {w: w + .1 * s, a: eje + gr / 2 + hueco + A.a + A.d, d: -eje + gr / 2 + hueco + B.a + B.d,
                dib(ctx, x, y) {
                    x += .05 * s;
                    A.dib(ctx, x + (w - A.w) / 2, y + yA); B.dib(ctx, x + (w - B.w) / 2, y + yB);
                    ctx.fillRect(x, y - eje - gr / 2, w, gr);
                }};
        }
        case 'exp': {
            const B = caja(n.b, s), sz = Math.max(s * .7, 5);
            const E = n['^'] ? cajaLista(n['^'].l, sz) : null, S = n['_'] ? cajaLista(n['_'].l, sz) : null;
            const sube = E ? Math.max(.4 * s, B.a - .38 * s) : 0, baja = S ? Math.max(.2 * s, B.d + .1 * s) : 0;
            const w = B.w + Math.max(E ? E.w : 0, S ? S.w : 0) + .03 * s;
            return {w, a: Math.max(B.a, E ? sube + E.a : 0), d: Math.max(B.d, S ? baja + S.d : 0),
                dib(ctx, x, y) { B.dib(ctx, x, y); if (E) E.dib(ctx, x + B.w - (n.b.f === FI ? .03 * s : 0), y - sube); if (S) S.dib(ctx, x + B.w, y + baja); }};
        }
        case 'raiz': {
            const C = cajaLista(n.a.l, s), N = n.n ? cajaLista(n.n.l, Math.max(s * .5, 5)) : null;
            const gr = Math.max(1, .055 * s), hueco = .12 * s, alto = C.a + hueco + gr, signo = .62 * s;
            const corre = N ? Math.max(0, N.w - .28 * s) : 0;
            return {w: corre + signo + C.w + .14 * s, a: alto + .04 * s, d: C.d + .04 * s,
                dib(ctx, x, y) {
                    x += corre;
                    const arriba = y - alto + gr / 2, abajo = y + C.d;
                    ctx.save(); ctx.lineWidth = gr; ctx.strokeStyle = ctx.fillStyle; ctx.lineJoin = 'round';
                    ctx.beginPath(); ctx.moveTo(x + .04 * s, y - .32 * s); ctx.lineTo(x + .16 * s, y - .38 * s);
                    ctx.lineTo(x + .32 * s, abajo); ctx.lineTo(x + signo - .04 * s, arriba); ctx.lineTo(x + signo + C.w + .1 * s, arriba);
                    ctx.stroke(); ctx.restore();
                    if (N) N.dib(ctx, x - corre + .02 * s, y - .5 * s);
                    C.dib(ctx, x + signo + .04 * s, y);
                }};
        }
        case 'del': {
            const C = cajaLista(n.l, s);
            const chico = C.a + C.d <= 1.15 * s;
            if (chico) {
                const A = n.a ? cajaTexto(n.a, FM, s) : null, B = n.b ? cajaTexto(n.b, FM, s) : null;
                const wa = A ? A.w : 0;
                return {w: wa + C.w + (B ? B.w : 0), a: Math.max(C.a, A ? A.a : 0), d: Math.max(C.d, A ? A.d : 0),
                    dib(ctx, x, y) { if (A) A.dib(ctx, x, y); C.dib(ctx, x + wa, y); if (B) B.dib(ctx, x + wa + C.w, y); }};
            }
            const ad = .36 * s, a = C.a + .06 * s, d = C.d + .06 * s;
            const raya = (ctx, ch, x, y, der) => {
                if (!ch) return;
                const t = y - a, b = y + d, m = (t + b) / 2;
                ctx.save(); ctx.lineWidth = Math.max(1, .07 * s); ctx.strokeStyle = ctx.fillStyle; ctx.beginPath();
                const ex = der ? x + .06 * s : x + ad - .06 * s, in_ = der ? x + ad - .1 * s : x + .1 * s;
                if (ch === '(' || ch === ')') { ctx.moveTo(ex, t); ctx.quadraticCurveTo(in_ - (der ? -.08 : .08) * s, m, ex, b); }
                else if (ch === '[' || ch === ']') { ctx.moveTo(ex, t); ctx.lineTo(in_, t); ctx.lineTo(in_, b); ctx.lineTo(ex, b); }
                else if (ch === '|' || ch === '‖') { ctx.moveTo(x + ad / 2, t); ctx.lineTo(x + ad / 2, b); }
                else { ctx.moveTo(ex, t); ctx.quadraticCurveTo(in_, t, in_, m - .1 * s); ctx.lineTo(der ? in_ + .08 * s : in_ - .08 * s, m);
                       ctx.lineTo(in_, m + .1 * s); ctx.quadraticCurveTo(in_, b, ex, b); }
                ctx.stroke(); ctx.restore();
            };
            return {w: ad * 2 + C.w, a, d, dib(ctx, x, y) { raya(ctx, n.a, x, y, false); C.dib(ctx, x + ad, y); raya(ctx, n.b, x + ad + C.w, y, true); }};
        }
        }
        return {w: 0, a: 0, d: 0, dib() {}};
    }

    const CACHE = new Map(), FORMULA = new Map();
    function cajaFormula(latex, s) {
        const k = s + '|' + latex;
        let c = CACHE.get(k);
        if (!c) {
            try { c = cajaLista(analizar(latex), s); } catch (e) { c = cajaTexto(latex, FM, s); }
            if (CACHE.size > 600) CACHE.clear();
            CACHE.set(k, c);
        }
        return c;
    }
    // Cuando terminen de cargar las letras de KaTeX se vuelve a medir todo
    if (document.fonts && document.fonts.load) {
        Promise.all(['16px KaTeX_Main', 'italic 16px KaTeX_Math'].map(f => document.fonts.load(f).catch(() => null)))
            .then(() => CACHE.clear());
        document.fonts.addEventListener && document.fonts.addEventListener('loadingdone', () => CACHE.clear());
    }

    function tieneFormula(texto) {
        texto = String(texto || '');
        let r = FORMULA.get(texto);
        if (r === undefined) {
            r = tramos(texto).some(z => z.t === undefined);
            if (FORMULA.size > 2000) FORMULA.clear();
            FORMULA.set(texto, r);
        }
        return r;
    }
    function pedazoTexto(t, o) {
        const c = mctx(), f = `${o.tam}px ${o.fuente}`; c.font = f;
        const a = c.measureText('H').actualBoundingBoxAscent || o.tam * .8;
        const w = c.measureText(t).width;
        return {w, a, d: 0, dib(ctx, x, y) { ctx.font = f; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; ctx.fillText(t, x, y); }};
    }
    // Un renglón (texto con fórmulas) como una sola caja
    function renglon(texto, o) {
        o = Object.assign({tam: 10, fuente: FM}, o);
        const s = o.tam * (o.escala || ESCALA);
        const piezas = []; let w = 0, a = 0, d = 0;
        tramos(texto).forEach(z => {
            const b = z.t !== undefined ? pedazoTexto(z.t, o) : cajaFormula(z.latex !== undefined ? z.latex : aLatex(z.m), s);
            piezas.push({b, x: w}); w += b.w; a = Math.max(a, b.a); d = Math.max(d, b.d);
        });
        return {w, a, d, dib(ctx, x, y) { piezas.forEach(p => p.b.dib(ctx, x + p.x, y)); }};
    }
    function dibujarLienzo(ctx, texto, x, y, o) {
        o = o || {};
        const r = renglon(String(texto || ''), o);
        const k = o.ancho && r.w > o.ancho ? Math.max(.4, o.ancho / r.w) : 1;
        const w = r.w * k, a = r.a * k, d = r.d * k;
        const al = o.alinear || 'left', base = o.base || 'top';
        const x0 = al === 'center' ? x - w / 2 : al === 'right' ? x - w : x;
        const yb = base === 'top' ? y + a : base === 'middle' ? y + (a - d) / 2 : base === 'bottom' ? y - d : y;
        ctx.save(); ctx.translate(x0, yb); if (k !== 1) ctx.scale(k, k);
        if (o.sombra) { ctx.save(); ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.translate(1 / k, 1 / k); r.dib(ctx, 0, 0); ctx.restore(); }
        ctx.fillStyle = o.color || '#fff'; r.dib(ctx, 0, 0);
        ctx.restore();
        return {w, a, d};
    }
    function medirLienzo(texto, o) { const r = renglon(String(texto || ''), o || {}); return {w: r.w, a: r.a, d: r.d}; }
    // Parte el texto en renglones que quepan en «ancho»; una fórmula nunca se parte
    function partirLienzo(texto, ancho, o) {
        const pedazos = [];
        tramos(String(texto || '')).forEach(z => {
            if (z.t !== undefined) z.t.split(/(\s+)/).forEach(p => { if (p) pedazos.push(p); });
            else pedazos.push(z.latex !== undefined ? '$' + z.latex + '$' : z.m);
        });
        const lineas = []; let linea = '';
        pedazos.forEach(p => {
            if (/^\s+$/.test(p)) { if (linea) linea += ' '; return; }
            const prueba = linea + p;
            if (linea.trim() && medirLienzo(prueba, o).w > ancho) { lineas.push(linea.trim()); linea = p; } else linea = prueba;
        });
        if (linea.trim()) lineas.push(linea.trim());
        return lineas;
    }

    function todos(raiz) { (raiz || document).querySelectorAll('.mate').forEach(render); }
    window.Mate = {render, html, plano, todos, aLatex, tramos, tieneFormula, dibujarLienzo, medirLienzo, partirLienzo};
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => todos()); else todos();
})();
