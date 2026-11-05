/* Une con líneas: a la izquierda las preguntas (1–5), a la derecha sus respuestas revueltas (A–E).
 * Se toca una pregunta y luego su respuesta: queda la línea verde si van juntas, roja si no.
 * Usa solo la respuesta correcta de cada pregunta. Al unir todas, sale otro tablero. */
(function () {
    'use strict';
    const Y0 = 50, IZQ = {x: 8, w: 206}, DER = {x: 266, w: 206}, POR_TABLERO = 5;

    function tablero(m) {
        const n = Math.min(POR_TABLERO, m.total - m.indice), alto = 254 / n;
        const izq = [], der = [];
        for (let j = 0; j < n; j++) {
            const q = m.preguntas[m.indice + j], ok = q.opciones.find(o => o.correcta);
            izq.push({q, n: j, y: Y0 + 4 + j * alto, h: alto - 6, hecho: false});
            der.push({texto: ok ? ok.texto : '', y: 0, h: alto - 6, usado: false});
        }
        der.sort(() => Math.random() - .5).forEach((d, j) => { d.y = Y0 + 4 + j * alto; d.n = j; });
        return {izq, der, sel: null, lineas: []};
    }

    function caja(m, ctx, x, w, item, texto, etiqueta, color, o) {
        ctx.fillStyle = o.sel ? '#fff3bf' : o.apagada ? '#343a40' : '#f8f9fa';
        ctx.beginPath(); ctx.roundRect(x, item.y, w, item.h, 6); ctx.fill();
        ctx.strokeStyle = o.sel ? '#fab005' : color; ctx.lineWidth = o.sel ? 3 : 2; ctx.stroke();
        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x + (o.derecha ? w - 12 : 12), item.y + item.h / 2, 9, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(etiqueta, x + (o.derecha ? w - 12 : 12), item.y + item.h / 2 + 1);
        ctx.font = `6px ${m.FUENTE}`;
        const cabe = Math.max(1, Math.floor((item.h - 6) / 9)), lineas = m.partir(texto, w - 34);
        const ver = lineas.slice(0, cabe);
        if (lineas.length > cabe) ver[cabe - 1] = ver[cabe - 1].slice(0, -2) + '…';
        const y0 = item.y + item.h / 2 - ver.length * 4.5;
        ver.forEach((l, i) => m.texto(l, x + (o.derecha ? 6 : 26), y0 + i * 9, {tam: 6, color: o.apagada ? '#adb5bd' : '#212529', sombra: false}));
    }

    const COLOR_N = n => Gamificacion.COLORES[(n + 4) % 8];

    Gamificacion.registrar('unir', {
        nombre: 'Une con líneas',
        instrucciones: 'Toque una pregunta (o su número) y luego su respuesta (o su letra). Si van juntas, la línea queda verde. Al terminar el tablero sale otro.',
        sinVidas: true,
        maxOpciones: 8,
        fondo: '#1b1f3a',
        textoArriba(m) {
            const s = m.s;
            if (s && s.sel && s.sel.lado === 'izq') return s.sel.item.q.texto;
            return 'Une cada pregunta con su respuesta.';
        },
        abajo(m, ctx) {
            const s = m.s;
            const t = s && s.sel ? (s.sel.lado === 'der' ? 'RESPUESTA: ' + s.sel.item.texto : 'Ahora toque la respuesta de la derecha.') : 'Toque una pregunta de la izquierda (1–5) y luego su respuesta (A–E).';
            ctx.font = `7px ${m.FUENTE}`;
            m.partir(t, 460).slice(0, 4).forEach((l, i) => m.texto(l, 10, m.ABAJO + 8 + i * 10, {tam: 7, color: '#e9ecef'}));
        },
        // La barra lateral muestra las preguntas completas del tablero
        leyenda(m) {
            const s = m.s; if (!s) return null;
            return {titulo: 'Une cada pregunta con su respuesta', filas: s.izq.map(i => ({letra: String(i.n + 1), color: COLOR_N(i.n), texto: i.q.texto, hecho: i.hecho}))};
        },
        icono(ctx, k, tam) { Gamificacion.icono('', ctx, k, tam); },
        nuevaPregunta(m) {
            if (!m.s || m.s.izq.every(i => i.hecho)) m.s = tablero(m);
            else m.s.sel = null;
        },
        elegir(m, lado, item) {
            const s = m.s;
            if (lado === 'izq' && item.hecho) return;
            if (lado === 'der' && item.usado) return;
            if (!s.sel || s.sel.lado === lado) { s.sel = {lado, item}; m.sonidos.toque(); return; }
            const izq = lado === 'izq' ? item : s.sel.item, der = lado === 'der' ? item : s.sel.item;
            s.sel = null;
            const q = izq.q, j = m.preguntas.indexOf(q);
            // La pregunta elegida pasa a ser «la de ahora» para que el motor la califique
            [m.preguntas[m.indice], m.preguntas[j]] = [m.preguntas[j], m.preguntas[m.indice]];
            let k = q.opciones.findIndex(o => o.texto === der.texto && o.correcta);
            const bien = k >= 0;
            if (!bien) k = q.opciones.findIndex(o => !o.correcta);
            izq.hecho = true;
            if (bien) der.usado = true;
            s.lineas.push({izq, der, bien, t: m.t});
            m.responder(k);
            if (!bien) m.aviso('¡NO VAN JUNTAS!', '#ff6b6b', 1.2);
        },
        alTocar(m, x, y) {
            const s = m.s;
            const en = (lista, caja) => lista.find(i => x >= caja.x && x <= caja.x + caja.w && y >= i.y && y <= i.y + i.h);
            const a = en(s.izq, IZQ); if (a) return this.elegir(m, 'izq', a);
            const b = en(s.der, DER); if (b) return this.elegir(m, 'der', b);
        },
        alTecla(m, t, crudo) {
            const c = String(crudo || '').toUpperCase(), s = m.s;
            const n = '12345'.indexOf(c), l = 'ABCDE'.indexOf(c);
            if (n >= 0 && s.izq[n]) this.elegir(m, 'izq', s.izq[n]);
            else if (l >= 0 && s.der[l]) this.elegir(m, 'der', s.der[l]);
        },
        actualizar() {},
        dibujar(m, ctx) {
            const s = m.s; if (!s) return;
            ctx.fillStyle = '#1b1f3a'; ctx.fillRect(0, Y0, 480, 260);
            // Las líneas ya trazadas (la roja se borra sola)
            s.lineas = s.lineas.filter(l => l.bien || m.t - l.t < 1.2);
            s.lineas.forEach(l => {
                ctx.strokeStyle = l.bien ? '#69db7c' : '#ff6b6b'; ctx.lineWidth = 4; ctx.lineCap = 'round';
                ctx.beginPath(); ctx.moveTo(IZQ.x + IZQ.w, l.izq.y + l.izq.h / 2); ctx.lineTo(DER.x, l.der.y + l.der.h / 2); ctx.stroke();
            });
            // La línea que se está trazando sigue al puntero
            if (s.sel && m.puntero) {
                const it = s.sel.item, x0 = s.sel.lado === 'izq' ? IZQ.x + IZQ.w : DER.x;
                ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 3; ctx.setLineDash([6, 5]);
                ctx.beginPath(); ctx.moveTo(x0, it.y + it.h / 2); ctx.lineTo(m.puntero.x, m.puntero.y); ctx.stroke(); ctx.setLineDash([]);
            }
            s.izq.forEach(i => caja(m, ctx, IZQ.x, IZQ.w, i, i.q.texto, String(i.n + 1), COLOR_N(i.n), {sel: s.sel && s.sel.item === i, apagada: i.hecho}));
            s.der.forEach(d => caja(m, ctx, DER.x, DER.w, d, d.texto, Gamificacion.LETRAS[d.n], '#adb5bd', {sel: s.sel && s.sel.item === d, apagada: d.usado, derecha: true}));
            // Puntos para enganchar la línea
            ctx.fillStyle = '#ffd43b';
            s.izq.forEach(i => { if (!i.hecho) { ctx.beginPath(); ctx.arc(IZQ.x + IZQ.w, i.y + i.h / 2, 4, 0, Math.PI * 2); ctx.fill(); } });
            s.der.forEach(d => { if (!d.usado) { ctx.beginPath(); ctx.arc(DER.x, d.y + d.h / 2, 4, 0, Math.PI * 2); ctx.fill(); } });
        },
    });
})();
