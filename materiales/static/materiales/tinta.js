/* Tinta como la de la pizarra digital: presión del lápiz (o simulada con la velocidad), puntos intermedios del
 * lápiz y un suavizado ligero. La usan el dibujo a mano alzada (dibujo.js) y las marcas sobre la hoja (marcar.js). */
(function () {
    'use strict';
    // ------------------------------------------------------------ Tinta como en la pizarra digital
    // Presión: la del lápiz (tableta) o, con dedo o ratón, simulada con la velocidad (rápido = más delgado).
    function presion(ev, ultimo) {
        if (ev.pointerType === 'pen' && ev.pressure > 0) return ev.pressure;
        if (!ultimo) return .6;
        var v = Math.hypot(ev.clientX - ultimo.sx, ev.clientY - ultimo.sy) / Math.max(1, ev.timeStamp - ultimo.t);
        return Math.max(.3, Math.min(1, 1.05 - v * .35));
    }
    // El contorno del trazo con un ancho distinto en cada punto (como OneNote)
    function tinta(c, o) {
        var p = o.p, n = p.length, ancho = function (q) { return o.g * (.3 + .85 * (q[2] === undefined ? .5 : q[2])); };
        c.fillStyle = o.c;
        if (n < 3) { p.forEach(function (q) { c.beginPath(); c.arc(q[0], q[1], ancho(q) / 2, 0, 7); c.fill(); }); return; }
        var L = [], R = [];
        for (var i = 0; i < n; i++) {
            var a = p[Math.max(0, i - 1)], b = p[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, w = ancho(p[i]) / 2;
            L.push([p[i][0] - dy / l * w, p[i][1] + dx / l * w]); R.push([p[i][0] + dy / l * w, p[i][1] - dx / l * w]);
        }
        c.beginPath(); c.moveTo(L[0][0], L[0][1]);
        for (var j = 1; j < n - 1; j++) c.quadraticCurveTo(L[j][0], L[j][1], (L[j][0] + L[j + 1][0]) / 2, (L[j][1] + L[j + 1][1]) / 2);
        c.lineTo(L[n - 1][0], L[n - 1][1]); c.lineTo(R[n - 1][0], R[n - 1][1]);
        for (var k = n - 2; k > 0; k--) c.quadraticCurveTo(R[k][0], R[k][1], (R[k][0] + R[k - 1][0]) / 2, (R[k][1] + R[k - 1][1]) / 2);
        c.lineTo(R[0][0], R[0][1]); c.closePath(); c.fill();
        [0, n - 1].forEach(function (i2) { c.beginPath(); c.arc(p[i2][0], p[i2][1], ancho(p[i2]) / 2, 0, 7); c.fill(); });
    }
    // Agrega al trazo los puntos que entregó el lápiz desde el último cuadro, con un suavizado ligero
    function sumarPuntos(t, ev, ult, aLogico) {
        var eventos = ev.getCoalescedEvents ? ev.getCoalescedEvents() : [];
        if (!eventos.length) eventos = [ev];
        eventos.forEach(function (e) {
            if (Math.hypot(e.clientX - ult.sx, e.clientY - ult.sy) < .8) return;
            var q = aLogico(e), k = e.pointerType === 'pen' ? .75 : .55;
            var x = ult.w[0] + (q[0] - ult.w[0]) * k, y = ult.w[1] + (q[1] - ult.w[1]) * k, pr = ult.pr;
            if (pr !== undefined) { pr = pr * .6 + presion(e, ult) * .4; t.p.push([Math.round(x * 10) / 10, Math.round(y * 10) / 10, Math.round(pr * 100) / 100]); }
            else t.p.push([Math.round(x * 10) / 10, Math.round(y * 10) / 10]);
            ult.sx = e.clientX; ult.sy = e.clientY; ult.t = e.timeStamp; ult.pr = pr; ult.w = [x, y];
        });
    }
    window.MMTinta = { presion: presion, tinta: tinta, sumarPuntos: sumarPuntos };
})();
