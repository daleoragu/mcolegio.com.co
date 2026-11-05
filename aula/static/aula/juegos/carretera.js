/* Carretera del saber: carrera con vista desde arriba, de ciudad en ciudad.
 * Por la vía bajan carros con las opciones: hay que tocar el de la respuesta correcta y esquivar los
 * de las equivocadas. Los carros blancos con la bomba dan gasolina; sin gasolina se pierde una vida.
 * Desde el nivel 2 hay tráfico. Con 3 aciertos seguidos llega el cóndor: llena el tanque y da turbo. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, RX = 148, RW = 184, CARRILES = 4, AN = RW / CARRILES, YA = 248;
    const RUTAS = [
        ['IBAGUÉ', 'CAJAMARCA', 'ARMENIA', 'PEREIRA', 'MANIZALES', 'MEDELLÍN', 'MONTERÍA', 'CARTAGENA'],
        ['BOGOTÁ', 'GIRARDOT', 'IBAGUÉ', 'ARMENIA', 'CALI', 'POPAYÁN', 'PASTO', 'IPIALES'],
        ['NEIVA', 'IBAGUÉ', 'HONDA', 'BOGOTÁ', 'TUNJA', 'BUCARAMANGA', 'CÚCUTA', 'SANTA MARTA'],
    ];
    const carril = c => RX + AN / 2 + c * AN;

    function carro(ctx, x, y, color, o) {
        o = o || {};
        ctx.save(); ctx.translate(x, y); if (o.giro) ctx.rotate(o.giro);
        ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.fillRect(-10, -16, 22, 36);
        ctx.fillStyle = '#212529'; ctx.fillRect(-13, -12, 4, 8); ctx.fillRect(9, -12, 4, 8); ctx.fillRect(-13, 6, 4, 8); ctx.fillRect(9, 6, 4, 8);   // llantas
        ctx.fillStyle = color; ctx.beginPath(); ctx.roundRect(-10, -18, 20, 36, 5); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.fillRect(-7, -16, 3, 30);
        ctx.fillStyle = '#a5d8ff'; ctx.fillRect(-7, o.jugador ? -10 : 6, 14, 6);   // parabrisas (hacia donde va)
        ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(-7, -2, 14, 6);
        if (o.letra !== undefined) {
            ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(0, 1, 7, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#111'; ctx.font = 'bold 9px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(Gamificacion.LETRAS[o.letra], 0, 2);
        }
        if (o.gasolina) {   // la bomba de gasolina en el techo
            ctx.fillStyle = '#e03131'; ctx.fillRect(-5, -4, 8, 10); ctx.fillRect(3, -2, 3, 2); ctx.fillStyle = '#fff'; ctx.fillRect(-3, -2, 4, 3);
        }
        ctx.restore();
    }

    /* El cóndor de los Andes (el ave nacional): llega volando cuando hay racha. */
    function condor(ctx, x, y, t) {
        const ala = Math.sin(t * 10) * 8;
        ctx.fillStyle = '#212529';
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 34, y - 6 + ala); ctx.lineTo(x - 30, y + 4 + ala); ctx.lineTo(x - 6, y + 8); ctx.fill();
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 34, y - 6 + ala); ctx.lineTo(x + 30, y + 4 + ala); ctx.lineTo(x + 6, y + 8); ctx.fill();
        ctx.fillStyle = '#f8f9fa'; ctx.fillRect(x - 26, y - 2 + ala * .8, 10, 3); ctx.fillRect(x + 16, y - 2 + ala * .8, 10, 3);   // plumas blancas
        ctx.fillStyle = '#343a40'; ctx.beginPath(); ctx.ellipse(x, y + 4, 6, 11, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#f8f9fa'; ctx.fillRect(x - 5, y - 6, 10, 3);                                      // collar blanco
        ctx.fillStyle = '#e8590c'; ctx.beginPath(); ctx.arc(x, y - 10, 4, 0, Math.PI * 2); ctx.fill();   // cabeza
        ctx.fillStyle = '#ffd43b'; ctx.fillRect(x - 1, y - 16, 2, 3);
    }

    Gamificacion.registrar('carretera', {
        nombre: 'Carretera del saber',
        instrucciones: 'Maneje con las flechas (o tocando a los lados). Choque el carro de la respuesta correcta y esquive los de las equivocadas. Los carros blancos con bomba dan gasolina. ¡Con 3 aciertos seguidos llega el cóndor!',
        controles: 'cruceta',
        maxOpciones: 6,
        fondo: '#2b8a3e',
        icono(ctx, k, tam) { ctx.save(); ctx.translate(tam / 2, tam / 2); ctx.scale(tam / 44, tam / 44); carro(ctx, 0, 0, Gamificacion.COLORES[k], {letra: k}); ctx.restore(); },
        nuevaPregunta(m, repetir) {
            if (!m.ruta) {
                m.ruta = RUTAS[Math.floor(Math.random() * RUTAS.length)];
                m.auto = {x: carril(1), meta: null, inv: 0}; m.gasolina = 100; m.racha = 0; m.calle = 0; m.km = 0;
                m.objetos = [];
            }
            const vel = 46 + m.nivel * 8;
            // Las opciones en los carriles (más de 4: una segunda fila más atrás)
            const carriles = [0, 1, 2, 3].sort(() => Math.random() - .5), otros = [0, 1, 2, 3].sort(() => Math.random() - .5);
            m.s = {ola: m.opciones.map((_, k) => ({k, x: carril(k < 4 ? carriles[k] : otros[k - 4]), y: k < 4 ? -30 : -110, vel, giro: 0, choco: false})),
                   eligio: false};
            m.objetos = m.objetos.filter(o => o.tipo === 'gasolina' && o.y < 150);
            const ciudad = Math.min(m.ruta.length - 1, m.nivel - 1);
            if (!repetir && ciudad !== m.ciudad) { m.ciudad = ciudad; if (ciudad > 0) m.letrero = {texto: 'BIENVENIDO A ' + m.ruta[ciudad], y: -40}; }
            m.auto.inv = m.t + 1.2;
        },
        alTocar(m, x) { m.auto.meta = Math.max(RX + 12, Math.min(RX + RW - 12, x)); },
        alTecla(m, t) { if (t === 'izquierda' || t === 'derecha') m.auto.meta = null; },
        avanzar(m, dt, jugando) {
            const vel = 150 + m.nivel * 12 + (m.turbo > m.t ? 120 : 0);
            m.calle = (m.calle + vel * dt) % 40; m.km += vel * dt / 300;
            // Gasolina, tráfico y letrero bajan con la vía
            m.objetos.forEach(o => { o.y += (vel - o.propia) * dt; });
            m.objetos = m.objetos.filter(o => o.y < 300);
            if (m.letrero) { m.letrero.y += vel * dt; if (m.letrero.y > 300) m.letrero = null; }
            if (!jugando) return;
            m.prox = m.prox || {gas: m.t + 4, trafico: m.t + 3};
            if (m.t > m.prox.gas) { m.objetos.push({tipo: 'gasolina', x: carril(Math.floor(Math.random() * 4)), y: -40, propia: vel - 70}); m.prox.gas = m.t + 6 + Math.random() * 4; }
            if (m.nivel >= 2 && m.t > m.prox.trafico) {
                m.objetos.push({tipo: 'trafico', x: carril(Math.floor(Math.random() * 4)), y: -40, propia: vel - 90 - m.nivel * 6,
                                color: ['#868e96', '#a0522d', '#5f3dc4', '#212529'][Math.floor(Math.random() * 4)]});
                m.prox.trafico = m.t + Math.max(1.6, 4.5 - m.nivel * .4) + Math.random() * 2;
            }
        },
        actualizar(m, dt) {
            const a = m.auto, s = m.s;
            this.avanzar(m, dt, true);
            // Manejar
            const izq = m.teclas.has('izquierda'), der = m.teclas.has('derecha');
            if (izq || der) { a.x += ((der ? 1 : 0) - (izq ? 1 : 0)) * 180 * dt; a.meta = null; }
            else if (a.meta !== null) { const d = a.meta - a.x; a.x += Math.sign(d) * Math.min(Math.abs(d), 180 * dt); }
            a.x = Math.max(RX + 12, Math.min(RX + RW - 12, a.x));
            // Gasolina
            m.gasolina -= (3 + m.nivel * .4) * dt;
            if (m.gasolina <= 0) { m.gasolina = 60; m.perderVida('¡SIN GASOLINA!'); return; }
            const toca = o => Math.abs(o.x - a.x) < 20 && Math.abs(o.y - YA) < 34;
            for (const o of m.objetos) {
                if (o.usado || !toca(o)) continue;
                if (o.tipo === 'gasolina') { o.usado = true; m.gasolina = Math.min(100, m.gasolina + 35); m.puntaje += 10; m.sonidos.toque(); m.aviso('+ GASOLINA', '#69db7c', .6); }
                else if (m.t > a.inv) { o.usado = true; m.perderVida('¡CHOQUE!'); return; }
            }
            m.objetos = m.objetos.filter(o => !o.usado);
            // La ola de carros con las opciones
            s.ola.forEach(o => { o.y += o.vel * dt; });
            const c = s.ola.find(o => !o.choco && toca(o));
            if (c) {
                c.choco = true; s.eligio = true;
                m.responder(c.k);
                return;
            }
            if (s.ola.every(o => o.y > 300)) { m.responder(null); m.aviso('¡NO ELIGIÓ NINGUNO!', '#ff6b6b', 1.3); }
        },
        alResponder(m, bien, k) {
            if (bien) {
                m.racha = (m.racha || 0) + 1;
                if (m.racha % 3 === 0) { m.condor = m.t; m.turbo = m.t + 4; m.gasolina = 100; m.puntaje += 50; setTimeout(() => m.aviso('¡EL CÓNDOR LE AYUDA!', '#ffd43b', 1.2), 950); }
            } else {
                m.racha = 0;
                const c = m.s.ola.find(o => o.k === k); if (c) c.giro = 1;
            }
        },
        actualizarEnPausa(m, dt) {
            this.avanzar(m, dt, false);
            if (m.s) m.s.ola.forEach(o => { o.y += o.vel * dt * .5; if (o.giro) o.giro += dt * 9; });
        },
        dibujar(m, ctx) {
            // Pasto, árboles y casas a los lados
            ctx.fillStyle = '#2f9e44'; ctx.fillRect(0, Y0, W, 260);
            const off = m.calle || 0;
            for (let y = -40; y < 300; y += 40) {
                const yy = Y0 + y + off;
                ctx.fillStyle = '#2b8a3e'; ctx.beginPath(); ctx.arc(40, yy, 12, 0, Math.PI * 2); ctx.arc(W - 40, yy + 20, 12, 0, Math.PI * 2); ctx.fill();
                if ((y / 40) % 3 === 0) {
                    ctx.fillStyle = '#f8f9fa'; ctx.fillRect(80, yy - 10, 30, 22); ctx.fillStyle = '#c92a2a'; ctx.fillRect(78, yy - 14, 34, 6);
                    ctx.fillStyle = '#ffe066'; ctx.fillRect(W - 112, yy + 4, 28, 20); ctx.fillStyle = '#1971c2'; ctx.fillRect(W - 114, yy, 32, 6);
                }
            }
            // La vía
            ctx.fillStyle = '#495057'; ctx.fillRect(RX - 8, Y0, RW + 16, 260);
            ctx.fillStyle = '#f8f9fa'; ctx.fillRect(RX - 6, Y0, 3, 260); ctx.fillRect(RX + RW + 3, Y0, 3, 260);
            ctx.fillStyle = '#ffd43b';
            for (let c = 1; c < CARRILES; c++) for (let y = -40; y < 300; y += 40) ctx.fillRect(RX + c * AN - 1, Y0 + y + off, 2, 20);
            // Letrero de la ciudad
            if (m.letrero) {
                const y = Y0 + m.letrero.y;
                ctx.fillStyle = '#5c3d2e'; ctx.fillRect(RX + RW + 30, y, 4, 30);
                ctx.fillStyle = '#2b8a3e'; ctx.fillRect(RX + RW + 14, y - 26, 130, 26); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(RX + RW + 16, y - 24, 126, 22);
                m.texto(m.letrero.texto, RX + RW + 79, y - 17, {tam: 6, alinear: 'center'});
            }
            if (!m.auto) return;
            m.objetos.forEach(o => carro(ctx, o.x, Y0 + o.y, o.tipo === 'gasolina' ? '#f8f9fa' : o.color, {gasolina: o.tipo === 'gasolina'}));
            if (m.s) m.s.ola.forEach(o => { if (!o.choco || o.giro) carro(ctx, o.x, Y0 + o.y, Gamificacion.COLORES[o.k], {letra: o.k, giro: o.giro}); });
            // Nuestro carro (titila al volver a la vía)
            if (m.t > m.auto.inv || Math.floor(m.t * 10) % 2) {
                if (m.turbo > m.t) { ctx.fillStyle = '#ff922b'; ctx.fillRect(m.auto.x - 6, Y0 + YA + 18, 4, 8 + Math.random() * 6); ctx.fillRect(m.auto.x + 2, Y0 + YA + 18, 4, 8 + Math.random() * 6); }
                carro(ctx, m.auto.x, Y0 + YA, '#e03131', {jugador: true});
            }
            if (m.condor && m.t - m.condor < 2.5) { const d = (m.t - m.condor) / 2.5; condor(ctx, -40 + d * (W + 80), Y0 + 70 - Math.sin(d * Math.PI) * 30, m.t); }
            // Tablero: gasolina, ruta y kilómetros
            ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(6, Y0 + 6, 118, 46);
            m.texto('GASOLINA', 12, Y0 + 11, {tam: 6});
            ctx.fillStyle = '#343a40'; ctx.fillRect(12, Y0 + 21, 104, 8);
            ctx.fillStyle = m.gasolina < 25 ? '#ff5d5d' : '#69db7c'; ctx.fillRect(12, Y0 + 21, 104 * Math.max(0, m.gasolina) / 100, 8);
            const ciudad = m.ciudad || 0, destino = m.ruta[Math.min(m.ruta.length - 1, Math.ceil(m.total / 3))];
            m.texto(`${m.ruta[ciudad]} → ${destino}`, 12, Y0 + 35, {tam: 5, color: '#ffd43b'});
            m.texto(`KM ${Math.floor(m.km)}${m.racha >= 2 ? ' · RACHA ' + m.racha : ''}`, 12, Y0 + 44, {tam: 5, color: '#ced4da'});
            // Progreso del viaje (a la derecha)
            const frac = Math.min(1, m.indice / Math.max(1, m.total));
            ctx.fillStyle = 'rgba(0,0,0,.4)'; ctx.fillRect(W - 14, Y0 + 10, 6, 240);
            ctx.fillStyle = '#ffd43b'; ctx.fillRect(W - 14, Y0 + 250 - 240 * frac, 6, 240 * frac);
            ctx.fillStyle = '#e03131'; ctx.fillRect(W - 17, Y0 + 246 - 240 * frac, 12, 6);
        },
        final(m, ctx) {
            const llego = m.vidas > 0, destino = m.ruta ? m.ruta[Math.min(m.ruta.length - 1, Math.ceil(m.total / 3))] : '';
            m.texto(llego ? `¡LLEGÓ A ${destino}!` : 'SE QUEDÓ EN EL CAMINO', 240, 80, {tam: 13, color: llego ? '#69db7c' : '#ff6b6b', alinear: 'center'});
            carro(ctx, 240, 140, '#e03131', {jugador: true});
            m.texto(`ACIERTOS: ${m.aciertos} de ${m.total} · KM ${Math.floor(m.km || 0)}`, 240, 190, {tam: 9, alinear: 'center'});
            m.texto(`PUNTAJE: ${m.puntaje}`, 240, 215, {tam: 10, alinear: 'center', color: '#ffd43b'});
            if (m.textoFinal) m.texto(m.textoFinal(), 240, 250, {tam: 8, alinear: 'center', color: '#aaa'});
        },
    });
})();
