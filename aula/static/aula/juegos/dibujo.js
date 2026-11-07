/* Arma el dibujo: cada respuesta correcta pinta una parte del dibujo (de abajo hacia arriba).
 * Las que se fallan quedan en gris. El dibujo depende de la materia: un árbol en Naturales,
 * un cohete en Física, un robot en Matemáticas, un libro en Lenguaje, un planeta en Sociales… */
(function () {
    'use strict';
    const Y0 = 50, COLS = 24, FILAS = 16, CEL = 9, DX = 16, DY = Y0 + 46;

    const DIBUJOS = {
        arbol: {nombre: 'EL ÁRBOL', paleta: {G: '#2f9e44', g: '#51cf66', R: '#e03131', T: '#8b5a2b', t: '#6b4423', s: '#94d82d'}, filas: [
            '..........GGGG..........',
            '.......GGGGGGGGGG.......',
            '.....GGGGGgGGGGGGGG.....',
            '....GGGRGGGGGGgGGRGG....',
            '...GGGGGGGGgGGGGGGGGG...',
            '...GGgGGGRGGGGGGRGGGG...',
            '...GGGGGGGGGGGgGGGGGG...',
            '....GGGRGGgGGGGGGGGG....',
            '.....GGGGGGGGGRGGGG.....',
            '.......GGGTTTTGGG.......',
            '..........TTTT..........',
            '..........TTtT..........',
            '..........TtTT..........',
            '.........TTTTTT.........',
            '...ssssssTTTTTTssssss...',
            '..ssssssssssssssssssss..']},
        cohete: {nombre: 'EL COHETE', paleta: {W: '#f1f3f5', R: '#e03131', B: '#1c7ed6', C: '#a5d8ff', O: '#ff922b', Y: '#ffd43b', S: '#ffe066'}, filas: [
            '...........RR.......S...',
            '..........RRRR..........',
            '.S.......WWWWWW.........',
            '.........WWWWWW.........',
            '........WWWBBWWW........',
            '........WWBCCBWW......S.',
            '........WWBCCBWW........',
            '........WWWBBWWW........',
            '..S.....WWWWWWWW........',
            '........WRRRRRRW........',
            '.......RWWWWWWWWR.......',
            '......RRWWWWWWWWRR......',
            '.....RRRWWWWWWWWRRR..S..',
            '........OOYYYYOO........',
            '.........OOYYOO.........',
            '..........OOOO..........']},
        robot: {nombre: 'EL ROBOT', paleta: {G: '#868e96', S: '#dee2e6', C: '#4dabf7', K: '#1864ab', M: '#495057', B: '#1971c2', Y: '#ffd43b', R: '#e03131'}, filas: [
            '...........RR...........',
            '...........RR...........',
            '...........GG...........',
            '.......GGGGGGGGGG.......',
            '.......GSSSSSSSSG.......',
            '.......GSCCSSCCSG.......',
            '.......GSCKSSKCSG.......',
            '.......GSSSSSSSSG.......',
            '.......GSSMMMMSSG.......',
            '.......GGGGGGGGGG.......',
            '....BB..BBBBBBBB..BB....',
            '....BBBBBBYYYYBBBBBB....',
            '........BBYRRYBB........',
            '........BBBBBBBB........',
            '........BB....BB........',
            '.......GGG....GGG.......']},
        libro: {nombre: 'EL LIBRO', paleta: {B: '#1971c2', W: '#fff9db', k: '#adb5bd', R: '#e03131'}, filas: [
            '........................',
            '..BBBBBBBBB..BBBBBBBBB..',
            '.BWWWWWWWWWBBWWWWWWWWWB.',
            '.BWkkkkkkWWBBWkkkkkkkWB.',
            '.BWWWWWWWWWBBWWWWWWWWWB.',
            '.BWkkkkkkkWBBWkkkkkWWWB.',
            '.BWWWWWWWWWBBWWWWWWWWWB.',
            '.BWkkkkkWWWBBWkkkkkkkWB.',
            '.BWWWWWWWWWBBWWWWWWWWWB.',
            '.BWkkkkkkkWBBWkkkkkkWWB.',
            '.BWWWWWWWWWBBWWWWWWWWWB.',
            '.BWWWWWWWWWBBWWWWWWWWWB.',
            '.BBBBBBBBBBBBBBBBBBBBBB.',
            '..RRRRRRRRRRRRRRRRRRRR..',
            '..........RR............',
            '..........RR............']},
        tortuga: {nombre: 'LA TORTUGA', paleta: {D: '#2b8a3e', L: '#69db7c', Y: '#e9c46a', H: '#94d82d', K: '#111', A: '#74c0fc'}, filas: [
            '........................',
            '........................',
            '........................',
            '.........DDDDDD.........',
            '.......DDLDDDDLDD.......',
            '......DLLDDLLDDLLD......',
            '.....DDDDLLDDLLDDDD.HH..',
            '.....DLLDDDDDDDDLLDHHHH.',
            '.....DDDLLDDLLDDDDDHKHH.',
            '....YYYYYYYYYYYYYYYYHHH.',
            '....YYYYYYYYYYYYYYYY....',
            '.....HH...........HH....',
            '.....HH...........HH....',
            '........................',
            'AAAAAAAAAAAAAAAAAAAAAAAA',
            'AAAAAAAAAAAAAAAAAAAAAAAA']},
        cafe: {nombre: 'EL CAFÉ', paleta: {S: '#ced4da', W: '#f8f9fa', C: '#6b4423', Y: '#ffd43b', B: '#1c7ed6', R: '#e03131', P: '#adb5bd'}, filas: [
            '..........S...S.........',
            '.........S...S..........',
            '..........S...S.........',
            '.........S...S..........',
            '....WWWWWWWWWWWWWW......',
            '....WCCCCCCCCCCCCW......',
            '....WWWWWWWWWWWWWWWWW...',
            '....WWWYYYYYYYYWWW..WW..',
            '....WWWYYYYYYYYWWW..WW..',
            '....WWWBBBBBBBBWWWWWW...',
            '....WWWRRRRRRRRWWW......',
            '.....WWWWWWWWWWWW.......',
            '......WWWWWWWWWW........',
            '........................',
            '..PPPPPPPPPPPPPPPPPP....',
            '...PPPPPPPPPPPPPPPP.....']},
    };
    // El planeta con su anillo se dibuja con fórmulas (círculo y elipse)
    DIBUJOS.planeta = (function () {
        const filas = [];
        const estrellas = ['0,0', '22,1', '3,13', '20,14', '1,6', '23,9', '6,2', '17,0'];
        for (let y = 0; y < FILAS; y++) {
            let f = '';
            for (let x = 0; x < COLS; x++) {
                const dx = x - 11.5, dy = y - 7.5, enPlaneta = dx * dx + dy * dy <= 30;
                const anillo = Math.abs((dx / 11.5) ** 2 + ((dy - .3) / 2.4) ** 2 - 1) < .32;
                if (anillo && (dy > -.5 || !enPlaneta)) f += 'R';
                else if (enPlaneta) f += ['O', 'Y', 'O', 'P'][Math.floor((y + 1) / 2) % 4];
                else if (estrellas.includes(x + ',' + y)) f += 'S';
                else f += '.';
            }
            filas.push(f);
        }
        return {nombre: 'EL PLANETA', paleta: {O: '#f08c00', Y: '#ffd43b', P: '#e8590c', R: '#c5f6fa', S: '#fff3bf'}, filas};
    })();

    function elegirDibujo(tema) {
        const t = String(tema || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
        const reglas = [[/natur|biolog|ambient|ecolog/, 'arbol'], [/fisic|quimic|tecnolog|informat|astron/, 'cohete'],
            [/matem|geomet|algebra|estadist|factoriz|calculo|aritm/, 'robot'], [/lengua|espanol|castell|literat|lectur|ingles|idioma|frances|filosof|relig/, 'libro'],
            [/social|histor|geograf|civic|etica|democr|econom|polit/, 'planeta'], [/colombia|cultura/, 'cafe'], [/artist|arte|music|danza|fisica y dep|deport|educacion fisica/, 'tortuga']];
        for (const [re, d] of reglas) if (re.test(t)) return d;
        const todos = Object.keys(DIBUJOS);
        return todos[Math.floor(Math.random() * todos.length)];
    }

    function gris(hex) {
        const n = parseInt(hex.slice(1), 16), l = Math.round(((n >> 16) * .3 + (n >> 8 & 255) * .59 + (n & 255) * .11) * .55 + 70);
        return `rgb(${l},${l},${l})`;
    }

    // Las celdas del dibujo, de abajo hacia arriba: cada pregunta pinta su tramo.
    function preparar(m) {
        const clave = elegirDibujo(m.tema), d = DIBUJOS[clave], celdas = [];
        d.filas.forEach((f, y) => { f = f.padEnd(COLS, '.').slice(0, COLS); for (let x = 0; x < COLS; x++) if (f[x] !== '.') celdas.push({x, y, color: d.paleta[f[x]] || '#888'}); });
        celdas.sort((a, b) => b.y - a.y || a.x - b.x);
        const T = Math.max(1, m.total);
        celdas.forEach((c, i) => { c.tramo = Math.min(T - 1, Math.floor(i * T / celdas.length)); c.orden = i; });
        m.dib = {clave, nombre: d.nombre, celdas, tramos: new Array(T).fill(null), desde: new Array(T).fill(0)};
    }

    function pintarCeldas(m, ctx, x0, y0, cel, animar) {
        const dib = m.dib;
        dib.celdas.forEach(c => {
            const est = dib.tramos[c.tramo];
            let color = '#dee2e6', lleno = false;
            if (est) {
                // El pincel va pasando por las celdas del tramo en 0.6 s
                const del = dib.celdas.filter(o => o.tramo === c.tramo), pos = del.indexOf(c) / Math.max(1, del.length);
                if (!animar || m.t - dib.desde[c.tramo] > pos * .6) { color = est === 'bien' ? c.color : gris(c.color); lleno = true; }
            }
            ctx.fillStyle = color;
            if (lleno) ctx.fillRect(x0 + c.x * cel, y0 + c.y * cel, cel, cel);
            else ctx.fillRect(x0 + c.x * cel + 1, y0 + c.y * cel + 1, cel - 2, cel - 2);
        });
    }

    function tarros(m) {
        const n = m.opciones.length, filas = Math.ceil(n / 2), alto = Math.min(58, 248 / filas);
        return m.opciones.map((_, k) => ({k, x: 254 + (k % 2) * 112, y: Y0 + 6 + Math.floor(k / 2) * alto, w: 104, h: alto - 6}));
    }

    function tarro(ctx, k, x, y, w, h) {
        const col = Gamificacion.COLORES[k];
        ctx.fillStyle = '#ced4da'; ctx.fillRect(x + 4, y + 4, 30, h - 6);                 // la lata
        ctx.fillStyle = col; ctx.fillRect(x + 4, y + 4, 30, Math.min(10, h / 3));       // la pintura de arriba
        ctx.fillRect(x + 8, y + 4, 5, h / 2);                                           // chorrito
        ctx.strokeStyle = '#495057'; ctx.lineWidth = 2; ctx.strokeRect(x + 4, y + 4, 30, h - 6);
        ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x + 19, y + h / 2 + 6, 8, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#111'; ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(Gamificacion.LETRAS[k], x + 19, y + h / 2 + 7);
    }

    Gamificacion.registrar('dibujo', {
        nombre: 'Arma el dibujo',
        instrucciones: 'Cada respuesta correcta pinta una parte del dibujo. Toque el tarro de pintura de la respuesta (o presione su letra). Las que falle quedan en gris.',
        conReloj: true,
        sinVidas: true,
        maxOpciones: 8,
        fondo: '#f1f3f5',
        icono(ctx, k, tam) { ctx.save(); ctx.scale(tam / 40, tam / 40); tarro(ctx, k, 0, 2, 40, 36); ctx.restore(); },
        nuevaPregunta(m) {
            if (!m.dib) preparar(m);
            m.s = {tarros: tarros(m), elegido: null};
        },
        alResponder(m, bien) {
            const i = Math.min(m.indice, m.dib.tramos.length - 1);
            m.dib.tramos[i] = bien ? 'bien' : 'mal'; m.dib.desde[i] = m.t;
        },
        alTocar(m, x, y) {
            const t = m.s.tarros.find(t => x >= t.x && x <= t.x + t.w && y >= t.y && y <= t.y + t.h);
            if (t) { m.s.elegido = t.k; m.responder(t.k); }
        },
        alTecla(m, t, crudo) {
            const k = 'ABCDEFGH'.indexOf(String(crudo || '').toUpperCase());
            if (k >= 0 && k < m.opciones.length) { m.s.elegido = k; m.responder(k); }
        },
        actualizar() {},
        dibujar(m, ctx) {
            // El atril con el lienzo
            ctx.fillStyle = '#e9ecef'; ctx.fillRect(0, Y0, 480, 260);
            ctx.fillStyle = '#8b5a2b'; ctx.fillRect(DX + 30, DY + FILAS * CEL, 8, 50); ctx.fillRect(DX + COLS * CEL - 38, DY + FILAS * CEL, 8, 50);
            ctx.fillRect(DX - 8, DY + FILAS * CEL + 2, COLS * CEL + 16, 6);
            ctx.fillStyle = '#fff'; ctx.fillRect(DX - 4, DY - 4, COLS * CEL + 8, FILAS * CEL + 8);
            ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 3; ctx.strokeRect(DX - 4, DY - 4, COLS * CEL + 8, FILAS * CEL + 8);
            if (!m.dib) return;
            pintarCeldas(m, ctx, DX, DY, CEL, true);
            const hechos = m.dib.tramos.filter(t => t === 'bien').length;
            m.texto(`OBRA: ${m.dib.nombre}`, DX, Y0 + 12, {tam: 8, color: '#495057', sombra: false});
            m.texto(`PINTADO ${Math.round(100 * hechos / m.dib.tramos.length)}%`, DX, Y0 + 26, {tam: 7, color: '#2f9e44', sombra: false});
            // Los tarros de pintura (las opciones)
            (m.s ? m.s.tarros : []).forEach(t => {
                ctx.fillStyle = m.s.elegido === t.k ? '#fff3bf' : '#fff'; ctx.fillRect(t.x, t.y, t.w, t.h);
                ctx.strokeStyle = Gamificacion.COLORES[t.k]; ctx.lineWidth = 2; ctx.strokeRect(t.x, t.y, t.w, t.h);
                tarro(ctx, t.k, t.x, t.y, t.w, t.h);
                if (m.conMate(m.opciones[t.k].texto)) { m.texto(m.opciones[t.k].texto, t.x + 40, t.y + t.h / 2, {tam: 7, mate: true, base: 'middle', color: '#212529', sombra: false, ancho: t.w - 44}); return; }
                ctx.font = `6px ${m.FUENTE}`;
                const lineas = m.partir(m.opciones[t.k].texto, t.w - 44).slice(0, Math.max(1, Math.floor((t.h - 6) / 9)));
                lineas.forEach((l, i) => m.texto(l, t.x + 40, t.y + 6 + i * 9, {tam: 6, color: '#212529', sombra: false}));
            });
        },
        final(m, ctx) {
            const ok = m.dib ? m.dib.tramos.filter(t => t === 'bien').length : 0, total = m.dib ? m.dib.tramos.length : 1;
            ctx.fillStyle = '#f1f3f5'; ctx.fillRect(0, 0, 480, 360);
            m.texto(ok === total ? '¡OBRA MAESTRA!' : 'SU OBRA', 240, 14, {tam: 14, color: '#e8590c', alinear: 'center'});
            if (m.dib) {
                ctx.fillStyle = '#fff'; ctx.fillRect(240 - COLS * 6 - 6, 44, COLS * 12 + 12, FILAS * 12 + 12);
                ctx.strokeStyle = '#8b5a2b'; ctx.lineWidth = 4; ctx.strokeRect(240 - COLS * 6 - 6, 44, COLS * 12 + 12, FILAS * 12 + 12);
                pintarCeldas(m, ctx, 240 - COLS * 6, 50, 12, false);
            }
            m.texto(`PINTÓ ${ok} DE ${total} PARTES · ACIERTOS ${m.aciertos}/${m.total}`, 240, 270, {tam: 8, color: '#212529', alinear: 'center', sombra: false});
            m.texto(`PUNTAJE: ${m.puntaje}`, 240, 290, {tam: 9, color: '#e8590c', alinear: 'center', sombra: false});
            if (m.textoFinal) m.texto(m.textoFinal(), 240, 315, {tam: 8, color: '#495057', alinear: 'center', sombra: false});
        },
    });
})();
