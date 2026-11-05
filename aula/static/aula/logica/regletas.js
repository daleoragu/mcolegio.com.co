/* Regletas (Cuisenaire) en la balanza: cada color es un número del 1 al 10.
 * Igualar: arme el lado derecho con las regletas que se piden para que la balanza quede derecha.
 * Incógnita: escoja la regleta x para que se cumpla la ecuación (a·x + b = c). */
(function () {
    'use strict';
    const COL = ['', '#f8f9fa', '#e03131', '#8ce99a', '#e64980', '#fcc419', '#2b8a3e', '#212529', '#8b5a2b', '#1c7ed6', '#fd7e14'];
    const NOM = ['', 'blanca', 'roja', 'verde clara', 'rosada', 'amarilla', 'verde oscura', 'negra', 'café', 'azul', 'naranja'];
    function reto(i) {
        // al azar pero igual para el mismo nivel
        let s = i * 7919 + 13; const az = (a, b) => { s = (s * 16807) % 2147483647; return a + s % (b - a + 1); };
        if (i < 10) { const a = az(3, 9), b = az(2, 9); return {tipo: 'igualar', izq: [a, b], k: 2, distintas: false}; }
        if (i < 20) { const a = az(4, 10), b = az(3, 10), c = az(2, 6); return {tipo: 'igualar', izq: [a, b, c], k: 3, distintas: true}; }
        const a = az(2, 4), x = az(2, Math.floor(30 / a) > 9 ? 9 : Math.floor(30 / a)), b = az(1, 9);
        return {tipo: 'incognita', a, b, c: a * x + b, x};
    }
    Logica.registrar('regletas', {
        nombre: 'Regletas en la balanza',
        instrucciones: 'Cada color de regleta vale un número (blanca 1, roja 2… naranja 10). Toque una regleta de la caja para ponerla en el platillo derecho y tóquela en el platillo para quitarla. Deje la balanza derecha cumpliendo lo que pide el reto.',
        total: () => 30,
        titulo: (d, i) => { const r = reto(i); return r.tipo === 'igualar' ? `Iguale con exactamente ${r.k} regletas${r.distintas ? ' de colores distintos' : ''}` : `¿Qué regleta es x? ${r.a}·x + ${r.b} = ${r.c}`; },
        iniciar(zona, datos, i, api) {
            const r = reto(i), W = 760, H = 420, L = api.lienzo(W, H), ctx = L.ctx, U = 18, UC = 11.5;
            let der = [], x = null;
            const izqSuma = () => r.tipo === 'igualar' ? r.izq.reduce((s, v) => s + v, 0) : (x ? r.a * x + r.b : r.b);
            const derSuma = () => r.tipo === 'igualar' ? der.reduce((s, v) => s + v, 0) : r.c;
            function regleta(v, x0, y0, alto, u) { u = u || U; ctx.fillStyle = COL[v]; ctx.fillRect(x0, y0, v * u - 2, alto); ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 1; ctx.strokeRect(x0, y0, v * u - 2, alto); for (let k = 1; k < v; k++) { ctx.strokeStyle = 'rgba(0,0,0,.12)'; ctx.beginPath(); ctx.moveTo(x0 + k * u - 1, y0); ctx.lineTo(x0 + k * u - 1, y0 + alto); ctx.stroke(); } }
            function pila(lista, cx, base, etiqueta) {
                lista.forEach((v, k) => {
                    const ancho = v * U, x0 = cx - ancho / 2, y0 = base - (k + 1) * 22;
                    if (v === 'x') { ctx.fillStyle = x ? COL[x] : '#dee2e6'; ctx.fillRect(cx - (x || 3) * U / 2, y0, (x || 3) * U - 2, 20); ctx.strokeStyle = '#495057'; ctx.setLineDash(x ? [] : [4, 3]); ctx.strokeRect(cx - (x || 3) * U / 2, y0, (x || 3) * U - 2, 20); ctx.setLineDash([]); L.texto('x', cx, y0 + 15, {tam: 14, negrita: true, alinear: 'center', color: x === 7 ? '#fff' : '#212529'}); return; }
                    regleta(v, x0, y0, 20);
                });
                if (etiqueta) L.texto(etiqueta, cx, base + 22, {tam: 15, negrita: true, alinear: 'center', color: '#495057'});
            }
            L.dibujar = function () {
                L.limpiar('#fff9ec');
                const dif = izqSuma() - derSuma(), ang = Math.max(-.22, Math.min(.22, dif * .03));
                // la balanza
                ctx.fillStyle = '#8b5a2b'; ctx.fillRect(W / 2 - 8, 120, 16, 220); ctx.fillRect(W / 2 - 70, 334, 140, 14);
                ctx.save(); ctx.translate(W / 2, 120); ctx.rotate(ang);
                ctx.fillStyle = '#a0703c'; ctx.fillRect(-250, -6, 500, 12);
                const platillo = (px, lista, etiqueta) => {
                    ctx.save(); ctx.translate(px, 0); ctx.rotate(-ang); ctx.strokeStyle = '#6b4423'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-100, 110); ctx.moveTo(0, 0); ctx.lineTo(100, 110); ctx.stroke(); ctx.restore();
                    ctx.save(); ctx.translate(px, 110); ctx.rotate(-ang);
                    ctx.fillStyle = '#ced4da'; ctx.fillRect(-105, 0, 210, 8);
                    pila(lista, 0, 0, etiqueta);
                    ctx.restore();
                };
                const izq = r.tipo === 'igualar' ? r.izq : Array(r.a).fill('x').concat([r.b]);
                platillo(-200, izq, r.tipo === 'igualar' ? `= ${izqSuma()}` : (x ? `${r.a}·${x} + ${r.b} = ${izqSuma()}` : `${r.a}·x + ${r.b}`));
                const derecha = r.tipo === 'igualar' ? der : [10, 10, 10].slice(0, Math.floor(r.c / 10)).concat(r.c % 10 ? [r.c % 10] : []);
                platillo(200, derecha, `= ${derSuma()}`);
                ctx.restore();
                // la caja de regletas
                L.texto(r.tipo === 'igualar' ? 'Toque una regleta para ponerla a la derecha:' : 'Escoja la regleta que vale x:', 20, 372, {tam: 13, color: '#495057'});
                let px = 20;
                for (let v = 1; v <= 10; v++) { regleta(v, px, 380, 24, UC); px += v * UC + 10; }
            };
            const caja = []; { let px = 20; for (let v = 1; v <= 10; v++) { caja.push([px, v * UC - 2, v]); px += v * UC + 10; } }
            function listo() {
                if (izqSuma() !== derSuma()) return false;
                if (r.tipo === 'incognita') return true;
                return der.length === r.k && (!r.distintas || new Set(der).size === der.length);
            }
            L.cv.addEventListener('pointerdown', ev => {
                const {x: px, y: py} = L.punto(ev);
                if (py >= 380 && py <= 404) {
                    const hit = caja.find(([cx, w]) => px >= cx && px <= cx + w);
                    if (!hit) return;
                    if (r.tipo === 'igualar') { if (der.length >= 6) return; der.push(hit[2]); } else x = hit[2];
                    api.movimiento(); api.sonido('toque');
                } else if (r.tipo === 'igualar' && px > W / 2 && der.length) { der.pop(); api.sonido('toque'); }
                L.dibujar();
                if (listo()) api.gano({estrellas: 3});
                else if (r.tipo === 'igualar' && der.length >= r.k && izqSuma() === derSuma()) api.aviso(r.distintas ? `Pesa igual, pero deben ser ${r.k} regletas de colores distintos.` : `Pesa igual, pero deben ser exactamente ${r.k} regletas.`);
            });
            return { deshacer() { if (r.tipo === 'igualar') der.pop(); else x = null; L.dibujar(); } };
        },
    });
})();
