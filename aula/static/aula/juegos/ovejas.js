/* Ovejas y lobos: los lobos bajan en canastas colgadas de un racimo de globos; cada canasta es una
 * opción. La oveja arquera, desde su torre, jala el arco (mantenga presionado, arrastre hacia atrás y
 * suelte, como una catapulta) y revienta los globos de la canasta con la respuesta correcta.
 * Algunas canastas llevan un corderito: si es la correcta, el corderito se salva en paracaídas.
 * Si las canastas aterrizan, se acabó el tiempo.
 * También: tocar sin arrastrar dispara hacia ese punto; A–F disparan a esa canasta; ↑ ↓ mueven la oveja. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, SUELO = 246, G = 240, TORRE = 428, OV = 1.3;   // OV: tamaño de la oveja

    function tono(hex, f) {
        const n = parseInt(hex.slice(1), 16), c = v => Math.max(0, Math.min(255, Math.round(f > 1 ? v + (255 - v) * (f - 1) : v * f)));
        return `rgb(${c(n >> 16)},${c(n >> 8 & 255)},${c(n & 255)})`;
    }
    function lana(ctx, x, y, r) {
        const g = ctx.createRadialGradient(x - r * .35, y - r * .4, r * .1, x, y, r);
        g.addColorStop(0, '#fffdf7'); g.addColorStop(.7, '#f3e9d6'); g.addColorStop(1, '#d9c9ad');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }

    /* La oveja arquera: lana esponjosa, cuernos en espiral, bufanda verde, correa con bolsitas y carcaj.
     * Se dibuja mirando a la derecha y se voltea (dispara hacia la izquierda). */
    function oveja(ctx, x, y, jalon, t) {
        const resp = Math.sin(t * 3) * .6;
        ctx.save(); ctx.translate(x, y + resp); ctx.scale(-OV, OV);
        ctx.fillStyle = 'rgba(0,0,0,.18)'; ctx.beginPath(); ctx.ellipse(0, 27, 16, 4, 0, 0, Math.PI * 2); ctx.fill();
        // patas con pezuñas
        [-9, 4].forEach(dx => { ctx.fillStyle = '#e9c3a5'; ctx.fillRect(dx, 15, 6, 9); ctx.fillStyle = '#5c3d2e'; ctx.fillRect(dx - 1, 23, 8, 4); });
        // carcaj en la espalda con las plumas de las flechas
        ctx.save(); ctx.translate(-13, -6); ctx.rotate(-.45);
        ctx.fillStyle = '#7a4a24'; ctx.fillRect(-4, -12, 8, 20); ctx.fillStyle = '#5c3d2e'; ctx.fillRect(-4, -12, 8, 3);
        [[-3, '#f8f9fa'], [0, '#ced4da'], [3, '#f8f9fa']].forEach(([dx, c]) => { ctx.fillStyle = '#8b5a2b'; ctx.fillRect(dx - .5, -18, 1, 6); ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(dx, -22); ctx.lineTo(dx - 2, -16); ctx.lineTo(dx + 2, -16); ctx.fill(); });
        ctx.restore();
        // cuerpo de lana
        [[0, 15, 10], [-11, 11, 9], [11, 11, 9], [-13, 1, 9], [13, 1, 9], [0, 4, 14], [-7, -7, 9], [7, -7, 9]].forEach(([dx, dy, r]) => lana(ctx, dx, dy, r));
        // correa cruzada, cinturón y bolsitas
        ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 3.5; ctx.beginPath(); ctx.moveTo(-11, -8); ctx.lineTo(10, 12); ctx.stroke();
        ctx.fillStyle = '#7a4a24'; ctx.fillRect(-15, 8, 30, 4); ctx.fillStyle = '#c9a227'; ctx.fillRect(-2, 7.5, 4, 5);
        ctx.fillStyle = '#6b4423'; ctx.fillRect(-16, 10, 7, 7); ctx.fillRect(9, 10, 7, 7);
        ctx.fillStyle = '#c9a227'; ctx.fillRect(-13.5, 12, 2, 2); ctx.fillRect(11.5, 12, 2, 2);
        // bufanda verde
        ctx.fillStyle = '#2f7d32'; ctx.beginPath(); ctx.ellipse(1, -12, 12, 4.5, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#3e9142'; ctx.beginPath(); ctx.moveTo(-6, -11); ctx.lineTo(-12, 0); ctx.lineTo(-6, -2); ctx.fill();
        // el brazo de adelante (sostiene el arco) y el de atrás (jala la cuerda)
        lana(ctx, 13, -4, 6); ctx.fillStyle = '#4a3020'; ctx.beginPath(); ctx.arc(19, -4, 3, 0, Math.PI * 2); ctx.fill();
        const tira = jalon ? Math.min(12, jalon.largo / 9) : 0;
        lana(ctx, 4 - tira * .4, -6, 5.5);
        // cabeza: copete de lana, orejas, cuernos en espiral y cara decidida
        [[-6, -31, 6], [0, -34, 7], [6, -31, 6], [-9, -26, 5], [9, -26, 5]].forEach(([dx, dy, r]) => lana(ctx, dx, dy, r));
        ctx.fillStyle = '#f2b8a0'; ctx.beginPath(); ctx.ellipse(-10, -21, 4, 2.5, .5, 0, Math.PI * 2); ctx.ellipse(13, -21, 4, 2.5, -.5, 0, Math.PI * 2); ctx.fill();
        [[-9, -27, 1], [12, -27, -1]].forEach(([cx, cy, s]) => {
            const g = ctx.createRadialGradient(cx, cy, 1, cx, cy, 6); g.addColorStop(0, '#d4a373'); g.addColorStop(1, '#8b5e34');
            ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, 5.5, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#6b4423'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(cx + s * .5, cy + .5, 3, 0, Math.PI * 1.6); ctx.stroke();
            ctx.beginPath(); ctx.arc(cx + s, cy + 1, 1.2, 0, Math.PI * 2); ctx.stroke();
        });
        const piel = ctx.createRadialGradient(2, -24, 1, 2, -21, 9); piel.addColorStop(0, '#fbe0cc'); piel.addColorStop(1, '#efbf9f');
        ctx.fillStyle = piel; ctx.beginPath(); ctx.ellipse(2, -21, 8.5, 7.5, 0, 0, Math.PI * 2); ctx.fill();
        lana(ctx, -1, -28, 4); lana(ctx, 4, -28.5, 4);                                 // flequillo
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(-1, -21, 2.3, 2.6, 0, 0, Math.PI * 2); ctx.ellipse(6, -21, 2.3, 2.6, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#5c3d2e'; ctx.beginPath(); ctx.arc(-.2, -20.6, 1.5, 0, Math.PI * 2); ctx.arc(6.8, -20.6, 1.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(0, -20.5, .8, 0, Math.PI * 2); ctx.arc(7, -20.5, .8, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#6b4423'; ctx.lineWidth = 1.3; ctx.beginPath(); ctx.moveTo(-4, -25.5); ctx.lineTo(1.5, -23.5); ctx.moveTo(9, -25.5); ctx.lineTo(4.5, -23.5); ctx.stroke();   // cejas decididas
        ctx.fillStyle = '#e08f8f'; ctx.beginPath(); ctx.ellipse(3, -16.5, 1.8, 1.2, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#8b5e34'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(1.5, -14.5); ctx.lineTo(4.5, -14.5); ctx.stroke();
        ctx.restore();
        arco(ctx, x - 22 * OV, y - 4 * OV + resp, jalon, tira);
    }

    // El arco de madera con hojitas; apunta hacia donde va a salir la flecha
    function arco(ctx, bx, by, jalon, tira) {
        const ang = jalon ? Math.atan2(jalon.dy, jalon.dx) : Math.PI;
        ctx.save(); ctx.translate(bx, by); ctx.rotate(ang); ctx.scale(OV, OV);
        const g = ctx.createLinearGradient(0, -18, 0, 18); g.addColorStop(0, '#a0703c'); g.addColorStop(.5, '#c68b4e'); g.addColorStop(1, '#8b5a2b');
        ctx.strokeStyle = g; ctx.lineWidth = 3.2; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(-3, -19); ctx.quadraticCurveTo(10, -12, 6, 0); ctx.quadraticCurveTo(10, 12, -3, 19); ctx.stroke();
        ctx.lineCap = 'butt';
        ctx.fillStyle = '#6b4423'; ctx.fillRect(4, -3, 4, 6);                                  // empuñadura
        ctx.fillStyle = '#69a84f'; [[5, -11, .6], [5, 11, -.6], [1, -16, .9]].forEach(([lx, ly, r]) => { ctx.beginPath(); ctx.ellipse(lx + 3, ly, 3, 1.4, r, 0, Math.PI * 2); ctx.fill(); });
        ctx.strokeStyle = '#f1f3f5'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-3, -19); ctx.lineTo(-3 - tira, 0); ctx.lineTo(-3, 19); ctx.stroke();
        if (jalon) {
            ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-3 - tira, 0); ctx.lineTo(24, 0); ctx.stroke();
            ctx.fillStyle = '#adb5bd'; ctx.beginPath(); ctx.moveTo(29, 0); ctx.lineTo(23, -3); ctx.lineTo(23, 3); ctx.fill();
            ctx.fillStyle = '#f8f9fa'; ctx.beginPath(); ctx.moveTo(-3 - tira, 0); ctx.lineTo(2 - tira, -3); ctx.lineTo(2 - tira, 3); ctx.fill();
        }
        ctx.restore();
    }

    /* Una cabeza de lobo asomada por el borde de la canasta (mirando hacia la oveja, a la derecha). */
    function lobo(ctx, x, y, e, o) {
        const pelo = o.tono || '#7d7466', claro = '#cbbca4';
        ctx.save(); ctx.translate(x, y); ctx.scale(e, e);
        // orejas
        ctx.fillStyle = pelo;
        ctx.beginPath(); ctx.moveTo(-7, -6); ctx.lineTo(-6, -19); ctx.lineTo(0, -9); ctx.fill();
        ctx.beginPath(); ctx.moveTo(3, -8); ctx.lineTo(8, -19); ctx.lineTo(9, -5); ctx.fill();
        ctx.fillStyle = '#d9a5a0'; ctx.beginPath(); ctx.moveTo(-5.5, -8); ctx.lineTo(-5.5, -15); ctx.lineTo(-2, -9); ctx.fill();
        ctx.beginPath(); ctx.moveTo(4.5, -9); ctx.lineTo(7.5, -15); ctx.lineTo(7.5, -7); ctx.fill();
        // cabeza peluda y hocico
        const g = ctx.createRadialGradient(-2, -6, 1, 0, -3, 11); g.addColorStop(0, tono(pelo, 1.25)); g.addColorStop(1, pelo);
        ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, -3, 9.5, 8.5, 0, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.moveTo(-9, 0); ctx.lineTo(-12, 3); ctx.lineTo(-7, 4); ctx.fill();               // pelo de la mejilla
        ctx.fillStyle = claro; ctx.beginPath(); ctx.ellipse(8, 0, 7, 4.2, .1, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#212529'; ctx.beginPath(); ctx.ellipse(14, -1.5, 2.2, 1.6, 0, 0, Math.PI * 2); ctx.fill();   // nariz
        // ojos amarillos y cejas bravas
        ctx.fillStyle = o.mareado ? '#fff' : '#ffd43b';
        ctx.beginPath(); ctx.ellipse(-1, -6, 2.4, 2, 0, 0, Math.PI * 2); ctx.ellipse(5.5, -6, 2.2, 1.9, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111';
        if (o.mareado) { ctx.font = 'bold 5px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('x', -1, -6); ctx.fillText('x', 5.5, -6); }
        else { ctx.beginPath(); ctx.arc(-.3, -6, 1, 0, Math.PI * 2); ctx.arc(6.2, -6, 1, 0, Math.PI * 2); ctx.fill(); }
        ctx.strokeStyle = '#3b2f2a'; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(-4, -10); ctx.lineTo(1.5, -8); ctx.moveTo(8.5, -10); ctx.lineTo(3.5, -8); ctx.stroke();
        // boca: gruñido con dientes (o abierta gritando)
        if (o.grita) { ctx.fillStyle = '#8b1a1a'; ctx.beginPath(); ctx.ellipse(8, 4, 4.5, 3, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillRect(5, 1.5, 1.5, 2); ctx.fillRect(9.5, 1.5, 1.5, 2); }
        else { ctx.fillStyle = '#fff'; ctx.fillRect(4, 2.5, 8, 2); ctx.strokeStyle = '#3b2f2a'; ctx.lineWidth = .8; ctx.beginPath(); ctx.moveTo(4, 2.5); ctx.lineTo(12, 2.5); ctx.moveTo(6.5, 2.5); ctx.lineTo(6.5, 4.5); ctx.moveTo(9, 2.5); ctx.lineTo(9, 4.5); ctx.stroke(); }
        // gafas de aviador
        if (o.gafas) {
            ctx.fillStyle = '#6b4423'; ctx.fillRect(-9, -11, 18, 2.5);
            ctx.fillStyle = '#a5d8ff'; ctx.strokeStyle = '#495057'; ctx.lineWidth = 1.2;
            ctx.beginPath(); ctx.arc(-2, -12, 3, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.arc(5, -12, 3, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        }
        ctx.restore();
    }

    function cordero(ctx, x, y, paraguas) {
        if (paraguas) {
            ctx.fillStyle = '#69db7c'; ctx.beginPath(); ctx.arc(x, y - 16, 11, Math.PI, 0); ctx.fill();
            ctx.strokeStyle = '#495057'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x - 10, y - 16); ctx.lineTo(x, y - 4); ctx.lineTo(x + 10, y - 16); ctx.stroke();
        }
        [[0, 0, 5.5], [-4, 1, 4], [4, 1, 4], [0, -4, 4]].forEach(([dx, dy, r]) => lana(ctx, x + dx, y + dy, r));
        ctx.fillStyle = '#f2c6ae'; ctx.beginPath(); ctx.ellipse(x - 5, y - 2, 3.2, 3, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.fillRect(x - 6.5, y - 3, 1.2, 1.2); ctx.fillRect(x - 4, y - 3, 1.2, 1.2);
    }

    // Los globos del racimo (tonos del color de su opción) y la letra en el del frente
    const GLOBOS = [[-13, 3, 10, .8], [13, 3, 10, 1.15], [-7, -11, 10, 1.25], [8, -11, 10, .9], [-19, -6, 8, 1.05], [19, -6, 8, .75], [0, 2, 12.5, 1]];
    function racimo(ctx, k, x, y, e, t) {
        const col = Gamificacion.COLORES[k];
        ctx.strokeStyle = 'rgba(80,60,40,.7)'; ctx.lineWidth = .8;
        GLOBOS.forEach(([dx, dy, r]) => { ctx.beginPath(); ctx.moveTo(x + dx * e, y + (dy + r) * e); ctx.lineTo(x, y + 32 * e); ctx.stroke(); });
        GLOBOS.forEach(([dx, dy, r, f], i) => {
            const bx = x + dx * e + Math.sin(t * 2 + i) * .6, by = y + dy * e, rr = r * e;
            const g = ctx.createRadialGradient(bx - rr * .35, by - rr * .4, rr * .1, bx, by, rr);
            g.addColorStop(0, tono(col, Math.min(1.6, f + .45))); g.addColorStop(1, tono(col, f * .85));
            ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(bx, by, rr, rr * 1.12, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = tono(col, .7); ctx.beginPath(); ctx.moveTo(bx - 2 * e, by + rr * 1.12 + 2 * e); ctx.lineTo(bx + 2 * e, by + rr * 1.12 + 2 * e); ctx.lineTo(bx, by + rr * 1.05); ctx.fill();
            ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.beginPath(); ctx.ellipse(bx - rr * .35, by - rr * .45, rr * .22, rr * .35, -.5, 0, Math.PI * 2); ctx.fill();
        });
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x, y + 2 * e, 7 * e, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(10 * e)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(Gamificacion.LETRAS[k], x, y + 3 * e);
    }

    /* La canasta de mimbre con sus lobos, cuerdas, aro y costalitos (x, y = borde de arriba de la canasta). */
    function canasta(ctx, l, x, y, t) {
        const e = l.e;
        if (!l.roto) {
            racimo(ctx, l.k, x, y - 58 * e, e, t);
            ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 1.5;
            ctx.beginPath(); ctx.ellipse(x, y - 26 * e, 10 * e, 2.5 * e, 0, 0, Math.PI * 2); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(x - 10 * e, y - 26 * e); ctx.lineTo(x - 19 * e, y); ctx.moveTo(x + 10 * e, y - 26 * e); ctx.lineTo(x + 19 * e, y); ctx.stroke();
        }
        // lobos asomados (detrás del borde)
        const pos = l.lobos === 1 ? [0] : l.lobos === 2 ? [-8, 8] : [-12, 0, 12];
        pos.forEach((dx, i) => lobo(ctx, x + dx * e, y - 3 * e + Math.sin(t * 4 + i) * .7, e * .95,
            {gafas: l.gafas === i, grita: i === 1 || l.roto, mareado: l.roto && l.y >= SUELO - 26 * e, tono: ['#7d7466', '#8a8070', '#6e675d'][i]}));
        if (l.cordero) cordero(ctx, x + 15 * e, y - 3 * e, false);
        // la canasta
        ctx.fillStyle = '#a8742f'; ctx.beginPath(); ctx.moveTo(x - 20 * e, y); ctx.lineTo(x + 20 * e, y); ctx.lineTo(x + 16 * e, y + 25 * e); ctx.lineTo(x - 16 * e, y + 25 * e); ctx.fill();
        ctx.strokeStyle = '#7a5020'; ctx.lineWidth = 1;
        for (let i = 1; i < 5; i++) {   // tejido
            const yy = y + i * 5 * e, w = 20 - i * .8;
            ctx.beginPath(); ctx.moveTo(x - w * e, yy); ctx.lineTo(x + w * e, yy); ctx.stroke();
            for (let xx = -w + (i % 2) * 2.5; xx < w; xx += 5) { ctx.beginPath(); ctx.moveTo(x + xx * e, yy - 5 * e); ctx.lineTo(x + xx * e, yy); ctx.stroke(); }
        }
        ctx.strokeStyle = '#d9b77a'; ctx.lineWidth = 3 * e; ctx.beginPath(); ctx.moveTo(x - 21 * e, y); ctx.lineTo(x + 21 * e, y); ctx.stroke();
        // patas en el borde
        ctx.fillStyle = '#9a8f7e'; pos.forEach(dx => { ctx.beginPath(); ctx.ellipse(x + (dx - 4) * e, y, 2.5 * e, 1.8 * e, 0, 0, Math.PI * 2); ctx.ellipse(x + (dx + 4) * e, y, 2.5 * e, 1.8 * e, 0, 0, Math.PI * 2); ctx.fill(); });
        // costalitos
        ctx.fillStyle = '#8b6b4a'; [-21, 21].forEach(dx => { ctx.beginPath(); ctx.ellipse(x + dx * e, y + 9 * e, 3.5 * e, 5 * e, 0, 0, Math.PI * 2); ctx.fill(); });
    }

    function boca(m) { return {x: TORRE - 34 * OV, y: m.ov.y - 4 * OV}; }
    const centroGlobos = l => ({x: l.x, y: l.y - 58 * l.e});
    function disparar(m, vx, vy, recto) {
        const b = boca(m);
        m.s.flechas.push({x: b.x, y: b.y, vx, vy, recto}); m.sonidos.toque();
    }

    Gamificacion.registrar('ovejas', {
        nombre: 'Ovejas y lobos',
        instrucciones: 'Mantenga presionado, arrastre hacia atrás y suelte para disparar con el arco (como una catapulta). Reviente los globos de la canasta con la respuesta correcta antes de que aterricen. ↑ ↓ (o arrastrar la torre con el dedo) mueven la oveja; A–F disparan directo.',
        maxOpciones: 6,
        fondo: '#a5d8ff',
        icono(ctx, k, tam) { ctx.save(); ctx.scale(tam / 56, tam / 56); racimo(ctx, k, 28, 26, 1, 0); ctx.restore(); },
        nuevaPregunta(m) {
            if (!m.ov) m.ov = {y: 150};
            const n = m.opciones.length, vel = 11 + m.nivel * 3, e = n <= 4 ? 1.2 : .95;
            const xs = Array.from({length: n}, (_, i) => (n === 1 ? 180 : 42 + i * (296 / (n - 1))) + (Math.random() - .5) * 10).sort(() => Math.random() - .5);
            m.s = {lobos: m.opciones.map((_, k) => ({k, x: xs[k], y: 76 * e + Math.random() * 10, e, vel, fase: Math.random() * 6, roto: false, vy: 0,
                                                       lobos: 1 + Math.floor(Math.random() * 3), gafas: Math.floor(Math.random() * 4), cordero: Math.random() < .35})),
                   flechas: [], jalon: null, salvados: [], estallidos: []};
        },
        alTocar(m, x, y) {
            // Tocar la torre (a la derecha) y arrastrar sube o baja la oveja; en otra parte, se jala el arco
            if (x > TORRE - 40) { m.s.subir = {y0: y, oy: m.ov.y}; return; }
            m.s.jalon = {x0: x, y0: y, dx: 0, dy: 0, largo: 0};
        },
        alArrastrar(m, x, y) {
            if (m.s.subir) { m.ov.y = Math.max(76, Math.min(206, m.s.subir.oy + y - m.s.subir.y0)); return; }
            const j = m.s.jalon; if (!j) return;
            j.dx = j.x0 - x; j.dy = j.y0 - y; j.largo = Math.hypot(j.dx, j.dy);
        },
        alSoltar(m, x, y) {
            if (m.s.subir) { m.s.subir = null; return; }
            const j = m.s.jalon; if (!j) return;
            m.s.jalon = null;
            if (j.largo > 12) {
                // Catapulta: dispara hacia el lado contrario del jalón, más fuerte entre más se jale
                const f = Math.min(560, j.largo * 4.2) / j.largo;
                disparar(m, j.dx * f, j.dy * f, false);
            } else {
                // Un toque: flecha derecha hacia ese punto
                const b = boca(m), dx = x - b.x, dy = y - Y0 - b.y, d = Math.hypot(dx, dy) || 1;
                disparar(m, dx / d * 520, dy / d * 520, true);
            }
        },
        alTecla(m, t, crudo) {
            const k = 'ABCDEF'.indexOf(String(crudo || '').toUpperCase());
            const l = k >= 0 && m.s.lobos.find(l => l.k === k && !l.roto);
            if (l) { const b = boca(m), c = centroGlobos(l), dx = c.x - b.x, dy = c.y - b.y, d = Math.hypot(dx, dy) || 1; disparar(m, dx / d * 560, dy / d * 560, true); }
        },
        actualizar(m, dt) {
            const s = m.s;
            if (m.teclas.has('arriba')) m.ov.y = Math.max(76, m.ov.y - 110 * dt);
            if (m.teclas.has('abajo')) m.ov.y = Math.min(206, m.ov.y + 110 * dt);
            this.mover(m, dt);
            // ¿Una flecha reventó los globos de una canasta?
            for (const f of s.flechas) {
                const l = s.lobos.find(l => { const c = centroGlobos(l); return !l.roto && Math.hypot(c.x - f.x, c.y - f.y) < 19 * l.e; });
                if (l) {
                    const c = centroGlobos(l);
                    l.roto = true; l.vy = 20; f.fuera = true; s.estallidos.push({x: c.x, y: c.y, t: m.t, k: l.k});
                    const bien = m.opciones[l.k] && m.opciones[l.k].correcta;
                    if (bien && l.cordero) { s.salvados.push({x: l.x + 15 * l.e, y: l.y - 3}); l.cordero = false; m.puntaje += 50; }
                    m.responder(l.k);
                    if (bien) setTimeout(() => m.aviso(s.salvados.length ? '¡SALVÓ AL CORDERITO!' : '¡LOBOS AL SUELO!', '#69db7c', .9), 0);
                    return;
                }
            }
            // Las canastas aterrizaron: se acabó el tiempo
            if (s.lobos.some(l => !l.roto && l.y + 25 * l.e >= SUELO)) { m.responder(null); setTimeout(() => m.aviso('¡LOS LOBOS ATERRIZARON!', '#ff6b6b', 1.3), 0); }
        },
        mover(m, dt) {
            const s = m.s;
            s.lobos.forEach(l => {
                if (l.roto) { l.vy += 520 * dt; l.y = Math.min(SUELO - 25 * l.e, l.y + l.vy * dt); return; }
                l.y += l.vel * dt; l.fase += dt * 1.6; l.x += Math.sin(l.fase) * 7 * dt;
            });
            s.flechas.forEach(f => { if (!f.recto) f.vy += G * dt; f.x += f.vx * dt; f.y += f.vy * dt; });
            s.flechas = s.flechas.filter(f => !f.fuera && f.x > -20 && f.x < W + 20 && f.y < 280 && f.y > -120);
            s.salvados.forEach(c => { c.y = Math.min(SUELO - 8, c.y + 30 * dt); c.x += 10 * dt; });
        },
        actualizarEnPausa(m, dt) { if (m.s) this.mover(m, dt); },
        dibujar(m, ctx) {
            // Cielo con nubes doradas, montañas, bosque y pasto
            const cielo = ctx.createLinearGradient(0, Y0, 0, Y0 + 260); cielo.addColorStop(0, '#8ec5f0'); cielo.addColorStop(1, '#d6ecfa');
            ctx.fillStyle = cielo; ctx.fillRect(0, Y0, W, 260);
            [[70, 34, 1], [250, 22, .8], [360, 60, .9]].forEach(([cx, cy, s], i) => {
                const x = (cx + m.t * 4 * (i + 1)) % (W + 120) - 60;
                [[0, 0, 16], [16, -6, 19], [34, 0, 15], [17, 6, 15]].forEach(([dx, dy, r]) => {
                    const g = ctx.createRadialGradient(x + dx * s, Y0 + cy + dy * s - 4, 2, x + dx * s, Y0 + cy + dy * s, r * s);
                    g.addColorStop(0, '#fffaf0'); g.addColorStop(1, '#f5deb3');
                    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x + dx * s, Y0 + cy + dy * s, r * s, 0, Math.PI * 2); ctx.fill();
                });
            });
            ctx.fillStyle = '#9cc7e8'; ctx.beginPath(); ctx.moveTo(0, Y0 + 205); ctx.lineTo(90, Y0 + 120); ctx.lineTo(170, Y0 + 195); ctx.lineTo(260, Y0 + 110); ctx.lineTo(380, Y0 + 205); ctx.fill();
            ctx.fillStyle = '#2b8a3e'; for (let x = 0; x < 400; x += 22) { ctx.beginPath(); ctx.moveTo(x, Y0 + SUELO - 4); ctx.lineTo(x + 11, Y0 + SUELO - 40 - (x % 3) * 6); ctx.lineTo(x + 22, Y0 + SUELO - 4); ctx.fill(); }
            ctx.fillStyle = '#40c057'; ctx.fillRect(0, Y0 + SUELO - 4, W, 260 - SUELO + 4);
            // La torre de la oveja con su cuerda
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(TORRE + 22, Y0 + 20, 9, 240); ctx.fillRect(TORRE + 42, Y0 + 20, 9, 240);
            ctx.fillStyle = '#5c3d2e'; for (let y = 30; y < 260; y += 26) ctx.fillRect(TORRE + 22, Y0 + y, 29, 4);
            ctx.strokeStyle = '#e9ecef'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(TORRE + 4, Y0 + 20); ctx.lineTo(TORRE + 4, Y0 + 260); ctx.stroke();
            if (!m.s) return;
            const oy = Y0 + m.ov.y;
            ctx.fillStyle = '#a0522d'; ctx.fillRect(TORRE - 24, oy + 34, 50, 7);    // plataforma
            const j = m.s.jalon;
            // La curva que va a hacer la flecha
            if (j && j.largo > 12) {
                const f = Math.min(560, j.largo * 4.2) / j.largo, b = boca(m);
                let x = b.x, y = Y0 + b.y, vx = j.dx * f, vy = j.dy * f;
                ctx.fillStyle = 'rgba(33,37,41,.55)';
                for (let i = 0; i < 22; i++) { vy += G * .05; x += vx * .05; y += vy * .05; if (i % 2 === 0) ctx.fillRect(x - 1.5, y - 1.5, 3, 3); }
            }
            oveja(ctx, TORRE, oy, j && j.largo > 4 ? j : null, m.t);
            // Canastas con lobos, globos que revientan y corderitos salvados
            m.s.lobos.forEach(l => canasta(ctx, l, l.x, Y0 + l.y, m.t));
            m.s.estallidos = m.s.estallidos.filter(b => m.t - b.t < .35);
            m.s.estallidos.forEach(b => {
                const d = (m.t - b.t) / .35; ctx.strokeStyle = Gamificacion.COLORES[b.k]; ctx.lineWidth = 2;
                for (let i = 0; i < 10; i++) { const a = i * Math.PI / 5; ctx.beginPath(); ctx.moveTo(b.x + Math.cos(a) * 10 * d, Y0 + b.y + Math.sin(a) * 10 * d); ctx.lineTo(b.x + Math.cos(a) * 26 * d, Y0 + b.y + Math.sin(a) * 26 * d); ctx.stroke(); }
            });
            m.s.lobos.forEach(l => { if (l.roto && l.y < SUELO - 30 * l.e) { ctx.fillStyle = '#495057'; ctx.font = 'bold 8px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('¡auuu!', l.x + 18, Y0 + l.y - 22); } });
            m.s.salvados.forEach(c => cordero(ctx, c.x, Y0 + c.y, true));
            // Flechas
            m.s.flechas.forEach(f => {
                const a = Math.atan2(f.vy, f.vx);
                ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(f.x - Math.cos(a) * 16, Y0 + f.y - Math.sin(a) * 16); ctx.lineTo(f.x, Y0 + f.y); ctx.stroke();
                ctx.save(); ctx.translate(f.x, Y0 + f.y); ctx.rotate(a);
                ctx.fillStyle = '#adb5bd'; ctx.beginPath(); ctx.moveTo(4, 0); ctx.lineTo(-2, -3); ctx.lineTo(-2, 3); ctx.fill();
                ctx.fillStyle = '#f8f9fa'; ctx.beginPath(); ctx.moveTo(-16, 0); ctx.lineTo(-12, -3); ctx.lineTo(-12, 3); ctx.fill(); ctx.restore();
            });
        },
    });
})();
