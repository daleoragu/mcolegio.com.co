/* Olimpiada de matemáticas (Eventos de Mi Salón Virtual).
 * Bloques contra reloj con descanso visual obligatorio entre bloques. Cada reto superado = 1 punto.
 * Cada `cada` puntos: pregunta de competencia (la califica el servidor); bien respondida resta `bono` segundos.
 * Lo que pasa se guarda en el equipo y se manda al servidor en orden (si no hay internet, se manda después). */
(function () {
    'use strict';
    const D = JSON.parse(document.getElementById('ol-datos').textContent), U = window.OL_URLS, C = D.config;
    const $ = s => document.querySelector(s);
    // El grupo del estudiante (nombre, grados y dificultad los pone el organizador)
    const GR = D.grupo || {nombre: '', grados: '', nivel: 0, gmax: 11};
    const CI = GR.nivel || 0, PEQUES = GR.gmax <= 2, PRIMARIA = GR.gmax <= 5;
    const CAT_COLOR = {Euclides: '#1971c2', Newton: '#e8590c', Bernoulli: '#2f9e44'};
    const NOMBRE = Object.fromEntries(D.juegos.map(j => [j[0], j[1]]));
    const MOTOR = D.motor || {};     // reto → juego arcade con que se juega
    const CLAVE = `mc-evento:${D.usuario}:${D.evento}${D.prueba ? ':prueba:' + D.ciclo : ''}`;
    const nuevo = () => ({fase: 'portada', bloque: 1, restante: C.minutos * 60, activo: 0, ultimoPunto: 0, seq: 0, cola: [], puntos: 0, bonos: 0,
                          hechas: 0, debe: 0, usados: {}, reto: null, descansoHasta: 0});
    let E;
    try { E = Object.assign(nuevo(), JSON.parse(localStorage.getItem(CLAVE) || 'null') || {}); } catch (e) { E = nuevo(); }
    // El servidor manda (puntos y preguntas que ya cuenta)
    if (D.servidor) {
        E.puntos = Math.max(E.puntos, D.servidor.puntos); E.bonos = Math.max(E.bonos, D.servidor.bonos);
        E.hechas = Math.max(E.hechas, D.servidor.preguntas); E.seq = Math.max(E.seq, D.servidor.secuencia);
        if (D.servidor.terminada) E.fase = 'fin';
    }
    const guardar = () => { try { localStorage.setItem(CLAVE, JSON.stringify(E)); } catch (e) { /* sin almacenamiento */ } };
    // Al salir, recargar o bloquear el celular, queda guardado el reloj del bloque
    window.addEventListener('pagehide', guardar);
    document.addEventListener('visibilitychange', () => { if (document.hidden) guardar(); });

    // --- Envío al servidor ------------------------------------------------------------
    // Toda petición tiene tiempo límite: con internet lento no se queda esperando para siempre.
    function pedir(url, op, ms) {
        const ctl = window.AbortController ? new AbortController() : null;
        const t = setTimeout(() => ctl && ctl.abort(), ms || 10000);
        return fetch(url, Object.assign({credentials: 'same-origin'}, op || {}, ctl ? {signal: ctl.signal} : {})).finally(() => clearTimeout(t));
    }
    let enviando = false;
    function encolar(ev) { E.seq += 1; E.cola.push(Object.assign({seq: E.seq}, ev)); guardar(); enviar(); }
    async function enviar() {
        if (D.prueba || enviando || !E.cola.length) return;
        enviando = true;
        try {
            const r = await pedir(U.registro, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': U.csrf},
                                               body: JSON.stringify({eventos: E.cola})});
            const j = await r.json();
            if (j.ok) { E.cola = E.cola.filter(e => e.seq > (j.secuencia || 0)); if (j.puntos !== undefined) { E.puntos = Math.max(E.puntos, j.puntos); E.debe = j.debe; E.tiempoServidor = j.tiempo; } guardar(); }
        } catch (e) { /* sin internet: se reintenta */ }
        enviando = false; pintarCab();
    }
    setInterval(enviar, 10000); window.addEventListener('online', enviar);

    // --- Cabecera y reloj ------------------------------------------------------------------
    const mmss = s => { s = Math.max(0, Math.round(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
    const efectivo = () => Math.max(0, E.ultimoPunto - C.bono * E.bonos);
    function pintarCab() {
        $('#ol-ciclo').textContent = `${GR.nombre} (${GR.grados}) · ${C.bloques} bloque(s) de ${C.minutos} min`;
        $('#ol-bloque').textContent = `${E.bloque}/${C.bloques}`;
        $('#ol-tiempo').textContent = mmss(E.restante);
        $('#ol-reloj').classList.toggle('poco', E.restante < 60);
        $('#ol-puntos').textContent = E.puntos; $('#ol-bonos').textContent = E.bonos; $('#ol-efectivo').textContent = mmss(efectivo());
    }
    let antes = performance.now();
    setInterval(() => {
        const ahora = performance.now(), dt = (ahora - antes) / 1000; antes = ahora;
        if (E.fase === 'jugando') {
            E.restante -= dt; E.activo += dt;
            if (E.restante <= 0) finDeBloque();
            pintarCab();
            if (Math.random() < .1) guardar();
        } else if (E.fase === 'descanso') pintarDescanso();
    }, 250);

    // --- Retos ------------------------------------------------------------------------------
    let actual = null, motor = null;
    function limpiarZona() { if (motor && motor.destruir) motor.destruir(); motor = null; actual = null; $('#ol-zona').innerHTML = ''; const bp = $('#ol-pausa'); if (bp) bp.hidden = true; }
    function rango(id) {
        // dificultad escogida por el organizador para ese juego; si no, la del ciclo del estudiante
        const ci = {facil: 0, media: 1, dificil: 2}[(D.dificultad || {})[id]] ?? CI;
        if (id === 'hanoi') return [ci, ci];          // 3, 4 o 5 discos
        const def = Logica.juego(id), total = def ? def.total(D.niveles[id] || {}) : 30;
        const a = Math.floor(total * ci / 3), b = Math.max(a, Math.floor(total * (ci + 1) / 3) - 1);
        return [a, b];
    }
    function escogerReto() {
        const ids = D.juegos.map(j => j[0]), previo = E.reto && E.reto.juego;
        const opciones = ids.length > 1 ? ids.filter(i => i !== previo) : ids;
        const juego = opciones[Math.floor(Math.random() * opciones.length)];
        let nivel = 0;
        if (!MOTOR[juego]) {
            const [a, b] = rango(juego), usados = E.usados[juego] || [];
            const libres = []; for (let k = a; k <= b; k++) if (!usados.includes(k)) libres.push(k);
            const lista = libres.length ? libres : Array.from({length: b - a + 1}, (_, k) => a + k);
            nivel = lista[Math.floor(Math.random() * lista.length)];
        }
        E.reto = {juego, nivel}; guardar();
    }
    let fallos = 0;
    function montarReto() {
        try { montarRetoSinCuidar(); fallos = 0; }
        catch (err) {
            // Un reto que no carga no deja la olimpiada en blanco: se cambia por otro
            if (window.console) console.error(err);
            E.reto = null; guardar(); fallos += 1;
            if (fallos < 6) { aviso('Ese reto no cargó: va otro.'); setTimeout(siguienteReto, 700); }
            else atascado();
        }
    }
    function montarRetoSinCuidar() {
        limpiarZona();
        if (!E.reto) escogerReto();
        const {juego, nivel} = E.reto, zona = $('#ol-zona');
        $('#ol-reto-nombre').textContent = 'Reto: ' + (NOMBRE[juego] || juego);
        const api = {
            movimiento() {}, sonido: Logica.sonido, compacto: true, ritmo: (D.ritmo || {})[juego] || 1,
            gano() { if (actual === api) superado(); },
            perdio() { if (actual === api) { aviso('¡Casi! Va otro reto.'); setTimeout(siguienteReto, 1200); } },
            aviso,
        };
        actual = api;
        if (MOTOR[juego]) {
            // Juego arcade: con operaciones según el grupo, o con las preguntas del juego propio del docente
            const propio = (D.propios || {})[juego], tipo = MOTOR[juego], def = Gamificacion.juego(tipo) || {};
            // Juego propio: sus preguntas · si el organizador lo pidió: preguntas del banco del grado · si no: operaciones
            const delBanco = D.arcade_preguntas && D.arcade_preguntas.length >= 3
                ? D.arcade_preguntas.slice().sort(() => Math.random() - .5).slice(0, 3).map((q, i) => Object.assign({i}, q)) : null;
            const preguntas = propio ? propio.preguntas.slice().sort(() => Math.random() - .5).slice(0, 3) : (delBanco || operaciones(3));
            $('#ol-reto-detalle').textContent = `Responda bien ${Math.min(2, preguntas.length)} de ${preguntas.length}.`;
            $('#ol-instrucciones').textContent = def.instrucciones || '';
            const cv = document.createElement('canvas'); cv.className = 'ol-motor'; zona.appendChild(cv);
            const bPausa = $('#ol-pausa');
            bPausa.hidden = false; bPausa.textContent = '⏸ Pausa';
            bPausa.onclick = () => { if (!motor) return; if (motor.enPausa) motor.seguir(); else if (!motor.pausar()) aviso('La pausa es mientras se responde una pregunta.'); };
            motor = Gamificacion.iniciar({lienzo: cv, tipo, preguntas, segundos: 20, minutos: 2, jugadores: 1,
                alPausar: pausado => { bPausa.textContent = pausado ? '▶ Seguir' : '⏸ Pausa'; if (pausado) aviso('Pausa: resuelva en papel. El reloj de la olimpiada sigue corriendo.'); }, ritmo: (D.ritmo || {})[juego] || 1, tema: propio ? propio.titulo : '',
                alTerminar: r => { if (actual !== api) return; const meta = Math.min(2, preguntas.length); if (r.aciertos >= meta) setTimeout(superado, 600); else { aviso(`${r.aciertos} de ${preguntas.length}: va otro reto.`); setTimeout(siguienteReto, 1500); } }});
            // En el celular los que se mueven usan la palanca que aparece donde se pone el dedo (motor.js)
            ['#ol-girar', '#ol-voltear', '#ol-deshacer'].forEach(s => { $(s).hidden = true; });
            return;
        }
        const def = Logica.juego(juego);
        $('#ol-instrucciones').textContent = def.instrucciones;
        $('#ol-reto-detalle').textContent = def.titulo ? def.titulo(D.niveles[juego] || {}, nivel) : '';
        const ctrl = Logica.montar(zona, juego, D.niveles[juego] || {}, nivel, api);
        $('#ol-girar').hidden = !ctrl.girar; $('#ol-voltear').hidden = !ctrl.voltear; $('#ol-deshacer').hidden = !ctrl.deshacer;
        $('#ol-girar').onclick = () => ctrl.girar && ctrl.girar(); $('#ol-voltear').onclick = () => ctrl.voltear && ctrl.voltear(); $('#ol-deshacer').onclick = () => ctrl.deshacer && ctrl.deshacer();
    }
    function superado() {
        if (E.fase !== 'jugando') return;
        const {juego, nivel} = E.reto;
        E.usados[juego] = (E.usados[juego] || []).concat([nivel]);
        E.puntos += 1; E.ultimoPunto = E.activo;
        encolar({tipo: 'punto', juego, nivel, t: Math.round(E.activo * 10) / 10});
        Logica.sonido('gano'); aviso('¡+1 punto!');
        pintarCab();
        if (E.puntos % C.cada === 0) { E.debe += C.por_parada; preguntar(); }
        else setTimeout(siguienteReto, 900);
    }
    function siguienteReto() { if (E.fase !== 'jugando') return; E.reto = null; escogerReto(); montarReto(); }
    $('#ol-saltar').addEventListener('click', () => { if (E.fase === 'jugando') { aviso('Reto saltado (sin punto).'); siguienteReto(); } });
    function aviso(t) { const a = $('#ol-aviso'); a.textContent = t; a.hidden = false; clearTimeout(a._t); a._t = setTimeout(() => { a.hidden = true; }, 2200); }

    // Operaciones para los retos arcade, según el ciclo
    function operaciones(n) {
        const az = (a, b) => a + Math.floor(Math.random() * (b - a + 1)), out = [];
        for (let k = 0; k < n; k++) {
            let txt, r;
            const t = az(0, 2);
            if (PEQUES) { if (t === 1) { const a = az(5, 20), b = az(1, a - 1); r = a - b; txt = `${a} − ${b}`; } else { const a = az(1, 10), b = az(1, 10); r = a + b; txt = `${a} + ${b}`; } }
            else if (PRIMARIA && CI === 0) { if (t === 0) { const a = az(10, 60), b = az(5, 39); r = a + b; txt = `${a} + ${b}`; } else if (t === 1) { const a = az(2, 10), b = az(2, 10); r = a * b; txt = `${a} × ${b}`; } else { const a = az(20, 99), b = az(5, 19); r = a - b; txt = `${a} − ${b}`; } }
            else if (CI === 0) { if (t === 0) { const a = az(12, 90), b = az(5, 60); r = a + b; txt = `${a} + ${b}`; } else if (t === 1) { const a = az(2, 9), b = az(2, 10); r = a * b; txt = `${a} × ${b}`; } else { const b = az(2, 9); r = az(2, 10); txt = `${b * r} ÷ ${b}`; } }
            else if (CI === 1) { if (t === 0) { const a = az(-15, 15), b = az(-15, 15); r = a * b; txt = `(${a}) × (${b})`; } else if (t === 1) { const a = az(2, 15); r = a * a; txt = `${a}²`; } else { const x = az(2, 15), b = az(2, 20); r = x; txt = `x + ${b} = ${x + b}; x = ?`; } }
            else { if (t === 0) { const a = az(2, 9), x = az(2, 12), b = az(1, 20); r = x; txt = `${a}x − ${b} = ${a * x - b}; x = ?`; } else if (t === 1) { const p = [5, 10, 15, 20, 25][az(0, 4)], v = az(2, 30) * 20; r = p * v / 100; txt = `${p} % de ${v}`; } else { const a = az(2, 5); r = 2 ** a * 3; txt = `2^${a} · 3`; } }
            const malos = new Set(); while (malos.size < 3) { const d = r + [-10, -2, -1, 1, 2, 10, 5, -5][az(0, 7)]; if (d !== r && d >= 0) malos.add(d); }
            const ops = [{texto: String(r), correcta: true}].concat([...malos].map(v => ({texto: String(v), correcta: false}))).sort(() => Math.random() - .5);
            out.push({i: k, texto: '¿' + txt + '?', opciones: ops});
        }
        return out;
    }

    // --- Preguntas de competencia --------------------------------------------------------
    async function preguntar() {
        E.fase = 'pregunta'; guardar(); limpiarZona();
        if (E.debe <= 0) return volverAJugar();
        let q = null;
        if (!D.prueba) {      // que el servidor ya tenga el último punto (máximo 12 s esperando)
            const hasta = Date.now() + 12000;
            while (enviando && Date.now() < hasta) await new Promise(r => setTimeout(r, 120));
            await enviar();
        }
        try { const r = await pedir(U.pregunta + (D.prueba ? '?ciclo=' + D.ciclo : ''), {}, 10000); q = (await r.json()).pregunta; } catch (e) { q = null; }
        if (!q) { E.debe = 0; aviso('Sin pregunta por ahora: siga jugando.'); return volverAJugar(); }
        capa(`<div class="mb-2"><span class="ol-cat" style="background:${CAT_COLOR[q.categoria] || '#495057'}">${q.categoria || 'Pregunta'}</span> <b>Pregunta de competencia</b></div>
              <p class="small text-muted mb-2">No da puntos, pero si la responde bien le resta ${C.bono} s a su tiempo.</p>
              <div class="fs-5 fw-semibold mb-3" id="ol-q"></div><div id="ol-ops"></div><div id="ol-res" class="fw-bold mt-2"></div>`);
        $('#ol-q').textContent = q.texto; if (window.Mate) Mate.render($('#ol-q'));
        q.opciones.forEach((t, k) => {
            const b = document.createElement('button'); b.type = 'button'; b.className = 'ol-op';
            b.textContent = 'ABCDEFGH'[k] + ') '; const s = document.createElement('span'); s.textContent = t; b.appendChild(s); if (window.Mate) Mate.render(s);
            b.addEventListener('click', () => responder(k, q)); $('#ol-ops').appendChild(b);
        });
    }
    async function responder(k, q) {
        const botones = [...document.querySelectorAll('.ol-op')]; botones.forEach(b => { b.disabled = true; });
        let bien = false, correcta = null;
        if (D.prueba) { bien = !!q.clave[k]; correcta = q.clave.indexOf(true); }
        else {
            try {
                const r = await pedir(U.responder, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': U.csrf}, body: JSON.stringify({k})});
                const j = await r.json(); bien = !!j.bien; correcta = j.correcta;
            } catch (e) { aviso('Sin conexión: no se pudo enviar la respuesta.'); }
        }
        if (correcta !== null && botones[correcta]) botones[correcta].classList.add('bien');
        if (!bien && botones[k]) botones[k].classList.add('mal');
        E.hechas += 1; E.debe -= 1; if (bien) E.bonos += 1; guardar(); pintarCab();
        $('#ol-res').textContent = bien ? `¡Correcta! −${C.bono} s a su tiempo.` : 'No era esa. ¡Siga adelante!';
        $('#ol-res').style.color = bien ? '#2f9e44' : '#e03131';
        Logica.sonido(bien ? 'bien' : 'mal');
        setTimeout(() => { if (E.debe > 0) preguntar(); else volverAJugar(); }, 1800);
    }
    function volverAJugar() { capa(null); E.fase = 'jugando'; antes = performance.now(); guardar(); siguienteReto(); }

    // --- Bloques, descanso y final -----------------------------------------------------------
    function finDeBloque() {
        limpiarZona(); E.restante = 0;
        if (E.bloque >= C.bloques) { E.fase = 'fin'; encolar({tipo: 'fin'}); guardar(); if (VIG) terminarGrabacion(); Sal.fin = true; return mostrarFin(); }
        E.fase = 'descanso'; E.descansoHasta = Date.now() + C.descanso * 60000; guardar(); mostrarDescanso();
    }
    function mostrarDescanso() {
        capa(`<h4 class="fw-bold text-center" style="color:#0c8599">Descanso visual 👀</h4>
              <p class="text-center mb-1">Terminó el bloque ${E.bloque}. Antes de seguir, cuide sus ojos:</p>
              <div class="ol-respira"></div><p class="text-center small text-muted">Respire con el círculo: crece, inhale · se encoge, exhale.</p>
              <ul class="small"><li>Mire algo lejano (por la ventana) durante 20 segundos.</li><li>Parpadee despacio 10 veces.</li><li>Estire el cuello y los hombros; tome agua.</li></ul>
              <div class="text-center fs-3 fw-bold" id="ol-desc-t"></div>
              <div class="text-center"><button class="btn au-oro btn-lg" id="ol-seguir" disabled>Seguir al bloque ${E.bloque + 1}</button></div>`);
        $('#ol-seguir').addEventListener('click', () => {
            if (Date.now() < E.descansoHasta) return;
            E.bloque += 1; E.restante = C.minutos * 60; encolar({tipo: 'bloque', n: E.bloque}); volverAJugar();
        });
        pintarDescanso();
    }
    function pintarDescanso() {
        const queda = (E.descansoHasta - Date.now()) / 1000, t = $('#ol-desc-t'), b = $('#ol-seguir');
        if (!t) return;
        t.textContent = queda > 0 ? mmss(queda) : '¡Listo!'; b.disabled = queda > 0;
    }
    function mostrarFin() {
        pintarCab();
        capa(`<h3 class="fw-bold text-center" style="color:#1f3a68">¡Terminó! 🏁</h3>
              <div class="d-flex justify-content-center gap-3 my-3 text-center">
                <div><div class="fs-1 fw-bold text-primary">${E.puntos}</div><small>puntos</small></div>
                <div><div class="fs-1 fw-bold text-success">${E.bonos}</div><small>preguntas bien</small></div>
                <div><div class="fs-1 fw-bold" style="color:#e8590c">${mmss(efectivo())}</div><small>tiempo efectivo</small></div>
              </div>
              <p class="text-center small text-muted">Gana quien tenga más puntos; si hay empate, el menor tiempo efectivo. ${D.prueba ? 'Era una prueba: no se guardó.' : (E.cola.length ? 'Guardando… (no cierre hasta que haya internet)' : 'Su resultado quedó guardado.')}</p>
              <div class="text-center"><a class="btn btn-outline-secondary" href="${U.volver}">Volver a Eventos</a>${D.prueba ? ' <button class="btn btn-link" id="ol-otra">Probar de nuevo</button>' : ''}</div>`);
        const otra = $('#ol-otra'); if (otra) otra.addEventListener('click', () => { localStorage.removeItem(CLAVE); location.reload(); });
    }
    function mostrarPortada() {
        const seguir = E.puntos > 0 || E.bloque > 1;
        capa(`<h3 class="fw-bold" style="color:#1f3a68">🏅 ${document.querySelector('.ol-cab h5').textContent.replace('🏅 ', '')}</h3>
              <p class="mb-2">Grupo <b>${GR.nombre}</b> (${GR.grados}). Así se juega:</p>
              <ul class="small">
                <li><b>${C.bloques} bloque(s) de ${C.minutos} minutos</b> contra reloj, con <b>${C.descanso} min de descanso visual</b> entre bloques.</li>
                <li>Cada reto superado (rompecabezas, arcade o manipulativo) suma <b>1 punto</b>. Si uno se le complica, puede saltarlo.</li>
                <li>Cada ${C.cada} puntos sale una <b>pregunta de competencia</b> (Euclides, Newton o Bernoulli): no da puntos, pero bien respondida le resta <b>${C.bono} segundos</b> a su tiempo.</li>
                <li>Gana quien tenga <b>más puntos</b>; si hay empate, el <b>menor tiempo efectivo</b>.</li>
              </ul>
              ${VIG ? `<div class="border rounded-3 p-2 mb-2" style="background:#fff5f5">
                <b>🛡️ Esta prueba es supervisada.</b>
                <div class="small">${VIG.texto}
                  ${VIG.camara ? ' Si apaga la cámara o el micrófono, el juego se detiene hasta que los vuelva a encender (el reloj sigue).' : ''}
                  ${PANT ? ' Al empezar debe <b>compartir la pantalla completa</b>; si deja de compartirla, el juego se detiene hasta que la comparta de nuevo.' : ''}
                  ${VIG.salidas ? ' <b>No se salga de la prueba:</b> cada salida queda anotada.' : ''}</div>
                <div class="form-check small mt-1"><input class="form-check-input" type="checkbox" id="ol-acepto" ${D.acepto_vigilancia ? 'checked' : ''}>
                  <label class="form-check-label" for="ol-acepto">Acepto estas condiciones de supervisión (mi acudiente lo autorizó).</label></div>
                <div class="d-flex flex-wrap align-items-center gap-2 mt-1">
                  ${VIG.camara ? '<button type="button" class="btn btn-sm btn-danger" id="ol-encender">📷🎤 Encender cámara y micrófono</button>' : ''}
                  ${PANT ? '<button type="button" class="btn btn-sm btn-dark" id="ol-compartir">🖥️ Compartir pantalla completa</button>' : ''}
                  <span class="small fw-semibold" id="ol-cam-estado"></span></div></div>` : ''}
              <div class="text-center"><button class="btn au-oro btn-lg" id="ol-empezar" ${VIG ? 'disabled' : ''}>${seguir ? 'Seguir' : '¡Empezar!'}</button></div>`);
        if (VIG) {
            const listo = () => { $('#ol-empezar').disabled = !(requisitos() && $('#ol-acepto').checked); };
            $('#ol-acepto').addEventListener('change', listo);
            const est = $('#ol-cam-estado');
            const boton = (id, fn, ok) => { const b = $(id); if (!b) return; b.addEventListener('click', async () => {
                try { await fn(); b.hidden = true; est.textContent = ok; est.style.color = '#2f9e44'; }
                catch (e) { est.textContent = permisoTexto(e); est.style.color = '#e03131'; }
                listo();
            }); };
            boton('#ol-encender', encender, '✅ Cámara y micrófono encendidos');
            boton('#ol-compartir', compartirPantalla, '✅ Pantalla compartida');
            if (VIG.graba && !puedeGrabar()) {
                est.textContent = 'Este navegador no puede grabar: use Chrome, Edge o Firefox actualizados (o Safari 14.5 o más nuevo).'; est.style.color = '#e03131';
                document.querySelectorAll('#ol-encender, #ol-compartir').forEach(b => { b.disabled = true; });
            }
            listo();
        }
        $('#ol-empezar').addEventListener('click', () => {
            if (VIG) { if (!requisitos()) return; avisoVig('acepto'); empezarGrabacion(); }
            if (!seguir) encolar({tipo: 'inicio'});
            const z = $('#ol'); if (z.requestFullscreen && !document.fullscreenElement) z.requestFullscreen().catch(() => {});
            volverAJugar();
        });
    }
    // --- Supervisión: lo que el organizador escogió en el menú del evento ---------------------------
    //   camara: cámara y micrófono · juego: se graba lo que hace en la prueba (con la cámara en un recuadro)
    //   pantalla: en computador se graba la pantalla completa (los celulares no lo permiten: allí se graba el juego)
    //   salidas: se anota cada vez que sale de la prueba (otra pestaña, ventana o aplicación) y cuánto tiempo
    // Se graba en trozos independientes de ~30 s (se puede ver cada uno solo) y se suben al servidor.
    const VIG = D.vigilancia;
    const esCelular = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && /Macintosh/.test(navigator.userAgent));
    const PANT = !!(VIG && VIG.pantalla && !esCelular && navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia);
    // El video se arma en un lienzo (juego o pantalla, con la cámara en un recuadro); en celular «pantalla» = juego
    const COMPUESTO = !!(VIG && VIG.graba && (VIG.juego || VIG.pantalla) && HTMLCanvasElement.prototype.captureStream);
    const Vig = {stream: null, pantalla: null, comp: null, rec: null, n: 0, cola: [], subiendo: false, apagada: false, parar: false};
    function avisoVig(tipo, motivo, extra) {
        if (D.prueba || !U.grabacion) return;
        const f = new FormData(); f.append('tipo', tipo); f.append('t', Math.round(E.activo)); if (motivo) f.append('motivo', motivo);
        Object.entries(extra || {}).forEach(([k, v]) => f.append(k, v));
        // sendBeacon llega aunque cierre la pestaña o bloquee el celular
        if (tipo === 'sale' && navigator.sendBeacon) { f.append('csrfmiddlewaretoken', U.csrf); if (navigator.sendBeacon(U.grabacion, f)) return; }
        pedir(U.grabacion, {method: 'POST', headers: {'X-CSRFToken': U.csrf}, body: f}, 10000).catch(() => {});
    }
    const puedeGrabar = () => !!(navigator.mediaDevices && window.MediaRecorder && (!VIG.camara || navigator.mediaDevices.getUserMedia));
    const vivo = s => !!(s && s.active && s.getTracks().every(t => t.readyState !== 'ended'));
    const requisitos = () => (!VIG.camara || vivo(Vig.stream)) && (!PANT || vivo(Vig.pantalla));
    function tipoVideo() {
        for (const t of ['video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4;codecs=avc1,mp4a', 'video/mp4']) {
            try { if (MediaRecorder.isTypeSupported(t)) return t; } catch (e) { /* sigue */ }
        }
        return '';
    }
    async function encender() {
        if (!VIG.camara) return null;
        if (!puedeGrabar()) throw new Error('Este navegador no puede grabar. Use Chrome, Edge o Firefox actualizados (o Safari 14.5 o más nuevo).');
        if (vivo(Vig.stream)) return Vig.stream;
        Sal.ignorar = true;
        try {
            Vig.stream = await navigator.mediaDevices.getUserMedia({video: {width: {ideal: 320}, height: {ideal: 240}, frameRate: {ideal: 10, max: 15}, facingMode: 'user'}, audio: true});
        } finally { setTimeout(() => { Sal.ignorar = false; }, 1500); }
        Vig.stream.getTracks().forEach(t => t.addEventListener('ended', () => apagada('camara', 'se apagó ' + (t.kind === 'video' ? 'la cámara' : 'el micrófono'))));
        espejo(); rehacerComp();
        return Vig.stream;
    }
    async function compartirPantalla() {
        if (!PANT) return null;
        if (vivo(Vig.pantalla)) return Vig.pantalla;
        Sal.ignorar = true;
        let s;
        try {
            s = await navigator.mediaDevices.getDisplayMedia({video: {displaySurface: 'monitor', frameRate: {ideal: 5, max: 10}}, audio: false,
                                                              monitorTypeSurfaces: 'include', selfBrowserSurface: 'include', surfaceSwitching: 'exclude'});
        } finally { setTimeout(() => { Sal.ignorar = false; }, 1500); }
        const v = s.getVideoTracks()[0], sup = v && v.getSettings ? v.getSettings().displaySurface : '';
        if (sup && sup !== 'monitor') {
            s.getTracks().forEach(t => t.stop());
            throw new Error('Debe compartir la PANTALLA COMPLETA (no una ventana ni una pestaña). Vuelva a intentar y escoja «Pantalla completa».');
        }
        Vig.pantalla = s;
        v.addEventListener('ended', () => apagada('pantalla', 'dejó de compartir la pantalla'));
        rehacerComp();
        return s;
    }
    function espejo() {
        let caja = document.getElementById('ol-espejo');
        if (!caja) {
            caja = document.createElement('div'); caja.id = 'ol-espejo';
            caja.style.cssText = 'position:fixed;left:8px;bottom:8px;z-index:2147483000;width:96px;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.4);background:#000;pointer-events:none';
            caja.innerHTML = '<video autoplay muted playsinline style="width:100%;display:block;transform:scaleX(-1)"></video><div style="position:absolute;top:3px;left:5px;color:#fff;font:700 10px system-ui;text-shadow:0 0 3px #000"><span style="color:#ff4d4f">●</span> GRABANDO</div>';
            $('#ol').appendChild(caja);
        }
        caja.querySelector('video').srcObject = Vig.stream;
    }
    // --- El video armado: arriba los datos de la prueba, en el centro el juego (o la pantalla), la cámara en un recuadro
    //     y una franja roja si el estudiante está fuera de la prueba.
    function videoOculto(stream) {
        const v = document.createElement('video'); v.muted = true; v.playsInline = true; v.autoplay = true; v.srcObject = stream;
        v.style.cssText = 'position:fixed;left:0;top:0;width:2px;height:2px;opacity:0;pointer-events:none';
        document.body.appendChild(v); v.play().catch(() => {});
        return v;
    }
    function rehacerComp() {
        if (!Vig.comp) return;
        clearInterval(Vig.comp.id); [Vig.comp.vCam, Vig.comp.vPan].forEach(v => v && v.remove()); Vig.comp = null;
    }
    function encajar(cx, fuente, fw, fh, x, y, w, h) {
        if (!fw || !fh) return false;
        const k = Math.min(w / fw, h / fh), dw = fw * k, dh = fh * k;
        try { cx.drawImage(fuente, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh); return true; } catch (e) { return false; }
    }
    function lienzoDelJuego() {
        let mejor = null, area = 0;
        document.querySelectorAll('#ol-zona canvas').forEach(c => { const a = c.offsetWidth * c.offsetHeight; if (a > area) { area = a; mejor = c; } });
        return mejor;
    }
    function flujoGrabacion() {
        if (!COMPUESTO) return Vig.stream;
        if (Vig.comp) return Vig.comp.stream;
        const W = 640, H = 400, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
        const cx = cv.getContext('2d');
        const vCam = vivo(Vig.stream) ? videoOculto(Vig.stream) : null, vPan = vivo(Vig.pantalla) ? videoOculto(Vig.pantalla) : null;
        const partir = (t, ancho) => { const out = []; let l = ''; t.split(/\s+/).forEach(p => { const pr = l ? l + ' ' + p : p; if (cx.measureText(pr).width > ancho && l) { out.push(l); l = p; } else l = pr; }); if (l) out.push(l); return out; };
        function pintar() {
            cx.fillStyle = '#10131c'; cx.fillRect(0, 0, W, H);
            // datos de la prueba
            cx.fillStyle = '#1f3a68'; cx.fillRect(0, 0, W, 22);
            cx.fillStyle = '#fff'; cx.font = '600 11px system-ui, sans-serif'; cx.textBaseline = 'middle';
            const reto = ($('#ol-reto-nombre') || {}).textContent || '';
            cx.fillText(`${GR.nombre} · Bloque ${E.bloque}/${C.bloques} · ⏱ ${mmss(E.restante)} · ${E.puntos} pts · ${E.fase === 'pregunta' ? 'PREGUNTA' : reto}`.slice(0, 95), 6, 11);
            cx.textAlign = 'right'; cx.fillText(new Date().toLocaleTimeString('es-CO', {hour12: false}), W - 6, 11); cx.textAlign = 'left';
            // lo que ve el estudiante
            let ok = false;
            if (vPan && vPan.readyState >= 2) ok = encajar(cx, vPan, vPan.videoWidth, vPan.videoHeight, 0, 22, W, H - 22);
            if (!ok && $('#ol-capa').hidden) { const c = lienzoDelJuego(); if (c) ok = encajar(cx, c, c.width, c.height, 0, 22, W, H - 22); }
            if (!ok) {         // pregunta, descanso o un juego sin lienzo: el texto que tiene en pantalla
                const el = $('#ol-capa').hidden ? $('#ol-zona') : $('#ol-caja');
                const t = ((el && el.innerText) || '').replace(/\s+/g, ' ').trim().slice(0, 600);
                cx.fillStyle = '#e9ecef'; cx.font = '15px system-ui, sans-serif'; cx.textBaseline = 'top';
                partir(t, W - 40).slice(0, 18).forEach((l, i) => cx.fillText(l, 20, 36 + i * 20));
            }
            // la cámara en un recuadro
            if (vCam && vCam.readyState >= 2) {
                const w = 150, h = vCam.videoHeight ? w * vCam.videoHeight / vCam.videoWidth : 112, x = W - w - 8, y = H - h - 8;
                cx.save(); cx.translate(x + w, y); cx.scale(-1, 1); try { cx.drawImage(vCam, 0, 0, w, h); } catch (e) { /* sigue */ } cx.restore();
                cx.strokeStyle = '#fff'; cx.lineWidth = 2; cx.strokeRect(x, y, w, h);
            }
            // fuera de la prueba
            if (Sal.fuera || document.hidden) {
                cx.fillStyle = 'rgba(201,42,42,.88)'; cx.fillRect(0, H / 2 - 30, W, 60);
                cx.fillStyle = '#fff'; cx.font = '700 22px system-ui, sans-serif'; cx.textAlign = 'center'; cx.textBaseline = 'middle';
                cx.fillText(`FUERA DE LA PRUEBA ${Sal.fuera ? mmss((Date.now() - Sal.desde) / 1000) : ''}`, W / 2, H / 2); cx.textAlign = 'left';
            }
        }
        pintar();
        const stream = cv.captureStream(5);
        if (vivo(Vig.stream)) Vig.stream.getAudioTracks().forEach(t => stream.addTrack(t));
        Vig.comp = {stream, vCam, vPan, cv, id: setInterval(pintar, 200)};
        return stream;
    }
    function grabarTrozo() {
        if (Vig.parar || !VIG.graba) return;
        const flujo = flujoGrabacion();
        if (!vivo(flujo)) return;
        const tipo = tipoVideo(), partes = [], inicio = E.activo;
        let rec;
        try { rec = new MediaRecorder(flujo, Object.assign({videoBitsPerSecond: COMPUESTO ? 200000 : 120000, audioBitsPerSecond: 32000}, tipo ? {mimeType: tipo} : {})); }
        catch (e) { rec = new MediaRecorder(flujo); }
        Vig.rec = rec;
        rec.ondataavailable = ev => { if (ev.data && ev.data.size) partes.push(ev.data); };
        rec.onstop = () => {
            if (partes.length) { Vig.n += 1; Vig.cola.push({n: Vig.n, t: inicio, blob: new Blob(partes, {type: rec.mimeType || tipo || 'video/webm'})}); if (Vig.cola.length > 40) Vig.cola.shift(); subirTrozos(); }
            if (!Vig.parar) grabarTrozo();       // el siguiente trozo, sin pausa
        };
        rec.start();
        setTimeout(() => { if (rec.state !== 'inactive') rec.stop(); }, 30000);
    }
    async function subirTrozos() {
        if (D.prueba) { Vig.cola = []; return; }
        if (Vig.subiendo || !Vig.cola.length) return;
        Vig.subiendo = true;
        while (Vig.cola.length) {
            const t = Vig.cola[0], f = new FormData(), ext = (t.blob.type || '').includes('mp4') ? 'mp4' : 'webm';
            f.append('trozo', t.blob, `trozo-${t.n}.${ext}`); f.append('n', t.n); f.append('t', Math.round(t.t));
            try {
                const r = await pedir(U.grabacion, {method: 'POST', headers: {'X-CSRFToken': U.csrf}, body: f}, 60000);
                if (!r.ok && r.status !== 400) throw new Error('reintentar');
                Vig.cola.shift();
            } catch (e) { break; }      // sin internet: se reintenta luego
        }
        Vig.subiendo = false;
    }
    setInterval(subirTrozos, 15000); window.addEventListener('online', subirTrozos);
    function empezarGrabacion() { if (VIG && VIG.graba && !Vig.rec) { Vig.parar = false; grabarTrozo(); } }
    function reiniciarGrabacion() {      // cambió la cámara o la pantalla: se cierra el trozo y el siguiente sale con lo nuevo
        if (!VIG.graba) return;
        if (Vig.rec && Vig.rec.state !== 'inactive') { try { Vig.rec.stop(); } catch (e) { /* sigue */ } } else { Vig.rec = null; empezarGrabacion(); }
    }
    function terminarGrabacion() {
        Vig.parar = true; if (Vig.rec && Vig.rec.state !== 'inactive') Vig.rec.stop();
        setTimeout(() => {
            [Vig.stream, Vig.pantalla].forEach(s => s && s.getTracks().forEach(t => t.stop()));
            rehacerComp(); const e = document.getElementById('ol-espejo'); if (e) e.remove();
        }, 800);
    }
    function apagada(que, motivo) {
        if (!VIG || !VIG.graba || Vig.apagada || E.fase === 'fin' || E.fase === 'portada') return;
        Vig.apagada = true; avisoVig('corte', motivo);
        let capa2 = document.getElementById('ol-camara');
        if (!capa2) {
            capa2 = document.createElement('div'); capa2.id = 'ol-camara';
            capa2.style.cssText = 'position:absolute;inset:0;z-index:50;background:rgba(15,20,35,.92);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px;border-radius:18px';
            $('#ol').style.position = 'relative'; $('#ol').appendChild(capa2);
        }
        const pan = que === 'pantalla';
        capa2.innerHTML = pan
            ? '<div style="font-size:2.5rem">🖥️</div><h5 class="fw-bold">Debe compartir la pantalla completa</h5><p class="small mb-3">Esta prueba graba la pantalla para supervisar que no se salga de ella. El reloj sigue corriendo: compártala para seguir jugando.</p><button type="button" class="btn btn-warning btn-lg">Compartir pantalla completa</button><div class="small mt-2 text-warning ol-cam-error"></div>'
            : '<div style="font-size:2.5rem">📷🎤</div><h5 class="fw-bold">Se apagó la cámara o el micrófono</h5><p class="small mb-3">Este evento exige tenerlos encendidos. El reloj sigue corriendo: enciéndalos para seguir jugando.</p><button type="button" class="btn btn-warning btn-lg">Encender de nuevo</button><div class="small mt-2 text-warning ol-cam-error"></div>';
        capa2.hidden = false;
        capa2.querySelector('button').addEventListener('click', async () => {
            try {
                if (pan) { Vig.pantalla = null; await compartirPantalla(); } else { Vig.stream = null; await encender(); }
                Vig.apagada = false; capa2.hidden = true; avisoVig('reanudo');
                if (!requisitos()) return apagada(vivo(Vig.stream) || !VIG.camara ? 'pantalla' : 'camara', 'falta encender');
                reiniciarGrabacion();
            } catch (e) { capa2.querySelector('.ol-cam-error').textContent = permisoTexto(e); }
        });
    }
    function permisoTexto(e) {
        if (e && (e.name === 'NotAllowedError' || e.name === 'SecurityError')) return 'No se dio el permiso. Toque el candado 🔒 junto a la dirección, permita cámara y micrófono (o vuelva a escoger «Pantalla completa») e intente de nuevo.';
        if (e && e.name === 'NotFoundError') return 'No se encontró cámara o micrófono en este equipo.';
        if (e && e.name === 'NotReadableError') return 'Otra aplicación está usando la cámara. Ciérrela y vuelva a intentar.';
        return (e && e.message) || 'No se pudo encender.';
    }
    // Revisa cada 2 s que sigan encendidos (si el sistema la apaga, el evento «ended» no siempre llega)
    setInterval(() => {
        if (!VIG || !VIG.graba || Vig.apagada || !['jugando', 'pregunta', 'descanso'].includes(E.fase)) return;
        if (VIG.camara && Vig.stream && !vivo(Vig.stream)) apagada('camara', 'se desconectó');
        else if (PANT && Vig.pantalla && !vivo(Vig.pantalla)) apagada('pantalla', 'dejó de compartir la pantalla');
    }, 2000);

    // --- Registro de salidas: cada vez que cambia de pestaña, ventana o aplicación durante la prueba -----------
    const Sal = {fuera: false, desde: 0, n: 0, total: 0, ignorar: false, fin: false, espera: null};
    const enPrueba = () => VIG && VIG.salidas && !Sal.fin && ['jugando', 'pregunta'].includes(E.fase);
    function salir(motivo) {
        if (!enPrueba() || Sal.fuera || Sal.ignorar) return;
        Sal.fuera = true; Sal.desde = Date.now();
        try { localStorage.setItem(CLAVE + ':fuera', String(Sal.desde)); } catch (e) { /* sin almacenamiento */ }
        avisoVig('sale', motivo);
    }
    function volver() {
        clearTimeout(Sal.espera);
        if (!Sal.fuera || document.hidden || !document.hasFocus()) return;
        Sal.fuera = false;
        try { localStorage.removeItem(CLAVE + ':fuera'); } catch (e) { /* sin almacenamiento */ }
        const seg = (Date.now() - Sal.desde) / 1000;
        Sal.n += 1; Sal.total += seg;
        avisoVig('vuelve', '', {seg: seg.toFixed(1)});
        aviso(`Salió de la prueba ${Math.round(seg)} s: quedó registrado (${Sal.n} vez${Sal.n === 1 ? '' : 'es'}).`);
    }
    if (VIG && VIG.salidas) {
        document.addEventListener('visibilitychange', () => { if (document.hidden) salir('cambió de pestaña o de aplicación'); else volver(); });
        // En computador: otra ventana encima (sin cambiar de pestaña). Se espera un poco para no contar parpadeos.
        window.addEventListener('blur', () => { clearTimeout(Sal.espera); Sal.espera = setTimeout(() => { if (!document.hasFocus() && !document.hidden) salir('cambió de ventana'); }, 2000); });
        window.addEventListener('focus', volver);
        window.addEventListener('pagehide', () => salir('cerró o recargó la página'));
        // Si cerró la página estando fuera, al volver se completa cuánto tiempo estuvo fuera
        let antes = 0;
        try { antes = +localStorage.getItem(CLAVE + ':fuera') || 0; } catch (e) { /* sin almacenamiento */ }
        if (antes) {
            Sal.fuera = true; Sal.desde = antes;
            setTimeout(() => { if (!document.hidden) { if (!document.hasFocus()) window.focus(); Sal.fuera = true; volverForzado(); } }, 600);
        }
    }
    function volverForzado() {
        if (!Sal.fuera) return;
        Sal.fuera = false;
        try { localStorage.removeItem(CLAVE + ':fuera'); } catch (e) { /* sin almacenamiento */ }
        const seg = (Date.now() - Sal.desde) / 1000;
        Sal.n += 1; Sal.total += seg;
        avisoVig('vuelve', '', {seg: seg.toFixed(1)});
    }

    // --- Actualizar: guarda, recarga la página y sigue donde iba (con otro reto) -----------------
    async function actualizar() {
        const b = $('#ol-actualizar'); if (b) { b.disabled = true; b.innerHTML = '<i class="fas fa-rotate fa-spin me-1"></i>Actualizando…'; }
        if (E.fase === 'jugando' || E.fase === 'pregunta') { E.reto = null; if (E.fase === 'pregunta') E.fase = 'jugando'; }
        guardar();
        Sal.ignorar = true;            // recargar con el botón Actualizar no cuenta como salida
        if (VIG && VIG.graba) {        // el trozo que se estaba grabando también se sube antes de recargar
            Vig.parar = true;
            if (Vig.rec && Vig.rec.state !== 'inactive') { try { Vig.rec.stop(); } catch (e) { /* sigue */ } }
            await new Promise(r => setTimeout(r, 400));
            try { await Promise.race([subirTrozos(), new Promise(r => setTimeout(r, 6000))]); } catch (e) { /* sigue */ }
        }
        try { await Promise.race([enviar(), new Promise(r => setTimeout(r, 4000))]); } catch (e) { /* sigue */ }
        try { sessionStorage.setItem(CLAVE + ':seguir', '1'); } catch (e) { /* sin almacenamiento */ }
        location.reload();
    }
    function atascado() {
        const a = $('#ol-atascado'); if (a) a.hidden = false;
    }
    document.querySelectorAll('#ol-actualizar, #ol-atascado-btn').forEach(b => b.addEventListener('click', actualizar));
    // Si algo falla en un juego, se ofrece actualizar (sin perder lo que lleva)
    window.addEventListener('error', () => { if (E.fase === 'jugando' || E.fase === 'pregunta') atascado(); });
    window.addEventListener('unhandledrejection', () => { if (E.fase === 'pregunta') atascado(); });

    function capa(html) { const c = $('#ol-capa'); if (html === null) { c.hidden = true; return; } $('#ol-caja').innerHTML = html; c.hidden = false; }
    $('#ol-completa').addEventListener('click', () => { const z = $('#ol'); if (document.fullscreenElement) document.exitFullscreen(); else if (z.requestFullscreen) z.requestFullscreen().catch(() => {}); });

    // --- Arranque: retoma donde iba ---------------------------------------------------------
    pintarCab();
    let vieneDeActualizar = false;
    try { vieneDeActualizar = sessionStorage.getItem(CLAVE + ':seguir') === '1'; sessionStorage.removeItem(CLAVE + ':seguir'); } catch (e) { /* sin almacenamiento */ }
    // Con vigilancia, a mitad del evento (después de Actualizar) se vuelve a encender la cámara antes de seguir
    const conCamara = fn => {
        if (!VIG || !VIG.graba) return fn();
        // la cámara se enciende sola (ya tenía permiso); la pantalla necesita que el estudiante toque «Compartir»
        encender().then(() => {
            empezarGrabacion(); avisoVig('reanudo'); fn();
            if (PANT && !vivo(Vig.pantalla)) { Vig.apagada = false; apagada('pantalla', 'debe volver a compartir la pantalla'); }
        }).catch(() => { E.fase = E.fase === 'portada' ? 'jugando' : E.fase; fn(); Vig.apagada = false; apagada('camara', 'no se pudo encender al volver'); });
    };
    if (E.fase === 'fin') mostrarFin();
    else if (E.fase === 'descanso') conCamara(mostrarDescanso);
    else if (E.fase === 'pregunta') conCamara(preguntar);
    else if (vieneDeActualizar && E.fase === 'jugando') conCamara(() => { aviso('Listo: siga donde iba.'); volverAJugar(); });
    else mostrarPortada();
    enviar();
    window.olimpiada = {estado: () => E, vigilancia: () => Vig};
    if (D.prueba) Object.assign(window.olimpiada, {superado, finDeBloque});      // solo en la prueba del organizador
})();
