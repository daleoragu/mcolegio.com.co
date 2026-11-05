/* Cálculo veloz: 10 operaciones contra reloj. Gana con 8 o más correctas antes de que se acabe el tiempo.
 * Los niveles suben de sumas y tablas a operaciones con negativos, potencias y porcentajes. */
(function () {
    'use strict';
    const az = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
    function operacion(nivel) {
        const t = nivel < 10 ? 0 : nivel < 20 ? 1 : 2, tipo = az(0, t === 0 ? 3 : t === 1 ? 5 : 7);
        let a, b, r, txt;
        switch (tipo) {
            case 0: a = az(8, 40 + t * 80); b = az(5, 30 + t * 60); r = a + b; txt = `${a} + ${b}`; break;
            case 1: a = az(20, 60 + t * 100); b = az(3, a - 1); r = a - b; txt = `${a} − ${b}`; break;
            case 2: a = az(2, t ? 12 : 6); b = az(2, 10); r = a * b; txt = `${a} × ${b}`; break;
            case 3: b = az(2, t ? 12 : 6); r = az(2, 10); a = b * r; txt = `${a} ÷ ${b}`; break;
            case 4: a = az(-20, 20); b = az(-20, 20); r = a - b; txt = `(${a}) − (${b})`; break;
            case 5: a = az(2, 15); r = a * a; txt = `${a}²`; break;
            case 6: a = [10, 20, 25, 50][az(0, 3)]; b = az(2, 20) * 20; r = a * b / 100; txt = `${a} % de ${b}`; break;
            default: a = az(2, 9); b = az(2, 9); const c = az(2, 20); r = a * b + c; txt = `${a} × ${b} + ${c}`;
        }
        return {txt, r};
    }
    Logica.registrar('speedrun', {
        nombre: 'Cálculo veloz',
        instrucciones: 'Resuelva 10 operaciones antes de que se acabe el tiempo. Escriba el resultado (o use el teclado de la pantalla) y presione Enter. Gana con 8 o más correctas.',
        total: () => 30,
        titulo: (d, i) => `Ronda ${i + 1} · ${i < 10 ? 'sumas, restas y tablas' : i < 20 ? 'con negativos y cuadrados' : 'con porcentajes y combinadas'}`,
        iniciar(zona, datos, i, api) {
            const TOTAL = 10, SEG = 75 - Math.floor(i / 10) * 5;
            const ops = Array.from({length: TOTAL}, () => operacion(i));
            let k = 0, bien = 0, fin = false, inicio = performance.now(), escrito = '';
            const caja = document.createElement('div');
            caja.style.cssText = 'width:100%;max-width:520px;margin:0 auto;text-align:center;font-family:system-ui,sans-serif';
            caja.innerHTML = `
              <div style="height:10px;background:#e9ecef;border-radius:6px;overflow:hidden;margin:6px 0 12px"><div class="sr-barra" style="height:100%;width:100%;background:#40c057;transition:width .2s"></div></div>
              <div class="sr-cont" style="font-size:.9rem;color:#495057"></div>
              <div class="sr-op" style="font-size:2.6rem;font-weight:800;margin:10px 0;color:#1864ab"></div>
              <div class="sr-resp" style="font-size:2rem;font-weight:700;min-height:2.6rem;border-bottom:3px solid #1864ab;width:200px;margin:0 auto 12px"></div>
              <div class="sr-teclas" style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;max-width:300px;margin:0 auto"></div>`;
            zona.appendChild(caja);
            const $ = s => caja.querySelector(s);
            ['7', '8', '9', '4', '5', '6', '1', '2', '3', '−', '0', '⌫'].concat(['OK']).forEach(t => {
                const b = document.createElement('button'); b.type = 'button'; b.textContent = t;
                b.className = 'btn ' + (t === 'OK' ? 'btn-success' : 'btn-outline-secondary');
                b.style.cssText = 'font-size:1.3rem;font-weight:700;padding:10px 0' + (t === 'OK' ? ';grid-column:span 3' : '');
                b.addEventListener('click', () => tecla(t === '−' ? '-' : t === '⌫' ? 'Backspace' : t === 'OK' ? 'Enter' : t));
                $('.sr-teclas').appendChild(b);
            });
            function pintar() {
                $('.sr-cont').textContent = `Operación ${Math.min(k + 1, TOTAL)} de ${TOTAL} · correctas: ${bien}`;
                $('.sr-op').textContent = k < TOTAL ? ops[k].txt + ' =' : '';
                $('.sr-resp').textContent = escrito;
            }
            function tecla(t) {
                if (fin) return;
                if (/^[0-9]$/.test(t) && escrito.length < 6) escrito += t;
                else if (t === '-' && !escrito) escrito = '-';
                else if (t === 'Backspace') escrito = escrito.slice(0, -1);
                else if (t === 'Enter' && escrito && escrito !== '-') {
                    const ok = parseInt(escrito, 10) === ops[k].r;
                    if (ok) bien += 1;
                    api.sonido(ok ? 'bien' : 'mal'); api.movimiento();
                    $('.sr-resp').style.color = ok ? '#2f9e44' : '#e03131';
                    if (!ok) api.aviso(`${ops[k].txt} = ${ops[k].r}`);
                    escrito = ''; k += 1;
                    setTimeout(() => { $('.sr-resp').style.color = ''; }, 250);
                    if (k >= TOTAL) return terminar();
                }
                pintar();
            }
            function terminar() {
                fin = true; pintar();
                const seg = Math.round((performance.now() - inicio) / 1000);
                if (bien >= 8) api.gano({estrellas: bien === 10 ? 3 : 2, detalle: `${bien} de ${TOTAL} correctas en ${seg} s`});
                else api.perdio({titulo: '¡Casi!', detalle: `${bien} de ${TOTAL} correctas. Se necesitan 8.`});
            }
            const teclado = ev => { if (!caja.isConnected) { document.removeEventListener('keydown', teclado); return; } if (/^[0-9]$|^-$|^Backspace$|^Enter$/.test(ev.key)) { ev.preventDefault(); tecla(ev.key); } };
            document.addEventListener('keydown', teclado);
            const reloj = setInterval(() => {
                if (!caja.isConnected || fin) { clearInterval(reloj); return; }
                const queda = Math.max(0, SEG - (performance.now() - inicio) / 1000);
                $('.sr-barra').style.width = (100 * queda / SEG) + '%';
                $('.sr-barra').style.background = queda < SEG * .25 ? '#fa5252' : '#40c057';
                if (queda <= 0) terminar();
            }, 200);
            pintar();
            return {};
        },
    });
})();
