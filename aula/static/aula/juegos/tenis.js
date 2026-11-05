/* Tenis: partido con reloj (el docente escoge cuántos minutos). A quien le llega la pelota responde:
 * si acierta, la pasa por encima de la malla; si se equivoca (o no alcanza a responder), la deja en la
 * malla o no le pega y el punto es del otro. Gana quien tenga más puntos al acabarse el tiempo; si
 * quedan empatados, se juega un punto de oro. Contra la compu, ella devuelve casi siempre. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, CX = 240;
    const CANCHA = {x: 130, y: Y0 + 14, w: 220, h: 232};
    const RED_Y = CANCHA.y + CANCHA.h / 2;

    Gamificacion.registrar('tenis', {
        nombre: 'Tenis',
        instrucciones: 'Cuando le llegue la pelota, responda (toque la opción de abajo o presione A, B, C o D). Bien: la pasa por encima de la malla. Mal: punto para el rival.',
        conReloj: true, sinVidas: true, finPropio: true, marcador: true, avisoPropio: true,
        fondo: '#1864ab',
        nuevaPregunta(m) {
            if (!m.tenis) m.tenis = {puntos: [0, 0], lado: 0, partido: Math.max(30, (m.opciones_juego && m.opciones_juego.minutos || 3) * 60),
                                     saque: 0, oro: false};
            const z = m.tenis;
            if (z.partido <= 0 && z.puntos[0] !== z.puntos[1]) { m.terminar(); return; }
            if (z.partido <= 0) z.oro = true;
            m.turno = m.jugadores === 2 ? z.lado : 0;
            m.s = {elegida: null, anim: null, msg: ''};
        },
        elegir(m, k) {
            if (m.s.elegida !== null || k < 0 || k >= m.opciones.length) return;
            m.s.elegida = k; m.responder(k);
        },
        alTocar(m, x, y) {
            if (y < m.ABAJO) return;
            const col = x < W / 2 ? 0 : 1, fila = y < m.ABAJO + 30 ? 0 : 1;
            this.elegir(m, fila * 2 + col);
        },
        alTecla(m, t, crudo) { this.elegir(m, 'ABCD'.indexOf(String(crudo || '').toUpperCase())); },
        alResponder(m, bien, k) {
            const z = m.tenis, s = m.s, golpea = z.lado;
            const otro = 1 - golpea;
            if (!bien) {
                z.puntos[otro] += 1; z.lado = otro;
                s.anim = {tipo: k === null ? 'no_le_pega' : 'malla', de: golpea, t0: m.t};
                s.msg = k === null ? '¡NO LE PEGÓ!' : '¡A LA MALLA!';
                return;
            }
            if (m.jugadores === 2) {
                z.lado = otro; s.anim = {tipo: 'pasa', de: golpea, t0: m.t}; s.msg = '¡BUEN GOLPE!';
                return;
            }
            // Contra la compu: ella devuelve (cada nivel un poco mejor) o falla.
            const devuelve = Math.random() < Math.min(.85, .6 + m.nivel * .05);
            if (devuelve) { s.anim = {tipo: 'rally', de: 0, t0: m.t}; s.msg = '¡LA DEVOLVIÓ!'; z.lado = 0; }
            else { z.puntos[0] += 1; s.anim = {tipo: 'pasa', de: 0, t0: m.t, cpuFalla: true}; s.msg = '¡PUNTO SUYO!'; z.lado = 0; }
        },
        // El reloj del partido corre en tiempo real (también mientras vuela la pelota).
        actualizar(m, dt) { if (m.tenis) m.tenis.partido -= dt; },
        actualizarEnPausa(m, dt) { if (m.tenis) m.tenis.partido -= dt; },
        posBola(m) {
            const s = m.s, z = m.tenis, abajo = CANCHA.y + CANCHA.h - 18, arriba = CANCHA.y + 18;
            const yDe = lado => lado === 0 ? abajo : arriba;
            if (!s || !s.anim) return {x: CX + (z.lado === 0 ? 20 : -20), y: yDe(z.lado), h: 0};
            const a = s.anim, p = Math.min(1, (m.t - a.t0) / .7);
            if (a.tipo === 'malla') return {x: CX, y: yDe(a.de) + (RED_Y - yDe(a.de)) * p, h: Math.sin(p * Math.PI) * 10};
            if (a.tipo === 'no_le_pega') return {x: CX + 40 * p, y: yDe(a.de) + (a.de === 0 ? 30 : -30) * p, h: 0};
            if (a.tipo === 'rally') {
                const q = Math.min(1, (m.t - a.t0) / 1.2), ida = q < .5;
                const r = ida ? q * 2 : (q - .5) * 2;
                return {x: CX + (ida ? -30 : 30) * r, y: ida ? abajo + (arriba - abajo) * r : arriba + (abajo - arriba) * r, h: Math.sin(r * Math.PI) * 22};
            }
            const destino = yDe(1 - a.de) + (a.cpuFalla ? -30 : 0);
            return {x: CX + (a.de === 0 ? -25 : 25) * p, y: yDe(a.de) + (destino - yDe(a.de)) * p, h: Math.sin(p * Math.PI) * 22};
        },
        dibujar(m, ctx) {
            ctx.fillStyle = '#1971c2'; ctx.fillRect(0, Y0, W, 260);
            ctx.fillStyle = '#2b8a3e'; ctx.fillRect(CANCHA.x - 20, CANCHA.y - 8, CANCHA.w + 40, CANCHA.h + 16);
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(CANCHA.x, CANCHA.y, CANCHA.w, CANCHA.h);
            ctx.beginPath(); ctx.moveTo(CX, CANCHA.y + 50); ctx.lineTo(CX, CANCHA.y + CANCHA.h - 50);
            ctx.moveTo(CANCHA.x, CANCHA.y + 50); ctx.lineTo(CANCHA.x + CANCHA.w, CANCHA.y + 50);
            ctx.moveTo(CANCHA.x, CANCHA.y + CANCHA.h - 50); ctx.lineTo(CANCHA.x + CANCHA.w, CANCHA.y + CANCHA.h - 50); ctx.stroke();
            // Malla
            ctx.fillStyle = '#e9ecef'; ctx.fillRect(CANCHA.x - 14, RED_Y - 2, CANCHA.w + 28, 4);
            ctx.fillStyle = 'rgba(255,255,255,.35)'; for (let x = CANCHA.x - 14; x < CANCHA.x + CANCHA.w + 14; x += 6) ctx.fillRect(x, RED_Y - 6, 1, 8);
            const z = m.tenis; if (!z) return;
            // Jugadores
            const jugador = (y, color, activo) => {
                ctx.fillStyle = color; ctx.fillRect(CX - 7, y - 10, 14, 18);
                ctx.fillStyle = '#ffc9a3'; ctx.fillRect(CX - 5, y - 18, 10, 8);
                ctx.fillStyle = '#f8f9fa'; ctx.fillRect(CX + 8, y - 8, 10, 3);
                if (activo) { ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 2; ctx.strokeRect(CX - 11, y - 22, 22, 34); }
            };
            const esperaRespuesta = m.s && m.s.elegida === null;
            jugador(CANCHA.y + CANCHA.h - 12, '#ff922b', esperaRespuesta && z.lado === 0);
            jugador(CANCHA.y + 26, '#4dabf7', esperaRespuesta && z.lado === 1);
            // Pelota y su sombra
            const b = this.posBola(m);
            ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.beginPath(); ctx.ellipse(b.x, b.y + 4, 5, 2, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#d8f5a2'; ctx.beginPath(); ctx.arc(b.x, b.y - b.h, 5, 0, Math.PI * 2); ctx.fill();
            // Marcador y reloj del partido
            const seg = Math.max(0, Math.ceil(z.partido)), reloj = z.oro ? 'PUNTO DE ORO' : `${Math.floor(seg / 60)}:${String(seg % 60).padStart(2, '0')}`;
            ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(8, Y0 + 8, 112, 64);
            m.texto(reloj, 64, Y0 + 14, {tam: z.oro ? 7 : 11, alinear: 'center', color: seg < 30 || z.oro ? '#ff6b6b' : '#69db7c'});
            m.texto(`${m.nombres[0].slice(0, 7)} ${z.puntos[0]}`, 14, Y0 + 36, {tam: 7, color: '#ff922b'});
            m.texto(`${m.nombres[1].slice(0, 7)} ${z.puntos[1]}`, 14, Y0 + 52, {tam: 7, color: '#4dabf7'});
            if (esperaRespuesta) m.texto(m.jugadores === 2 ? `LE TOCA A ${m.nombres[z.lado]}` : 'LE TOCA A USTED', W - 10, Y0 + 14, {tam: 7, alinear: 'right', color: '#ffd43b'});
            if (m.s && m.s.msg) m.texto(m.s.msg, W - 10, Y0 + 230, {tam: 9, alinear: 'right', color: '#fff'});
        },
        final(m) {
            const [a, b] = m.tenis ? m.tenis.puntos : [0, 0];
            m.texto('FIN DEL PARTIDO', 240, 80, {tam: 14, alinear: 'center', color: '#ffd43b'});
            m.texto(`${m.nombres[0]} ${a} - ${b} ${m.nombres[1]}`, 240, 130, {tam: 10, alinear: 'center'});
            m.texto(a === b ? 'EMPATE' : `${a > b ? m.nombres[0] : m.nombres[1]} GANA`, 240, 165, {tam: 14, alinear: 'center', color: '#69db7c'});
            if (m.jugadores === 1) m.texto(`ACIERTOS: ${m.aciertos} DE ${m.respuestas.length}`, 240, 210, {tam: 9, alinear: 'center'});
        },
    });
})();
