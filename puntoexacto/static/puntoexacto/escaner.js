/* PuntoExacto · motor del escáner (sin interfaz).
 *
 *   PEScan.disenos(GEOS)                     las formas de hoja que puede haber (1, 2, 4 u 8 por página)
 *   new PEScan.Detector(disenos)             busca las cuatro marcas negras en un video, imagen o lienzo
 *     .buscar(fuente, ancho, alto)           → {quad, girada} · quad en el orden de la HOJA (sup. izq., sup. der.,
 *                                              inf. der., inf. izq.), sin importar cómo esté girada en la foto
 *     .buscarTodas(lienzo)                   → [quad, …] varias hojas en una misma página (PDF escaneado)
 *   PEScan.enderezar(lienzo, quad, diseno, px_por_mm)  la hoja derecha y sin perspectiva, del tamaño real
 *   PEScan.mejorar(lienzo)                   «efecto escáner»: papel blanco y tinta negra, sin sombras
 *   PEScan.armarPDF(paginas, nombre)         descarga un PDF hecho en el navegador (nada se sube)
 *   PEScan.leerArchivo(archivo)              → lienzos de las páginas de un PDF o de una imagen
 *
 * La hoja puede estar vertical, acostada o al revés: las cuatro marcas son iguales, así que la orientación
 * se saca del código de barras, que va pegado al borde izquierdo de la hoja.
 */
