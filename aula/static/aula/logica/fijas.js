/* Picas y fijas con figuras: hay un orden secreto de figuras. El jugador acomoda las suyas y prueba;
 * solo se le dice cuántas están exactas en su sitio (fijas) y cuántas están pero en otro sitio (picas),
 * nunca cuáles. Cuenta el tiempo y los intentos hasta acertar.
 * Modo entre dos: un compañero arma el orden secreto, lo cierra y le pasa el celular al otro. */
(function () {
    'use strict';
    // Las figuras: forma y color (dibujadas en SVG, iguales en todos los equipos)
    const FIG = [
        {n: 'Círculo rojo', c: '#e03131', d: '<circle cx="20" cy="20" r="15"/>'},
        {n: 'Cuadrado azul', c: '#1971c2', d: '<rect x="6" y="6" width="28" height="28" rx="3"/>'},
        {n: 'Triángulo verde', c: '#2f9e44', d: '<path d="M20 4 L36 34 L4 34 Z"/>'},
        {n: 'Estrella amarilla', c: '#f59f00', d: '<path d="M20 3 L25 15 L38 15 L27.5 23 L31.5 36 L20 28 L8.5 36 L12.5 23 L2 15 L15 15 Z"/>'},
        {n: 'Corazón rosado', c: '#e64980', d: '<path d="M20 35 C6 25 2 17 7 10 C11 5 17 6 20 11 C23 6 29 5 33 10 C38 17 34 25 20 35 Z"/>'},
        {n: 'Rombo morado', c: '#7048e8', d: '<path d="M20 3 L36 20 L20 37 L4 20 Z"/>'},
        {n: 'Hexágono naranja', c: '#e8590c', d: '<path d="M11 5 L29 5 L38 20 L29 35 L11 35 L2 20 Z"/>'},
        {n: 'Luna turquesa', c: '#0c8599', d: '<path d="M26 4 A16 16 0 1 0 36 28 A13 13 0 1 1 26 4 Z"/>'},
    ];
    const PRESETS = [[4, 3], [5, 3], [5, 4], [6, 4], [6, 5], [7, 5], [8, 5], [8, 6], [8, 6, true]];
    const svg = (k, tam) => `<svg viewBox="0 0 40 40" width="${tam}" height="${tam}" aria-label="${FIG[k].n}"><g fill="${FIG[k].c}" stroke="rgba(0,0,0,.25)" stroke-width="1.5">${FIG[k].d}</g></svg>`;
    function puntuar(secreto, intento) {
        let fijas = 0; const a = {}, b = {};
        secreto.forEach((s, i) => { if (s === intento[i]) fijas++; else { a[s] = (a[s] || 0) + 1; b[intento[i]] = (b[intento[i]] || 0) + 1; } });
        let picas = 0; Object.keys(b).forEach(k => { picas += Math.min(b[k], a[k] || 0); });
        return {fijas, picas};
    }
    Logica.registrar('fijas', {
        nombre: 'Picas y fijas con figuras',
        instrucciones: 'Adivine el orden secreto de figuras. Toque las figuras para ponerlas en los puestos y presione Probar. Fijas = figuras exactas en su sitio; picas = figuras que sí están pero en otro sitio. Nunca se dice cuáles. Con «Ajustes» escoge cuántas figuras y puestos, y el modo entre dos.',
        total: () => PRESETS.length,
        titulo: (d, i) => { const [f, p, r] = PRESETS[i]; return `${f} figuras · ${p} puestos${r ? ' · con repetidas' : ''}`; },
        iniciar(zona, datos, i, api) {
            let [nFig, nPos, repetidas] = PRESETS[i], modo = 'solo';
            let secreto = [], actual = [], intentos = [], inicio = 0, fin = false, fase = 'juego';
            const caja = document.createElement('div');
            caja.style.cssText = 'width:100%;max-width:760px;margin:0 auto;font-family:system-ui,sans-serif';
            zona.appendChild(caja);
            const az = n => Math.floor(Math.random() * n);
            function nuevoSecreto() {
                if (repetidas) return Array.from({length: nPos}, () => az(nFig));
                const lista = [...Array(nFig).keys()].sort(() => Math.random() - .5); return lista.slice(0, nPos);
            }
            function empezar() {
                actual = []; intentos = []; fin = false; inicio = 0;
                const t = document.getElementById('lg-nivel-titulo');
                if (t && !api.compacto) t.textContent = `${nFig} figuras · ${nPos} puestos${repetidas ? ' · con repetidas' : ''}${modo === 'dos' ? ' · entre dos' : ''}`;
                if (modo === 'dos') { fase = 'armar'; secreto = []; } else { fase = 'juego'; secreto = nuevoSecreto(); }
                pintar();
            }
            const reloj = () => { if (!inicio) return '0:00'; const s = Math.floor((performance.now() - inicio) / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
            const tic = setInterval(() => { if (!caja.isConnected) { clearInterval(tic); return; } if (!fin && fase === 'juego') { const r = caja.querySelector('.fj-reloj'); if (r) r.textContent = reloj(); } }, 500);
            function puestos(lista, tam, clic) {
                return `<div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">${Array.from({length: nPos}, (_, k) => `<button type="button" data-p="${k}" ${clic ? '' : 'disabled'} style="width:${tam + 14}px;height:${tam + 14}px;border-radius:12px;border:3px ${lista[k] === undefined ? 'dashed #adb5bd' : 'solid #dee2e6'};background:#fff;padding:4px">${lista[k] === undefined ? `<small style="color:#adb5bd">${k + 1}</small>` : svg(lista[k], tam)}</button>`).join('')}</div>`;
            }
            function paleta() {
                return `<div style="display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin:10px 0">${Array.from({length: nFig}, (_, k) => {
                    const usada = !repetidas && actual.includes(k);
                    return `<button type="button" data-f="${k}" ${usada ? 'disabled' : ''} title="${FIG[k].n}" style="border:2px solid #dee2e6;border-radius:12px;background:#f8f9fa;padding:4px;opacity:${usada ? .3 : 1}">${svg(k, 40)}</button>`;
                }).join('')}</div>`;
            }
            function pintar() {
                const ajustes = api.compacto ? '' : `<details class="mb-2" ${fase === 'config' ? 'open' : ''}><summary class="small fw-bold" style="cursor:pointer">⚙️ Ajustes (figuras, puestos y modo)</summary>
                    <div class="d-flex flex-wrap gap-2 align-items-end mt-2 small">
                      <label>Figuras <select class="form-select form-select-sm fj-nf">${[4, 5, 6, 7, 8].map(v => `<option ${v === nFig ? 'selected' : ''}>${v}</option>`).join('')}</select></label>
                      <label>Puestos <select class="form-select form-select-sm fj-np">${[3, 4, 5, 6].map(v => `<option ${v === nPos ? 'selected' : ''}>${v}</option>`).join('')}</select></label>
                      <label class="mb-1"><input type="checkbox" class="form-check-input fj-rep" ${repetidas ? 'checked' : ''}> Se pueden repetir</label>
                      <label>Modo <select class="form-select form-select-sm fj-modo"><option value="solo" ${modo === 'solo' ? 'selected' : ''}>Contra la máquina</option><option value="dos" ${modo === 'dos' ? 'selected' : ''}>Entre dos (un compañero arma el orden)</option></select></label>
                      <button type="button" class="btn btn-sm btn-primary fj-aplicar">Aplicar y empezar</button>
                    </div></details>`;
                if (fase === 'armar') {
                    caja.innerHTML = ajustes + `<div class="alert alert-info text-center py-2 mb-2"><b>Modo entre dos.</b> Quien arma: ponga el orden secreto (sin que su compañero mire) y presione «Cerrar el orden».</div>
                      ${puestos(actual, 46, true)}${paleta()}
                      <div class="text-center"><button type="button" class="btn btn-dark fj-cerrar" ${actual.filter(x => x !== undefined).length === nPos ? '' : 'disabled'}>🔒 Cerrar el orden</button></div>`;
                } else if (fase === 'pasar') {
                    caja.innerHTML = ajustes + `<div class="text-center p-4" style="background:#1f3a68;color:#fff;border-radius:16px">
                      <div style="font-size:3rem">🔒📱</div><h4 class="fw-bold">Orden cerrado</h4><p>Pásele el celular a su compañero. Cuando esté listo, empieza el cronómetro.</p>
                      <button type="button" class="btn btn-warning btn-lg fj-listo">Listo, ¡a adivinar!</button></div>`;
                } else {
                    const ult = intentos.slice().reverse();
                    caja.innerHTML = ajustes + `<div class="d-flex justify-content-center gap-3 mb-2 small">
                        <span>⏱ <b class="fj-reloj">${reloj()}</b></span><span>Intentos: <b>${intentos.length}</b></span>
                        <span>Secreto: ${fin ? '' : `<b>${nPos}</b> figura(s) de <b>${nFig}</b>${repetidas ? ' (pueden repetirse)' : ''}`}</span></div>
                      ${fin ? `<div class="text-center mb-2"><div class="small fw-bold text-success mb-1">El orden secreto era:</div>${puestos(secreto, 40, false)}</div>` : ''}
                      ${fin ? '' : puestos(actual, 46, true) + paleta() + `<div class="text-center d-flex gap-2 justify-content-center"><button type="button" class="btn btn-success btn-lg fj-probar" ${actual.filter(x => x !== undefined).length === nPos ? '' : 'disabled'}>Probar</button>${modo === 'dos' ? '<button type="button" class="btn btn-outline-secondary fj-rendir">Rendirse y revelar</button>' : ''}</div>`}
                      <div class="mt-3" style="max-height:280px;overflow:auto">${ult.map((t, j) => `<div class="d-flex align-items-center gap-2 border-bottom py-1 justify-content-center">
                        <small class="text-muted" style="width:26px">${intentos.length - j}.</small>
                        <div class="d-flex gap-1">${t.lista.map(k => svg(k, 26)).join('')}</div>
                        <span class="badge" style="background:#2f9e44;font-size:.85rem" title="Exactas en su sitio">✔ ${t.fijas} fija${t.fijas === 1 ? '' : 's'}</span>
                        <span class="badge" style="background:#f59f00;font-size:.85rem" title="Están, pero en otro sitio">↔ ${t.picas} pica${t.picas === 1 ? '' : 's'}</span></div>`).join('')}</div>`;
                }
                // eventos
                caja.querySelectorAll('[data-f]').forEach(b => b.addEventListener('click', () => {
                    const libre = [...Array(nPos).keys()].find(k => actual[k] === undefined);
                    if (libre === undefined) return;
                    actual[libre] = +b.dataset.f; if (!inicio && fase === 'juego') inicio = performance.now(); api.sonido('toque'); pintar();
                }));
                caja.querySelectorAll('[data-p]').forEach(b => b.addEventListener('click', () => { actual[+b.dataset.p] = undefined; pintar(); }));
                const q = s => caja.querySelector(s);
                if (q('.fj-probar')) q('.fj-probar').addEventListener('click', probar);
                if (q('.fj-cerrar')) q('.fj-cerrar').addEventListener('click', () => { secreto = actual.slice(); actual = []; fase = 'pasar'; pintar(); });
                if (q('.fj-listo')) q('.fj-listo').addEventListener('click', () => { fase = 'juego'; inicio = performance.now(); pintar(); });
                if (q('.fj-rendir')) q('.fj-rendir').addEventListener('click', () => { fin = true; api.aviso('Se reveló el orden secreto.'); pintar(); });
                if (q('.fj-aplicar')) q('.fj-aplicar').addEventListener('click', () => {
                    nFig = +q('.fj-nf').value; nPos = +q('.fj-np').value; repetidas = q('.fj-rep').checked; modo = q('.fj-modo').value;
                    if (!repetidas && nPos > nFig) { nPos = nFig; api.aviso('Sin repetidas, los puestos no pueden ser más que las figuras.'); }
                    empezar();
                });
            }
            function probar() {
                const lista = actual.slice(), r = puntuar(secreto, lista);
                intentos.push({lista, ...r}); actual = []; api.movimiento();
                api.sonido(r.fijas === nPos ? 'gano' : r.fijas || r.picas ? 'bien' : 'mal');
                if (r.fijas === nPos) {
                    fin = true; pintar();
                    const n = intentos.length, meta = nPos + 1;
                    api.gano({estrellas: n <= meta ? 3 : n <= meta * 2 ? 2 : 1, detalle: `${n} intento(s) en ${reloj()}`});
                    return;
                }
                pintar();
            }
            empezar();
            return {};
        },
    });
})();
