/* Expulsa al impostor: en la nave andan tripulantes, cada uno con una opción.
 * Los impostores son los que llevan una respuesta equivocada: hay que mandarlos por la compuerta
 * hasta que quede solo el de la respuesta correcta. Si expulsa al inocente, falla la pregunta. */
(function () {
    'use strict';
    const Y0 = 50, W = 480;
    // La nave (zona donde caminan) y la compuerta de la izquierda
    const SALA = {x: 78, y: 96, w: 372, h: 192};
    const COMPUERTA = {x: 22, y: 150, w: 26, h: 64};

    function azar(a, b) { return a + Math.random() * (b - a); }
    function destino() { return {x: azar(SALA.x + 15, SALA.x + SALA.w - 15), y: azar(SALA.y + 15, SALA.y + SALA.h - 15)}; }

    /* El tripulante: un alienígena redondo de un solo ojo, con dos antenas y patitas, del color de su opción. */
    function tripulante(ctx, k, x, y, o) {
        o = o || {};
        const col = Gamificacion.COLORES[k], e = o.e || 1, paso = o.paso || 0;
        ctx.save(); ctx.translate(x, y); ctx.scale(e, e); if (o.giro) ctx.rotate(o.giro);
        // sombra
        if (!o.giro) { ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.ellipse(0, 13, 11, 3, 0, 0, Math.PI * 2); ctx.fill(); }
        // patitas
        ctx.fillStyle = '#343a40';
        ctx.fillRect(-7, 7 + (paso > 0 ? -2 : 0), 4, 6); ctx.fillRect(3, 7 + (paso < 0 ? -2 : 0), 4, 6);
        // antenas
        ctx.strokeStyle = '#343a40'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(-5, -9); ctx.lineTo(-9, -18); ctx.moveTo(5, -9); ctx.lineTo(9, -18); ctx.stroke();
        ctx.fillStyle = o.malo ? '#ff2d2d' : col; ctx.beginPath(); ctx.arc(-9, -18, 2.5, 0, Math.PI * 2); ctx.arc(9, -18, 2.5, 0, Math.PI * 2); ctx.fill();
        // cuerpo
        ctx.fillStyle = col; ctx.beginPath(); ctx.arc(0, 0, 11, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,.45)'; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = 'rgba(255,255,255,.3)'; ctx.beginPath(); ctx.arc(-4, -4, 4, 0, Math.PI * 2); ctx.fill();
        // el ojo (mira hacia donde camina); rojo si se descubre que era impostor
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(0, -1, 5.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = o.malo ? '#e03131' : '#111'; ctx.beginPath(); ctx.arc((o.mira || 0) * 2, -1, 2.6, 0, Math.PI * 2); ctx.fill();
        // la boca
        ctx.strokeStyle = '#111'; ctx.lineWidth = 1.2; ctx.beginPath();
        if (o.malo) { ctx.moveTo(-4, 7); ctx.lineTo(-1, 5); ctx.lineTo(1, 7); ctx.lineTo(4, 5); } else ctx.arc(0, 5, 3, .2, Math.PI - .2);
        ctx.stroke();
        ctx.restore();
    }

    Gamificacion.registrar('impostor', {
        nombre: 'Expulsa al impostor',
        instrucciones: 'Los impostores llevan la respuesta equivocada. Tóquelos (o presione su letra) para sacarlos por la compuerta. ¡No expulse al tripulante de la respuesta correcta!',
        conReloj: true,
        maxOpciones: 8,
        fondo: '#0b0d1f',
        icono(ctx, k, tam) { tripulante(ctx, k, tam / 2, tam * .56, {e: tam / 44}); },
        nuevaPregunta(m) {
            const vel = 28 + m.nivel * 9;
            m.s = {
                gente: m.opciones.map((_, k) => {
                    const p = destino();
                    return Object.assign(p, {k, meta: destino(), vel: vel * azar(.8, 1.2), espera: 0, fase: Math.random() * 6, mira: 0, fuera: false, saliendo: null});
                }),
                puerta: 0, revelado: null, ocupado: false,
                estrellas: Array.from({length: 40}, () => ({x: Math.random() * W, y: Math.random(), v: azar(8, 30)})),
            };
        },
        expulsar(m, t) {
            const s = m.s;
            if (s.ocupado || t.fuera || t.saliendo) return;
            s.ocupado = true; t.saliendo = {t: m.t, x: t.x, y: t.y}; m.sonidos.toque();
        },
        alTocar(m, x, y) {
            const t = m.s.gente.filter(t => !t.fuera && !t.saliendo).sort((a, b) => Math.hypot(a.x - x, Y0 + a.y - y) - Math.hypot(b.x - x, Y0 + b.y - y))[0];
            if (t && Math.hypot(t.x - x, Y0 + t.y - y) < 24) this.expulsar(m, t);
        },
        alTecla(m, t, crudo) {
            const k = 'ABCDEFGH'.indexOf(String(crudo || '').toUpperCase());
            const p = k >= 0 && m.s.gente.find(g => g.k === k);
            if (p) this.expulsar(m, p);
        },
        actualizar(m, dt) {
            const s = m.s, opciones = m.opciones;
            s.estrellas.forEach(e => { e.x -= e.v * dt; if (e.x < 0) e.x += W; });
            s.puerta = Math.max(0, s.puerta - dt * 1.5);
            s.gente.forEach(t => {
                if (t.fuera) return;
                if (t.saliendo) {
                    // Lo llevan a la compuerta; al llegar, sale disparado al espacio.
                    const d = (m.t - t.saliendo.t) / .7;
                    s.puerta = Math.min(1, s.puerta + dt * 4);
                    const cx = COMPUERTA.x + COMPUERTA.w / 2, cy = COMPUERTA.y + COMPUERTA.h / 2 - Y0;
                    t.x = t.saliendo.x + (cx - t.saliendo.x) * Math.min(1, d);
                    t.y = t.saliendo.y + (cy - t.saliendo.y) * Math.min(1, d);
                    if (d >= 1) {
                        t.fuera = true; s.ocupado = false;
                        const inocente = opciones[t.k] && opciones[t.k].correcta;
                        s.revelado = {k: t.k, malo: !inocente, t: m.t};
                        if (inocente) {
                            // Expulsó al de la respuesta correcta: la respuesta queda como uno de los impostores que seguían adentro.
                            const otro = s.gente.find(g => !g.fuera && !(opciones[g.k] && opciones[g.k].correcta));
                            m.responder(otro ? otro.k : null);
                            m.aviso('¡ERA INOCENTE! LA CORRECTA ERA LA ' + Gamificacion.LETRAS[t.k], '#ff6b6b', 1.3);
                        } else {
                            const quedan = s.gente.filter(g => !g.fuera && !(opciones[g.k] && opciones[g.k].correcta)).length;
                            if (!quedan) {
                                m.responder(s.gente.find(g => opciones[g.k] && opciones[g.k].correcta).k);
                                m.aviso('¡NAVE A SALVO!', '#69db7c', .9);
                            } else {
                                m.aviso('¡ERA IMPOSTOR! QUEDA' + (quedan > 1 ? 'N ' : ' ') + quedan, '#ffd43b', .8);
                                m.puntaje += 25;
                            }
                        }
                    }
                    return;
                }
                // Caminan por la nave hacia un punto, esperan un rato y eligen otro.
                if (t.espera > 0) { t.espera -= dt; return; }
                const dx = t.meta.x - t.x, dy = t.meta.y - t.y, d = Math.hypot(dx, dy);
                if (d < 3) { t.meta = destino(); t.espera = azar(.2, 1.2) / m.nivel; return; }
                t.x += dx / d * t.vel * dt; t.y += dy / d * t.vel * dt; t.fase += dt * 10; t.mira = Math.sign(dx);
            });
        },
        actualizarEnPausa(m, dt) { if (m.s) m.s.estrellas.forEach(e => { e.x -= e.v * dt; if (e.x < 0) e.x += W; }); },
        dibujar(m, ctx) {
            const s = m.s;
            // El espacio
            ctx.fillStyle = '#05061a'; ctx.fillRect(0, Y0, W, 260);
            if (s) { ctx.fillStyle = '#fff'; s.estrellas.forEach(e => ctx.fillRect(e.x, Y0 + e.y * 260, e.v > 20 ? 2 : 1, e.v > 20 ? 2 : 1)); }
            // El casco de la nave
            ctx.fillStyle = '#495057'; ctx.beginPath(); ctx.roundRect(40, Y0 + 22, 430, 226, 30); ctx.fill();
            ctx.fillStyle = '#343a40'; ctx.beginPath(); ctx.roundRect(48, Y0 + 30, 414, 210, 24); ctx.fill();
            // Ventanas de arriba
            for (let i = 0; i < 5; i++) {
                const x = 120 + i * 66; ctx.fillStyle = '#0b1a3a'; ctx.beginPath(); ctx.roundRect(x, Y0 + 30, 40, 12, 6); ctx.fill();
                ctx.fillStyle = 'rgba(116,192,252,.35)'; ctx.fillRect(x + 6, Y0 + 33, 10, 3);
            }
            // El piso de placas
            ctx.fillStyle = '#868e96'; ctx.fillRect(SALA.x - 18, SALA.y - 6, SALA.w + 30, SALA.h + 16);
            ctx.strokeStyle = '#6c757d'; ctx.lineWidth = 1;
            for (let x = SALA.x - 18; x <= SALA.x + SALA.w + 12; x += 32) { ctx.beginPath(); ctx.moveTo(x, SALA.y - 6); ctx.lineTo(x, SALA.y + SALA.h + 10); ctx.stroke(); }
            for (let y = SALA.y - 6; y <= SALA.y + SALA.h + 10; y += 32) { ctx.beginPath(); ctx.moveTo(SALA.x - 18, y); ctx.lineTo(SALA.x + SALA.w + 12, y); ctx.stroke(); }
            // Consolas
            [[SALA.x + SALA.w - 40, SALA.y - 4], [SALA.x + 120, SALA.y + SALA.h - 6]].forEach(([x, y], i) => {
                ctx.fillStyle = '#212529'; ctx.fillRect(x, y, 36, 14);
                ctx.fillStyle = Math.floor(m.t * 3 + i) % 2 ? '#69db7c' : '#4dabf7'; ctx.fillRect(x + 4, y + 3, 8, 4); ctx.fillStyle = '#ffd43b'; ctx.fillRect(x + 16, y + 3, 4, 4); ctx.fillRect(x + 24, y + 3, 6, 4);
            });
            // La compuerta (se abre al expulsar)
            const ab = s ? s.puerta : 0, c = COMPUERTA;
            ctx.fillStyle = '#05061a'; ctx.fillRect(c.x, c.y, c.w, c.h);
            ctx.fillStyle = '#adb5bd'; ctx.fillRect(c.x, c.y, c.w, c.h / 2 * (1 - ab)); ctx.fillRect(c.x, c.y + c.h - c.h / 2 * (1 - ab), c.w, c.h / 2 * (1 - ab));
            for (let i = 0; i < 4; i++) { ctx.fillStyle = i % 2 ? '#212529' : '#fab005'; ctx.fillRect(c.x + c.w, c.y + i * 16, 6, 16); }
            m.texto('SALIDA', c.x + c.w / 2 + 3, c.y - 12, {tam: 6, alinear: 'center', color: '#fab005'});
            if (!s) return;
            // Los tripulantes (el de más abajo se dibuja encima)
            s.gente.filter(t => !t.fuera).sort((a, b) => a.y - b.y).forEach(t => {
                if (t.saliendo) {
                    const d = Math.min(1, (m.t - t.saliendo.t) / .7);
                    tripulante(ctx, t.k, t.x, Y0 + t.y, {e: 1 - d * .5, giro: d * 8});
                    return;
                }
                tripulante(ctx, t.k, t.x, Y0 + t.y, {paso: t.espera > 0 ? 0 : Math.sin(t.fase), mira: t.mira});
                m.etiqueta(t.k, t.x, Y0 + t.y - 30, 8);
            });
            // El que acaba de salir flota en el espacio y se ve si era impostor
            if (s.revelado && m.t - s.revelado.t < 1.4) {
                const d = m.t - s.revelado.t;
                tripulante(ctx, s.revelado.k, COMPUERTA.x - 4 - d * 30, COMPUERTA.y + 30 - d * 40, {e: .8, giro: d * 4, malo: s.revelado.malo});
            }
            if (m.puntero) {
                const {x, y} = m.puntero; ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.arc(x, y, 14, 0, Math.PI * 2); ctx.stroke();
            }
        },
    });
})();
