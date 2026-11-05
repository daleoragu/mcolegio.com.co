/* Penaltis: el arco tiene 9 secciones; las opciones quedan en algunas. Patear a la sección con la
 * respuesta correcta es gol; si se equivoca, el portero la tapa. Contra la compu se alterna: patea usted
 * y luego tapa (escoger la correcta es lanzarse bien). Con 2 jugadores cada uno patea su pregunta.
 * 5 penales por equipo y, si quedan empatados, muerte súbita. */
(function () {
    'use strict';
    const Y0 = 50, W = 480;
    const ARCO = {x: 120, y: Y0 + 30, w: 240, h: 120};

    function seccion(i) {
        const c = i % 3, f = Math.floor(i / 3), w = ARCO.w / 3, h = ARCO.h / 3;
        return {x: ARCO.x + c * w, y: ARCO.y + f * h, w, h, cx: ARCO.x + c * w + w / 2, cy: ARCO.y + f * h + h / 2};
    }

    function decidido(t) {
        const [a, b] = t.goles, [ta, tb] = [t.tiros[0].length, t.tiros[1].length];
        if (ta <= 5 && tb <= 5) {
            if (a > b + (5 - tb)) return true;
            if (b > a + (5 - ta)) return true;
            return ta === 5 && tb === 5 && a !== b;
        }
        return ta === tb && a !== b;          // muerte súbita: cada pareja de tiros
    }

    Gamificacion.registrar('penaltis', {
        nombre: 'Penaltis',
        instrucciones: 'Toque la sección del arco con la respuesta correcta (o presione A, B, C o D). Correcta: ¡gol! o ¡atajada! Equivocada: la tapan o le meten gol.',
        conReloj: true, sinVidas: true, finPropio: true, marcador: true, avisoPropio: true,
        fondo: '#2b8a3e',
        nuevaPregunta(m) {
            if (!m.tanda) m.tanda = {goles: [0, 0], tiros: [[], []], equipo: 0};
            const t = m.tanda;
            if (decidido(t)) { m.terminar(); return; }
            // En 1 jugador: equipo 0 = usted patea, equipo 1 = la compu patea y usted tapa.
            m.turno = m.jugadores === 2 ? t.equipo : 0;
            const casillas = [0, 1, 2, 3, 4, 5, 6, 7, 8].sort(() => Math.random() - .5).slice(0, m.opciones.length);
            m.s = {casillas, elegida: null, balon: null, portero: 4, desde: 0, msg: '', patea: t.equipo};
        },
        elegir(m, k) {
            if (m.s.elegida !== null || k < 0 || k >= m.opciones.length) return;
            m.s.elegida = k; m.responder(k);
        },
        alTocar(m, x, y) {
            const s = m.s;
            const k = s.casillas.findIndex(i => { const r = seccion(i); return x > r.x && x < r.x + r.w && y > r.y && y < r.y + r.h; });
            if (k >= 0) this.elegir(m, k);
        },
        alTecla(m, t, crudo) { this.elegir(m, 'ABCD'.indexOf(String(crudo || '').toUpperCase())); },
        alResponder(m, bien, k) {
            const s = m.s, t = m.tanda, patea = t.equipo;
            const correcta = m.opciones.findIndex(o => o.correcta);
            const usuarioPatea = m.jugadores === 2 || patea === 0;
            let gol;
            if (usuarioPatea) {
                gol = bien;
                s.balon = s.casillas[k === null ? correcta : k];
                s.portero = gol ? [0, 1, 2, 3, 4, 5, 6, 7, 8].filter(i => i !== s.balon)[Math.floor(Math.random() * 8)] : s.balon;
                s.msg = gol ? '¡GOOOL!' : (k === null ? '¡NO PATEÓ!' : '¡LA TAPÓ!');
            } else {
                // Usted tapa: si acierta, se lanza a donde va el balón.
                gol = !bien;
                s.balon = s.casillas[correcta];
                s.portero = bien ? s.balon : s.casillas[k === null ? (correcta + 1) % s.casillas.length : k];
                s.msg = bien ? '¡ATAJADA!' : '¡GOL DE LA COMPU!';
            }
            t.tiros[patea].push(gol); if (gol) t.goles[patea] += 1;
            t.equipo = 1 - patea;
            s.desde = m.t;
        },
        actualizar() {},
        dibujar(m, ctx) {
            // Césped y área
            for (let y = 0; y < 260; y += 20) { ctx.fillStyle = (y / 20) % 2 ? '#2f9e44' : '#37b24d'; ctx.fillRect(0, Y0 + y, W, 20); }
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(60, Y0 + 150, 360, 110);
            ctx.beginPath(); ctx.arc(240, Y0 + 230, 3, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();
            const s = m.s, t = m.tanda; if (!s) return;
            // Arco con red
            ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.fillRect(ARCO.x, ARCO.y, ARCO.w, ARCO.h);
            ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 1;
            for (let x = ARCO.x; x <= ARCO.x + ARCO.w; x += 12) { ctx.beginPath(); ctx.moveTo(x, ARCO.y); ctx.lineTo(x, ARCO.y + ARCO.h); ctx.stroke(); }
            for (let y = ARCO.y; y <= ARCO.y + ARCO.h; y += 12) { ctx.beginPath(); ctx.moveTo(ARCO.x, y); ctx.lineTo(ARCO.x + ARCO.w, y); ctx.stroke(); }
            ctx.strokeStyle = 'rgba(255,255,255,.6)'; ctx.setLineDash([4, 4]);
            for (let i = 1; i < 3; i++) {
                ctx.beginPath(); ctx.moveTo(ARCO.x + i * ARCO.w / 3, ARCO.y); ctx.lineTo(ARCO.x + i * ARCO.w / 3, ARCO.y + ARCO.h); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(ARCO.x, ARCO.y + i * ARCO.h / 3); ctx.lineTo(ARCO.x + ARCO.w, ARCO.y + i * ARCO.h / 3); ctx.stroke();
            }
            ctx.setLineDash([]);
            ctx.fillStyle = '#f1f3f5'; ctx.fillRect(ARCO.x - 6, ARCO.y - 6, ARCO.w + 12, 6); ctx.fillRect(ARCO.x - 6, ARCO.y, 6, ARCO.h); ctx.fillRect(ARCO.x + ARCO.w, ARCO.y, 6, ARCO.h);
            if (s.elegida === null) s.casillas.forEach((i, k) => { const r = seccion(i); m.etiqueta(k, r.cx, r.cy, 11); });
            // Portero (se lanza a su sección)
            const avance = s.balon === null ? 0 : Math.min(1, (m.t - s.desde) / .45);
            const centro = seccion(4), destino = seccion(s.portero);
            const px = centro.cx + (destino.cx - centro.cx) * avance, py = centro.cy + 12 + (destino.cy - centro.cy) * avance;
            const portero = m.jugadores === 1 && s.patea === 1 ? '#ffd43b' : '#212529';
            ctx.fillStyle = portero; ctx.fillRect(px - 9, py - 14, 18, 22);
            ctx.fillStyle = '#ffc9a3'; ctx.fillRect(px - 6, py - 24, 12, 10);
            ctx.fillStyle = portero; ctx.fillRect(px - 20, py - 12, 11, 5); ctx.fillRect(px + 9, py - 12, 11, 5);
            // Balón: del punto penal a la sección
            const bx0 = 240, by0 = Y0 + 228;
            let bx = bx0, by = by0;
            if (s.balon !== null) { const d = seccion(s.balon); bx = bx0 + (d.cx - bx0) * avance; by = by0 + (d.cy - by0) * avance; }
            ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(bx, by, 6 - avance * 2, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#212529'; ctx.fillRect(bx - 1.5, by - 1.5, 3, 3);
            // Quién patea y el marcador de la tanda
            const pateaTxt = m.jugadores === 2 ? `PATEA ${m.nombres[s.patea]}` : (s.patea === 0 ? 'USTED PATEA' : '¡USTED TAPA! ESCOJA LA CORRECTA');
            m.texto(pateaTxt, W / 2, Y0 + 6, {tam: 8, alinear: 'center', color: '#fff'});
            [0, 1].forEach(e => {
                const y = Y0 + 160 + e * 18;
                m.texto(m.nombres[e].slice(0, 9), 8, y, {tam: 7, color: e ? '#4dabf7' : '#ff922b'});
                const tiros = t.tiros[e];
                for (let i = 0; i < Math.max(5, tiros.length); i++) {
                    ctx.fillStyle = i < tiros.length ? (tiros[i] ? '#69db7c' : '#ff6b6b') : 'rgba(255,255,255,.3)';
                    ctx.beginPath(); ctx.arc(20 + i * 11, y + 13, 4, 0, Math.PI * 2); ctx.fill();
                }
                m.texto(String(t.goles[e]), 100, y + 2, {tam: 10, color: '#fff'});
            });
            if (s.msg && avance >= 1) m.texto(s.msg, W / 2, Y0 + 165, {tam: 16, alinear: 'center', color: s.msg.includes('GO') && !s.msg.includes('COMPU') ? '#ffd43b' : '#fff'});
        },
        final(m, ctx) {
            const [a, b] = m.tanda ? m.tanda.goles : [0, 0];
            const gana = a === b ? 'EMPATE' : (a > b ? m.nombres[0] : m.nombres[1]) + ' GANA';
            m.texto('FIN DE LA TANDA', W / 2, 80, {tam: 14, alinear: 'center', color: '#ffd43b'});
            m.texto(`${m.nombres[0]} ${a} - ${b} ${m.nombres[1]}`, W / 2, 130, {tam: 10, alinear: 'center'});
            m.texto(gana, W / 2, 165, {tam: 14, alinear: 'center', color: '#69db7c'});
            if (m.jugadores === 1) m.texto(`ACIERTOS: ${m.aciertos} DE ${m.respuestas.length}`, W / 2, 210, {tam: 9, alinear: 'center'});
        },
    });
})();
