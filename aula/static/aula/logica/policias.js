/* Policías y ladrón: policías y un ladrón se mueven por turnos por un mapa de caminos o por las casillas oscuras
 * de un tablero de ajedrez. Los policías ganan si el ladrón queda sin a dónde moverse; el ladrón gana si llega a
 * una salida. En el tablero los policías solo avanzan en diagonal hacia adelante y el ladrón va en diagonal a
 * los cuatro lados, una casilla a la vez (el juego clásico de tablero). Hay retos de policía y retos de ladrón.
 * La computadora juega el otro lado sin errores: cada posición se resuelve (análisis retrógrado) al empezar.
 * Los retos se generaron y se verificaron con aula/logica_generadores/policias.py. */
(function () {
    'use strict';
    const POL = 1, LAD = 2;
    const INSTR = {
        policias: 'Usted maneja a los policías. En cada turno mueva UN policía por un camino a un punto vecino libre; luego se mueve el ladrón. Gana si el ladrón queda sin a dónde moverse. Si el ladrón llega a una salida (🚪), se escapa.',
        policias_fuga: 'Usted es el ladrón. En su turno pase por un camino a un punto vecino libre; luego la computadora mueve UN policía. Gana si llega a una salida (🚪). Si queda sin a dónde moverse, lo atraparon.',
        policias_tablero: 'Usted maneja a los policías en el tablero: solo avanzan hacia adelante (hacia abajo) en diagonal, una casilla. El ladrón va en diagonal a los cuatro lados, una casilla a la vez. Gana si lo deja sin movimientos; si llega a la fila de arriba, se escapa.',
        policias_tablero_fuga: 'Usted es el ladrón en el tablero: se mueve en diagonal a los cuatro lados, una casilla a la vez. Los policías solo avanzan en diagonal hacia abajo. Gana si llega a la fila de arriba; si queda sin movimientos, lo atraparon.',
    };
    const NOMBRES = {policias: 'Policías y ladrón · mapas (policía)', policias_fuga: 'Policías y ladrón · mapas (ladrón)',
                     policias_tablero: 'Policías y ladrón · tablero (policía)', policias_tablero_fuga: 'Policías y ladrón · tablero (ladrón)'};

    // ------------------------------------------------------------------ el juego resuelto
    function Juego(R) {
        this.R = R; this.salidas = new Set(R.salidas);
    }
    Juego.prototype.clave = (l, ps, t) => l + '|' + ps.join(',') + '|' + t;
    Juego.prototype.hijos = function (l, ps, t) {
        const R = this.R, oc = new Set(ps), out = [];
        if (t === LAD) { R.adyL[l].forEach(v => { if (!oc.has(v)) out.push([v, ps, POL]); }); return out; }
        ps.forEach((p, i) => R.adyP[p].forEach(v => {
            if (!oc.has(v) && v !== l) { const n = ps.slice(); n[i] = v; n.sort((a, b) => a - b); out.push([l, n, LAD]); }
        }));
        return out;
    };
    Juego.prototype.resolver = function (inicio) {
        const est = new Map(), lista = [], hijosDe = [], padres = [];
        const id = s => { const k = this.clave(s[0], s[1], s[2]); let n = est.get(k); if (n === undefined) { n = lista.length; est.set(k, n); lista.push(s); hijosDe.push(null); padres.push([]); } return n; };
        id(inicio);
        for (let n = 0; n < lista.length; n++) {
            const s = lista[n];
            const h = this.salidas.has(s[0]) ? [] : this.hijos(s[0], s[1], s[2]).map(id);
            hijosDe[n] = h; h.forEach(x => padres[x].push(n));
        }
        const gan = new Int8Array(lista.length), dist = new Int32Array(lista.length), cuenta = new Int32Array(lista.length), cola = [];
        lista.forEach((s, n) => {
            cuenta[n] = hijosDe[n].length;
            if (this.salidas.has(s[0])) { gan[n] = LAD; cola.push(n); }
            else if (!hijosDe[n].length) { gan[n] = s[2] === LAD ? POL : LAD; cola.push(n); }
        });
        for (let q = 0; q < cola.length; q++) {
            const x = cola[q], g = gan[x], d = dist[x];
            padres[x].forEach(s => {
                if (gan[s]) return;
                if (g === lista[s][2]) { gan[s] = g; dist[s] = d + 1; cola.push(s); }
                else if (--cuenta[s] === 0) {
                    gan[s] = g; dist[s] = 1 + Math.max(...hijosDe[s].map(y => dist[y])); cola.push(s);
                }
            });
        }
        this.est = est; this.lista = lista; this.hijosDe = hijosDe; this.gan = gan; this.dist = dist;
    };
    Juego.prototype.valor = function (l, ps, t) { const n = this.est.get(this.clave(l, ps, t)); return n === undefined ? null : {g: this.gan[n], d: this.dist[n], n}; };
    // La mejor jugada para el lado que mueve: gana lo más rápido; si pierde, resiste lo más largo; si puede, empata.
    Juego.prototype.mejor = function (l, ps, t) {
        const v = this.valor(l, ps, t); if (!v) return null;
        const h = this.hijosDe[v.n].map(n => ({s: this.lista[n], g: this.gan[n], d: this.dist[n]}));
        if (!h.length) return null;
        const gana = h.filter(x => x.g === t), empate = h.filter(x => !x.g);
        let pool;
        if (gana.length) { const m = Math.min(...gana.map(x => x.d)); pool = gana.filter(x => x.d === m); }
        else if (empate.length) pool = empate;
        else { const m = Math.max(...h.map(x => x.d)); pool = h.filter(x => x.d === m); }
        return pool[Math.floor(Math.random() * pool.length)].s;
    };

    // ------------------------------------------------------------------ dibujo y juego
    function crear(id) {
        return {
            nombre: NOMBRES[id],
            instrucciones: INSTR[id],
            total: d => d.length,
            titulo: (d, i) => {
                const R = d[i], tam = R.tipo === 'tablero' ? `tablero ${R.N}×${R.N}` : `mapa ${R.filas}×${R.cols}`;
                return `${tam} · ${R.policias.length} policías · ${R.rol === 'policia' ? 'acorrálelo' : 'escápese'} en ${R.jugadas} jugada(s)`;
            },
            iniciar(zona, datos, i, api) { return jugar(datos[i], api); },
        };
    }

    function jugar(R, api) {
        const tablero = R.tipo === 'tablero', rolJ = R.rol === 'policia' ? POL : LAD, rolC = rolJ === POL ? LAD : POL;
        const W = 640, H = tablero ? 600 : 560, L = api.lienzo(W, H), ctx = L.ctx;
        const J = new Juego(R);
        let l = R.ladron, ps = R.policias.slice().sort((a, b) => a - b), t = R.turno === 'ladron' ? LAD : POL;
        let sel = null, listo = false, fin = false, pensando = false, mias = 0, ayudas = 0, mensaje = 'Analizando el mapa…';
        const historia = [];
        // posiciones en pantalla
        let pos;
        if (tablero) {
            const N = R.N, cel = Math.floor(Math.min(W - 80, H - 90) / N), x0 = (W - cel * N) / 2, y0 = 50;
            pos = k => ({x: x0 + R.nodos[k][1] * cel + cel / 2, y: y0 + R.nodos[k][0] * cel + cel / 2});
            pos.cel = cel; pos.x0 = x0; pos.y0 = y0;
        } else {
            const cw = (W - 120) / Math.max(1, R.cols - 1), ch = (H - 150) / Math.max(1, R.filas - 1), paso = Math.min(cw, ch, 150);
            const x0 = (W - paso * (R.cols - 1)) / 2, y0 = 70 + ((H - 150) - paso * (R.filas - 1)) / 2;
            pos = k => ({x: x0 + R.nodos[k][1] * paso, y: y0 + R.nodos[k][0] * paso});
            pos.r = Math.min(30, paso * .26);
        }
        const radio = tablero ? pos.cel * .42 : pos.r;
        function destinos(desde) {
            const oc = new Set(ps);
            if (rolJ === LAD) return R.adyL[l].filter(v => !oc.has(v));
            return R.adyP[desde].filter(v => !oc.has(v) && v !== l);
        }
        const emoji = (e, x, y, tam) => { ctx.font = `${tam}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(e, x, y + 1); };
        L.dibujar = function () {
            L.limpiar(tablero ? '#f1f3f5' : '#d3f9d8');
            const marcar = new Set(sel !== null && !fin && listo && t === rolJ ? destinos(sel) : []);
            if (tablero) {
                const N = R.N, c = pos.cel;
                for (let f = 0; f < N; f++) for (let k = 0; k < N; k++) {
                    ctx.fillStyle = (f + k) % 2 ? '#8d6e63' : '#efebe9';
                    ctx.fillRect(pos.x0 + k * c, pos.y0 + f * c, c, c);
                }
                ctx.strokeStyle = '#4e342e'; ctx.lineWidth = 3; ctx.strokeRect(pos.x0, pos.y0, N * c, N * c);
                // la fila de arriba es la meta del ladrón
                ctx.fillStyle = 'rgba(250,82,82,.25)'; ctx.fillRect(pos.x0, pos.y0, N * c, c);
                L.texto('▲ Meta del ladrón: la fila de arriba', W / 2, pos.y0 - 16, {tam: 13, negrita: true, alinear: 'center', color: '#c92a2a'});
            } else {
                // caminos
                ctx.lineCap = 'round';
                R.aristas.forEach(([a, b]) => {
                    const p = pos(a), q = pos(b);
                    ctx.strokeStyle = '#8d6e63'; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
                    ctx.strokeStyle = '#d7ccc8'; ctx.lineWidth = 4; ctx.setLineDash([8, 8]); ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); ctx.setLineDash([]);
                });
                R.nodos.forEach((_, k) => {
                    const {x, y} = pos(k), salida = J.salidas.has(k);
                    ctx.fillStyle = salida ? '#ffe3e3' : '#fff4e6'; ctx.strokeStyle = salida ? '#e03131' : '#e8590c'; ctx.lineWidth = 4;
                    ctx.beginPath(); ctx.arc(x, y, radio, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
                    if (salida) emoji('🚪', x + radio * .95, y - radio * .95, radio * .8);
                });
            }
            // destinos posibles
            marcar.forEach(k => { const {x, y} = pos(k); ctx.fillStyle = 'rgba(64,192,87,.45)'; ctx.beginPath(); ctx.arc(x, y, radio * .8, 0, Math.PI * 2); ctx.fill(); });
            if (tablero) J.salidas.forEach(k => { if (!ps.includes(k) && k !== l) { const {x, y} = pos(k); emoji('🚪', x, y, radio * .9); } });
            ps.forEach(p => {
                const {x, y} = pos(p);
                if (sel === p && rolJ === POL) { ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(x, y, radio * 1.08, 0, Math.PI * 2); ctx.stroke(); }
                ctx.fillStyle = '#1c7ed6'; ctx.beginPath(); ctx.arc(x, y, radio * .92, 0, Math.PI * 2); ctx.fill();
                emoji('👮', x, y, radio * 1.25);
            });
            {
                const {x, y} = pos(l);
                if (rolJ === LAD && t === LAD && !fin) { ctx.strokeStyle = '#ffd43b'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(x, y, radio * 1.08, 0, Math.PI * 2); ctx.stroke(); }
                ctx.fillStyle = '#343a40'; ctx.beginPath(); ctx.arc(x, y, radio * .92, 0, Math.PI * 2); ctx.fill();
                emoji('🦹', x, y, radio * 1.25);
            }
            L.texto(mensaje, W / 2, H - 22, {tam: 15, negrita: true, alinear: 'center', color: fin ? '#c92a2a' : '#343a40'});
        };
        function terminado() {
            if (J.salidas.has(l)) return LAD;
            const h = J.hijos(l, ps, t);
            if (!h.length) return t === LAD ? POL : LAD;
            return 0;
        }
        function revisarFin() {
            const g = terminado();
            if (!g) return false;
            fin = true;
            if (g === rolJ) {
                const est = ayudas ? 1 : mias <= R.jugadas ? 3 : mias <= R.jugadas + 2 ? 2 : 1;
                mensaje = rolJ === POL ? '¡Acorralado! Ganaron los policías.' : '¡Se escapó! Ganó el ladrón.';
                L.dibujar(); api.sonido('bien'); api.gano({estrellas: est, detalle: `${mias} jugada(s) · mínimo ${R.jugadas}`});
            } else {
                mensaje = rolJ === POL ? 'El ladrón se escapó. Deshaga o reinicie.' : 'Lo atraparon. Deshaga o reinicie.';
                api.sonido('mal'); L.dibujar();
            }
            return true;
        }
        function turnoTexto() {
            mensaje = t === rolJ ? (rolJ === POL ? 'Su turno: toque un policía y luego a dónde va.' : 'Su turno: toque a dónde se mueve el ladrón.') : 'Pensando…';
        }
        function juegaComputadora() {
            if (fin || t !== rolC) return;
            pensando = true; turnoTexto(); L.dibujar();
            setTimeout(() => {
                const s = J.mejor(l, ps, t);
                pensando = false;
                if (!s) { revisarFin(); return; }
                l = s[0]; ps = s[1]; t = s[2];
                api.sonido('toque');
                if (revisarFin()) return;
                // ¿la jugada del estudiante dejó escapar la victoria?
                const v = J.valor(l, ps, t);
                turnoTexto();
                if (v && v.g !== rolJ) api.aviso(v.g ? 'Ojo: así el rival ya puede ganar. Puede deshacer la jugada.' : 'Ojo: así el rival puede salvarse. Puede deshacer la jugada.');
                L.dibujar();
            }, 450);
        }
        function mover(destino) {
            historia.push({l, ps: ps.slice(), t, mias});
            if (rolJ === LAD) l = destino;
            else { const n = ps.slice(); n[n.indexOf(sel)] = destino; n.sort((a, b) => a - b); ps = n; }
            sel = null; t = rolC; mias++; api.movimiento(); api.sonido('toque');
            if (revisarFin()) return;
            juegaComputadora();
        }
        L.cv.addEventListener('pointerdown', ev => {
            if (!listo || fin || pensando || t !== rolJ) return;
            const {x, y} = L.punto(ev);
            const k = R.nodos.findIndex((_, j) => { const p = pos(j); return Math.hypot(p.x - x, p.y - y) < radio * 1.15; });
            if (k < 0) return;
            if (rolJ === POL) {
                if (ps.includes(k)) { sel = sel === k ? null : k; if (sel !== null && !destinos(sel).length) api.aviso('Ese policía no tiene a dónde moverse.'); L.dibujar(); return; }
                if (sel !== null && destinos(sel).includes(k)) { mover(k); return; }
                api.aviso(sel === null ? 'Primero toque un policía.' : 'Ahí no puede ir ese policía.'); return;
            }
            if (destinos(null).includes(k)) mover(k); else if (k !== l) api.aviso('El ladrón solo pasa a un vecino libre por un camino.');
        });
        // análisis al empezar (un momento en los tableros grandes)
        L.dibujar();
        setTimeout(() => {
            J.resolver([l, ps.slice(), t]);
            listo = true;
            if (t === rolC) juegaComputadora(); else { turnoTexto(); L.dibujar(); }
        }, 30);
        return {
            deshacer() {
                if (pensando || !historia.length) return;
                const u = historia.pop(); l = u.l; ps = u.ps; t = u.t; mias = u.mias; fin = false; sel = null;
                api.movimiento(-1); turnoTexto(); L.dibujar();
            },
            ayuda() {
                if (!listo || fin || pensando || t !== rolJ) return;
                const s = J.mejor(l, ps, t);
                if (!s) return;
                ayudas++;
                if (rolJ === LAD) { api.aviso('Una buena jugada: mueva el ladrón al punto marcado.'); mover(s[0]); return; }
                const de = ps.find(p => !s[1].includes(p)), a = s[1].find(p => !ps.includes(p));
                sel = de; api.aviso('Una buena jugada: ese policía, al punto marcado.'); mover(a);
            },
        };
    }

    Object.keys(NOMBRES).forEach(id => Logica.registrar(id, crear(id)));
    window.PoliciasJuego = Juego;          // para las pruebas
})();