(function (global) {
    'use strict';

    function homografia(src, dst) {
        var A = [], b = [];
        for (var i = 0; i < 4; i++) {
            var x = src[i][0], y = src[i][1], u = dst[i][0], v = dst[i][1];
            A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
            A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
        }
        for (var c = 0; c < 8; c++) {
            var p = c;
            for (var r = c + 1; r < 8; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
            var t = A[c]; A[c] = A[p]; A[p] = t; t = b[c]; b[c] = b[p]; b[p] = t;
            if (Math.abs(A[c][c]) < 1e-12) return null;
            for (r = c + 1; r < 8; r++) {
                var f = A[r][c] / A[c][c];
                for (var k = c; k < 8; k++) A[r][k] -= f * A[c][k];
                b[r] -= f * b[c];
            }
        }
        var h = new Array(8);
        for (c = 7; c >= 0; c--) {
            var s = b[c];
            for (k = c + 1; k < 8; k++) s -= A[c][k] * h[k];
            h[c] = s / A[c][c];
        }
        var fn = function (x, y) {
            var w = h[6] * x + h[7] * y + 1;
            return [(h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w];
        };
        fn.h = h;
        return fn;
    }

    // Marcas en mm con el origen arriba a la izquierda (el generador las da desde abajo).
    function disenos(GEOS) {
        return GEOS.map(function (g) {
            var m = g.marcas_mm.map(function (p) { return [p[0], g.alto_mm - p[1]]; });
            var sw = m[1][0] - m[0][0], sh = m[3][1] - m[0][1];
            return {pp: g.por_pagina, marcas: m, spanW: sw, spanH: sh, prop: sh / sw, marca: g.marca_mm,
                    ancho: g.ancho_mm, alto: g.alto_mm,
                    barras: g.barras_x_mm ? {x: g.barras_x_mm, grosor: g.barras_grosor_mm,
                                             y1: g.alto_mm - g.barras_y0_mm,
                                             largo: Math.min(28, (g.barras_largo_max_mm || 40) * 0.55)} : null,
                    borde: [[0, 0], [g.ancho_mm, 0], [g.ancho_mm, g.alto_mm], [0, g.alto_mm]]};
        });
    }

    // ------------------------------------------------------------------ detector
    function Detector(lista, anchoAnalisis) {
        this.disenos = lista;
        this.ancho = anchoAnalisis || 320;
        this.maxCandidatos = 12;
        this.porTamano = 7;
        this.lienzo = document.createElement('canvas');
        this.ctx = this.lienzo.getContext('2d', {willReadFrequently: true});
    }

    Detector.prototype.buscar = function (fuente, vw, vh, varias) {
        var W = this.ancho, s = W / vw, H = Math.round(vh * s), DZ = this.disenos;
        if (this.lienzo.width !== W || this.lienzo.height !== H) { this.lienzo.width = W; this.lienzo.height = H; }
        this.ctx.drawImage(fuente, 0, 0, W, H);
        var px = this.ctx.getImageData(0, 0, W, H).data;
        var gris = new Float32Array(W * H);
        var W1 = W + 1, integ = new Float64Array(W1 * (H + 1));
        for (var y = 0; y < H; y++) {
            var fila = 0;
            for (var x = 0; x < W; x++) {
                var i = (y * W + x) * 4, v = px[i] * 0.299 + px[i + 1] * 0.587 + px[i + 2] * 0.114;
                gris[y * W + x] = v;
                fila += v;
                integ[(y + 1) * W1 + x + 1] = integ[y * W1 + x + 1] + fila;
            }
        }
        function suma(x0, y0, x1, y1) {
            return integ[y1 * W1 + x1] - integ[y0 * W1 + x1] - integ[y1 * W1 + x0] + integ[y0 * W1 + x0];
        }
        // Tamaños posibles de la marca: la hoja ocupa del ~30 % al ~100 % del cuadro, derecha o acostada.
        var tamanos = [], corto = Math.min(W, H), largo = Math.max(W, H);
        DZ.forEach(function (dz) {
            [Math.min(W, H / dz.prop), Math.min(H, W / dz.prop), Math.min(corto, largo / dz.prop)].forEach(function (lado) {
                var base = dz.marca / dz.spanW * lado;
                [0.3, 0.42, 0.58, 0.8, 1.0].forEach(function (f) {
                    var L = base * f;
                    if (L >= 4.5 && !tamanos.some(function (t) { return Math.abs(t - L) < L * 0.15; })) tamanos.push(L);
                });
            });
        });
        var candidatos = [], porTam = this.porTamano;
        tamanos.forEach(function (L) {
            var c = Math.max(2, Math.round(L * 0.35)), ri = Math.max(c + 1, Math.round(L * 0.78)),
                ro = Math.max(ri + 2, Math.round(L * 1.25)), paso = Math.max(1, Math.round(L / 4));
            var areaC = 4 * c * c, areaR = 4 * ro * ro - 4 * ri * ri;
            var locales = [];
            for (var y = ro; y < H - ro; y += paso) {
                for (var x = ro; x < W - ro; x += paso) {
                    var cen = suma(x - c, y - c, x + c, y + c) / areaC;
                    if (cen > 150) continue;
                    var anillo = (suma(x - ro, y - ro, x + ro, y + ro) - suma(x - ri, y - ri, x + ri, y + ri)) / areaR;
                    var val = anillo - cen;
                    if (val > 34 && cen < anillo * 0.6) locales.push({x: x, y: y, v: val, L: L, cen: cen, anillo: anillo});
                }
            }
            locales.sort(function (a, b) { return b.v - a.v; });
            var elegidos = [];
            for (var k = 0; k < locales.length && elegidos.length < porTam; k++) {
                var a = locales[k], cerca = false;
                for (var j = 0; j < elegidos.length; j++) {
                    if (Math.abs(elegidos[j].x - a.x) < L * 1.5 && Math.abs(elegidos[j].y - a.y) < L * 1.5) { cerca = true; break; }
                }
                if (!cerca) elegidos.push(a);
            }
            candidatos = candidatos.concat(elegidos);
        });
        candidatos.sort(function (a, b) { return b.v - a.v; });
        var unicos = [], maxC = this.maxCandidatos;
        candidatos.forEach(function (a) {
            if (unicos.length >= maxC) return;
            for (var j = 0; j < unicos.length; j++) {
                var b = unicos[j], r = Math.max(a.L, b.L) * 1.2;
                if (Math.abs(a.x - b.x) < r && Math.abs(a.y - b.y) < r) return;
            }
            unicos.push(a);
        });

        var mejor = null, mejorV = -1, n = unicos.length;
        var d = function (a, b) { return Math.hypot(a.x - b.x, a.y - b.y); };
        for (var i1 = 0; i1 < n; i1++) for (var i2 = i1 + 1; i2 < n; i2++)
        for (var i3 = i2 + 1; i3 < n; i3++) for (var i4 = i3 + 1; i4 < n; i4++) {
            var q = [unicos[i1], unicos[i2], unicos[i3], unicos[i4]];
            var tl = q[0], br = q[0], tr = q[0], bl = q[0];
            q.forEach(function (p) {
                if (p.x + p.y < tl.x + tl.y) tl = p;
                if (p.x + p.y > br.x + br.y) br = p;
                if (p.x - p.y > tr.x - tr.y) tr = p;
                if (p.x - p.y < bl.x - bl.y) bl = p;
            });
            if (tl === br || tl === tr || tl === bl || br === tr || br === bl || tr === bl) continue;
            var arriba = d(tl, tr), abajo = d(bl, br), izq = d(tl, bl), der = d(tr, br);
            if (Math.min(arriba, abajo) / Math.max(arriba, abajo) < 0.75) continue;
            if (Math.min(izq, der) / Math.max(izq, der) < 0.75) continue;
            var d1 = d(tl, br), d2 = d(tr, bl);
            if (Math.min(d1, d2) / Math.max(d1, d2) < 0.85) continue;
            var ancho = (arriba + abajo) / 2, alto = (izq + der) / 2;
            if (Math.max(ancho, alto) < Math.max(W, H) * 0.18) continue;
            var suma4 = tl.v + tr.v + br.v + bl.v;
            // Una hoja de verdad no tiene otra marca del mismo tamaño adentro (varias hojas en una página).
            var Lm = (tl.L + tr.L + br.L + bl.L) / 4, poli = [tl, tr, br, bl];
            for (var o = 0; o < n; o++) {
                var u = unicos[o];
                if (poli.indexOf(u) >= 0 || u.L < Lm * 0.82 || u.L > Lm * 1.22) continue;
                // Con una sola hoja (cámara) basta mirar adentro. En una página con varias hojas, las marcas de la
                // vecina quedan justo sobre los lados de un rectángulo falso: ahí cuentan también, si son macizas.
                if (varias ? (dentro(poli, u, Lm, -0.8) && maciza(fuente, u, s)) : dentro(poli, u, Lm, 0.6)) { suma4 *= 0.4; break; }
            }
            for (var di = 0; di < DZ.length; di++) {
                var dz = DZ[di];
                // Derecha (o al revés): el ancho en pantalla es el ancho de la hoja. Acostada: es su alto.
                var derecha = (alto / ancho) / dz.prop, acostada = (ancho / alto) / dz.prop;
                var esDerecha = derecha > 0.84 && derecha < 1.19, esAcostada = acostada > 0.84 && acostada < 1.19;
                if (!esDerecha && !esAcostada) continue;
                var esperado = dz.marca * (esDerecha ? ancho : alto) / dz.spanW;
                if (!q.every(function (p) { return p.L > esperado * 0.5 && p.L < esperado * 1.9; })) continue;
                var v = suma4 * (di === 0 ? 1.02 : 1);
                if (v > mejorV) {
                    mejorV = v;
                    mejor = {pts: [tl, tr, br, bl], dz: dz, girada: !esDerecha};
                }
                break;
            }
        }
        if (!mejor) return {quad: null};
        // Centro fino de cada marca: centroide de lo oscuro alrededor.
        var finos = mejor.pts.map(function (m) {
            var r = Math.round(m.L * 0.9), umbral = (m.cen + m.anillo) / 2, sx = 0, sy = 0, cnt = 0;
            for (var yy = Math.max(0, m.y - r); yy < Math.min(H, m.y + r); yy++) {
                for (var xx = Math.max(0, m.x - r); xx < Math.min(W, m.x + r); xx++) {
                    if (gris[yy * W + xx] <= umbral) { sx += xx; sy += yy; cnt++; }
                }
            }
            return [cnt >= 4 ? sx / cnt : m.x, cnt >= 4 ? sy / cnt : m.y];
        });
        var TL = finos[0], TR = finos[1], BR = finos[2], BL = finos[3];
        // Las dos maneras en que puede estar la hoja; el código de barras decide.
        var opciones = mejor.girada
            ? [{giro: 90, q: [TR, BR, BL, TL]}, {giro: -90, q: [BL, TL, TR, BR]}]
            : [{giro: 0, q: [TL, TR, BR, BL]}, {giro: 180, q: [BR, BL, TL, TR]}];
        var dz = mejor.dz;
        opciones.forEach(function (o) { o.puntos = puntajeBarras(o.q, dz, gris, W, H); });
        var elegida = opciones[0];
        // Derecha: solo se voltea si el código se ve claramente al otro lado.
        var margen = mejor.girada ? 0 : 12;
        if (opciones[1].puntos > opciones[0].puntos + margen) elegida = opciones[1];
        var quad = elegida.q.map(function (p) { return [p[0] / s, p[1] / s]; });
        quad.diseno = dz;
        quad.giro = elegida.giro;
        return {quad: quad, girada: mejor.girada};
    };

    // ¿Es un cuadrado macizo en la imagen original? (las barras del código de barras dejan papel entre barra y barra)
    function maciza(fuente, u, s) {
        if (!fuente.getContext) return true;
        var cx = u.x / s, cy = u.y / s, r = Math.max(2, Math.round(u.L / s * 0.35));
        var d = fuente.getContext('2d', {willReadFrequently: true}).getImageData(Math.round(cx - r), Math.round(cy - r), 2 * r, 2 * r).data;
        var umbral = (u.cen + u.anillo) / 2, osc = 0, tot = d.length / 4;
        for (var i = 0; i < d.length; i += 4) if (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114 <= umbral) osc++;
        return tot > 0 && osc / tot >= 0.8;
    }

    function dentro(poli, p, holgura, factor) {
        // Convexo y en el sentido de las agujas del reloj: adentro (o sobre un lado) si no queda afuera de ningún lado.
        for (var i = 0; i < 4; i++) {
            var a = poli[i], b = poli[(i + 1) % 4];
            var cruz = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
            var lado = Math.hypot(b.x - a.x, b.y - a.y) || 1;
            if (cruz / lado < holgura * factor) return false;
        }
        // Las esquinas mismas no cuentan.
        for (i = 0; i < 4; i++) if (Math.hypot(poli[i].x - p.x, poli[i].y - p.y) < holgura * 1.5) return false;
        return true;
    }

    // ------------------------------------------------------------------ visores fijos (como los de la cámara de ZipGrade)
    // Dónde van los 4 visores para este cuadro: las marcas de la hoja ocupando ~82 % de la pantalla, derecha si el
    // celular está vertical y acostada si está horizontal. Devuelve los centros (orden de pantalla: sup. izq.,
    // sup. der., inf. der., inf. izq.), el lado de cada visor y si la hoja va acostada.
    function visores(vw, vh, dz) {
        var acostada = vw > vh;
        var prop = acostada ? 1 / dz.prop : dz.prop;          // alto/ancho del rectángulo de marcas en pantalla
        var ancho = Math.min(vw * 0.82, vh * 0.82 / prop), alto = ancho * prop;
        var x0 = (vw - ancho) / 2, y0 = (vh - alto) / 2;
        var lado = Math.max(Math.min(vw, vh) * 0.10, dz.marca / (acostada ? dz.spanH : dz.spanW) * ancho * 2.2);
        return {centros: [[x0, y0], [x0 + ancho, y0], [x0 + ancho, y0 + alto], [x0, y0 + alto]],
                lado: lado, acostada: acostada, marca: dz.marca / (acostada ? dz.spanH : dz.spanW) * ancho};
    }

    // Busca una marca negra dentro de cada visor (solo ahí: es rápido y el fondo no confunde).
    Detector.prototype.buscarEnVisores = function (fuente, vw, vh, dz) {
        var W = this.ancho, s = W / vw, H = Math.round(vh * s);
        if (this.lienzo.width !== W || this.lienzo.height !== H) { this.lienzo.width = W; this.lienzo.height = H; }
        this.ctx.drawImage(fuente, 0, 0, W, H);
        var px = this.ctx.getImageData(0, 0, W, H).data;
        var gris = new Float32Array(W * H), W1 = W + 1, integ = new Float64Array(W1 * (H + 1));
        for (var y = 0; y < H; y++) {
            var fila = 0;
            for (var x = 0; x < W; x++) {
                var i = (y * W + x) * 4, v = px[i] * 0.299 + px[i + 1] * 0.587 + px[i + 2] * 0.114;
                gris[y * W + x] = v; fila += v;
                integ[(y + 1) * W1 + x + 1] = integ[y * W1 + x + 1] + fila;
            }
        }
        function suma(x0, y0, x1, y1) {
            return integ[y1 * W1 + x1] - integ[y0 * W1 + x1] - integ[y1 * W1 + x0] + integ[y0 * W1 + x0];
        }
        var vis = visores(vw, vh, dz), encontrados = [], puntos = [];
        vis.centros.forEach(function (c) {
            var cx = c[0] * s, cy = c[1] * s, R = vis.lado * s / 2, mejor = null;
            // Tamaños de marca posibles dentro del visor (la hoja un poco más cerca o más lejos).
            [0.7, 0.85, 1.0, 1.2].forEach(function (f) {
                var L = Math.max(4, vis.marca * s * f);
                var cc = Math.max(2, Math.round(L * 0.35)), ri = Math.max(cc + 1, Math.round(L * 0.78)),
                    ro = Math.max(ri + 2, Math.round(L * 1.25)), paso = Math.max(1, Math.round(L / 5));
                var areaC = 4 * cc * cc, areaR = 4 * ro * ro - 4 * ri * ri;
                for (var yy = Math.max(ro, Math.round(cy - R)); yy <= Math.min(H - ro - 1, Math.round(cy + R)); yy += paso) {
                    for (var xx = Math.max(ro, Math.round(cx - R)); xx <= Math.min(W - ro - 1, Math.round(cx + R)); xx += paso) {
                        var cen = suma(xx - cc, yy - cc, xx + cc, yy + cc) / areaC;
                        if (cen > 150) continue;
                        var anillo = (suma(xx - ro, yy - ro, xx + ro, yy + ro) - suma(xx - ri, yy - ri, xx + ri, yy + ri)) / areaR;
                        var val = anillo - cen;
                        if (val > 34 && cen < anillo * 0.6 && (!mejor || val > mejor.v)) mejor = {x: xx, y: yy, v: val, L: L, cen: cen, anillo: anillo};
                    }
                }
            });
            encontrados.push(!!mejor);
            if (mejor) {
                var r = Math.round(mejor.L * 0.9), umbral = (mejor.cen + mejor.anillo) / 2, sx = 0, sy = 0, cnt = 0;
                for (var yy = Math.max(0, mejor.y - r); yy < Math.min(H, mejor.y + r); yy++)
                    for (var xx = Math.max(0, mejor.x - r); xx < Math.min(W, mejor.x + r); xx++)
                        if (gris[yy * W + xx] <= umbral) { sx += xx; sy += yy; cnt++; }
                puntos.push(cnt >= 4 ? [sx / cnt, sy / cnt] : [mejor.x, mejor.y]);
            } else puntos.push(null);
        });
        var res = {quad: null, encontrados: encontrados, visores: vis};
        if (puntos.some(function (p) { return !p; })) return res;
        var TL = puntos[0], TR = puntos[1], BR = puntos[2], BL = puntos[3];
        var opciones = vis.acostada ? [{giro: 90, q: [TR, BR, BL, TL]}, {giro: -90, q: [BL, TL, TR, BR]}]
                                    : [{giro: 0, q: [TL, TR, BR, BL]}, {giro: 180, q: [BR, BL, TL, TR]}];
        opciones.forEach(function (o) { o.puntos = puntajeBarras(o.q, dz, gris, W, H); });
        var elegida = opciones[1].puntos > opciones[0].puntos + (vis.acostada ? 0 : 12) ? opciones[1] : opciones[0];
        var quad = elegida.q.map(function (p) { return [p[0] / s, p[1] / s]; });
        quad.diseno = dz; quad.giro = elegida.giro;
        res.quad = quad;
        return res;
    };

    // Cuánto más oscura es la franja del código de barras (borde izquierdo) que la misma franja del borde derecho.
    function puntajeBarras(q, dz, gris, W, H) {
        if (!dz.barras) return 0;
        var Hm = homografia(dz.marcas, q);
        if (!Hm) return 0;
        var b = dz.barras, izq = 0, der = 0, n = 0;
        for (var k = 0; k < 24; k++) {
            var ymm = b.y1 - b.largo * (k + 0.5) / 24;
            for (var t = -1; t <= 1; t++) {
                var xmm = b.x + t * b.grosor * 0.25;
                var p1 = Hm(xmm, ymm), p2 = Hm(dz.ancho - xmm, ymm);
                var x1 = Math.round(p1[0]), y1 = Math.round(p1[1]), x2 = Math.round(p2[0]), y2 = Math.round(p2[1]);
                if (x1 < 0 || y1 < 0 || x1 >= W || y1 >= H || x2 < 0 || y2 < 0 || x2 >= W || y2 >= H) continue;
                izq += gris[y1 * W + x1]; der += gris[y2 * W + x2]; n++;
            }
        }
        return n ? (der - izq) / n : 0;
    }

    // Varias hojas en una página: se busca, se tapa la que se encontró y se vuelve a buscar.
    Detector.prototype.buscarTodas = function (lienzo, maximo) {
        var copia = document.createElement('canvas');
        copia.width = lienzo.width; copia.height = lienzo.height;
        var c = copia.getContext('2d');
        c.drawImage(lienzo, 0, 0);
        var halladas = [], ancho = this.ancho, maxC = this.maxCandidatos;
        this.ancho = Math.min(640, Math.max(320, Math.round(lienzo.width / 3)));
        this.maxCandidatos = 20; this.porTamano = 20;
        for (var i = 0; i < (maximo || 8); i++) {
            var r = this.buscar(copia, copia.width, copia.height, true);
            if (!r.quad) break;
            halladas.push(r.quad);
            // Se tapa lo que encierran las cuatro marcas, con una marca de margen: así no se toca la hoja vecina.
            var dz = r.quad.diseno, Hm = homografia(dz.marcas, r.quad), mk = dz.marca;
            var signos = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
            var borde = dz.marcas.map(function (m, k) { return Hm(m[0] + signos[k][0] * mk, m[1] + signos[k][1] * mk); });
            c.fillStyle = '#fff';
            c.beginPath();
            borde.forEach(function (p, k) { if (k) c.lineTo(p[0], p[1]); else c.moveTo(p[0], p[1]); });
            c.closePath(); c.fill();
        }
        this.ancho = ancho; this.maxCandidatos = maxC; this.porTamano = 7;
        // En el orden de lectura de la página: de arriba abajo y de izquierda a derecha.
        halladas.sort(function (a, b) {
            var ya = (a[0][1] + a[2][1]) / 2, yb = (b[0][1] + b[2][1]) / 2;
            var alto = Math.abs(a[2][1] - a[0][1]) || 1;
            if (Math.abs(ya - yb) > alto * 0.4) return ya - yb;
            return (a[0][0] + a[2][0]) / 2 - (b[0][0] + b[2][0]) / 2;
        });
        return halladas;
    };

    // ------------------------------------------------------------------ esquinas tocadas con el dedo
    // Lleva un toque al centro de la marca negra más cercana: no hace falta atinarle exacto.
    function ajustarEsquina(lienzo, x, y, radio) {
        var R = Math.max(8, Math.round(radio)), x0 = Math.max(0, Math.round(x - R)), y0 = Math.max(0, Math.round(y - R));
        var w = Math.min(lienzo.width - x0, 2 * R), h = Math.min(lienzo.height - y0, 2 * R);
        if (w < 4 || h < 4) return [x, y];
        var k = Math.min(1, 140 / Math.max(w, h)), ww = Math.max(4, Math.round(w * k)), hh = Math.max(4, Math.round(h * k));
        var c = document.createElement('canvas'); c.width = ww; c.height = hh;
        var cx = c.getContext('2d', {willReadFrequently: true});
        cx.drawImage(lienzo, x0, y0, w, h, 0, 0, ww, hh);
        var d = cx.getImageData(0, 0, ww, hh).data, g = new Float32Array(ww * hh), lo = 255, hi = 0;
        for (var i = 0; i < ww * hh; i++) {
            g[i] = d[i * 4] * 0.299 + d[i * 4 + 1] * 0.587 + d[i * 4 + 2] * 0.114;
            if (g[i] < lo) lo = g[i]; if (g[i] > hi) hi = g[i];
        }
        if (hi - lo < 40) return [x, y];                      // no hay nada oscuro: se deja donde tocó
        var umbral = lo + (hi - lo) * 0.42, visto = new Uint8Array(ww * hh), mejor = null, tx = (x - x0) * k, ty = (y - y0) * k;
        for (var j = 0; j < ww * hh; j++) {
            if (visto[j] || g[j] > umbral) continue;
            var pila = [j], n = 0, sx = 0, sy = 0, bx0 = ww, bx1 = 0, by0 = hh, by1 = 0; visto[j] = 1;
            while (pila.length) {
                var q = pila.pop(), qx = q % ww, qy = (q / ww) | 0;
                n++; sx += qx; sy += qy;
                if (qx < bx0) bx0 = qx; if (qx > bx1) bx1 = qx; if (qy < by0) by0 = qy; if (qy > by1) by1 = qy;
                [q - 1, q + 1, q - ww, q + ww].forEach(function (v, t) {
                    if (v < 0 || v >= ww * hh || visto[v] || g[v] > umbral) return;
                    if ((t === 0 && qx === 0) || (t === 1 && qx === ww - 1)) return;
                    visto[v] = 1; pila.push(v);
                });
            }
            if (n < 6) continue;
            // Una marca es un cuadrado macizo y entero: la mesa o una sombra tocan el borde de la ventana o no son macizas.
            var bw = bx1 - bx0 + 1, bh = by1 - by0 + 1;
            if (bx0 === 0 || by0 === 0 || bx1 === ww - 1 || by1 === hh - 1) continue;
            if (n / (bw * bh) < 0.6 || bw / bh > 1.8 || bh / bw > 1.8) continue;
            var mx = sx / n, my = sy / n, dist = Math.hypot(mx - tx, my - ty);
            var puntos = n / (1 + dist * 0.15);               // grande y cerca del dedo
            if (!mejor || puntos > mejor.p) mejor = {p: puntos, x: mx, y: my};
        }
        return mejor ? [x0 + mejor.x / k, y0 + mejor.y / k] : [x, y];
    }

    // Cuatro toques (en cualquier orden) → quad en el orden de la hoja, con su diseño y su giro.
    function desdeEsquinas(lienzo, toques, lista) {
        var lado = Math.min(lienzo.width, lienzo.height) * 0.07;
        var p = toques.map(function (t) { return ajustarEsquina(lienzo, t[0], t[1], lado); });
        var orden = p.slice().sort(function (a, b) { return (a[0] + a[1]) - (b[0] + b[1]); });
        var TL = orden[0], BR = orden[3], resto = [orden[1], orden[2]];
        var TR = (resto[0][0] - resto[0][1]) > (resto[1][0] - resto[1][1]) ? resto[0] : resto[1];
        var BL = TR === resto[0] ? resto[1] : resto[0];
        var dd = function (a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1]); };
        var ancho = (dd(TL, TR) + dd(BL, BR)) / 2, alto = (dd(TL, BL) + dd(TR, BR)) / 2;
        var mejor = null;
        lista.forEach(function (dz, i) {
            [false, true].forEach(function (acostada) {
                var r = (acostada ? ancho / alto : alto / ancho) / dz.prop, err = Math.abs(Math.log(r)) - (i === 0 ? 0.02 : 0);
                if (!mejor || err < mejor.err) mejor = {err: err, dz: dz, acostada: acostada};
            });
        });
        var dz = mejor.dz;
        var opciones = mejor.acostada ? [{giro: 90, q: [TR, BR, BL, TL]}, {giro: -90, q: [BL, TL, TR, BR]}]
                                      : [{giro: 0, q: [TL, TR, BR, BL]}, {giro: 180, q: [BR, BL, TL, TR]}];
        // La orientación, por el código de barras (en una copia pequeña en gris).
        var W = Math.min(640, lienzo.width), s = W / lienzo.width, H = Math.round(lienzo.height * s);
        var c = document.createElement('canvas'); c.width = W; c.height = H;
        var cx = c.getContext('2d', {willReadFrequently: true}); cx.drawImage(lienzo, 0, 0, W, H);
        var d = cx.getImageData(0, 0, W, H).data, gris = new Float32Array(W * H);
        for (var i = 0; i < W * H; i++) gris[i] = d[i * 4] * 0.299 + d[i * 4 + 1] * 0.587 + d[i * 4 + 2] * 0.114;
        opciones.forEach(function (o) {
            o.puntos = puntajeBarras(o.q.map(function (v) { return [v[0] * s, v[1] * s]; }), dz, gris, W, H);
        });
        var elegida = opciones[1].puntos > opciones[0].puntos + (mejor.acostada ? 0 : 12) ? opciones[1] : opciones[0];
        var quad = elegida.q.map(function (v) { return [v[0], v[1]]; });
        quad.diseno = dz; quad.giro = elegida.giro;
        return quad;
    }

    // ------------------------------------------------------------------ enderezar
    // La hoja completa, derecha y del tamaño real (px_por_mm), interpolando entre los píxeles de la foto.
    // Lleva un borde alrededor (margen_mm, de la misma foto): el lector necesita ver papel o mesa alrededor
    // de cada marca para reconocerla.
    function enderezar(fuente, quad, dz, pxPorMm, margenMm) {
        var k = pxPorMm, mg = margenMm === undefined ? Math.max(4, dz.ancho * 0.035) : margenMm;
        var Wd = Math.round((dz.ancho + 2 * mg) * k), Hd = Math.round((dz.alto + 2 * mg) * k);
        var sw = fuente.width, sh = fuente.height;
        var src = fuente.getContext('2d', {willReadFrequently: true}).getImageData(0, 0, sw, sh).data;
        var Hm = homografia(dz.marcas, quad);
        var salida = document.createElement('canvas');
        salida.width = Wd; salida.height = Hd;
        var cx = salida.getContext('2d');
        var img = cx.createImageData(Wd, Hd), dst = img.data;
        var h = Hm.h;
        for (var y = 0; y < Hd; y++) {
            var my = (y + 0.5) / k - mg;
            for (var x = 0; x < Wd; x++) {
                var mx = (x + 0.5) / k - mg;
                var w = h[6] * mx + h[7] * my + 1;
                var u = (h[0] * mx + h[1] * my + h[2]) / w - 0.5, v = (h[3] * mx + h[4] * my + h[5]) / w - 0.5;
                var o = (y * Wd + x) * 4;
                if (u < 0 || v < 0 || u >= sw - 1 || v >= sh - 1) { dst[o] = dst[o + 1] = dst[o + 2] = 255; dst[o + 3] = 255; continue; }
                var x0 = u | 0, y0 = v | 0, fx = u - x0, fy = v - y0;
                var a = (y0 * sw + x0) * 4, b2 = a + 4, c2 = a + sw * 4, d2 = c2 + 4;
                for (var ch = 0; ch < 3; ch++) {
                    var top = src[a + ch] + (src[b2 + ch] - src[a + ch]) * fx;
                    var bot = src[c2 + ch] + (src[d2 + ch] - src[c2 + ch]) * fx;
                    dst[o + ch] = top + (bot - top) * fy;
                }
                dst[o + 3] = 255;
            }
        }
        cx.putImageData(img, 0, 0);
        salida.diseno = dz;
        salida.margen = mg * k;          // px de borde a cada lado
        return salida;
    }

    // Lo mismo, pero en un «trabajador» aparte: el celular no se congela mientras endereza y la cámara sigue buscando.
    var CODIGO_TRABAJADOR = 'onmessage=function(e){var m=e.data,src=new Uint8ClampedArray(m.src),sw=m.sw,sh=m.sh,Wd=m.Wd,Hd=m.Hd,h=m.h,k=m.k,mg=m.mg;' +
        'var dst=new Uint8ClampedArray(Wd*Hd*4);for(var y=0;y<Hd;y++){var my=(y+0.5)/k-mg;for(var x=0;x<Wd;x++){var mx=(x+0.5)/k-mg;' +
        'var w=h[6]*mx+h[7]*my+1,u=(h[0]*mx+h[1]*my+h[2])/w-0.5,v=(h[3]*mx+h[4]*my+h[5])/w-0.5,o=(y*Wd+x)*4;' +
        'if(u<0||v<0||u>=sw-1||v>=sh-1){dst[o]=dst[o+1]=dst[o+2]=255;dst[o+3]=255;continue;}' +
        'var x0=u|0,y0=v|0,fx=u-x0,fy=v-y0,a=(y0*sw+x0)*4,b=a+4,c=a+sw*4,d=c+4;' +
        'for(var ch=0;ch<3;ch++){var t=src[a+ch]+(src[b+ch]-src[a+ch])*fx,bo=src[c+ch]+(src[d+ch]-src[c+ch])*fx;dst[o+ch]=t+(bo-t)*fy;}dst[o+3]=255;}}' +
        'postMessage({dst:dst.buffer,id:m.id},[dst.buffer]);};';
    var trabajador = null, pendientes = {}, siguiente = 1;
    function enderezarAsync(fuente, quad, dz, pxPorMm, margenMm) {
        var k = pxPorMm, mg = margenMm === undefined ? Math.max(4, dz.ancho * 0.035) : margenMm;
        try {
            if (!trabajador) {
                trabajador = new Worker(URL.createObjectURL(new Blob([CODIGO_TRABAJADOR], {type: 'text/javascript'})));
                trabajador.onmessage = function (e) { var f = pendientes[e.data.id]; delete pendientes[e.data.id]; if (f) f(e.data.dst); };
            }
        } catch (e) { trabajador = null; }
        if (!trabajador) return Promise.resolve(enderezar(fuente, quad, dz, pxPorMm, margenMm));
        var Wd = Math.round((dz.ancho + 2 * mg) * k), Hd = Math.round((dz.alto + 2 * mg) * k);
        var img = fuente.getContext('2d', {willReadFrequently: true}).getImageData(0, 0, fuente.width, fuente.height);
        var Hm = homografia(dz.marcas, quad), id = siguiente++;
        return new Promise(function (ok) {
            pendientes[id] = function (buf) {
                var salida = document.createElement('canvas');
                salida.width = Wd; salida.height = Hd;
                salida.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(buf), Wd, Hd), 0, 0);
                salida.diseno = dz; salida.margen = mg * k;
                ok(salida);
            };
            trabajador.postMessage({src: img.data.buffer, sw: fuente.width, sh: fuente.height, Wd: Wd, Hd: Hd, h: Hm.h, k: k, mg: mg, id: id},
                                   [img.data.buffer]);
        });
    }

    // Píxeles por mm para enderezar sin inventar detalle que la foto no tiene.
    function resolucion(quad, dz, maxAncho) {
        var lado = Math.hypot(quad[1][0] - quad[0][0], quad[1][1] - quad[0][1]);
        var real = lado / dz.spanW;
        // El lector del servidor necesita unos 7,5 px por mm para descifrar el código de barras.
        return Math.max(7.5, Math.min(real * 1.2, maxAncho ? maxAncho / (dz.ancho * 1.07) : 12));
    }

    // ------------------------------------------------------------------ efecto escáner
    // Divide cada píxel por el «papel» de su zona (lo más claro alrededor): se van las sombras y el papel queda blanco.
    function mejorar(lienzo) {
        var W = lienzo.width, H = lienzo.height;
        var cw = Math.max(16, Math.round(W / 24)), chh = Math.max(16, Math.round(H / 24));
        var chico = document.createElement('canvas');
        chico.width = cw; chico.height = chh;
        var cc = chico.getContext('2d', {willReadFrequently: true});
        cc.drawImage(lienzo, 0, 0, cw, chh);
        var p = cc.getImageData(0, 0, cw, chh), pd = p.data, m = new Uint8ClampedArray(pd.length);
        for (var y = 0; y < chh; y++) for (var x = 0; x < cw; x++) {
            var o = (y * cw + x) * 4, mx = 0;
            for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) {
                var yy = Math.min(chh - 1, Math.max(0, y + dy)), xx = Math.min(cw - 1, Math.max(0, x + dx));
                var q = (yy * cw + xx) * 4, l = pd[q] * 0.299 + pd[q + 1] * 0.587 + pd[q + 2] * 0.114;
                if (l > mx) mx = l;
            }
            m[o] = m[o + 1] = m[o + 2] = mx; m[o + 3] = 255;
        }
        cc.putImageData(new ImageData(m, cw, chh), 0, 0);
        var fondo = document.createElement('canvas');
        fondo.width = W; fondo.height = H;
        var fc = fondo.getContext('2d', {willReadFrequently: true});
        fc.imageSmoothingQuality = 'high';
        fc.drawImage(chico, 0, 0, W, H);
        var bg = fc.getImageData(0, 0, W, H).data;
        var salida = document.createElement('canvas');
        salida.width = W; salida.height = H;
        var sc = salida.getContext('2d');
        var src = lienzo.getContext('2d', {willReadFrequently: true}).getImageData(0, 0, W, H);
        var d = src.data;
        for (var i = 0; i < d.length; i += 4) {
            var lum = d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114;
            var r = lum / Math.max(40, bg[i]);
            var v = r >= 0.9 ? 255 : 255 * Math.pow(Math.max(0, (r - 0.3) / 0.6), 1.35);
            d[i] = d[i + 1] = d[i + 2] = v;
        }
        sc.putImageData(src, 0, 0);
        return salida;
    }

    // ------------------------------------------------------------------ PDF
    var CDN = 'https://cdnjs.cloudflare.com/ajax/libs/';
    function cargar(url, prueba) {
        if (prueba()) return Promise.resolve();
        return new Promise(function (ok, mal) {
            var s = document.createElement('script');
            s.src = url; s.onload = function () { ok(); }; s.onerror = function () { mal(new Error('No se pudo cargar ' + url)); };
            document.head.appendChild(s);
        });
    }
    function jsPDF() {
        return cargar(CDN + 'jspdf/2.5.1/jspdf.umd.min.js', function () { return global.jspdf; })
            .then(function () { return global.jspdf.jsPDF; });
    }
    function pdfjs() {
        return cargar(CDN + 'pdf.js/3.11.174/pdf.min.js', function () { return global.pdfjsLib; }).then(function () {
            global.pdfjsLib.GlobalWorkerOptions.workerSrc = CDN + 'pdf.js/3.11.174/pdf.worker.min.js';
            return global.pdfjsLib;
        });
    }
    function aBytes(blob) {
        return blob.arrayBuffer ? blob.arrayBuffer().then(function (b) { return new Uint8Array(b); })
            : new Promise(function (ok) { var r = new FileReader(); r.onload = function () { ok(new Uint8Array(r.result)); }; r.readAsArrayBuffer(blob); });
    }

    // paginas: [{blob (JPEG), ancho_mm, alto_mm}] → descarga el PDF.
    function armarPDF(paginas, nombre) {
        return jsPDF().then(function (PDF) {
            var doc = null;
            var cadena = Promise.resolve();
            paginas.forEach(function (pg) {
                cadena = cadena.then(function () { return aBytes(pg.blob); }).then(function (bytes) {
                    var w = pg.ancho_mm, h = pg.alto_mm, o = w > h ? 'l' : 'p';
                    if (!doc) doc = new PDF({orientation: o, unit: 'mm', format: [w, h], compress: true});
                    else doc.addPage([w, h], o);
                    doc.addImage(bytes, 'JPEG', 0, 0, w, h, undefined, 'FAST');
                });
            });
            return cadena.then(function () { if (doc) doc.save(nombre || 'hojas.pdf'); });
        });
    }

    // Un PDF (cada página a ~2000 px) o una imagen → lista de lienzos.
    function leerArchivo(archivo, alAvanzar) {
        if (/pdf$/i.test(archivo.type) || /\.pdf$/i.test(archivo.name || '')) {
            return Promise.all([pdfjs(), aBytes(archivo)]).then(function (r) {
                return r[0].getDocument({data: r[1]}).promise;
            }).then(function (pdf) {
                var lienzos = [], cadena = Promise.resolve();
                for (var n = 1; n <= pdf.numPages; n++) (function (n) {
                    cadena = cadena.then(function () { return pdf.getPage(n); }).then(function (pg) {
                        var v1 = pg.getViewport({scale: 1});
                        var esc = 2000 / Math.max(v1.width, v1.height);
                        var vp = pg.getViewport({scale: esc});
                        var c = document.createElement('canvas');
                        c.width = Math.round(vp.width); c.height = Math.round(vp.height);
                        var cx = c.getContext('2d', {willReadFrequently: true});
                        cx.fillStyle = '#fff'; cx.fillRect(0, 0, c.width, c.height);
                        return pg.render({canvasContext: cx, viewport: vp}).promise.then(function () {
                            lienzos.push(c);
                            if (alAvanzar) alAvanzar(n, pdf.numPages);
                        });
                    });
                })(n);
                return cadena.then(function () { return lienzos; });
            });
        }
        return new Promise(function (ok, mal) {
            var url = URL.createObjectURL(archivo), img = new Image();
            img.onload = function () {
                var k = Math.min(1, 2600 / Math.max(img.naturalWidth, img.naturalHeight));
                var c = document.createElement('canvas');
                c.width = Math.round(img.naturalWidth * k); c.height = Math.round(img.naturalHeight * k);
                c.getContext('2d', {willReadFrequently: true}).drawImage(img, 0, 0, c.width, c.height);
                URL.revokeObjectURL(url);
                ok([c]);
            };
            img.onerror = function () { URL.revokeObjectURL(url); mal(new Error('No se pudo abrir la imagen.')); };
            img.src = url;
        });
    }

    function aJPEG(lienzo, calidad) {
        return new Promise(function (ok) { lienzo.toBlob(ok, 'image/jpeg', calidad || 0.85); });
    }

    global.PEScan = {homografia: homografia, disenos: disenos, Detector: Detector, enderezar: enderezar,
                     resolucion: resolucion, mejorar: mejorar, armarPDF: armarPDF, leerArchivo: leerArchivo,
                     aJPEG: aJPEG, visores: visores, enderezarAsync: enderezarAsync, ajustarEsquina: ajustarEsquina, desdeEsquinas: desdeEsquinas};
})(window);
