/* Animaplano: resuelva la operación y toque el punto del resultado en la cuadrícula del 1 al 100
 * (o escríbalo y presione Enter). Cada punto se une con el anterior y al final aparece la figura.
 * «(nuevo trazo)» al comienzo de una pregunta levanta el lápiz. Si se equivoca, la línea queda
 * punteada en gris (la figura sigue) y el punto que tocó se pone rojo. */
(function () {
    'use strict';
    const Y0 = 50, SP = 24, GX = 132, GY = Y0 + 22, NUEVO = /^\s*\(nuevo trazo\)\s*/i;
    const xy = n => ({x: GX + ((n - 1) % 10) * SP, y: GY + Math.floor((n - 1) / 10) * SP});
    const correcto = p => parseInt((p.opciones.find(o => o.correcta) || {}).texto, 10);
    const limpio = t => String(t || '').replace(NUEVO, '').replace(/\s*=\s*$/, '');

    function cerca(x, y) {
        const c = Math.round((x - GX) / SP), f = Math.round((y - GY) / SP);
        if (c < 0 || c > 9 || f < 0 || f > 9) return null;
        const n = f * 10 + c + 1, p = xy(n);
        return Math.hypot(p.x - x, p.y - y) < 12 ? n : null;
    }

    function pintar(m, ctx, escala, x0, y0, finalizado) {
        const a = m.ap, P = n => ({x: x0 + (xy(n).x - GX) * escala, y: y0 + (xy(n).y - GY) * escala});
        // Puntos y números de guía (fila de arriba, columna izquierda, 50 y 100), como en la guía
        for (let n = 1; n <= 100; n++) {
            const p = P(n);
            ctx.fillStyle = a.puntos[n] === 'bien' ? '#2f9e44' : a.puntos[n] === 'mal' ? '#e03131' : '#495057';
            ctx.beginPath(); ctx.arc(p.x, p.y, (a.puntos[n] ? 3.6 : 2.6) * escala, 0, Math.PI * 2); ctx.fill();
            if (!finalizado && (n <= 10 || n % 10 === 1 || n === 50 || n === 100)) {
                const arriba = n <= 10, izq = n % 10 === 1 && n > 1;
                m.texto(String(n), p.x + (izq ? -14 : n === 50 || n === 100 ? 12 : 0), p.y + (arriba ? -13 : -3), {tam: 6, alinear: 'center', color: '#212529', sombra: false});
            }
        }
        a.lineas.forEach(l => {
            const p = P(l.a), q = P(l.b);
            ctx.strokeStyle = finalizado ? '#1971c2' : l.bien ? '#1971c2' : '#adb5bd'; ctx.lineWidth = (finalizado ? 3 : 2.5) * Math.min(1.4, escala);
            ctx.setLineDash(l.bien || finalizado ? [] : [4, 4]);
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); ctx.setLineDash([]);
        });
    }

    Gamificacion.registrar('animaplano', {
        nombre: 'Animaplano',
        instrucciones: 'Resuelva la operación y toque el punto del resultado (o escriba el número y presione Enter). Los puntos se van uniendo: ¡descubra la figura!',
        sinVidas: true,
        maxOpciones: 8,
        fondo: '#fffdf5',
        icono(ctx, k, tam) { Gamificacion.icono('', ctx, k, tam); },
        textoArriba(m) { const p = m.pregunta; return p ? `${m.indice + 1}) ${limpio(p.texto)} = ?` : ''; },
        abajo(m, ctx) {
            const s = m.s || {}, p = m.pregunta;
            const nuevo = p && NUEVO.test(p.texto) && m.indice > 0;
            m.texto(s.tecleado ? `ESCRIBIÓ: ${s.tecleado}  (ENTER)` : 'TOQUE EL PUNTO DEL RESULTADO O ESCRIBA EL NÚMERO', 10, m.ABAJO + 10, {tam: 7, color: '#ffd43b'});
            m.texto(nuevo ? '✎ TRAZO NUEVO: ESTE PUNTO NO SE UNE CON EL ANTERIOR' : `PUNTOS UNIDOS: ${m.aciertos} DE ${m.total}`, 10, m.ABAJO + 28, {tam: 6, color: '#ced4da'});
        },
        // La barra lateral es la lista de operaciones, como en la guía
        leyenda(m) {
            const a = m.ap; if (!a) return null;
            const filas = a.hechas.slice(-10).map(h => ({letra: h.bien ? '✓' : '✗', color: h.bien ? '#69db7c' : '#ff6b6b', texto: `${h.num}) ${h.op} = ${h.res}`}));
            const p = m.pregunta;
            if (p) filas.push({letra: '?', color: '#ffd43b', texto: `${m.indice + 1}) ${limpio(p.texto)} = ?`});
            return {titulo: 'Operaciones', filas};
        },
        nuevaPregunta(m) {
            if (!m.ap) m.ap = {puntos: {}, lineas: [], ultimo: null, hechas: []};
            m.s = {tecleado: '', rojo: null};
        },
        elegir(m, n) {
            const p = m.pregunta, a = m.ap, ok = correcto(p), bien = n === ok;
            let k = p.opciones.findIndex(o => parseInt(o.texto, 10) === n);
            if (k < 0 || (!bien && p.opciones[k].correcta)) k = p.opciones.findIndex(o => !o.correcta);
            if (bien) k = p.opciones.findIndex(o => o.correcta);
            // La línea siempre va al punto correcto (así la figura sigue); punteada si se equivocó
            if (a.ultimo && !NUEVO.test(p.texto) && ok >= 1 && ok <= 100) a.lineas.push({a: a.ultimo, b: ok, bien});
            if (ok >= 1 && ok <= 100) { a.ultimo = ok; a.puntos[ok] = bien ? 'bien' : (a.puntos[ok] || 'falta'); }
            if (!bien && n >= 1 && n <= 100 && n !== ok) { a.puntos[n] = a.puntos[n] || 'mal'; m.s.rojo = {n, t: m.t}; }
            a.hechas.push({num: m.indice + 1, op: limpio(p.texto), res: ok, bien});
            m.responder(k);
            if (!bien) setTimeout(() => m.aviso(`ERA EL ${ok}`, '#ff6b6b', 1.2), 0);
        },
        alTocar(m, x, y) { const n = cerca(x, y); if (n) this.elegir(m, n); },
        alTecla(m, t, crudo) {
            const s = m.s;
            if (/^[0-9]$/.test(String(crudo)) && s.tecleado.length < 3) s.tecleado += crudo;
            else if (crudo === 'Backspace') s.tecleado = s.tecleado.slice(0, -1);
            else if (t === 'aceptar' && s.tecleado) { const n = parseInt(s.tecleado, 10); s.tecleado = ''; this.elegir(m, n); }
        },
        actualizar() {},
        dibujar(m, ctx) {
            ctx.fillStyle = '#fffdf5'; ctx.fillRect(0, Y0, 480, 260);
            ctx.fillStyle = '#fff'; ctx.fillRect(GX - 26, GY - 20, SP * 9 + 52, SP * 9 + 34);
            ctx.strokeStyle = '#dee2e6'; ctx.lineWidth = 1; ctx.strokeRect(GX - 26, GY - 20, SP * 9 + 52, SP * 9 + 34);
            if (!m.ap) return;
            pintar(m, ctx, 1, GX, GY, false);
            // El número del punto bajo el dedo o el mouse (ayuda a contar)
            if (m.puntero) {
                const n = cerca(m.puntero.x, m.puntero.y);
                if (n) { const p = xy(n); ctx.strokeStyle = '#fab005'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, Math.PI * 2); ctx.stroke(); }
            }
            const r = m.s && m.s.rojo;
            if (r && m.t - r.t < 1) { const p = xy(r.n); ctx.strokeStyle = '#e03131'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(p.x, p.y, 7 + (m.t - r.t) * 10, 0, Math.PI * 2); ctx.stroke(); }
            if (m.ap.ultimo) { const p = xy(m.ap.ultimo); ctx.fillStyle = '#1971c2'; ctx.beginPath(); ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2); ctx.fill(); }
        },
        final(m, ctx) {
            ctx.fillStyle = '#fffdf5'; ctx.fillRect(0, 0, 480, 360);
            m.texto('¡DESCUBRIÓ LA FIGURA!', 240, 14, {tam: 13, color: '#1971c2', alinear: 'center', sombra: false});
            if (m.ap) pintar(m, ctx, 1.05, 240 - SP * 4.5 * 1.05, 52, true);
            m.texto(`PUNTOS BIEN UNIDOS: ${m.aciertos} DE ${m.total}`, 240, 300, {tam: 8, color: '#212529', alinear: 'center', sombra: false});
            if (m.textoFinal) m.texto(m.textoFinal(), 240, 322, {tam: 8, color: '#495057', alinear: 'center', sombra: false});
        },
    });
})();
