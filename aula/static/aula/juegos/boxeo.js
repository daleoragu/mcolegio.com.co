/* Boxeo del saber (primera persona): el rival se pone en guardia y sale la pregunta.
 * Cada guante es una opción (izquierdo = A, derecho = B). Si acierta, golpea y le baja vida al rival;
 * si falla (o se acaba el tiempo), el rival lo golpea, y en cada pelea pega más fuerte.
 * Si lo tumban: preguntas rápidas para levantarse antes de la cuenta (a la tercera caída es KO). Tres rivales para ser campeón.
 * Entre dos (mismo equipo): por turnos ataca uno; si falla, el otro esquiva y contraataca. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, CX = 240;
    const RIVALES = [
        {nombre: 'TORO RAMÍREZ', piel: '#a0522d', pelo: '#111', short: '#c92a2a', grande: 1, golpe: 20, vida: 100},
        {nombre: 'LA MOLE', piel: '#f1c27d', pelo: null, short: '#2b8a3e', grande: 1.15, golpe: 26, barba: '#5c3d2e', vida: 130},
        {nombre: 'RAYO MARTÍNEZ', piel: '#c68642', pelo: '#3b2a1a', short: '#fab005', grande: .95, golpe: 32, banda: '#1971c2', vida: 160},
    ];
    const JUGADORES = [{nombre: 'JUGADOR 1', piel: '#f1c27d', pelo: '#3b2a1a', short: '#e8590c', grande: 1, golpe: 18},
                       {nombre: 'JUGADOR 2', piel: '#8d5524', pelo: '#111', short: '#1971c2', grande: 1, golpe: 18}];
    const DANO = 25;

    function guante(ctx, x, y, r, color, k, lado) {
        ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.beginPath(); ctx.ellipse(x + 4, y + 6, r, r * .9, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = color; ctx.beginPath(); ctx.ellipse(x, y, r, r * .9, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,.3)'; ctx.beginPath(); ctx.ellipse(x - r * .3, y - r * .35, r * .35, r * .22, -.4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.ellipse(x + lado * r * .55, y + r * .1, r * .3, r * .45, 0, 0, Math.PI * 2); ctx.fill();   // pulgar
        ctx.fillStyle = '#f8f9fa'; ctx.fillRect(x - r * .7, y + r * .7, r * 1.4, r * .4);    // puño
        if (k !== undefined) {
            ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x, y, r * .38, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(r * .5)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(Gamificacion.LETRAS[k], x, y + 1);
        }
    }

    function rival(ctx, R, estado, t, o) {
        o = o || {};
        const e = R.grande, base = Y0 + 262;
        let dx = Math.sin(t * 3) * 4, dy = Math.sin(t * 6) * 2, giro = 0, caida = 0;
        if (estado === 'golpeado') { dx += 18 * (o.lado || 1); giro = .25 * (o.lado || 1); }
        if (estado === 'ko') { caida = Math.min(1, o.d || 0); giro = -caida * .5; dy += caida * 60; }
        ctx.save(); ctx.translate(CX + dx, base + dy); ctx.rotate(giro); ctx.scale(e, e * (1 - caida * .3));
        // cuerpo
        ctx.fillStyle = R.piel; ctx.beginPath(); ctx.moveTo(-62, 0); ctx.lineTo(-52, -120); ctx.lineTo(52, -120); ctx.lineTo(62, 0); ctx.fill();
        ctx.fillStyle = 'rgba(0,0,0,.12)'; ctx.fillRect(-2, -110, 4, 60); ctx.fillRect(-30, -95, 24, 3); ctx.fillRect(6, -95, 24, 3);
        ctx.fillStyle = R.short; ctx.fillRect(-60, -18, 120, 18);
        // cabeza
        const hx = estado === 'golpeado' ? 10 * (o.lado || 1) : 0;
        ctx.fillStyle = R.piel; ctx.beginPath(); ctx.ellipse(hx, -150, 30, 36, 0, 0, Math.PI * 2); ctx.fill();
        if (R.pelo) { ctx.fillStyle = R.pelo; ctx.fillRect(hx - 8, -192, 16, 24); }
        if (R.banda) { ctx.fillStyle = R.banda; ctx.fillRect(hx - 30, -170, 60, 8); }
        if (R.barba) { ctx.fillStyle = R.barba; ctx.beginPath(); ctx.ellipse(hx, -126, 22, 12, 0, 0, Math.PI); ctx.fill(); }
        // cara: ojos, cejas y boca según el momento
        ctx.fillStyle = '#fff'; ctx.fillRect(hx - 16, -160, 10, 7); ctx.fillRect(hx + 6, -160, 10, 7);
        ctx.fillStyle = '#111';
        if (estado === 'ko' || estado === 'golpeado') {
            ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('x', hx - 11, -156); ctx.fillText('x', hx + 11, -156);
        } else { ctx.fillRect(hx - 12, -159, 4, 5); ctx.fillRect(hx + 9, -159, 4, 5); }
        ctx.fillRect(hx - 18, -167, 13, 3); ctx.fillRect(hx + 5, -167, 13, 3);
        ctx.fillRect(hx - 9, estado === 'golpea' ? -136 : -134, 18, estado === 'golpea' ? 6 : 3);
        if (estado === 'golpeado') { ctx.fillStyle = '#74c0fc'; ctx.beginPath(); ctx.arc(hx + 34, -170, 4, 0, Math.PI * 2); ctx.arc(hx + 40, -150, 3, 0, Math.PI * 2); ctx.fill(); }
        // guantes del rival: en guardia, o uno que viene hacia la pantalla
        const color = '#c92a2a';
        if (estado === 'golpea') {
            const d = Math.min(1, o.d || 0), r = 26 + d * 70;
            guante(ctx, 60, -110, 22, color, undefined, 1);
            guante(ctx, -30 + d * 20, -120 + d * 40, r, color, undefined, -1);
        } else if (estado !== 'ko') {
            const sube = estado === 'guardia' ? -12 : 0;
            guante(ctx, -42, -132 + sube + Math.sin(t * 6) * 3, 22, color, undefined, -1);
            guante(ctx, 42, -132 + sube - Math.sin(t * 6) * 3, 22, color, undefined, 1);
        }
        ctx.restore();
    }

    function barra(m, ctx, x, nombre, valor, color, derecha) {
        m.texto(nombre, derecha ? x + 190 : x, Y0 + 6, {tam: 7, alinear: derecha ? 'right' : 'left', color});
        ctx.fillStyle = '#212529'; ctx.fillRect(x, Y0 + 17, 190, 10);
        const ancho = 186 * Math.max(0, valor) / 100;
        ctx.fillStyle = valor < 30 ? '#ff5d5d' : color; ctx.fillRect(derecha ? x + 188 - ancho : x + 2, Y0 + 19, ancho, 6);
    }

    Gamificacion.registrar('boxeo', {
        nombre: 'Boxeo del saber',
        instrucciones: 'Cada guante es una respuesta: izquierdo (A) o derecho (B). Toque el guante, use las flechas o presione A o B. Si acierta, golpea; si falla, lo golpean. ¡Gánele a los tres rivales!',
        conReloj: true, sinVidas: true, finPropio: true, avisoPropio: true,
        maxOpciones: 2,
        fondo: '#1b1b2f',
        icono(ctx, k, tam) { guante(ctx, tam / 2, tam / 2, tam * .4, Gamificacion.COLORES[k], k, k ? 1 : -1); },
        relojTotal(m) { return m.b && m.b.caido ? 7 : m.tiempoDeLaPregunta(); },
        nuevaPregunta(m) {
            const dos = m.jugadores === 2;
            if (!m.b) m.b = {salud: [100, 100], rivalN: 0, rival: RIVALES[0].vida, caidas: 0, caidasJ: [0, 0], caido: null, anim: null, campeon: false};
            const b = m.b;
            if (b.fin) { m.terminar(); return; }
            if (b.caido) { m.reloj = 7; m.aviso(`¡LEVÁNTESE! CUENTA ${b.caido.intentos ? '6' : '1'}…`, '#ffd43b', 1.2); }
            else if (dos) { m.turno = (b.turnos = (b.turnos || 0) + 1) % 2 === 1 ? 0 : 1; }
            m.s = {elegido: null};
        },
        // Quién está en el ring: en 1 jugador, el rival; entre dos, el que se defiende
        quien(m) { const b = m.b; return m.jugadores === 2 ? JUGADORES[1 - m.turno] : RIVALES[b.rivalN]; },
        elegir(m, k) { if (!m.s || m.s.elegido !== null || (m.b.anim && m.t - m.b.anim.t < .5)) return; m.s.elegido = k; m.responder(k); },
        alTocar(m, x, y) { if (y > Y0 + 80) this.elegir(m, x < CX ? 0 : 1); },
        alTecla(m, t, crudo) {
            const c = String(crudo || '').toUpperCase();
            if (t === 'izquierda' || c === 'A') this.elegir(m, 0);
            else if (t === 'derecha' || c === 'B') this.elegir(m, 1);
        },
        alAcabarReloj(m) { this.elegir(m, null); },
        alResponder(m, bien) {
            // El motor borra el aviso al terminar de responder: los nuestros van justo después
            const aviso = (...a) => setTimeout(() => m.aviso(...a), 0);
            const b = m.b, dos = m.jugadores === 2, yo = dos ? m.turno : 0, otro = 1 - yo;
            const lado = m.s && m.s.elegido === 1 ? 1 : -1;
            if (b.caido) {
                // Pregunta rápida para levantarse
                if (bien) { b.salud[b.caido.quien] = 50; b.caido = null; aviso('¡SE LEVANTÓ!', '#69db7c', 1); }
                else if (++b.caido.intentos >= 2) {
                    b.fin = true;
                    aviso(dos ? `¡KO! GANA ${JUGADORES[1 - b.caido.quien].nombre}` : '¡KO! PERDIÓ LA PELEA', '#ff6b6b', 2);
                    b.anim = {tipo: 'ko-yo', t: m.t};
                } else aviso('¡SIGUE EN LA LONA! OTRA…', '#ff922b', 1.1);
                return;
            }
            if (bien) {
                // Golpe: más fuerte si respondió rápido
                const dano = DANO + Math.round(10 * Math.max(0, m.reloj) / m.tiempoDeLaPregunta());
                b.anim = {tipo: 'pego', lado, t: m.t};
                if (dos) { m.marcador[yo] += 1; b.salud[otro] -= dano; } else b.rival -= dano;
                aviso('¡PUM! +' + dano, '#69db7c', .8);
                const caeRival = dos ? b.salud[otro] <= 0 : b.rival <= 0;
                if (caeRival && dos) { b.salud[otro] = 0; this.tumbar(m, otro, aviso); }
                else if (caeRival) {
                    b.anim = {tipo: 'ko-rival', t: m.t};
                    m.puntaje += 300;
                    if (b.rivalN >= RIVALES.length - 1) { b.fin = true; b.campeon = true; aviso('¡KO! ¡ES EL CAMPEÓN!', '#ffd43b', 2.5); }
                    else { aviso(`¡KO A ${RIVALES[b.rivalN].nombre}!`, '#ffd43b', 1.4); setTimeout(() => { b.rivalN += 1; b.rival = RIVALES[b.rivalN].vida; b.salud[0] = Math.min(100, b.salud[0] + 30); }, 1200); }
                }
            } else {
                // Lo golpean: en 1 jugador, cada rival pega más; entre dos, el otro esquiva y contraataca
                const R = this.quien(m), dano = R.golpe + (dos ? 0 : b.rivalN * 4);
                b.anim = {tipo: 'recibo', t: m.t};
                b.salud[yo] -= dano;
                aviso(dos ? `¡ESQUIVÓ Y CONTRAATACA! −${dano}` : `¡AUCH! −${dano}`, '#ff6b6b', 1);
                if (b.salud[yo] <= 0) { b.salud[yo] = 0; b.caidas += 1; this.tumbar(m, yo, aviso); }
            }
        },
        // A la lona: a la tercera caída es KO; si no, preguntas rápidas para levantarse
        tumbar(m, quien, aviso) {
            const b = m.b, dos = m.jugadores === 2;
            b.caidasJ[quien] += 1;
            if (b.caidasJ[quien] >= 3) {
                b.fin = true; b.anim = {tipo: 'ko-yo', t: m.t};
                aviso(dos ? `¡KO! GANA ${JUGADORES[1 - quien].nombre}` : '¡TRES CAÍDAS: KO!', '#ff6b6b', 2);
                return;
            }
            b.caido = {quien, intentos: 0};
            if (dos) m.turno = quien;
            aviso(dos ? `¡${JUGADORES[quien].nombre} A LA LONA!` : '¡A LA LONA!', '#ffd43b', 1.3);
        },
        actualizar() {},
        dibujar(m, ctx) {
            const b = m.b, dos = m.jugadores === 2;
            // Público, cuerdas y lona
            ctx.fillStyle = '#1b1b2f'; ctx.fillRect(0, Y0, W, 260);
            for (let i = 0; i < 90; i++) { ctx.fillStyle = ['#343a40', '#495057', '#5c3d2e', '#2b2b45'][i % 4]; ctx.beginPath(); ctx.arc((i * 53) % W, Y0 + 30 + (i % 5) * 14, 8, 0, Math.PI * 2); ctx.fill(); }
            if (Math.floor(m.t * 3) % 4 === 0) { ctx.fillStyle = 'rgba(255,255,255,.7)'; ctx.fillRect((m.t * 97) % W, Y0 + 30 + (m.t * 31) % 60, 3, 3); }   // flashes
            ctx.fillStyle = '#4dabf7'; ctx.fillRect(0, Y0 + 205, W, 60);
            ctx.fillStyle = '#e03131'; ctx.fillRect(0, Y0 + 110, W, 4); ctx.fillStyle = '#f8f9fa'; ctx.fillRect(0, Y0 + 140, W, 4); ctx.fillStyle = '#1971c2'; ctx.fillRect(0, Y0 + 170, W, 4);
            if (!b) return;
            const anim = b.anim, d = anim ? (m.t - anim.t) : 9;
            // Sacudón cuando lo golpean
            ctx.save();
            if (anim && anim.tipo === 'recibo' && d < .4) ctx.translate(Math.sin(d * 80) * 8, Math.cos(d * 70) * 5);
            const R = this.quien(m);
            let estado = 'quieto', o = {};
            if (anim && anim.tipo === 'pego' && d < .6) { estado = 'golpeado'; o.lado = anim.lado; }
            else if (anim && anim.tipo === 'recibo' && d < .5) { estado = 'golpea'; o.d = d / .25; }
            else if (anim && anim.tipo === 'ko-rival' && d < 1.2) { estado = 'ko'; o.d = d; }
            else if (m.estado === 'jugando') estado = 'guardia';
            if (!(b.caido && !dos)) rival(ctx, R, estado, m.t, o);
            ctx.restore();
            if (anim && anim.tipo === 'recibo' && d < .25) { ctx.fillStyle = `rgba(255,0,0,${.45 - d})`; ctx.fillRect(0, Y0, W, 260); }
            // Tumbado: todo de lado, oscuro, y la cuenta
            if (b.caido) {
                ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(0, Y0, W, 260);
                const cuenta = Math.min(10, (b.caido.intentos ? 6 : 1) + Math.floor((7 - Math.max(0, m.reloj)) / 1.6));
                m.texto(String(cuenta), CX, Y0 + 60, {tam: 40, color: '#ffd43b', alinear: 'center'});
                m.texto(dos ? `${JUGADORES[b.caido.quien].nombre}: ¡RESPONDA RÁPIDO PARA LEVANTARSE!` : '¡RESPONDA RÁPIDO PARA LEVANTARSE!', CX, Y0 + 115, {tam: 7, alinear: 'center'});
            }
            // Barras de vida
            if (dos) { barra(m, ctx, 10, JUGADORES[0].nombre, b.salud[0], '#ff922b'); barra(m, ctx, W - 200, JUGADORES[1].nombre, b.salud[1], '#4dabf7', true); }
            else { barra(m, ctx, 10, 'USTED', b.salud[0], '#69db7c'); barra(m, ctx, W - 200, `${R.nombre} ${b.rivalN + 1}/3`, 100 * b.rival / R.vida, '#ff6b6b', true); }
            // Nuestros guantes: cada uno es una opción, con su texto encima
            const ops = m.opciones, empuja = anim && anim.tipo === 'pego' && d < .3 ? (1 - d / .3) : 0;
            ops.forEach((op, k) => {
                const lado = k ? 1 : -1, x = CX + lado * 120, gx = x - lado * empuja * (anim && anim.lado === lado ? 60 : 0), gy = Y0 + 238 - (anim && anim.lado === lado ? empuja * 70 : 0);
                const caja = {x: k ? CX + 8 : 8, y: Y0 + 150, w: 224, h: 48};
                ctx.fillStyle = 'rgba(0,0,0,.65)'; ctx.fillRect(caja.x, caja.y, caja.w, caja.h);
                ctx.strokeStyle = Gamificacion.COLORES[k]; ctx.lineWidth = 2; ctx.strokeRect(caja.x, caja.y, caja.w, caja.h);
                // El texto de la opción, grande y centrado (más chico si es largo)
                if (m.conMate(op.texto)) {
                    m.texto(op.texto, caja.x + caja.w / 2, caja.y + caja.h / 2, {tam: 10, mate: true, alinear: 'center', base: 'middle', ancho: caja.w - 12});
                } else {
                    let tam = 10, lineas;
                    do { ctx.font = `${tam}px ${m.FUENTE}`; lineas = m.partir(op.texto, caja.w - 12); } while (lineas.length * (tam + 3) > caja.h - 6 && --tam > 5);
                    lineas = lineas.slice(0, Math.floor((caja.h - 6) / (tam + 3)));
                    lineas.forEach((l, i) => m.texto(l, caja.x + caja.w / 2, caja.y + caja.h / 2 - lineas.length * (tam + 3) / 2 + i * (tam + 3), {tam, alinear: 'center'}));
                }
                guante(ctx, gx, gy, 38 * (1 - empuja * .3), dos ? (m.turno ? '#1971c2' : '#e8590c') : Gamificacion.COLORES[k], k, lado);
            });
            if (dos && !b.caido) m.texto(`ATACA ${JUGADORES[m.turno].nombre}`, CX, Y0 + 40, {tam: 8, alinear: 'center', color: m.turno ? '#4dabf7' : '#ff922b'});
        },
        final(m) {
            const b = m.b || {salud: [0, 0]}, dos = m.jugadores === 2;
            let titulo, color;
            if (dos) { const g = b.salud[0] === b.salud[1] ? -1 : (b.salud[0] > b.salud[1] ? 0 : 1); titulo = g < 0 ? '¡EMPATE!' : `¡GANA ${JUGADORES[g].nombre}!`; color = '#ffd43b'; }
            else if (b.campeon) { titulo = '¡CAMPEÓN DEL SABER!'; color = '#ffd43b'; }
            else { titulo = b.fin ? 'PERDIÓ POR KO' : 'FIN DEL COMBATE'; color = '#ff6b6b'; }
            m.texto(titulo, 240, 80, {tam: 14, color, alinear: 'center'});
            if (!dos) m.texto(`RIVALES VENCIDOS: ${b.campeon ? 3 : (b.rivalN || 0)} DE 3 · CAÍDAS: ${b.caidas || 0}`, 240, 130, {tam: 8, alinear: 'center'});
            else m.texto(`GOLPES: ${m.marcador[0]} – ${m.marcador[1]}`, 240, 130, {tam: 9, alinear: 'center'});
            m.texto(`ACIERTOS: ${m.aciertos} de ${m.respuestas.length}`, 240, 160, {tam: 9, alinear: 'center'});
            m.texto(`PUNTAJE: ${m.puntaje}`, 240, 190, {tam: 10, alinear: 'center', color: '#ffd43b'});
            if (m.textoFinal) m.texto(m.textoFinal(), 240, 230, {tam: 8, alinear: 'center', color: '#aaa'});
        },
    });
})();
