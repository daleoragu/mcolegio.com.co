/* Ovejas y lobos: los lobos bajan colgados de globos, cada globo con una opción. La oveja arquera,
 * en su torre, jala el arco (mantenga presionado, arrastre hacia atrás y suelte, como una catapulta)
 * y revienta el globo de la respuesta correcta. Algunos lobos llevan un corderito: si revienta el
 * correcto, el corderito se salva. Si los lobos llegan al suelo, se acabó el tiempo.
 * También: tocar sin arrastrar dispara hacia ese punto; A–F disparan al globo de esa letra; ↑ ↓ mueven la oveja. */
(function () {
    'use strict';
    const Y0 = 50, W = 480, SUELO = 246, G = 240, TORRE = 430;

    function oveja(ctx, x, y, jalon, t) {
        // Lana: nubecitas blancas
        ctx.fillStyle = '#f8f9fa';
        [[0, 0, 11], [-9, -3, 8], [9, -3, 8], [-6, 6, 8], [7, 6, 8], [0, -8, 8]].forEach(([dx, dy, r]) => { ctx.beginPath(); ctx.arc(x + dx, y + dy, r, 0, Math.PI * 2); ctx.fill(); });
        ctx.strokeStyle = '#ced4da'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, 11, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = '#212529'; ctx.fillRect(x - 6, y + 12, 3, 8); ctx.fillRect(x + 4, y + 12, 3, 8);           // patas
        // Cabeza negra mirando a la izquierda, con orejas y ojo
        ctx.beginPath(); ctx.ellipse(x - 15, y - 6, 7, 6, -.2, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.ellipse(x - 11, y - 13, 4, 2, -.6, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#fff'; ctx.fillRect(x - 19, y - 8, 3, 3); ctx.fillStyle = '#111'; ctx.fillRect(x - 19, y - 7, 2, 2);
        ctx.fillStyle = '#f8f9fa'; ctx.beginPath(); ctx.arc(x - 12, y - 14, 4, 0, Math.PI * 2); ctx.fill();   // copete
        // El arco (adelante) y la cuerda, que se estira con el jalón
        const bx = x - 26, by = y - 2, ang = jalon ? Math.atan2(jalon.dy, jalon.dx) : Math.PI, tira = jalon ? Math.min(14, jalon.largo / 8) : 0;
        ctx.save(); ctx.translate(bx, by); ctx.rotate(ang + Math.PI);
        ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 0, 14, -Math.PI / 2.2, Math.PI / 2.2); ctx.stroke();
        ctx.strokeStyle = '#e9ecef'; ctx.lineWidth = 1;
        const ex = 14 * Math.cos(Math.PI / 2.2), ey = 14 * Math.sin(Math.PI / 2.2);
        ctx.beginPath(); ctx.moveTo(ex, -ey); ctx.lineTo(-tira, 0); ctx.lineTo(ex, ey); ctx.stroke();
        if (jalon) { ctx.strokeStyle = '#5c3d2e'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-tira, 0); ctx.lineTo(20 - tira, 0); ctx.stroke(); ctx.fillStyle = '#adb5bd'; ctx.fillRect(18 - tira, -2, 4, 4); }
        ctx.restore();
    }

    function lobo(ctx, x, y, o) {
        o = o || {};
        const gris = o.cae ? '#868e96' : '#6c757d';
        // brazos arriba agarrando la cuerda del globo
        ctx.fillStyle = gris; ctx.fillRect(x - 7, y - 14, 3, 10); ctx.fillRect(x + 4, y - 14, 3, 10);
        ctx.beginPath(); ctx.ellipse(x, y + 4, 9, 12, 0, 0, Math.PI * 2); ctx.fill();                     // cuerpo
        ctx.fillStyle = '#ced4da'; ctx.beginPath(); ctx.ellipse(x, y + 7, 5, 7, 0, 0, Math.PI * 2); ctx.fill();   // pecho
        ctx.fillStyle = gris; ctx.fillRect(x - 6, y + 14, 4, 7); ctx.fillRect(x + 2, y + 14, 4, 7);         // patas
        ctx.beginPath(); ctx.moveTo(x + 8, y + 8); ctx.lineTo(x + 18, y + 2); ctx.lineTo(x + 10, y + 13); ctx.fill();   // cola
        // cabeza con orejas puntudas y hocico
        ctx.beginPath(); ctx.arc(x, y - 12, 7, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.moveTo(x - 7, y - 15); ctx.lineTo(x - 5, y - 24); ctx.lineTo(x - 1, y - 17); ctx.fill();
        ctx.beginPath(); ctx.moveTo(x + 7, y - 15); ctx.lineTo(x + 5, y - 24); ctx.lineTo(x + 1, y - 17); ctx.fill();
        ctx.fillStyle = '#adb5bd'; ctx.beginPath(); ctx.ellipse(x + 6, y - 10, 5, 3, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.fillRect(x + 9, y - 12, 2, 2);
        ctx.fillStyle = o.cae ? '#fff' : '#ffd43b'; ctx.fillRect(x - 3, y - 15, 3, 3); ctx.fillRect(x + 2, y - 15, 3, 3);
        if (o.cordero) cordero(ctx, x - 12, y + 16, 0);
    }

    function cordero(ctx, x, y, paraguas) {
        if (paraguas) {   // se salva bajando con una hojita de paracaídas
            ctx.fillStyle = '#69db7c'; ctx.beginPath(); ctx.arc(x, y - 16, 11, Math.PI, 0); ctx.fill();
            ctx.strokeStyle = '#495057'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x - 10, y - 16); ctx.lineTo(x, y - 4); ctx.lineTo(x + 10, y - 16); ctx.stroke();
        }
        ctx.fillStyle = '#fff';
        [[0, 0, 6], [-5, 1, 4], [5, 1, 4], [0, -4, 4]].forEach(([dx, dy, r]) => { ctx.beginPath(); ctx.arc(x + dx, y + dy, r, 0, Math.PI * 2); ctx.fill(); });
        ctx.fillStyle = '#343a40'; ctx.beginPath(); ctx.arc(x - 7, y - 2, 3.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillRect(x - 3, y + 5, 2, 4); ctx.fillRect(x + 2, y + 5, 2, 4);
    }

    function globo(ctx, k, x, y) {
        ctx.strokeStyle = '#495057'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, y + 13); ctx.lineTo(x, y + 26); ctx.stroke();
        ctx.fillStyle = Gamificacion.COLORES[k]; ctx.beginPath(); ctx.ellipse(x, y, 12, 14, 0, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.moveTo(x - 3, y + 15); ctx.lineTo(x + 3, y + 15); ctx.lineTo(x, y + 12); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.ellipse(x - 4, y - 5, 3, 5, -.4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(Gamificacion.LETRAS[k], x, y + 1);
    }

    function boca(m) { return {x: TORRE - 26, y: m.ov.y - 2}; }
    function disparar(m, vx, vy, recto) {
        const b = boca(m);
        m.s.flechas.push({x: b.x, y: b.y, vx, vy, recto}); m.sonidos.toque();
    }

    Gamificacion.registrar('ovejas', {
        nombre: 'Ovejas y lobos',
        instrucciones: 'Mantenga presionado, arrastre hacia atrás y suelte para disparar con el arco (como una catapulta). Reviente el globo del lobo con la respuesta correcta antes de que lleguen al suelo. ↑ ↓ mueven la oveja; A–F disparan directo.',
        maxOpciones: 6,
        fondo: '#a5d8ff',
        icono(ctx, k, tam) { ctx.save(); ctx.scale(tam / 40, tam / 40); globo(ctx, k, 20, 16); ctx.restore(); },
        nuevaPregunta(m) {
            if (!m.ov) m.ov = {y: 150};
            const n = m.opciones.length, vel = 12 + m.nivel * 3, base = 46 + Math.random() * 8;   // empiezan arriba, a la vista
            const xs = Array.from({length: n}, (_, i) => 40 + i * (300 / Math.max(1, n - 1 || 1)) + (Math.random() - .5) * 16).sort(() => Math.random() - .5);
            m.s = {lobos: m.opciones.map((_, k) => ({k, x: n === 1 ? 180 : xs[k], y: base - Math.random() * 18, vel, fase: Math.random() * 6, cordero: Math.random() < .35, roto: false, vy: 0})),
                   flechas: [], jalon: null, salvados: []};
        },
        alTocar(m, x, y) { m.s.jalon = {x0: x, y0: y, dx: 0, dy: 0, largo: 0}; },
        alArrastrar(m, x, y) {
            const j = m.s.jalon; if (!j) return;
            j.dx = j.x0 - x; j.dy = j.y0 - y; j.largo = Math.hypot(j.dx, j.dy);
        },
        alSoltar(m, x, y) {
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
            if (l) { const b = boca(m), dx = l.x - b.x, dy = l.y - 30 - b.y, d = Math.hypot(dx, dy) || 1; disparar(m, dx / d * 560, dy / d * 560, true); }
        },
        actualizar(m, dt) {
            const s = m.s;
            if (m.teclas.has('arriba')) m.ov.y = Math.max(70, m.ov.y - 110 * dt);
            if (m.teclas.has('abajo')) m.ov.y = Math.min(225, m.ov.y + 110 * dt);
            this.mover(m, dt);
            // ¿Una flecha reventó un globo?
            for (const f of s.flechas) {
                const l = s.lobos.find(l => !l.roto && Math.hypot(l.x - f.x, l.y - 30 - f.y) < 14);
                if (l) {
                    l.roto = true; l.vy = 30; f.fuera = true;
                    const bien = m.opciones[l.k] && m.opciones[l.k].correcta;
                    if (bien && l.cordero) { s.salvados.push({x: l.x - 12, y: l.y + 16}); l.cordero = false; m.puntaje += 50; }
                    m.responder(l.k);
                    if (bien) setTimeout(() => m.aviso(s.salvados.length ? '¡SALVÓ AL CORDERITO!' : '¡LOBO AL SUELO!', '#69db7c', .9), 0);
                    return;
                }
            }
            // Los lobos llegaron al suelo: se acabó el tiempo
            if (s.lobos.some(l => !l.roto && l.y + 22 >= SUELO)) { m.responder(null); setTimeout(() => m.aviso('¡LOS LOBOS LLEGARON!', '#ff6b6b', 1.3), 0); }
        },
        mover(m, dt) {
            const s = m.s;
            s.lobos.forEach(l => {
                if (l.roto) { l.vy += 500 * dt; l.y = Math.min(SUELO - 20, l.y + l.vy * dt); return; }
                l.y += l.vel * dt; l.fase += dt * 2; l.x += Math.sin(l.fase) * 8 * dt;
            });
            s.flechas.forEach(f => { if (!f.recto) f.vy += G * dt; f.x += f.vx * dt; f.y += f.vy * dt; });
            s.flechas = s.flechas.filter(f => !f.fuera && f.x > -20 && f.x < W + 20 && f.y < 280 && f.y > -120);
            s.salvados.forEach(c => { c.y = Math.min(SUELO - 8, c.y + 30 * dt); c.x += 10 * dt; });
        },
        actualizarEnPausa(m, dt) { if (m.s) this.mover(m, dt); },
        dibujar(m, ctx) {
            // Cielo, montañas, bosque y pasto
            ctx.fillStyle = '#a5d8ff'; ctx.fillRect(0, Y0, W, 260);
            ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(80, Y0 + 30, 12, 0, Math.PI * 2); ctx.arc(96, Y0 + 26, 15, 0, Math.PI * 2); ctx.arc(112, Y0 + 32, 11, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#74c0fc'; ctx.beginPath(); ctx.moveTo(0, Y0 + 200); ctx.lineTo(90, Y0 + 110); ctx.lineTo(170, Y0 + 190); ctx.lineTo(260, Y0 + 100); ctx.lineTo(380, Y0 + 200); ctx.fill();
            ctx.fillStyle = '#2b8a3e'; for (let x = 0; x < 400; x += 22) { ctx.beginPath(); ctx.moveTo(x, Y0 + SUELO - 4); ctx.lineTo(x + 11, Y0 + SUELO - 40 - (x % 3) * 6); ctx.lineTo(x + 22, Y0 + SUELO - 4); ctx.fill(); }
            ctx.fillStyle = '#40c057'; ctx.fillRect(0, Y0 + SUELO - 4, W, 260 - SUELO + 4);
            // La torre de la oveja con su cuerda
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(TORRE + 20, Y0 + 20, 10, 240); ctx.fillRect(TORRE + 40, Y0 + 20, 10, 240);
            ctx.fillStyle = '#5c3d2e'; for (let y = 30; y < 260; y += 26) ctx.fillRect(TORRE + 20, Y0 + y, 30, 4);
            ctx.strokeStyle = '#e9ecef'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(TORRE + 2, Y0 + 20); ctx.lineTo(TORRE + 2, Y0 + 260); ctx.stroke();
            if (!m.s) return;
            const oy = Y0 + m.ov.y;
            ctx.fillStyle = '#a0522d'; ctx.fillRect(TORRE - 16, oy + 18, 36, 6);    // canasta
            ctx.fillStyle = '#c58940'; ctx.fillRect(TORRE - 14, oy + 10, 32, 9);
            const j = m.s.jalon;
            // La curva que va a hacer la flecha
            if (j && j.largo > 12) {
                const f = Math.min(560, j.largo * 4.2) / j.largo, b = boca(m);
                let x = b.x, y = Y0 + b.y, vx = j.dx * f, vy = j.dy * f;
                ctx.fillStyle = 'rgba(33,37,41,.55)';
                for (let i = 0; i < 22; i++) { vy += G * .05; x += vx * .05; y += vy * .05; if (i % 2 === 0) ctx.fillRect(x - 1.5, y - 1.5, 3, 3); }
            }
            oveja(ctx, TORRE, oy, j && j.largo > 4 ? j : null, m.t);
            // Lobos, globos y corderitos
            m.s.lobos.forEach(l => {
                if (!l.roto) globo(ctx, l.k, l.x, Y0 + l.y - 30);
                lobo(ctx, l.x, Y0 + l.y, {cae: l.roto, cordero: l.cordero});
                if (l.roto && l.y < SUELO - 22) { ctx.fillStyle = '#495057'; ctx.font = '8px sans-serif'; ctx.fillText('¡auuu!', l.x + 14, Y0 + l.y - 20); }
            });
            m.s.salvados.forEach(c => cordero(ctx, c.x, Y0 + c.y, true));
            // Flechas
            ctx.strokeStyle = '#5c3d2e'; ctx.lineWidth = 2;
            m.s.flechas.forEach(f => {
                const a = Math.atan2(f.vy, f.vx);
                ctx.beginPath(); ctx.moveTo(f.x - Math.cos(a) * 14, Y0 + f.y - Math.sin(a) * 14); ctx.lineTo(f.x, Y0 + f.y); ctx.stroke();
                ctx.fillStyle = '#adb5bd'; ctx.beginPath(); ctx.arc(f.x, Y0 + f.y, 2.5, 0, Math.PI * 2); ctx.fill();
            });
        },
    });
})();
