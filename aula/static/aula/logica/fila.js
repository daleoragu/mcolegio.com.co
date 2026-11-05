/* La fila exacta: ordene a las personas en la fila cumpliendo todas las pistas.
 * Las pistas se generan para que haya una sola respuesta (se revisan todas las permutaciones). */
(function () {
    'use strict';
    const NOMBRES = [['Ana', '#e64980'], ['Beto', '#1c7ed6'], ['Caro', '#f59f00'], ['Dani', '#2f9e44'], ['Eva', '#7048e8'], ['Fede', '#e8590c'], ['Gina', '#0ca678']];
    function perms(a) { if (a.length <= 1) return [a]; const r = []; a.forEach((x, i) => perms(a.slice(0, i).concat(a.slice(i + 1))).forEach(p => r.push([x].concat(p)))); return r; }
    const az = n => Math.floor(Math.random() * n);
    // Cada pista: {txt, ok(p)} donde p[i] = persona en el puesto i
    function pistaAlAzar(sol, n) {
        const pos = {}; sol.forEach((x, i) => { pos[x] = i; });
        const A = az(n); let B = az(n); while (B === A) B = az(n);
        const nA = NOMBRES[A][0], nB = NOMBRES[B][0], tipo = az(8);
        const donde = p => { const o = {}; p.forEach((x, i) => { o[x] = i; }); return o; };
        if (tipo === 0 && pos[A] < pos[B]) return {txt: `${nA} está a la izquierda de ${nB} (no necesariamente al lado).`, ok: p => donde(p)[A] < donde(p)[B]};
        if (tipo === 1 && Math.abs(pos[A] - pos[B]) === 1) return {txt: `${nA} está al lado de ${nB}.`, ok: p => Math.abs(donde(p)[A] - donde(p)[B]) === 1};
        if (tipo === 2 && Math.abs(pos[A] - pos[B]) > 1) return {txt: `${nA} y ${nB} no están juntos.`, ok: p => Math.abs(donde(p)[A] - donde(p)[B]) > 1};
        if (tipo === 3) return {txt: `${nA} está en el puesto ${pos[A] + 1}.`, ok: p => donde(p)[A] === pos[A]};
        if (tipo === 4 && (pos[A] === 0 || pos[A] === n - 1)) return {txt: `${nA} está en uno de los extremos.`, ok: p => donde(p)[A] === 0 || donde(p)[A] === n - 1};
        if (tipo === 5 && pos[A] !== 0 && pos[A] !== n - 1) return {txt: `${nA} no está en ningún extremo.`, ok: p => donde(p)[A] !== 0 && donde(p)[A] !== n - 1};
        if (tipo === 6 && pos[A] !== 0 && pos[A] !== pos[B] + 1) { const d = pos[A] - pos[B]; if (d > 1) return {txt: `Entre ${nB} y ${nA} hay ${d - 1} persona(s), y ${nB} está más a la izquierda.`, ok: p => donde(p)[A] - donde(p)[B] === d}; }
        if (tipo === 7 && pos[A] !== pos[B] - 1) { const C = sol.find((x, i) => i > Math.min(pos[A], pos[B]) && i < Math.max(pos[A], pos[B])); if (C !== undefined) return {txt: `${NOMBRES[C][0]} está entre ${nA} y ${nB}.`, ok: p => { const o = donde(p); return o[C] > Math.min(o[A], o[B]) && o[C] < Math.max(o[A], o[B]); }}; }
        return null;
    }
    function generar(n) {
        for (let intento = 0; intento < 50; intento++) {
            const sol = perms([...Array(n).keys()])[az(perms([...Array(n).keys()]).length)];
            const todas = perms([...Array(n).keys()]);
            let pistas = [], quedan = todas;
            for (let k = 0; k < 400 && quedan.length > 1; k++) {
                const p = pistaAlAzar(sol, n); if (!p) continue;
                const nuevas = quedan.filter(p.ok);
                if (nuevas.length < quedan.length) { pistas.push(p); quedan = nuevas; }
            }
            if (quedan.length !== 1) continue;
            // quitar las pistas que sobran (así hay que pensar con todas)
            for (let j = pistas.length - 1; j >= 0; j--) {
                const sin = pistas.filter((_, x) => x !== j);
                if (todas.filter(p => sin.every(c => c.ok(p))).length === 1) pistas = sin;
            }
            if (pistas.some(c => /puesto/.test(c.txt)) && pistas.filter(c => /puesto/.test(c.txt)).length > 1 && intento < 40) continue;
            return {sol, pistas};
        }
        return null;
    }
    Logica.registrar('fila', {
        nombre: 'La fila exacta',
        instrucciones: 'Ponga a cada persona en su puesto de la fila para que se cumplan todas las pistas. Toque una persona y luego un puesto (si está ocupado, cambian de lugar). Las pistas se ponen en verde cuando se cumplen.',
        total: () => 30,
        titulo: (d, i) => `Fila ${i + 1} · ${i < 10 ? 4 : i < 20 ? 5 : 6} personas`,
        iniciar(zona, datos, i, api) {
            const n = i < 10 ? 4 : i < 20 ? 5 : 6, reto = generar(n);
            let fila = Array(n).fill(null), sel = null;
            const caja = document.createElement('div');
            caja.style.cssText = 'width:100%;max-width:760px;margin:0 auto;font-family:system-ui,sans-serif';
            caja.innerHTML = `<div class="fx-puestos" style="display:flex;gap:8px;justify-content:center;margin:8px 0 6px"></div>
              <div style="text-align:center;font-size:.8rem;color:#868e96;margin-bottom:10px">← izquierda · · · derecha →</div>
              <div class="fx-gente" style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;min-height:76px;margin-bottom:12px"></div>
              <ol class="fx-pistas" style="max-width:620px;margin:0 auto;font-size:1rem;line-height:1.5"></ol>`;
            zona.appendChild(caja);
            const $ = s => caja.querySelector(s);
            function ficha(x) {
                const d = document.createElement('div'), [nom, col] = NOMBRES[x];
                d.style.cssText = `width:74px;height:70px;border-radius:14px;background:${col};color:#fff;font-weight:800;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;user-select:none;${sel === x ? 'outline:4px solid #ffd43b;' : ''}`;
                d.innerHTML = `<span style="font-size:1.6rem">☺</span><span>${nom}</span>`;
                return d;
            }
            function pintar() {
                const P = $('.fx-puestos'); P.innerHTML = '';
                fila.forEach((x, k) => {
                    const slot = document.createElement('div');
                    slot.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:4px';
                    const hueco = x === null ? Object.assign(document.createElement('div'), {}) : ficha(x);
                    if (x === null) hueco.style.cssText = 'width:74px;height:70px;border-radius:14px;border:3px dashed #adb5bd;cursor:pointer';
                    hueco.addEventListener('click', () => tocarPuesto(k));
                    const num = document.createElement('small'); num.textContent = 'Puesto ' + (k + 1); num.style.color = '#495057';
                    slot.appendChild(hueco); slot.appendChild(num); P.appendChild(slot);
                });
                const G = $('.fx-gente'); G.innerHTML = '';
                [...Array(n).keys()].filter(x => !fila.includes(x)).forEach(x => { const f = ficha(x); f.addEventListener('click', () => { sel = sel === x ? null : x; pintar(); }); G.appendChild(f); });
                const completa = fila.every(x => x !== null);
                const L = $('.fx-pistas'); L.innerHTML = '';
                reto.pistas.forEach(c => {
                    const li = document.createElement('li'); li.textContent = c.txt;
                    if (completa) li.style.color = c.ok(fila) ? '#2f9e44' : '#e03131';
                    L.appendChild(li);
                });
                if (completa && reto.pistas.every(c => c.ok(fila))) api.gano({estrellas: 3});
                else if (completa) api.aviso('Hay pistas que no se cumplen (en rojo).');
            }
            function tocarPuesto(k) {
                if (sel !== null) {
                    const antes = fila.indexOf(sel);
                    if (antes >= 0) fila[antes] = fila[k];
                    fila[k] = sel; sel = null; api.movimiento(); api.sonido('toque');
                } else if (fila[k] !== null) { sel = fila[k]; }
                pintar();
            }
            pintar();
            return {};
        },
    });
})();
