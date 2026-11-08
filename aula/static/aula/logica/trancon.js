/* Trancón (6×6), Safari (7×7) y Escape de la selva (7×7, fauna de Colombia y Latinoamérica):
 * saque el carro rojo (o el jeep) por la salida de la derecha.
 * Escape de la selva tiene además dos modos con el jeep grande (2×2, va a los cuatro lados): 11 animales de 1×2,
 * 5 de 1×3 y 2 charcos de lodo 2×2 que en un modo no se mueven (P, Q) y en el otro sí (L, M).
 * Cada vehículo o animal se arrastra solo a lo largo de su dirección; el hipopótamo (2×2) se mueve
 * en las cuatro direcciones y las rocas no se mueven. Un movimiento = mover una pieza cualquier distancia. */
(function () {
    'use strict';
    const AUTOS = ['#4dabf7', '#69db7c', '#ffd43b', '#da77f2', '#ff922b', '#20c997', '#f783ac', '#748ffc', '#a9e34b', '#ffa94d', '#63e6be', '#e599f7'];
    const ANIM2 = ['🦓', '🦁', '🐆', '🐗', '🦌'], ANIM3 = ['🦒', '🐘', '🐊'];
    // Escape de la selva: jaguares en vez de leones, anacondas en vez de cebras y otras especies de Latinoamérica.
    const SELVA2 = ['🐆', '🐍', '🐆', '🐍', '🐒', '🦫', '🐗', '🦜', '🦥'], SELVA3 = ['🐊', '🐍', '🐢'];
    const SELVA_FONDO = {'🐆': '#ffe8a3', '🐍': '#d3f9d8', '🐒': '#ffd8a8', '🦫': '#f1e0c5', '🐗': '#e9dccb', '🦜': '#c5f6fa',
                         '🦥': '#e6dccf', '🐊': '#c3e6cb', '🐢': '#d8f5a2'};
    // Jeep grande: 11 especies de 1×2 y 5 de 1×3, cada una con su nombre en la ficha
    const ESPECIES2 = [['🐆', 'Jaguar', '#ffe8a3'], ['🦫', 'Chigüiro', '#f1e0c5'], ['🐒', 'Mono aullador', '#ffd8a8'], ['🦜', 'Guacamaya', '#c5f6fa'],
                       ['🦥', 'Perezoso', '#e6dccf'], ['🐗', 'Pecarí', '#e9dccb'], ['🐸', 'Rana dorada', '#fff3bf'], ['🦙', 'Llama', '#f8f0fc'],
                       ['🦦', 'Nutria gigante', '#d0ebff'], ['🦩', 'Flamenco', '#ffdeeb'], ['🦋', 'Morfo azul', '#dbe4ff']];
    const ESPECIES3 = [['🐍', 'Anaconda', '#d3f9d8'], ['🐊', 'Caimán llanero', '#c3e6cb'], ['🐬', 'Delfín rosado', '#ffe3e3'],
                       ['🐢', 'Tortuga charapa', '#d8f5a2'], ['🦅', 'Cóndor', '#e9ecef']];
    const SALIDA_JEEP = 3;   // el jeep grande sale por las filas 4 y 5
    const INSTR = {
        trancon: 'Saque el carro rojo por la salida de la derecha. Arrastre cada carro o camión solo hacia adelante o hacia atrás (no puede girar).',
        safari: 'Saque el jeep por la salida de la derecha. Arrastre cada animal a lo largo de su dirección; el hipopótamo se mueve hacia los cuatro lados y las rocas no se mueven.',
        selva: 'Saque el jeep de los guardaparques por la salida de la derecha. Arrastre cada animal a lo largo de su dirección (jaguares, anacondas, caimanes…); el oso de anteojos se mueve hacia los cuatro lados y las ceibas no se mueven.',
        selva_fijo: 'Jeep grande, lodo fijo: el jeep de los guardaparques ocupa 2×2 y se mueve hacia los cuatro lados; sáquelo por la salida de la derecha. Cada animal (de 2 o de 3 casillas) solo se arrastra a lo largo de su dirección y los charcos de lodo no se mueven.',
        selva_movil: 'Jeep grande, lodo móvil: el jeep de los guardaparques ocupa 2×2 y se mueve hacia los cuatro lados; sáquelo por la salida de la derecha. Cada animal (de 2 o de 3 casillas) solo se arrastra a lo largo de su dirección y los charcos de lodo también se empujan hacia los cuatro lados.',
    };
    const DATOS_SELVA = [
        'El jaguar es el felino más grande de América y nada muy bien.',
        'La anaconda es una de las serpientes más pesadas del mundo.',
        'El chigüiro es el roedor más grande del planeta.',
        'El oso de anteojos es el único oso de Suramérica y vive en los Andes.',
        'El caimán llanero vive en el Orinoco y está en peligro.',
        'Al mono aullador se le oye a más de 3 kilómetros de distancia.',
        'El perezoso baja del árbol solo una vez por semana.',
        'Colombia es el país con más especies de aves del mundo.',
        'La tortuga charapa anida en las playas de los ríos amazónicos.',
        'El pecarí anda en manadas y siembra la selva con semillas.',
        'La ceiba es un árbol gigante y sagrado para muchos pueblos.',
        'La rana dorada del Chocó es uno de los animales más venenosos.',
        'La llama vive en los Andes y carga peso por las montañas.',
        'La nutria gigante del Amazonas mide hasta 1,8 metros.',
        'El delfín rosado vive en los ríos Amazonas y Orinoco.',
        'El cóndor de los Andes es el ave símbolo de Colombia.',
        'La mariposa morfo azul brilla porque sus alas reflejan la luz.',
    ];

    function leer(filas) {
        const N = filas.length, piezas = {}, orden = [];
        filas.forEach((fila, f) => [...fila].forEach((ch, c) => {
            if (ch === '.') return;
            const k = ch === '#' ? '#' + f + ',' + c : ch;
            if (!piezas[k]) { piezas[k] = {id: k, f, c, alto: 1, ancho: 1, letra: ch}; orden.push(k); }
            const p = piezas[k];
            p.alto = Math.max(p.alto, f - p.f + 1); p.ancho = Math.max(p.ancho, c - p.c + 1);
        }));
        const lista = orden.map(k => piezas[k]);
        lista.forEach(p => {
            // P y Q: charcos de lodo fijos; toda pieza 2×2 (hipopótamo, oso, jeep grande, lodo L y M) va a los cuatro lados
            p.tipo = p.letra === '#' || p.letra === 'P' || p.letra === 'Q' ? 'fija' : p.alto > 1 && p.ancho > 1 ? '4' : p.ancho > 1 ? 'h' : 'v';
            p.lodo = 'LMPQ'.includes(p.letra);
            p.rojo = p.letra === 'x';
        });
        lista.sort((a, b) => (b.rojo ? 1 : 0) - (a.rojo ? 1 : 0));
        return {N, piezas: lista};
    }

    function crear(tema) {
        const safari = tema !== 'trancon', selva = tema.startsWith('selva'), grande = tema.startsWith('selva_');
        return {
            nombre: tema === 'selva_fijo' ? 'Escape de la selva · lodo fijo' : tema === 'selva_movil' ? 'Escape de la selva · lodo móvil'
                : selva ? 'Escape de la selva' : safari ? 'Safari' : 'Trancón',
            instrucciones: INSTR[tema],
            total: d => d.length,
            titulo: (d, i) => `Nivel ${i + 1} · se puede en ${d[i][0]} movimientos`,
            iniciar(zona, datos, i, api) {
                const [minimo, filas] = datos[i], {N, piezas} = leer(filas);
                const CEL = safari ? 56 : 64, M = 30, W = N * CEL + M * 2 + 50, H = N * CEL + M * 2 + 24 + (selva ? 22 : 0), L = api.lienzo(W, H), ctx = L.ctx;
                const filaSalida = grande ? SALIDA_JEEP : piezas[0].f, altoSalida = piezas[0].alto;
                const cuenta = {2: 0, 3: 0};
                let arrastre = null, movs = 0, saliendo = null;
                const historia = [];
                piezas.forEach((p, k) => {
                    p.color = p.rojo ? '#e03131' : AUTOS[k % AUTOS.length];
                    const largo3 = Math.max(p.alto, p.ancho) === 3;
                    if (grande) {
                        if (p.rojo) { p.emoji = '🚙'; return; }
                        if (p.lodo) { p.emoji = ''; return; }
                        const largo = Math.max(p.alto, p.ancho), lista = largo === 3 ? ESPECIES3 : ESPECIES2, e = lista[cuenta[largo]++ % lista.length];
                        [p.emoji, p.especie, p.fondo] = e;
                    } else if (selva) {
                        const lista = largo3 ? SELVA3 : SELVA2;
                        p.emoji = p.tipo === '4' ? '🐻' : p.tipo === 'fija' ? '🌳' : p.rojo ? '🚙' : lista[k % lista.length];
                        p.fondo = p.tipo === '4' ? '#e3c9a8' : SELVA_FONDO[p.emoji] || '#e9fac8';
                    } else {
                        p.emoji = p.tipo === '4' ? '🦛' : p.tipo === 'fija' ? '🪨' : p.rojo ? '🚙' : (largo3 ? ANIM3 : ANIM2)[k % (largo3 ? 3 : 5)];
                    }
                });
                function libre(f, c, salvo) {
                    if (f < 0 || c < 0 || f >= N || c >= N) return false;
                    return !piezas.some(p => p !== salvo && f >= p.f && f < p.f + p.alto && c >= p.c && c < p.c + p.ancho);
                }
                // Hasta dónde puede ir la pieza en una dirección
                function alcance(p, df, dc) {
                    let n = 0;
                    while (true) {
                        const f = p.f + df * (n + 1), c = p.c + dc * (n + 1);
                        let ok = true;
                        for (let a = 0; a < p.alto && ok; a++) for (let b = 0; b < p.ancho && ok; b++) if (!libre(f + a, c + b, p)) ok = false;
                        if (!ok) return n;
                        n += 1;
                    }
                }
                const X = c => M + c * CEL, Y = f => M + f * CEL;
                L.dibujar = function () {
                    L.limpiar(selva ? '#d8f3dc' : safari ? '#e9d8a6' : '#dee2e6');
                    // el piso
                    ctx.fillStyle = selva ? '#2d6a4f' : safari ? '#b5c99a' : '#495057'; Logica.redondo(ctx, M - 8, M - 8, N * CEL + 16, N * CEL + 16, 14); ctx.fill();
                    for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) {
                        ctx.fillStyle = selva ? ((f + c) % 2 ? '#74c69d' : '#95d5b2') : safari ? ((f + c) % 2 ? '#c9d8a8' : '#bfd29a') : '#5c636a';
                        ctx.fillRect(X(c) + 1, Y(f) + 1, CEL - 2, CEL - 2);
                    }
                    // la salida (en la selva, por el camino hacia el río)
                    ctx.fillStyle = selva ? '#a5d8ff' : safari ? '#e9d8a6' : '#dee2e6'; ctx.fillRect(M + N * CEL, Y(filaSalida) + 4, 14, CEL * altoSalida - 8);
                    ctx.fillStyle = '#2f9e44'; ctx.beginPath(); const sy = Y(filaSalida) + CEL * altoSalida / 2;
                    ctx.moveTo(M + N * CEL + 20, sy - 12); ctx.lineTo(M + N * CEL + 40, sy); ctx.lineTo(M + N * CEL + 20, sy + 12); ctx.fill();
                    L.texto('SALIDA', M + N * CEL + 30, Y(filaSalida) - 6, {tam: 11, negrita: true, alinear: 'center', color: '#2f9e44'});
                    piezas.forEach(p => {
                        let x = X(p.c), y = Y(p.f);
                        if (arrastre && arrastre.p === p) { x += arrastre.dx; y += arrastre.dy; }
                        if (saliendo && p.rojo) x += saliendo.d;
                        pintar(p, x, y);
                    });
                    L.texto(`Movimientos: ${movs}`, M, H - 6 - (selva ? 22 : 0), {tam: 13, color: '#495057'});
                    if (selva) L.texto('🌿 ' + DATOS_SELVA[(i + (tema === 'selva_fijo' ? 3 : tema === 'selva_movil' ? 7 : 0)) % DATOS_SELVA.length], M - 8, H - 8, {tam: 11.5, color: '#1b4332'});
                };
                function pintar(p, x, y) {
                    const w = p.ancho * CEL - 8, h = p.alto * CEL - 8;
                    x += 4; y += 4;
                    if (p.lodo) { lodo(p, x, y, w, h); return; }
                    if (p.tipo === 'fija') { ctx.fillStyle = selva ? '#40916c' : '#868e96'; Logica.redondo(ctx, x + 4, y + 4, w - 8, h - 8, 14); ctx.fill(); }
                    else if (safari) {
                        ctx.fillStyle = p.rojo ? '#e03131' : selva ? p.fondo : p.tipo === '4' ? '#9775fa' : '#fff3bf'; Logica.redondo(ctx, x, y, w, h, 12); ctx.fill();
                        ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 2; ctx.stroke();
                    } else {
                        ctx.fillStyle = p.color; Logica.redondo(ctx, x, y, w, h, 10); ctx.fill();
                        ctx.fillStyle = 'rgba(255,255,255,.25)'; Logica.redondo(ctx, x + 4, y + 4, w - 8, 6, 3); ctx.fill();
                        // vidrios y luces
                        ctx.fillStyle = '#212529';
                        if (p.ancho > 1) { ctx.fillRect(x + w - 22, y + 8, 10, h - 16); ctx.fillRect(x + 10, y + 10, 8, h - 20); ctx.fillStyle = '#fff3bf'; ctx.fillRect(x + w - 5, y + 6, 4, 8); ctx.fillRect(x + w - 5, y + h - 14, 4, 8); }
                        else { ctx.fillRect(x + 8, y + 10, w - 16, 10); ctx.fillRect(x + 10, y + h - 20, w - 20, 8); ctx.fillStyle = '#fff3bf'; ctx.fillRect(x + 6, y + 2, 8, 4); ctx.fillRect(x + w - 14, y + 2, 8, 4); }
                        if (Math.max(p.ancho, p.alto) === 3) { ctx.fillStyle = 'rgba(0,0,0,.15)'; if (p.ancho > 1) ctx.fillRect(x + w / 3, y + 4, 3, h - 8); else ctx.fillRect(x + 4, y + h / 3, w - 8, 3); }
                    }
                    if (p.especie) {
                        // la especie con su nombre debajo (o al lado, si la ficha es acostada)
                        const acostada = p.ancho > 1, t = Math.min(w, h) * .6;
                        ctx.font = `${t}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                        ctx.fillText(p.emoji, acostada ? x + t * .75 : x + w / 2, acostada ? y + h / 2 + 2 : y + h / 2 - 8);
                        let tam = 11; ctx.font = `600 ${tam}px system-ui, sans-serif`;
                        const ancho = acostada ? w - t * 1.6 : w - 4;
                        const minimo = acostada ? 7 : 9.5;
                        while (tam > minimo && ctx.measureText(p.especie).width > ancho) { tam -= .5; ctx.font = `600 ${tam}px system-ui, sans-serif`; }
                        ctx.fillStyle = '#1b4332';
                        if (acostada || ctx.measureText(p.especie).width <= ancho) ctx.fillText(p.especie, acostada ? x + t * 1.5 + ancho / 2 : x + w / 2, acostada ? y + h / 2 : y + h / 2 + t * .55);
                        else {   // ficha parada y nombre largo: en dos renglones
                            tam = 10.5; ctx.font = `600 ${tam}px system-ui, sans-serif`;
                            p.especie.split(' ').forEach((pal, n, todas) => ctx.fillText(pal, x + w / 2, y + h / 2 + t * .6 + (n - (todas.length - 1) / 2) * (tam + 2)));
                        }
                        return;
                    }
                    if (safari || p.tipo === 'fija') {
                        ctx.font = `${Math.min(w, h) * .62}px serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                        ctx.fillText(p.emoji, x + w / 2, y + h / 2 + 2);
                    }
                }
                // Charco de lodo (2×2): manchas cafés; el fijo lleva un candado
                function lodo(p, x, y, w, h) {
                    ctx.fillStyle = p.tipo === 'fija' ? '#6f4e37' : '#9c6b43'; Logica.redondo(ctx, x, y, w, h, 26); ctx.fill();
                    ctx.fillStyle = 'rgba(255,255,255,.12)';
                    [[.3, .32, .16], [.68, .4, .12], [.45, .7, .18], [.75, .75, .09]].forEach(([a, b, r]) => { ctx.beginPath(); ctx.ellipse(x + w * a, y + h * b, w * r, h * r * .7, 0, 0, 7); ctx.fill(); });
                    if (p.tipo !== 'fija') { ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 2; Logica.redondo(ctx, x, y, w, h, 26); ctx.stroke(); }
                    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#fff';
                    ctx.font = '700 13px system-ui, sans-serif'; ctx.fillText('LODO', x + w / 2, y + h / 2 + 14);
                    ctx.font = `${h * .28}px serif`; ctx.fillText(p.tipo === 'fija' ? '🔒' : '🐾', x + w / 2, y + h / 2 - 12);
                }
                L.cv.addEventListener('pointerdown', ev => {
                    if (saliendo) return;
                    const {x, y} = L.punto(ev), c = Math.floor((x - M) / CEL), f = Math.floor((y - M) / CEL);
                    const p = piezas.find(p => p.tipo !== 'fija' && f >= p.f && f < p.f + p.alto && c >= p.c && c < p.c + p.ancho);
                    if (!p) return;
                    try { L.cv.setPointerCapture(ev.pointerId); } catch (e) { /* */ }
                    arrastre = {p, x0: x, y0: y, dx: 0, dy: 0, eje: p.tipo === 'h' ? 'x' : p.tipo === 'v' ? 'y' : null,
                                lim: {izq: alcance(p, 0, -1), der: alcance(p, 0, 1), arr: alcance(p, -1, 0), aba: alcance(p, 1, 0)}};
                });
                L.cv.addEventListener('pointermove', ev => {
                    if (!arrastre) return;
                    const {x, y} = L.punto(ev), a = arrastre;
                    let dx = x - a.x0, dy = y - a.y0;
                    if (!a.eje && Math.hypot(dx, dy) > 8) a.eje = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y';
                    if (a.eje === 'x') { a.dx = Math.max(-a.lim.izq * CEL, Math.min((a.p.rojo && a.p.f === filaSalida ? a.lim.der + (a.p.c + a.p.ancho + a.lim.der === N ? 2 : 0) : a.lim.der) * CEL, dx)); a.dy = 0; }
                    else if (a.eje === 'y') { a.dy = Math.max(-a.lim.arr * CEL, Math.min(a.lim.aba * CEL, dy)); a.dx = 0; }
                    L.dibujar();
                });
                const soltar = () => {
                    if (!arrastre) return;
                    const a = arrastre, p = a.p; arrastre = null;
                    const dc = Math.max(-a.lim.izq, Math.min(a.lim.der, Math.round(a.dx / CEL))), df = Math.round(a.dy / CEL);
                    if (dc || df) {
                        historia.push([p, p.f, p.c]); p.c += dc; p.f += df; movs += 1; api.movimiento(); api.sonido('toque');
                    }
                    L.dibujar();
                    if (p.rojo && p.c + p.ancho === N && p.f === filaSalida) salir();
                };
                L.cv.addEventListener('pointerup', soltar); L.cv.addEventListener('pointercancel', soltar);
                function salir() {
                    saliendo = {d: 0};
                    const paso = () => { saliendo.d += 9; L.dibujar(); if (saliendo.d < CEL * 2.5) requestAnimationFrame(paso); else api.gano({estrellas: movs <= minimo ? 3 : movs <= minimo * 1.5 ? 2 : 1, detalle: `mínimo: ${minimo}`}); };
                    requestAnimationFrame(paso);
                }
                return {
                    deshacer() { if (saliendo) return; const u = historia.pop(); if (!u) return; u[0].f = u[1]; u[0].c = u[2]; movs -= 1; api.movimiento(-1); L.dibujar(); },
                };
            },
        };
    }
    Logica.registrar('trancon', crear('trancon'));
    Logica.registrar('safari', crear('safari'));
    Logica.registrar('selva', crear('selva'));
    Logica.registrar('selva_fijo', crear('selva_fijo'));
    Logica.registrar('selva_movil', crear('selva_movil'));
})();
