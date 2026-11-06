/* Editor de preguntas de los juegos (Gamificación).
 *
 * Dos formas de escribir las preguntas, las dos llenan el mismo cuadro de texto que recibe el servidor:
 *   · «Una por una»: cada pregunta con su cuadro y debajo sus opciones (A, B, C…), con la correcta marcada.
 *     El botón «Agregar opción» llega hasta las que caben en el juego escogido (boxeo: 2; carretera: 6…).
 *     Si se pega en el enunciado un bloque con varias preguntas y sus opciones, se reparten solas.
 *   · «Pegar varias»: el cuadro de texto de siempre (1. Pregunta / A) … / *B) …).
 * Y la calculadora de símbolos (² √ π ≤ ∈ …) escribe en el último cuadro que se tocó.
 *
 *   EditorPreguntas.montar({form, texto, tipos: {tipo: maxOpciones}})
 */
(function () {
    'use strict';
    const LETRAS = 'ABCDEFGH';
    const NUM = /^\s*(?:pregunta\s*)?\d{1,3}\s*[.)\-:]\s*(.*)$/i, TIEMPO = /^\s*[\[(]\s*\d{1,2}(?::\d{1,2}){1,2}\s*[\])]\s*(.*)$/;
    const OPC = /^\s*(\*)?\s*([A-Ha-h])[).\-:]\s+(.+)$/, RESP = /^\s*(ANSWER|RESPUESTA|CORRECTA)\s*[:=]\s*([A-Ha-h])\s*$/i;

    // Lee el texto pegado igual que el servidor (aula/invertida.py: leer_preguntas)
    function leer(texto) {
        const lista = [];
        let actual = null;
        function cerrar() {
            if (actual) {
                const t = actual.texto.join(' ').trim();
                if (t || actual.opciones.length) {
                    lista.push({texto: t, opciones: actual.opciones.map(o => ({texto: o.texto, correcta: o.marcada || o.letra === actual.respuesta}))});
                }
            }
            actual = null;
        }
        String(texto || '').split(/\r?\n/).forEach(linea => {
            const l = linea.trim();
            if (!l) { cerrar(); return; }
            let m = RESP.exec(l);
            if (m && actual) { actual.respuesta = m[2].toUpperCase(); cerrar(); return; }
            m = OPC.exec(l);
            if (m && actual && actual.texto.length) { actual.opciones.push({letra: m[2].toUpperCase(), texto: m[3].trim(), marcada: !!m[1]}); return; }
            m = NUM.exec(l) || TIEMPO.exec(l);
            if (m) { cerrar(); actual = {texto: m[1].trim() ? [m[1].trim()] : [], opciones: [], respuesta: null}; return; }
            if (!actual || actual.opciones.length) { cerrar(); actual = {texto: [], opciones: [], respuesta: null}; }
            actual.texto.push(l);
        });
        cerrar();
        return lista;
    }

    function escribir(lista) {
        return lista.filter(p => p.texto.trim() || p.opciones.some(o => o.texto.trim())).map((p, i) => {
            const ops = p.opciones.filter(o => o.texto.trim());
            return `${i + 1}. ${p.texto.replace(/\s*\n\s*/g, ' ').trim()}\n` +
                ops.map((o, k) => `${o.correcta ? '*' : ''}${LETRAS[k]}) ${o.texto.replace(/\s*\n\s*/g, ' ').trim()}`).join('\n');
        }).join('\n\n');
    }

    // ---------------- Calculadora de símbolos ----------------
    const GRUPOS = [
        ['Operaciones', '+ − × ÷ = ≠ ≈ ± ∓ · / % ( ) [ ] { } | …'],
        ['Potencias y raíces', '² ³ ⁴ ⁿ ⁻¹ √ ∛ ∜ ⁰ ¹ ⁵ ⁶ ⁷ ⁸ ⁹ ⁺ ⁻ ₀ ₁ ₂ ₃ ₙ'],
        ['Fracciones', '½ ⅓ ⅔ ¼ ¾ ⅕ ⅖ ⅗ ⅘ ⅙ ⅚ ⅛ ⅜ ⅝ ⅞ ⁄'],
        ['Comparar', '< > ≤ ≥ ≪ ≫ ∞ ∝ ≡'],
        ['Geometría', '° ∠ △ □ ○ ⊥ ∥ ≅ ∼ π ⌀ ′ ″ ⟂ ↔ →'],
        ['Conjuntos y lógica', '∈ ∉ ⊂ ⊆ ⊄ ∪ ∩ ∅ ℕ ℤ ℚ 𝕀 ℝ ℂ ∀ ∃ ⇒ ⇔ ¬ ∧ ∨ ∴'],
        ['Letras griegas', 'α β γ δ Δ ε θ λ μ π ρ σ Σ τ φ ω Ω'],
        ['Cálculo y funciones', '∑ ∏ ∫ ∂ ∇ lím→ f(x) f′(x) log ln sen cos tan dx'],
    ];
    function calcular(expr) {
        let e = String(expr || '').trim();
        if (!e) return '';
        const sup = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'};
        e = e.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]+/g, d => '^' + [...d].map(c => sup[c]).join(''))
             .replace(/×|·/g, '*').replace(/÷|:/g, '/').replace(/−/g, '-').replace(/,/g, '.').replace(/π/g, '(P)')
             .replace(/√\s*(\d+(?:\.\d+)?)/g, 'R($1)').replace(/√/g, 'R').replace(/∛\s*(\d+(?:\.\d+)?)/g, 'C($1)').replace(/∛/g, 'C')
             .replace(/(\d+(?:\.\d+)?)\s*%/g, '($1/100)').replace(/\^/g, '**');
        if (!/^[\d+\-*/().\sPRC]*$/.test(e)) return 'No entiendo la operación';
        try {
            const r = Function('P', 'R', 'C', '"use strict";return (' + e + ');')(Math.PI, Math.sqrt, Math.cbrt);
            if (typeof r !== 'number' || !isFinite(r)) return 'No da un número';
            return String(Math.round(r * 1e9) / 1e9).replace('.', ',');
        } catch (err) { return 'Revise la operación'; }
    }
    function calculadora(contenedor, destino) {
        const caja = document.createElement('div');
        caja.className = 'ep-calc border rounded-3 p-2 mb-2';
        caja.hidden = true;
        caja.innerHTML = `<div class="d-flex flex-wrap gap-1 mb-2 ep-tabs"></div><div class="d-flex flex-wrap gap-1 ep-simbolos"></div>
          <div class="d-flex gap-1 mt-2 align-items-center"><input type="text" class="form-control form-control-sm ep-expr" placeholder="Calcule: 3/4 + 1/2, 2³ − √49, 15% de 80 → 15%*80">
          <button type="button" class="btn btn-sm btn-outline-primary ep-igual" title="Calcular">=</button></div>
          <div class="d-flex gap-2 align-items-center mt-1 small"><span class="ep-res fw-bold"></span><button type="button" class="btn btn-sm btn-link p-0 ep-meter" hidden>Escribir el resultado</button></div>
          <div class="form-text m-0">Toque un símbolo y queda escrito en el cuadro donde estaba escribiendo.</div>`;
        contenedor.appendChild(caja);
        const tabs = caja.querySelector('.ep-tabs'), sims = caja.querySelector('.ep-simbolos');
        function verGrupo(g) {
            tabs.querySelectorAll('button').forEach((b, k) => b.className = 'btn btn-sm ' + (k === g ? 'btn-primary' : 'btn-outline-secondary'));
            sims.innerHTML = '';
            GRUPOS[g][1].split(' ').forEach(t => {
                const b = document.createElement('button'); b.type = 'button'; b.textContent = t;
                b.className = 'btn btn-sm btn-light border'; b.style.minWidth = '38px'; b.style.fontSize = '1.05rem';
                b.addEventListener('mousedown', ev => ev.preventDefault());      // no le quita el cursor al cuadro
                b.addEventListener('click', () => destino(t === 'lím→' ? 'lím x→' : t));
                sims.appendChild(b);
            });
        }
        GRUPOS.forEach((g, k) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = g[0]; b.addEventListener('click', () => verGrupo(k)); tabs.appendChild(b); });
        verGrupo(0);
        const expr = caja.querySelector('.ep-expr'), res = caja.querySelector('.ep-res'), meter = caja.querySelector('.ep-meter');
        function igual() { const r = calcular(expr.value); res.textContent = r ? '= ' + r : ''; meter.hidden = !r || /[a-z]/i.test(r); meter.dataset.valor = r; }
        caja.querySelector('.ep-igual').addEventListener('click', igual);
        expr.addEventListener('keydown', ev => { if (ev.key === 'Enter') { ev.preventDefault(); igual(); } });
        meter.addEventListener('mousedown', ev => ev.preventDefault());
        meter.addEventListener('click', () => destino(meter.dataset.valor || ''));
        return caja;
    }

    // ---------------- Editor ----------------
    function montar(cfg) {
        const form = cfg.form, area = cfg.texto, tipos = cfg.tipos || {};
        if (!form || !area) return;
        area.required = false;          // lo revisa el editor (el cuadro puede estar escondido)
        let preguntas = [], modo = 'una', ultimo = null;
        const max = () => { const t = form.querySelector('input[name="tipo"]:checked'); return (t && tipos[t.value]) || 4; };
        const nombreJuego = () => { const t = form.querySelector('input[name="tipo"]:checked'); return t ? (t.closest('label').querySelector('b') || {}).textContent || '' : ''; };

        const raiz = document.createElement('div');
        raiz.className = 'ep mb-2';
        raiz.innerHTML = `
          <div class="d-flex flex-wrap gap-2 align-items-center mb-2">
            <div class="btn-group btn-group-sm" role="group">
              <button type="button" class="btn ep-modo" data-modo="una"><i class="fas fa-list-ol me-1"></i>Una por una</button>
              <button type="button" class="btn ep-modo" data-modo="pegar"><i class="fas fa-paste me-1"></i>Pegar varias</button>
            </div>
            <button type="button" class="btn btn-sm btn-outline-dark ep-abrir-calc"><span class="fw-bold">∑√π</span> Calculadora de símbolos</button>
          </div>
          <div class="ep-calc-sitio"></div>
          <div class="small mb-2 ep-limite text-primary fw-semibold"></div>
          <div class="ep-lista"></div>
          <button type="button" class="btn btn-sm btn-outline-primary w-100 mb-2 ep-mas"><i class="fas fa-plus me-1"></i>Agregar pregunta</button>
          <div class="small text-danger fw-semibold ep-errores" aria-live="polite"></div>`;
        area.parentNode.insertBefore(raiz, area);
        // el cuadro de pegar queda dentro del editor, debajo de la lista
        raiz.insertBefore(area, raiz.querySelector('.ep-errores'));
        const lista = raiz.querySelector('.ep-lista'), errores = raiz.querySelector('.ep-errores');

        function escribirEn(t) {
            const el = ultimo && document.body.contains(ultimo) ? ultimo : (modo === 'pegar' ? area : lista.querySelector('textarea'));
            if (!el) return;
            const a = el.selectionStart ?? el.value.length, b = el.selectionEnd ?? el.value.length;
            el.value = el.value.slice(0, a) + t + el.value.slice(b);
            el.focus(); el.selectionStart = el.selectionEnd = a + t.length;
            el.dispatchEvent(new Event('input', {bubbles: true}));
        }
        const calc = calculadora(raiz.querySelector('.ep-calc-sitio'), escribirEn);
        raiz.querySelector('.ep-abrir-calc').addEventListener('click', () => { calc.hidden = !calc.hidden; });
        form.addEventListener('focusin', ev => { if (ev.target.matches('textarea, input[type="text"].ep-op, .ep-enun') && !ev.target.closest('.ep-calc')) ultimo = ev.target; });

        function vacia() { const n = Math.min(4, max()); return {texto: '', opciones: Array.from({length: n}, (_, k) => ({texto: '', correcta: k === 0}))}; }

        function sincronizar() { if (modo === 'una') area.value = escribir(preguntas); revisar(); }

        function revisar() {
            const mx = max(), ps = modo === 'una' ? preguntas : leer(area.value), malas = [], largas = [];
            ps.forEach((p, i) => {
                const ops = p.opciones.filter(o => o.texto.trim());
                if (!p.texto.trim() && !ops.length) return;
                if (ops.length > mx) largas.push(i + 1);
                else if (ops.length < 2 || ops.filter(o => o.correcta).length !== 1 || !p.texto.trim()) malas.push(i + 1);
            });
            const n = ps.filter(p => p.texto.trim() || p.opciones.some(o => o.texto.trim())).length;
            raiz.querySelector('.ep-limite').textContent = `${nombreJuego() || 'Este juego'}: cada pregunta lleva de 2 a ${mx} opciones (A a ${LETRAS[mx - 1]}) y una correcta.` + (n ? ` Lleva ${n} pregunta${n === 1 ? '' : 's'}.` : '');
            let msg = '';
            if (largas.length) msg += `Las preguntas ${largas.join(', ')} tienen más de ${mx} opciones: en este juego solo caben ${mx}. `;
            if (malas.length) msg += `Revise las preguntas ${malas.join(', ')}: falta el enunciado, opciones o marcar la correcta.`;
            errores.textContent = msg;
            lista.querySelectorAll('.ep-preg').forEach((c, i) => c.classList.toggle('border-danger', largas.includes(i + 1)));
            return !msg;
        }

        function pintar() {
            lista.innerHTML = '';
            const mx = max();
            preguntas.forEach((p, i) => {
                const c = document.createElement('div');
                c.className = 'ep-preg border rounded-3 p-2 mb-2 bg-light';
                c.innerHTML = `<div class="d-flex align-items-center gap-1 mb-1"><b class="small me-auto">Pregunta ${i + 1}</b>
                    <button type="button" class="btn btn-sm btn-link p-0 px-1 ep-sube" title="Subir">▲</button>
                    <button type="button" class="btn btn-sm btn-link p-0 px-1 ep-baja" title="Bajar">▼</button>
                    <button type="button" class="btn btn-sm btn-link text-danger p-0 px-1 ep-quita" title="Quitar la pregunta"><i class="fas fa-trash"></i></button></div>
                  <textarea class="form-control form-control-sm mb-1 ep-enun" rows="2" placeholder="Escriba la pregunta (o pegue aquí varias con sus opciones)"></textarea>
                  <div class="ep-ops"></div>
                  <button type="button" class="btn btn-sm btn-link p-0 ep-mas-op"></button>`;
                const enun = c.querySelector('.ep-enun');
                enun.value = p.texto;
                enun.addEventListener('input', () => { p.texto = enun.value; sincronizar(); });
                enun.addEventListener('paste', ev => {
                    // Si pegan un bloque con varias preguntas y opciones, se reparten en tarjetas
                    const t = (ev.clipboardData || window.clipboardData).getData('text');
                    const leidas = leer(t);
                    if (leidas.length > 1 || (leidas.length === 1 && leidas[0].opciones.length)) {
                        ev.preventDefault();
                        const vacio = !p.texto.trim() && !p.opciones.some(o => o.texto.trim());
                        preguntas.splice(i, vacio ? 1 : 0, ...leidas.map(q => ({texto: q.texto, opciones: q.opciones.length ? q.opciones : vacia().opciones})));
                        pintar(); sincronizar();
                    }
                });
                const ops = c.querySelector('.ep-ops');
                p.opciones.forEach((o, k) => {
                    const fila = document.createElement('div');
                    fila.className = 'd-flex align-items-center gap-1 mb-1' + (k >= mx ? ' opacity-50' : '');
                    fila.innerHTML = `<input type="radio" class="form-check-input mt-0" name="ep-c${i}" title="Es la correcta">
                      <span class="small fw-bold" style="width:1.4em">${LETRAS[k]})</span>
                      <input type="text" class="form-control form-control-sm ep-op" placeholder="Opción ${LETRAS[k]}${k === 0 ? ' (marque la correcta con el círculo)' : ''}">
                      <button type="button" class="btn btn-sm btn-link text-danger p-0 px-1" title="Quitar la opción">×</button>`;
                    const radio = fila.querySelector('input[type="radio"]'), txt = fila.querySelector('.ep-op');
                    radio.checked = !!o.correcta; txt.value = o.texto;
                    radio.addEventListener('change', () => { p.opciones.forEach(x => { x.correcta = x === o; }); sincronizar(); });
                    txt.addEventListener('input', () => { o.texto = txt.value; sincronizar(); });
                    fila.querySelector('button').addEventListener('click', () => {
                        p.opciones.splice(k, 1);
                        if (o.correcta && p.opciones[0]) p.opciones[0].correcta = true;
                        pintar(); sincronizar();
                    });
                    ops.appendChild(fila);
                });
                const masOp = c.querySelector('.ep-mas-op');
                masOp.innerHTML = p.opciones.length < mx ? `<i class="fas fa-plus me-1"></i>Agregar opción (${p.opciones.length} de ${mx})` : `Ya tiene las ${mx} opciones que caben en este juego`;
                masOp.disabled = p.opciones.length >= mx;
                masOp.addEventListener('click', () => { if (p.opciones.length < max()) { p.opciones.push({texto: '', correcta: !p.opciones.length}); pintar(); sincronizar(); const l = lista.children[i].querySelectorAll('.ep-op'); l[l.length - 1].focus(); } });
                c.querySelector('.ep-sube').addEventListener('click', () => { if (i) { [preguntas[i - 1], preguntas[i]] = [preguntas[i], preguntas[i - 1]]; pintar(); sincronizar(); } });
                c.querySelector('.ep-baja').addEventListener('click', () => { if (i < preguntas.length - 1) { [preguntas[i + 1], preguntas[i]] = [preguntas[i], preguntas[i + 1]]; pintar(); sincronizar(); } });
                c.querySelector('.ep-quita').addEventListener('click', () => { preguntas.splice(i, 1); if (!preguntas.length) preguntas.push(vacia()); pintar(); sincronizar(); });
                lista.appendChild(c);
            });
        }

        function ponerModo(m) {
            if (m === 'una' && modo === 'pegar') { preguntas = leer(area.value); if (!preguntas.length) preguntas = [vacia()]; }
            if (m === 'pegar' && modo === 'una') area.value = escribir(preguntas);
            modo = m;
            raiz.querySelectorAll('.ep-modo').forEach(b => { b.className = 'btn ep-modo ' + (b.dataset.modo === m ? 'btn-primary' : 'btn-outline-primary'); });
            const una = m === 'una';
            lista.hidden = !una; raiz.querySelector('.ep-mas').hidden = !una;
            area.hidden = una;
            const ayuda = form.querySelector('.ep-ayuda-pegar'); if (ayuda) ayuda.hidden = una;
            if (una) pintar();
            revisar();
        }
        raiz.querySelectorAll('.ep-modo').forEach(b => b.addEventListener('click', () => ponerModo(b.dataset.modo)));
        raiz.querySelector('.ep-mas').addEventListener('click', () => { preguntas.push(vacia()); pintar(); sincronizar(); const t = lista.querySelectorAll('.ep-enun'); t[t.length - 1].focus(); });
        area.addEventListener('input', revisar);
        form.querySelectorAll('input[name="tipo"]').forEach(r => r.addEventListener('change', () => { if (modo === 'una') pintar(); revisar(); }));
        form.addEventListener('submit', ev => {
            if (modo === 'una') area.value = escribir(preguntas);
            const vacio = !area.value.trim();
            if (vacio && area.dataset.opcional === '1') return;   // animaplano: la plataforma arma las preguntas
            if (!revisar() || vacio) { ev.preventDefault(); errores.textContent = errores.textContent || 'Escriba al menos una pregunta con sus opciones.'; errores.scrollIntoView({block: 'center'}); }
        });

        // Empieza en «una por una» con lo que traiga el borrador (o una pregunta vacía)
        modo = 'pegar';
        ponerModo('una');
    }

    window.EditorPreguntas = {montar, leer, escribir, calcular};
})();
