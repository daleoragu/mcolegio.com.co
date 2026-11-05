/* Búsqueda del tesoro: en la isla hay sitios marcados, uno por opción. El explorador camina
 * hasta el de la respuesta correcta y cava: encuentra un trozo del mapa. Si cava donde no es,
 * sale un cangrejo y pierde una vida. Con los trozos del mapa se abre el cofre al final. */
(function () {
    'use strict';
    const Y0 = 50, W = 480;
    // Sitios posibles para cavar (coordenadas dentro de la zona de juego, 0–260 de alto)
    const SITIOS = [[110, 70], [190, 50], [280, 60], [370, 85], [140, 140], [235, 125], [330, 150], [400, 185],
                    [95, 200], [185, 205], [280, 200]];
    const PALMAS = [[70, 95], [250, 90], [420, 130], [150, 175], [345, 215]];
    const MUELLE = {x: 40, y: 235};

    function explorador(ctx, x, y, o) {
        o = o || {};
        const paso = o.paso || 0;
        ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.ellipse(x, y + 10, 8, 3, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#5c3d2e'; ctx.fillRect(x - 5, y + 3 + (paso > 0 ? -1 : 0), 4, 7); ctx.fillRect(x + 1, y + 3 + (paso < 0 ? -1 : 0), 4, 7);   // botas
        ctx.fillStyle = '#e67700'; ctx.fillRect(x - 7, y - 8, 14, 12);               // camisa
        ctx.fillStyle = '#8b5a2b'; ctx.fillRect(o.dir < 0 ? x + 5 : x - 10, y - 7, 5, 9);   // morral
        ctx.fillStyle = '#f1c27d'; ctx.beginPath(); ctx.arc(x, y - 13, 6, 0, Math.PI * 2); ctx.fill();   // cara
        ctx.fillStyle = '#111'; ctx.fillRect(x + (o.dir < 0 ? -3 : 1), y - 14, 2, 2);
        ctx.fillStyle = '#c9a227'; ctx.fillRect(x - 10, y - 18, 20, 3); ctx.fillRect(x - 6, y - 23, 12, 6);   // sombrero
        if (o.cavando) {   // la pala sube y baja
            const a = Math.sin(o.cavando * 18) * .6;
            ctx.save(); ctx.translate(x + 8, y - 4); ctx.rotate(.6 + a);
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(-1, 0, 2, 14); ctx.fillStyle = '#adb5bd'; ctx.fillRect(-3, 13, 6, 6);
            ctx.restore();
        }
    }

    function marca(ctx, k, x, y, cavado) {
        // Una X en la arena y una banderita con la letra
        ctx.strokeStyle = cavado ? '#5c3d2e' : '#c92a2a'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(x - 6, y - 4); ctx.lineTo(x + 6, y + 4); ctx.moveTo(x + 6, y - 4); ctx.lineTo(x - 6, y + 4); ctx.stroke();
        if (cavado) { ctx.fillStyle = '#5c3d2e'; ctx.beginPath(); ctx.ellipse(x, y, 9, 5, 0, 0, Math.PI * 2); ctx.fill(); return; }
        ctx.fillStyle = '#495057'; ctx.fillRect(x + 7, y - 26, 2, 26);
        ctx.fillStyle = Gamificacion.COLORES[k]; ctx.beginPath(); ctx.moveTo(x + 9, y - 26); ctx.lineTo(x + 27, y - 20); ctx.lineTo(x + 9, y - 13); ctx.fill();
        ctx.fillStyle = '#111'; ctx.font = 'bold 8px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(Gamificacion.LETRAS[k], x + 15, y - 19);
    }

    function palma(ctx, x, y, t) {
        ctx.fillStyle = '#8b5a2b'; for (let i = 0; i < 6; i++) ctx.fillRect(x + Math.sin(i * .5) * 2 - 2, y - i * 5, 5, 5);
        ctx.fillStyle = '#2f9e44';
        for (let i = 0; i < 5; i++) {
            const a = i * 1.25 + Math.sin(t * 2 + x) * .08;
            ctx.beginPath(); ctx.ellipse(x + Math.cos(a) * 9, y - 30 + Math.sin(a) * 4, 11, 3, a, 0, Math.PI * 2); ctx.fill();
        }
        ctx.fillStyle = '#7a5442'; ctx.beginPath(); ctx.arc(x, y - 28, 3, 0, Math.PI * 2); ctx.fill();
    }

    Gamificacion.registrar('tesoro', {
        nombre: 'Búsqueda del tesoro',
        instrucciones: 'Lleve al explorador a la marca de la respuesta correcta (tóquela, presione su letra o camine con las flechas) y cave. Cada acierto es un trozo del mapa del cofre.',
        conReloj: true,
        maxOpciones: 8,
        controles: 'cruceta',
        fondo: '#1864ab',
        icono(ctx, k, tam) {
            ctx.save(); ctx.scale(tam / 40, tam / 40);
            ctx.fillStyle = '#ffe066'; ctx.beginPath(); ctx.ellipse(18, 30, 16, 7, 0, 0, Math.PI * 2); ctx.fill();
            marca(ctx, k, 12, 30, false); ctx.restore();
        },
        nuevaPregunta(m) {
            if (!m.ex) m.ex = {x: MUELLE.x, y: MUELLE.y, dir: 1};
            const sitios = SITIOS.slice().sort(() => Math.random() - .5)
                .filter(p => Math.hypot(p[0] - m.ex.x, p[1] - m.ex.y) > 40).slice(0, m.opciones.length);
            m.s = {marcas: sitios.map((p, k) => ({k, x: p[0], y: p[1]})), meta: null, cava: null, sale: null};
            m.ex.meta = null;
        },
        ir(m, mk) { if (!m.s.cava) m.ex.meta = mk; },
        alTocar(m, x, y) {
            const mk = m.s.marcas.find(mk => Math.hypot(mk.x - x, Y0 + mk.y - y) < 26 || Math.hypot(mk.x + 15 - x, Y0 + mk.y - 20 - y) < 14);
            if (mk) this.ir(m, mk);
        },
        alTecla(m, t, crudo) {
            const k = 'ABCDEFGH'.indexOf(String(crudo || '').toUpperCase());
            if (k >= 0 && k < m.s.marcas.length) this.ir(m, m.s.marcas[k]);   // las flechas caminan; las letras van a su marca
        },
        actualizar(m, dt) {
            const s = m.s, ex = m.ex;
            if (s.cava) {
                s.cava.t += dt;
                if (s.cava.t > .7) { const k = s.cava.k; s.cava = null; s.sale = {k, t: m.t, x: ex.x, y: ex.y}; m.responder(k); }
                return;
            }
            // Caminar: hacia la marca elegida, o con las flechas
            let vx = 0, vy = 0;
            if (ex.meta) {
                const dx = ex.meta.x - ex.x, dy = ex.meta.y + 2 - ex.y, d = Math.hypot(dx, dy);
                if (d > 3) { vx = dx / d; vy = dy / d; }
            } else {
                vx = (m.teclas.has('derecha') ? 1 : 0) - (m.teclas.has('izquierda') ? 1 : 0);
                vy = (m.teclas.has('abajo') ? 1 : 0) - (m.teclas.has('arriba') ? 1 : 0);
            }
            const vel = 120;
            ex.x = Math.max(30, Math.min(W - 30, ex.x + vx * vel * dt)); ex.y = Math.max(30, Math.min(245, ex.y + vy * vel * dt));
            if (vx) ex.dir = Math.sign(vx);
            ex.paso = (vx || vy) ? Math.sin(m.t * 14) : 0;
            // ¿Llegó a una marca? Cava.
            const mk = s.marcas.find(mk => Math.hypot(mk.x - ex.x, mk.y + 2 - ex.y) < 8);
            if (mk) { s.cava = {k: mk.k, t: 0}; ex.meta = null; mk.cavado = true; m.sonidos.toque(); }
        },
        actualizarEnPausa() {},
        dibujar(m, ctx) {
            // Mar con olas
            ctx.fillStyle = '#1c7ed6'; ctx.fillRect(0, Y0, W, 260);
            ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 1;
            for (let y = 10; y < 260; y += 26) for (let x = (y % 52 ? 0 : 20) + (m.t * 8 % 40); x < W; x += 40) {
                ctx.beginPath(); ctx.arc(x, Y0 + y, 5, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
            }
            // La isla: arena con borde mojado y pasto
            const isla = [[240, 135, 215, 115], [120, 170, 90, 70], [380, 160, 80, 75]];
            ctx.fillStyle = '#fcc419'; isla.forEach(([x, y, a, b]) => { ctx.beginPath(); ctx.ellipse(x, Y0 + y, a + 6, b + 6, 0, 0, Math.PI * 2); ctx.fill(); });
            ctx.fillStyle = '#ffe066'; isla.forEach(([x, y, a, b]) => { ctx.beginPath(); ctx.ellipse(x, Y0 + y, a, b, 0, 0, Math.PI * 2); ctx.fill(); });
            ctx.fillStyle = '#94d82d'; [[230, 120, 60, 26], [330, 105, 30, 14]].forEach(([x, y, a, b]) => { ctx.beginPath(); ctx.ellipse(x, Y0 + y, a, b, 0, 0, Math.PI * 2); ctx.fill(); });
            // Muelle
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(10, Y0 + MUELLE.y - 6, 50, 12);
            ctx.fillStyle = '#5c3d2e'; for (let x = 12; x < 60; x += 8) ctx.fillRect(x, Y0 + MUELLE.y - 6, 2, 12);
            PALMAS.forEach(([x, y]) => palma(ctx, x, Y0 + y, m.t));
            const s = m.s; if (!s) return;
            s.marcas.forEach(mk => marca(ctx, mk.k, mk.x, Y0 + mk.y, mk.cavado));
            explorador(ctx, m.ex.x, Y0 + m.ex.y - 10, {dir: m.ex.dir, paso: m.ex.paso, cavando: s.cava ? s.cava.t : 0});
            // Lo que sale del hueco: un trozo de mapa o un cangrejo
            if (s.sale && m.t - s.sale.t < 1.3) {
                const d = m.t - s.sale.t, y = Y0 + s.sale.y - 30 - d * 20;
                if (s.sale.bien) {
                    ctx.fillStyle = '#fff3bf'; ctx.fillRect(s.sale.x - 9, y - 7, 18, 14); ctx.strokeStyle = '#8b5a2b'; ctx.strokeRect(s.sale.x - 9, y - 7, 18, 14);
                    ctx.strokeStyle = '#c92a2a'; ctx.beginPath(); ctx.moveTo(s.sale.x - 4, y - 3); ctx.lineTo(s.sale.x + 4, y + 3); ctx.moveTo(s.sale.x + 4, y - 3); ctx.lineTo(s.sale.x - 4, y + 3); ctx.stroke();
                } else if (s.sale.bien === false) {
                    ctx.fillStyle = '#e8590c'; ctx.beginPath(); ctx.ellipse(s.sale.x, y, 9, 6, 0, 0, Math.PI * 2); ctx.fill();
                    ctx.fillRect(s.sale.x - 14, y - 6 + Math.sin(d * 20) * 2, 5, 4); ctx.fillRect(s.sale.x + 9, y - 6 - Math.sin(d * 20) * 2, 5, 4);
                    ctx.fillStyle = '#fff'; ctx.fillRect(s.sale.x - 4, y - 6, 2, 2); ctx.fillRect(s.sale.x + 2, y - 6, 2, 2);
                }
            }
            // El mapa del tesoro que se va armando (arriba a la derecha)
            const piezas = Math.round(9 * m.aciertos / Math.max(1, m.total));
            ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(W - 66, Y0 + 6, 60, 60);
            for (let i = 0; i < 9; i++) {
                const x = W - 63 + (i % 3) * 18, y = Y0 + 9 + Math.floor(i / 3) * 18;
                ctx.fillStyle = i < piezas ? '#fff3bf' : 'rgba(255,255,255,.12)'; ctx.fillRect(x, y, 17, 17);
            }
            if (piezas >= 5) { ctx.strokeStyle = '#c92a2a'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(W - 40, Y0 + 30); ctx.lineTo(W - 30, Y0 + 40); ctx.moveTo(W - 30, Y0 + 30); ctx.lineTo(W - 40, Y0 + 40); ctx.stroke(); }
            m.texto('MAPA', W - 36, Y0 + 70, {tam: 6, alinear: 'center'});
        },
        alResponder(m, bien) { if (m.s && m.s.sale) m.s.sale.bien = bien; },
        final(m, ctx) {
            const gana = m.aciertos / Math.max(1, m.total) >= .6;
            ctx.fillStyle = '#ffe066'; ctx.fillRect(0, 0, 480, 360);
            m.texto(gana ? '¡ENCONTRÓ EL TESORO!' : 'EL TESORO SIGUE ESCONDIDO', 240, 40, {tam: 13, color: gana ? '#2b8a3e' : '#c92a2a', alinear: 'center', sombra: false});
            // El cofre (abierto con monedas si ganó)
            const x = 190, y = 120;
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(x, y + 30, 100, 60); ctx.fillStyle = '#5c3d2e'; ctx.fillRect(x, y + 55, 100, 6);
            ctx.fillStyle = '#fab005'; ctx.fillRect(x + 44, y + 48, 12, 16);
            if (gana) {
                ctx.fillStyle = '#ffd43b'; for (let i = 0; i < 14; i++) { ctx.beginPath(); ctx.arc(x + 12 + (i % 7) * 13, y + 26 - Math.floor(i / 7) * 8 + Math.sin(m.t * 4 + i) * 2, 6, 0, Math.PI * 2); ctx.fill(); }
                ctx.fillStyle = '#8b5a2b'; ctx.fillRect(x, y - 10, 100, 14);
            } else { ctx.fillStyle = '#7a5442'; ctx.fillRect(x, y + 12, 100, 22); }
            m.texto(`TROZOS DEL MAPA: ${m.aciertos} DE ${m.total}`, 240, 240, {tam: 9, color: '#212529', alinear: 'center', sombra: false});
            m.texto(`PUNTAJE: ${m.puntaje}`, 240, 265, {tam: 9, color: '#e8590c', alinear: 'center', sombra: false});
            if (m.textoFinal) m.texto(m.textoFinal(), 240, 300, {tam: 8, color: '#495057', alinear: 'center', sombra: false});
        },
    });
})();
