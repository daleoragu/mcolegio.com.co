/* Motor de la Gamificación del aula: lo común a todos los juegos.
 *
 *   Gamificacion.registrar('laberinto', {nombre, conReloj, controles, nuevaPregunta(m), actualizar(m, dt),
 *                                         dibujar(m, ctx), alTocar(m, x, y), alTecla(m, tecla)});
 *   Gamificacion.iniciar({lienzo, tipo, preguntas, segundos, alTerminar});
 *
 * Pantalla lógica de 480 × 360: arriba (0–50) la pregunta, abajo (310–360) las
 * opciones A–D, y en medio (50–310) el juego. Cada pregunta se responde una vez:
 * bien suma puntos; mal (o se acabó el tiempo) cuenta como error y quita una vida.
 * Los peligros del juego (virus, balas, caídas) quitan una vida y repiten la pregunta.
 */
(function () {
    'use strict';
    const W = 480, H = 360, ARRIBA = 50, ABAJO = 310;
    // Hasta 8 opciones (A–H), como en PuntoExacto. Cada juego dice cuántas caben (maxOpciones, 4 si no dice).
    const LETRAS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
    const COLORES = ['#ff5d5d', '#4dabf7', '#ffd43b', '#69db7c', '#da77f2', '#ff922b', '#20c997', '#f783ac'];
    const FUENTE = '"Press Start 2P", ui-monospace, monospace';
    const JUEGOS = {};

    let audio = null;
    function sonido(frec, dur, tipo) {
        try {
            audio = audio || new (window.AudioContext || window.webkitAudioContext)();
            const o = audio.createOscillator(), g = audio.createGain();
            o.type = tipo || 'square'; o.frequency.value = frec; g.gain.value = 0.06;
            o.connect(g); g.connect(audio.destination);
            o.start(); g.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + dur); o.stop(audio.currentTime + dur);
        } catch (e) { /* sin sonido */ }
    }
    const SONIDOS = {
        bien: () => { sonido(660, .09); setTimeout(() => sonido(990, .14), 90); },
        mal: () => { sonido(180, .3, 'sawtooth'); },
        vida: () => { sonido(240, .12); setTimeout(() => sonido(150, .25), 110); },
        toque: () => sonido(520, .05),
        fin: () => { [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => sonido(f, .15), i * 120)); },
    };

    function registrar(tipo, def) { JUEGOS[tipo] = def; }

    function partir(ctx, texto, ancho) {
        const palabras = String(texto || '').split(/\s+/), lineas = [];
        let linea = '';
        palabras.forEach(p => {
            const prueba = linea ? linea + ' ' + p : p;
            if (ctx.measureText(prueba).width > ancho && linea) { lineas.push(linea); linea = p; } else { linea = prueba; }
        });
        if (linea) lineas.push(linea);
        return lineas;
    }

    /* Si la pregunta trae más opciones de las que caben en el juego, quedan la correcta y otras al azar.
     * Cada opción guarda su número original (_k): con ese se califica en el servidor. */
    function recortar(opciones, max) {
        const ops = opciones.map((o, k) => Object.assign({}, o, {_k: k}));
        if (ops.length <= max) return ops;
        const buena = ops.filter(o => o.correcta).slice(0, 1), malas = ops.filter(o => !o.correcta).sort(() => Math.random() - .5);
        return buena.concat(malas.slice(0, max - buena.length)).sort((a, b) => a._k - b._k);
    }

    function iniciar(op) {
        const def = JUEGOS[op.tipo];
        const lienzo = op.lienzo, ctx = lienzo.getContext('2d');
        const m = {
            W, H, ARRIBA, ABAJO, LETRAS, COLORES, FUENTE, ctx, sonidos: SONIDOS, partir: (t, a) => partir(ctx, t, a),
            preguntas: op.preguntas.filter(p => (p.opciones || []).length >= 2).map(p => Object.assign({}, p, {opciones: recortar(p.opciones, def.maxOpciones || 4)})),
            indice: 0, vidas: 3, puntaje: 0, aciertos: 0, respuestas: [], estado: 'inicio',
            // Dos jugadores en el mismo equipo: se turnan las preguntas y cada uno lleva su marcador.
            jugadores: op.jugadores === 2 ? 2 : 1, turno: 0, marcador: [0, 0],
            opciones_juego: {minutos: op.minutos || 3},
            nombres: op.nombres || (op.jugadores === 2 ? ['JUGADOR 1', 'JUGADOR 2'] : ['USTED', 'COMPU']),
            segundos: Math.max(5, op.segundos || 20), reloj: 0, aviso: null, avisoHasta: 0, teclas: new Set(), t: 0,
            def, tema: op.tema || '', textoFinal: op.textoFinal,
        };
        m.total = m.preguntas.length;
        Object.defineProperty(m, 'pregunta', {get: () => m.preguntas[m.indice]});
        Object.defineProperty(m, 'opciones', {get: () => (m.pregunta ? m.pregunta.opciones : [])});
        // El nivel sube cada 3 preguntas: los juegos lo usan para ir más rápido o poner más obstáculos.
        Object.defineProperty(m, 'nivel', {get: () => 1 + Math.floor(m.indice / 3)});

        // --- Tamaño: nítido en cualquier pantalla ----------------------------------
        function ajustar() {
            const ancho = lienzo.clientWidth || W, ratio = window.devicePixelRatio || 1;
            lienzo.width = Math.round(ancho * ratio); lienzo.height = Math.round(ancho * H / W * ratio);
            lienzo.style.height = (ancho * H / W) + 'px';
            m.escala = lienzo.width / W;
        }
        ajustar(); window.addEventListener('resize', ajustar);

        // --- Ayudas de dibujo ------------------------------------------------------------
        m.texto = function (t, x, y, o) {
            o = o || {};
            ctx.font = `${o.tam || 10}px ${FUENTE}`; ctx.fillStyle = o.color || '#fff';
            ctx.textAlign = o.alinear || 'left'; ctx.textBaseline = o.base || 'top';
            if (o.sombra !== false) { ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fillText(t, x + 1, y + 1); ctx.fillStyle = o.color || '#fff'; }
            ctx.fillText(t, x, y);
        };
        m.etiqueta = function (k, x, y, r) {
            r = r || 9;
            ctx.fillStyle = COLORES[k]; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.stroke();
            m.texto(LETRAS[k], x, y + 1, {tam: Math.round(r * 1.05), color: '#111', alinear: 'center', base: 'middle', sombra: false});
        };
        m.aviso = function (texto, color, seg) { m.avisoTexto = texto; m.avisoColor = color; m.avisoHasta = m.t + (seg || 1); };

        // Cada pregunta nueva se le avisa a la página (para la barra lateral con las opciones).
        function nueva(repetir) {
            def.nuevaPregunta(m, repetir);
            if (op.alCambiarPregunta && m.estado !== 'fin') op.alCambiarPregunta(m);
        }

        // --- Reglas ------------------------------------------------------------------
        let enPausa = false, terminado = false, esperaHasta = 0;
        function siguiente() {
            const nivelAntes = m.nivel;
            m.indice += 1;
            if (def.finPropio && m.indice >= m.total) {
                // Los juegos que terminan solos (penaltis, tenis…) vuelven a barajar las preguntas.
                m.preguntas.sort(() => Math.random() - .5); m.indice = 0; m.vuelta = (m.vuelta || 0) + 1;
            }
            if (m.indice >= m.total || m.vidas <= 0) return terminar();
            m.reloj = tiempoDeLaPregunta();
            if (m.nivel > nivelAntes) { m.aviso('¡NIVEL ' + m.nivel + '!', '#ffd43b', 1.2); sonido(880, .1); setTimeout(() => sonido(1175, .2), 100); }
            nueva();
        }
        // Con cada nivel hay un poco menos de tiempo (nunca menos de la mitad ni de 5 s).
        function tiempoDeLaPregunta() { return Math.max(5, m.segundos * Math.max(.5, 1 - (m.nivel - 1) * .1)); }
        m.tiempoDeLaPregunta = tiempoDeLaPregunta;
        m.responder = function (k) {
            if (m.estado !== 'jugando' || m.t < esperaHasta) return;
            const p = m.pregunta, bien = k !== null && k !== undefined && p.opciones[k] && p.opciones[k].correcta;
            const original = k === null || k === undefined || !p.opciones[k] ? null : (p.opciones[k]._k !== undefined ? p.opciones[k]._k : k);
            m.respuestas.push({i: p.i !== undefined ? p.i : m.indice, opcion: original});
            if (def.alResponder) def.alResponder(m, bien, k);
            if (bien) {
                m.aciertos += 1; m.puntaje += 100 + (def.conReloj ? Math.round(m.reloj * 5) : 0);
                SONIDOS.bien(); m.aviso('¡CORRECTO!', '#69db7c', .9);
            } else {
                m.vidas -= def.sinVidas ? 0 : 1; SONIDOS.mal();
                const correcta = p.opciones.findIndex(o => o.correcta);
                m.aviso(k === null ? '¡SE ACABÓ EL TIEMPO!' : 'ERA LA ' + LETRAS[correcta], '#ff6b6b', 1.3);
            }
            if (def.avisoPropio) m.avisoHasta = 0;
            esperaHasta = m.t + (bien ? .9 : 1.3);
            m.estado = 'pausa';
            setTimeout(() => { if (!terminado) { m.estado = 'jugando'; siguiente(); } }, (bien ? 900 : 1300));
        };
        m.perderVida = function (motivo) {
            if (m.estado !== 'jugando') return;
            m.vidas -= 1; SONIDOS.vida(); m.aviso(motivo || '¡AY!', '#ff922b', 1.1);
            if (m.vidas <= 0) {
                // Las preguntas que faltaban quedan sin responder.
                for (let i = m.indice; i < m.total; i++) m.respuestas.push({i: m.preguntas[i].i !== undefined ? m.preguntas[i].i : i, opcion: null});
                m.estado = 'pausa'; setTimeout(terminar, 1100); return;
            }
            m.estado = 'pausa';
            setTimeout(() => { if (!terminado) { m.estado = 'jugando'; nueva(true); } }, 1100);
        };
        function terminar() {
            if (terminado) return;
            terminado = true; m.estado = 'fin'; SONIDOS.fin();
            if (op.alTerminar) op.alTerminar({respuestas: m.respuestas, puntaje: m.puntaje, aciertos: m.aciertos, total: m.total});
        }
        m.terminar = terminar;

        function empezar() {
            if (m.estado !== 'inicio') return;
            if (!m.total) { m.estado = 'fin'; return; }
            m.estado = 'jugando'; m.reloj = tiempoDeLaPregunta(); nueva(); SONIDOS.toque();
        }

        // --- Entrada ------------------------------------------------------------------
        const MAPA = {ArrowUp: 'arriba', ArrowDown: 'abajo', ArrowLeft: 'izquierda', ArrowRight: 'derecha', w: 'arriba', s: 'abajo',
                      a: 'izquierda', d: 'derecha', ' ': 'disparo', Enter: 'aceptar'};
        function tecla(t, abajo) {
            const nombre = MAPA[t] || MAPA[t.toLowerCase && t.toLowerCase()] || t;
            if (abajo) {
                m.teclas.add(nombre);
                if (m.estado === 'inicio' && (nombre === 'aceptar' || nombre === 'disparo')) return empezar();
                if (nombre === 'p' || nombre === 'P' || nombre === 'Escape') { enPausa = !enPausa; return; }
                if (m.estado === 'jugando' && def.alTecla) def.alTecla(m, nombre, t);
            } else { m.teclas.delete(nombre); }
        }
        m.pulsar = (nombre) => tecla(nombre, true);
        m.soltar = (nombre) => tecla(nombre, false);
        document.addEventListener('keydown', ev => {
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(ev.key)) ev.preventDefault();
            if (!ev.repeat) tecla(ev.key, true);
        });
        document.addEventListener('keyup', ev => tecla(ev.key, false));
        function punto(ev) {
            const r = lienzo.getBoundingClientRect();
            return [(ev.clientX - r.left) * W / r.width, (ev.clientY - r.top) * H / r.height];
        }
        lienzo.addEventListener('pointerdown', ev => {
            ev.preventDefault();
            if (m.estado === 'inicio') return empezar();
            const [x, y] = punto(ev);
            try { lienzo.setPointerCapture(ev.pointerId); } catch (e) { /* sin captura */ }
            m.puntero = {x, y};
            if (m.estado === 'jugando' && def.alTocar) def.alTocar(m, x, y);
        });
        lienzo.addEventListener('pointermove', ev => {
            const [x, y] = punto(ev); m.puntero = {x, y};
            if (m.estado === 'jugando' && def.alArrastrar && ev.buttons) def.alArrastrar(m, x, y);
        });
        // Soltar (el arco de la oveja se jala y se suelta)
        ['pointerup', 'pointercancel'].forEach(e => lienzo.addEventListener(e, ev => {
            const [x, y] = punto(ev);
            if (m.estado === 'jugando' && def.alSoltar) def.alSoltar(m, x, y);
        }));

        // --- Ciclo ----------------------------------------------------------------------
        let antes = performance.now();
        function cuadro(ahora) {
            const dt = Math.min(0.05, (ahora - antes) / 1000); antes = ahora;
            if (!enPausa) {
                m.t += dt;
                if (m.estado === 'jugando') {
                    if (def.conReloj) {
                        m.reloj -= dt;
                        if (m.reloj <= 0) { m.reloj = 0; if (def.alAcabarReloj) def.alAcabarReloj(m); else m.responder(null); }
                    }
                    def.actualizar(m, dt);
                } else if (m.estado === 'pausa' && def.actualizarEnPausa) {
                    def.actualizarEnPausa(m, dt);
                }
            }
            dibujar();
            requestAnimationFrame(cuadro);
        }

        function dibujar() {
            ctx.setTransform(m.escala, 0, 0, m.escala, 0, 0);
            ctx.imageSmoothingEnabled = false;
            ctx.fillStyle = def.fondo || '#0b1021'; ctx.fillRect(0, 0, W, H);
            if (m.estado === 'inicio') return portada();
            if (m.estado === 'fin') return final();
            ctx.save(); ctx.beginPath(); ctx.rect(0, ARRIBA, W, ABAJO - ARRIBA); ctx.clip();
            def.dibujar(m, ctx);
            ctx.restore();
            hud();
            if (m.avisoHasta > m.t) {
                ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(0, 160, W, 40);
                m.texto(m.avisoTexto, W / 2, 173, {tam: 14, color: m.avisoColor, alinear: 'center'});
            }
            if (enPausa) {
                ctx.fillStyle = 'rgba(0,0,0,.7)'; ctx.fillRect(0, 0, W, H);
                m.texto('PAUSA', W / 2, 160, {tam: 18, alinear: 'center'});
                m.texto('Presione P para seguir', W / 2, 195, {tam: 8, alinear: 'center', color: '#ccc'});
            }
        }

        function hud() {
            ctx.fillStyle = '#05070f'; ctx.fillRect(0, 0, W, ARRIBA); ctx.fillRect(0, ABAJO, W, H - ABAJO);
            ctx.fillStyle = '#ffd43b'; ctx.fillRect(0, ARRIBA - 2, W, 2); ctx.fillRect(0, ABAJO, W, 2);
            const p = m.pregunta;
            const arriba = def.textoArriba ? def.textoArriba(m) : (p && p.texto);
            if (arriba) {
                ctx.font = `9px ${FUENTE}`;
                const lineas = partir(ctx, arriba, W - 130).slice(0, 3);
                lineas.forEach((l, i) => m.texto(l, 8, 8 + i * 13, {tam: 9}));
            }
            m.texto(`NIV ${m.nivel} · ${Math.min(m.indice + 1, m.total)}/${m.total}`, W - 8, 7, {tam: 8, alinear: 'right', color: '#aaa'});
            m.texto(String(m.puntaje).padStart(5, '0'), W - 8, 20, {tam: 9, alinear: 'right', color: '#ffd43b'});
            if (!def.sinVidas) m.texto('♥'.repeat(Math.max(0, m.vidas)), W - 8, 34, {tam: 9, alinear: 'right', color: '#ff5d5d'});
            if (def.marcador) m.texto(`${m.nombres[m.turno]} RESPONDE`, W - 8, 34, {tam: 7, alinear: 'right', color: m.turno ? '#4dabf7' : '#ff922b'});
            if (def.conReloj) {
                const frac = Math.max(0, m.reloj / (def.relojTotal ? def.relojTotal(m) : tiempoDeLaPregunta()));
                ctx.fillStyle = frac < .25 ? '#ff5d5d' : '#69db7c'; ctx.fillRect(0, ARRIBA - 6, W * frac, 4);
            }
            // Opciones abajo, en dos columnas
            if (def.abajo) return def.abajo(m, ctx);
            const ops = p ? p.opciones : [], col = ops.length > 4 ? 4 : 2, tam = col === 4 ? 6 : 8;
            ops.forEach((o, k) => {
                const x = 8 + (k % col) * (W / col), y = ABAJO + 8 + Math.floor(k / col) * 22;
                m.etiqueta(k, x + 8, y + 7, 8);
                ctx.font = `${tam}px ${FUENTE}`;
                let t = o.texto; while (ctx.measureText(t).width > W / col - 30 && t.length > 3) t = t.slice(0, -2);
                if (t !== o.texto) t = t.slice(0, -1) + '…';
                m.texto(t, x + 20, y + 3 + (8 - tam) / 2, {tam});
            });
        }

        function portada() {
            m.texto(def.nombre.toUpperCase(), W / 2, 70, {tam: 16, color: '#ffd43b', alinear: 'center'});
            ctx.font = `8px ${FUENTE}`;
            partir(ctx, def.instrucciones || '', W - 60).forEach((l, i) => m.texto(l, W / 2, 120 + i * 16, {tam: 8, alinear: 'center', color: '#ddd'}));
            if (!m.total) { m.texto('Este juego no tiene preguntas', W / 2, 260, {tam: 9, alinear: 'center', color: '#ff6b6b'}); return; }
            m.texto(m.jugadores === 2 ? `2 JUGADORES · ${m.total} preguntas` : `${m.total} preguntas`, W / 2, 245, {tam: 9, alinear: 'center', color: '#aaa'});
            if (Math.floor(performance.now() / 500) % 2 === 0) m.texto('TOQUE O PRESIONE ENTER', W / 2, 285, {tam: 10, alinear: 'center'});
        }

        function final() {
            if (def.final) return def.final(m, ctx);
            m.texto(m.vidas > 0 ? '¡MISIÓN CUMPLIDA!' : 'FIN DEL JUEGO', W / 2, 90, {tam: 16, color: m.vidas > 0 ? '#69db7c' : '#ff6b6b', alinear: 'center'});
            m.texto(`ACIERTOS: ${m.aciertos} de ${m.total}`, W / 2, 150, {tam: 11, alinear: 'center'});
            m.texto(`PUNTAJE: ${m.puntaje}`, W / 2, 180, {tam: 11, alinear: 'center', color: '#ffd43b'});
            if (op.textoFinal) m.texto(op.textoFinal(), W / 2, 225, {tam: 9, alinear: 'center', color: '#aaa'});
        }

        requestAnimationFrame(cuadro);
        return m;
    }

    /* El ícono de la opción k para la barra lateral: el del juego (tanque, bandera…) o la letra con su color. */
    function icono(tipo, ctx, k, tam) {
        ctx.clearRect(0, 0, tam, tam);
        const def = JUEGOS[tipo];
        if (def && def.icono) { def.icono(ctx, k, tam); return; }
        ctx.fillStyle = COLORES[k]; ctx.beginPath(); ctx.arc(tam / 2, tam / 2, tam * .42, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#111'; ctx.font = `bold ${Math.round(tam * .5)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(LETRAS[k], tam / 2, tam / 2 + 1);
    }

    window.Gamificacion = {registrar, iniciar, icono, LETRAS, COLORES, W, H, ARRIBA, ABAJO, juego: tipo => JUEGOS[tipo]};
})();
