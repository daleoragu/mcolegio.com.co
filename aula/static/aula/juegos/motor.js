/* Motor de la Gamificación del aula: lo común a todos los juegos.
 *
 *   Gamificacion.registrar('laberinto', {nombre, conReloj, controles, nuevaPregunta(m), actualizar(m, dt),
 *                                         dibujar(m, ctx), alTocar(m, x, y), alTecla(m, tecla)});
 *   Gamificacion.iniciar({lienzo, tipo, preguntas, segundos, ritmo, alTerminar});   ritmo: 0.6 lento · 1 normal · 1.3 rápido
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
            // ritmo: velocidad del juego (lenta 0.6, normal 1, rápida 1.3); en lenta también hay más tiempo para responder
            ritmo: Math.max(.3, Math.min(2, op.ritmo || 1)),
            segundos: Math.max(5, op.segundos || 20) / Math.max(.3, Math.min(2, op.ritmo || 1)), reloj: 0, aviso: null, avisoHasta: 0, teclas: new Set(), t: 0,
            def, tema: op.tema || '', textoFinal: op.textoFinal,
        };
        m.total = m.preguntas.length;
        Object.defineProperty(m, 'pregunta', {get: () => m.preguntas[m.indice]});
        Object.defineProperty(m, 'opciones', {get: () => (m.pregunta ? m.pregunta.opciones : [])});
        // El nivel sube cada 3 preguntas: los juegos lo usan para ir más rápido o poner más obstáculos.
        Object.defineProperty(m, 'nivel', {get: () => 1 + Math.floor(m.indice / 3)});

        // --- Tamaño: nítido en cualquier pantalla ----------------------------------
        // El juego cabe entero en la pantalla de cualquier equipo: el ancho que deja su caja y el alto
        // visible de la pantalla (en el celular, sin la barra del navegador), menos lo que va debajo.
        function ajustar() {
            const padre = lienzo.parentElement, cs = padre ? getComputedStyle(padre) : null, cl = getComputedStyle(lienzo);
            const bordes = (parseFloat(cl.borderLeftWidth) || 0) + (parseFloat(cl.borderRightWidth) || 0);
            let anchoPadre = padre ? padre.clientWidth - (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0) - bordes : W;
            // en fila (celular acostado) el enunciado va al lado del juego y le quita ancho
            const enFila = cs && cs.display.includes('flex') && cs.flexDirection === 'row';
            if (enunciado) enunciado.style.maxWidth = enFila ? '190px' : lienzo.style.width || '';
            if (enFila && enunciado && enunciado.style.display !== 'none') anchoPadre -= enunciado.offsetWidth + (parseFloat(cs.columnGap) || 0);
            const vh = window.visualViewport ? window.visualViewport.height : window.innerHeight;
            const completa = !!(document.fullscreenElement || lienzo.closest('.completa'));
            const reserva = (op.reservaAbajo ? op.reservaAbajo() : 0) + bordes;
            const arriba = completa ? Math.max(0, lienzo.getBoundingClientRect().top) : 0;
            const altoMax = completa ? vh - arriba - reserva - 10 : vh * .86 - reserva;
            const ancho = Math.max(220, Math.min(anchoPadre || W, altoMax * W / H)), ratio = window.devicePixelRatio || 1;
            lienzo.style.width = ancho + 'px'; lienzo.style.height = (ancho * H / W) + 'px';
            lienzo.width = Math.round(ancho * ratio); lienzo.height = Math.round(ancho * H / W * ratio);
            m.escala = lienzo.width / W;
        }
        // Enunciado completo encima del juego: en el celular la letra del lienzo queda muy pequeña. La página del
        // juego ya lo muestra en su leyenda (.jg-leyenda); en las demás (olimpiada) lo pone el motor.
        let enunciado = null, textoEnunciado = null;
        if (op.enunciado !== false && !document.querySelector('.jg-leyenda') && lienzo.parentElement) {
            enunciado = document.createElement('div');
            enunciado.className = 'motor-enunciado';
            enunciado.style.cssText = 'display:none;margin:0 auto 6px;padding:6px 10px;border-radius:8px;background:#05070f;color:#fff;font:600 15px/1.3 system-ui,sans-serif;text-align:left;overflow-wrap:anywhere';
            lienzo.parentElement.insertBefore(enunciado, lienzo);
        }
        function verEnunciado() {
            if (!enunciado) return;
            const p = m.pregunta, t = m.estado === 'jugando' ? ((def.textoArriba ? def.textoArriba(m) : (p && p.texto)) || '') : '';
            const mostrar = !!t && (m.enunciadoCortado || lienzo.clientWidth < 640);
            const nuevo = mostrar ? t : '';
            if (nuevo === textoEnunciado) return;
            textoEnunciado = nuevo; enunciado.textContent = nuevo; enunciado.style.display = nuevo ? '' : 'none';
            ajustar();
        }
        const reajustar = () => { ajustar(); setTimeout(ajustar, 120); };
        ajustar(); requestAnimationFrame(ajustar);
        window.addEventListener('resize', reajustar); window.addEventListener('orientationchange', reajustar);
        document.addEventListener('fullscreenchange', reajustar); document.addEventListener('webkitfullscreenchange', reajustar);
        if (window.visualViewport) window.visualViewport.addEventListener('resize', reajustar);
        m.ajustar = reajustar;
        let vivo = true;

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
        const alBajar = ev => {
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(ev.key)) ev.preventDefault();
            if (!ev.repeat) tecla(ev.key, true);
        };
        const alSubir = ev => tecla(ev.key, false);
        document.addEventListener('keydown', alBajar);
        document.addEventListener('keyup', alSubir);
        // Apagar el juego (las olimpiadas cambian de reto sin recargar la página)
        m.destruir = () => {
            vivo = false; soltarPalanca(); quitarPalanca(); quitarZona(); if (enunciado) enunciado.remove(); document.removeEventListener('keydown', alBajar); document.removeEventListener('keyup', alSubir);
            window.removeEventListener('resize', reajustar); window.removeEventListener('orientationchange', reajustar);
            document.removeEventListener('fullscreenchange', reajustar); document.removeEventListener('webkitfullscreenchange', reajustar);
            if (window.visualViewport) window.visualViewport.removeEventListener('resize', reajustar);
        };
        function punto(ev) {
            const r = lienzo.getBoundingClientRect();
            return [(ev.clientX - r.left) * W / r.width, (ev.clientY - r.top) * H / r.height];
        }
        // Con el dedo: en los juegos que se mueven con flechas (def.joystick: '8' libre, '4' sin diagonales,
        // 'h' solo a los lados) un toque en cualquier parte del juego pone ahí una palanca: arrastrar mueve
        // y soltar se detiene. Un toque corto, sin arrastrar, sigue siendo un toque normal (alTocar).
        const conPalanca = !!def.joystick;
        const zonaDedo = conPalanca ? (op.zonaTactil || lienzo.closest('.jg-zona, #ol-zona, #ol') || lienzo.parentElement || lienzo) : lienzo;
        let palanca = null, perilla = null;
        function verPalanca(x0, y0, x, y) {
            if (!perilla) {
                perilla = document.createElement('div');
                perilla.innerHTML = '<div></div>';
                perilla.style.cssText = 'position:fixed;width:110px;height:110px;margin:-55px 0 0 -55px;border-radius:50%;border:3px solid rgba(255,255,255,.55);background:rgba(0,0,0,.18);pointer-events:none;z-index:2147483000';
                perilla.firstChild.style.cssText = 'position:absolute;left:50%;top:50%;width:50px;height:50px;margin:-25px 0 0 -25px;border-radius:50%;background:rgba(255,255,255,.75);box-shadow:0 2px 8px rgba(0,0,0,.4)';
                (document.fullscreenElement || document.webkitFullscreenElement || document.body).appendChild(perilla);
            }
            perilla.style.left = x0 + 'px'; perilla.style.top = y0 + 'px';
            perilla.firstChild.style.transform = `translate(${x - x0}px,${y - y0}px)`;
        }
        function quitarPalanca() { if (perilla) { perilla.remove(); perilla = null; } }
        function direcciones(dx, dy) {
            const d = Math.hypot(dx, dy), modo = def.joystick, r = new Set();
            if (d < 14) return r;
            if (modo === 'h') { if (Math.abs(dx) > 10) r.add(dx < 0 ? 'izquierda' : 'derecha'); return r; }
            if (modo === '4') { if (Math.abs(dx) > Math.abs(dy)) r.add(dx < 0 ? 'izquierda' : 'derecha'); else r.add(dy < 0 ? 'arriba' : 'abajo'); return r; }
            if (Math.abs(dx) > d * .38) r.add(dx < 0 ? 'izquierda' : 'derecha');
            if (Math.abs(dy) > d * .38) r.add(dy < 0 ? 'arriba' : 'abajo');
            return r;
        }
        function moverPalanca(ev) {
            const p = palanca, R = 50;
            let dx = ev.clientX - p.x0, dy = ev.clientY - p.y0;
            const d = Math.hypot(dx, dy);
            if (d > 10) p.arrastro = true;
            if (d > R) { dx *= R / d; dy *= R / d; }
            verPalanca(p.x0, p.y0, p.x0 + dx, p.y0 + dy);
            const nuevas = direcciones(dx, dy);
            p.dirs.forEach(t => { if (!nuevas.has(t)) m.soltar(t); });
            nuevas.forEach(t => { if (!p.dirs.has(t)) m.pulsar(t); });
            p.dirs = nuevas;
        }
        function soltarPalanca() { if (!palanca) return; palanca.dirs.forEach(t => m.soltar(t)); palanca = null; quitarPalanca(); }
        // La palanca también sale tocando fuera del lienzo (el borde negro, la pantalla completa). Solo mientras
        // este juego esté vivo: al cambiar de juego (olimpiada) se quita, para no robarles los toques a los
        // juegos de escoger fichas (conejos, ranas, piezas...). Nunca sobre otro lienzo ni sobre botones.
        const vivoYMio = () => vivo && lienzo.isConnected;
        const zonaAbajo = ev => {
            if (!vivoYMio() || ev.pointerType === 'mouse' || ev.target === lienzo || ev.target.closest('button, a, input, select, textarea, label, canvas, .ins-velo')) return;
            ev.preventDefault();
            if (m.estado === 'inicio') return empezar();
            if (palanca) return;
            palanca = {id: ev.pointerId, x0: ev.clientX, y0: ev.clientY, dirs: new Set(), arrastro: true};
            try { zonaDedo.setPointerCapture(ev.pointerId); } catch (e) { /* sin captura */ }
            verPalanca(ev.clientX, ev.clientY, ev.clientX, ev.clientY);
        };
        const zonaMueve = ev => { if (palanca && palanca.id === ev.pointerId && ev.target !== lienzo) moverPalanca(ev); };
        const zonaArriba = ev => { if (palanca && palanca.id === ev.pointerId) soltarPalanca(); };
        const tactilAntes = zonaDedo.style.touchAction;
        function quitarZona() {
            if (!conPalanca || zonaDedo === lienzo) return;
            zonaDedo.removeEventListener('pointerdown', zonaAbajo); zonaDedo.removeEventListener('pointermove', zonaMueve);
            zonaDedo.removeEventListener('pointerup', zonaArriba); zonaDedo.removeEventListener('pointercancel', zonaArriba);
            zonaDedo.style.touchAction = tactilAntes;
        }
        if (conPalanca && zonaDedo !== lienzo) {
            zonaDedo.style.touchAction = 'none';
            zonaDedo.addEventListener('pointerdown', zonaAbajo);
            zonaDedo.addEventListener('pointermove', zonaMueve);
            zonaDedo.addEventListener('pointerup', zonaArriba); zonaDedo.addEventListener('pointercancel', zonaArriba);
        }
        lienzo.addEventListener('pointerdown', ev => {
            ev.preventDefault();
            if (m.estado === 'inicio') return empezar();
            const [x, y] = punto(ev);
            try { lienzo.setPointerCapture(ev.pointerId); } catch (e) { /* sin captura */ }
            m.puntero = {x, y};
            if (conPalanca && ev.pointerType !== 'mouse') {
                if (palanca) return;
                palanca = {id: ev.pointerId, x0: ev.clientX, y0: ev.clientY, dirs: new Set(), arrastro: false, x, y};
                verPalanca(ev.clientX, ev.clientY, ev.clientX, ev.clientY);
                return;
            }
            if (m.estado === 'jugando' && def.alTocar) def.alTocar(m, x, y);
        });
        lienzo.addEventListener('pointermove', ev => {
            if (palanca && palanca.id === ev.pointerId) { moverPalanca(ev); return; }
            const [x, y] = punto(ev); m.puntero = {x, y};
            if (m.estado === 'jugando' && def.alArrastrar && ev.buttons) def.alArrastrar(m, x, y);
        });
        // Soltar (el arco de la oveja se jala y se suelta)
        ['pointerup', 'pointercancel'].forEach(e => lienzo.addEventListener(e, ev => {
            if (palanca && palanca.id === ev.pointerId) {
                const toque = !palanca.arrastro && e === 'pointerup' ? palanca : null;
                soltarPalanca();
                if (toque && m.estado === 'jugando' && def.alTocar) def.alTocar(m, toque.x, toque.y);
                return;
            }
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
                    def.actualizar(m, dt * m.ritmo);
                } else if (m.estado === 'pausa' && def.actualizarEnPausa) {
                    def.actualizarEnPausa(m, dt * m.ritmo);
                }
            }
            dibujar(); verEnunciado();
            if (vivo) requestAnimationFrame(cuadro);
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
                // La letra se achica hasta que quepa todo el enunciado (de 9 a 6 puntos); si aun así no cabe,
                // el enunciado completo también se ve encima del juego (ver «enunciado» abajo).
                let tam = 9, lineas = [];
                for (tam = 9; tam >= 6; tam--) {
                    ctx.font = `${tam}px ${FUENTE}`; lineas = partir(ctx, arriba, W - 130);
                    if (lineas.length * (tam + 4) <= 44) break;
                }
                tam = Math.max(6, tam); const caben = Math.floor(44 / (tam + 4));
                if (lineas.length > caben) { lineas = lineas.slice(0, caben); lineas[caben - 1] += '…'; }
                lineas.forEach((l, i) => m.texto(l, 8, 6 + i * (tam + 4), {tam}));
                m.enunciadoCortado = lineas.length && lineas[lineas.length - 1].endsWith('…');
            } else { m.enunciadoCortado = false; }
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
