/* Ranas saltarinas: una rana salta sobre otra (en línea recta, también en diagonal) hasta un nenúfar
 * vacío, y la que quedó debajo se va. Gana cuando solo queda la rana roja.
 * Toque una rana y luego el nenúfar a donde salta. */
Logica.registrar('ranas', {
    nombre: 'Ranas saltarinas',
    instrucciones: 'Toque una rana y luego el nenúfar vacío a donde salta: debe saltar por encima de otra rana, en línea recta (también en diagonal). La rana saltada sale del estanque. Gana cuando solo queda la rana roja.',
    total: d => d.retos.length,
    titulo: (d, i) => `Estanque ${i + 1} · ${d.retos[i].verdes.length} rana(s) verde(s)`,
    iniciar(zona, datos, i, api) {
        const PADS = datos.pads, reto = datos.retos[i], W = 520, H = 470, L = api.lienzo(W, H), ctx = L.ctx;
        const pos = k => ({x: 60 + PADS[k][1] * 100, y: 50 + PADS[k][0] * 92});
        const idx = {}; PADS.forEach(([f, c], k) => { idx[f + ',' + c] = k; });
        let verdes = new Set(reto.verdes), roja = reto.roja, sel = null, salto = null;
        const historia = [];
        function medio(a, b) {
            const [f1, c1] = PADS[a], [f2, c2] = PADS[b], df = f2 - f1, dc = c2 - c1;
            const valido = (Math.abs(df) === 4 && dc === 0) || (Math.abs(dc) === 4 && df === 0) || (Math.abs(df) === 2 && Math.abs(dc) === 2);
            return valido ? idx[(f1 + df / 2) + ',' + (c1 + dc / 2)] : undefined;
        }
        const hay = k => verdes.has(k) || roja === k;
        L.dibujar = function () {
            L.limpiar('#a5d8ff');
            ctx.fillStyle = '#74c0fc'; Logica.redondo(ctx, 20, 14, W - 40, H - 40, 40); ctx.fill();
            // las líneas por donde se puede saltar
            ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 3;
            for (let a = 0; a < PADS.length; a++) for (let b = a + 1; b < PADS.length; b++) {
                if (medio(a, b) === undefined) continue;
                const p = pos(a), q = pos(b); ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
            }
            PADS.forEach((_, k) => {
                const {x, y} = pos(k);
                ctx.fillStyle = sel !== null && k !== sel && !hay(k) && medio(sel, k) !== undefined && hay(medio(sel, k)) ? '#d8f5a2' : '#69db7c';
                ctx.beginPath(); ctx.arc(x, y, 34, .35, Math.PI * 2 - .1); ctx.lineTo(x, y); ctx.fill();
                ctx.strokeStyle = '#2f9e44'; ctx.lineWidth = 2; ctx.stroke();
            });
            PADS.forEach((_, k) => {
                if (!hay(k) || (salto && salto.de === k)) return;
                rana(pos(k).x, pos(k).y, k === roja, sel === k);
            });
            if (salto) { const p = pos(salto.de), q = pos(salto.a), t = salto.t; rana(p.x + (q.x - p.x) * t, p.y + (q.y - p.y) * t - Math.sin(t * Math.PI) * 40, salto.roja, false); }
        };
        function rana(x, y, esRoja, elegida) {
            const cuerpo = esRoja ? '#e03131' : '#2b8a3e', claro = esRoja ? '#ff8787' : '#69db7c';
            if (elegida) { ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(x, y, 30, 0, Math.PI * 2); ctx.stroke(); }
            ctx.fillStyle = cuerpo; ctx.beginPath(); ctx.ellipse(x, y + 4, 20, 16, 0, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.ellipse(x - 18, y + 14, 8, 5, -.4, 0, Math.PI * 2); ctx.ellipse(x + 18, y + 14, 8, 5, .4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = claro; ctx.beginPath(); ctx.ellipse(x, y + 9, 11, 7, 0, 0, Math.PI * 2); ctx.fill();
            [-9, 9].forEach(dx => { ctx.fillStyle = cuerpo; ctx.beginPath(); ctx.arc(x + dx, y - 10, 7, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x + dx, y - 11, 4.5, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(x + dx, y - 11, 2.2, 0, Math.PI * 2); ctx.fill(); });
            ctx.strokeStyle = '#111'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y + 1, 7, .3, Math.PI - .3); ctx.stroke();
        }
        function tocar(k) {
            if (salto) return;
            if (hay(k)) { sel = sel === k ? null : k; api.sonido('toque'); L.dibujar(); return; }
            if (sel === null) return;
            const m = medio(sel, k);
            if (m === undefined || !hay(m)) { api.aviso('Solo puede saltar en línea recta, por encima de otra rana, a un nenúfar vacío.'); api.sonido('mal'); return; }
            const de = sel, esRoja = de === roja;
            historia.push({verdes: new Set(verdes), roja});
            salto = {de, a: k, t: 0, roja: esRoja}; sel = null;
            const anim = () => {
                salto.t += .08;
                if (salto.t >= 1) {
                    if (esRoja) roja = k; else { verdes.delete(de); verdes.add(k); }
                    verdes.delete(m); salto = null; api.movimiento(); api.sonido('bien'); L.dibujar();
                    if (!verdes.size) api.gano({estrellas: 3});
                    else if (!hayJugada()) api.aviso('No quedan saltos posibles: deshaga o reinicie.');
                    return;
                }
                L.dibujar(); requestAnimationFrame(anim);
            };
            requestAnimationFrame(anim);
        }
        function hayJugada() {
            for (let a = 0; a < PADS.length; a++) if (hay(a)) for (let b = 0; b < PADS.length; b++) { const m = medio(a, b); if (!hay(b) && m !== undefined && hay(m)) return true; }
            return false;
        }
        L.cv.addEventListener('pointerdown', ev => {
            const {x, y} = L.punto(ev);
            const k = PADS.findIndex((_, j) => Math.hypot(pos(j).x - x, pos(j).y - y) < 38);
            if (k >= 0) tocar(k);
        });
        return {
            deshacer() { const u = historia.pop(); if (!u || salto) return; verdes = u.verdes; roja = u.roja; sel = null; api.movimiento(-1); L.dibujar(); },
        };
    },
});
