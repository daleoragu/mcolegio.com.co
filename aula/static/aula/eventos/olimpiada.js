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
        if (E.bloque >= C.bloques) { E.fase = 'fin'; encolar({tipo: 'fin'}); guardar(); if (VIG) terminarGrabacion(); return mostrarFin(); }
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
                <b>📷🎤 Este evento exige cámara y micrófono encendidos.</b>
                <div class="small">Se graba su imagen y su voz mientras juega, solo para vigilar la prueba. Lo ven únicamente los organizadores y se borra a los ${VIG.dias} días.
                  Si apaga la cámara o el micrófono, el juego se detiene hasta que los vuelva a encender (el reloj sigue).</div>
                <div class="form-check small mt-1"><input class="form-check-input" type="checkbox" id="ol-acepto" ${D.acepto_vigilancia ? 'checked' : ''}>
                  <label class="form-check-label" for="ol-acepto">Acepto que me graben durante el evento (mi acudiente lo autorizó).</label></div>
                <div class="d-flex align-items-center gap-2 mt-1"><button type="button" class="btn btn-sm btn-danger" id="ol-encender">Encender cámara y micrófono</button>
                  <span class="small fw-semibold" id="ol-cam-estado"></span></div></div>` : ''}
              <div class="text-center"><button class="btn au-oro btn-lg" id="ol-empezar" ${VIG ? 'disabled' : ''}>${seguir ? 'Seguir' : '¡Empezar!'}</button></div>`);
        if (VIG) {
            const listo = () => { $('#ol-empezar').disabled = !(Vig.stream && Vig.stream.active && $('#ol-acepto').checked); };
            $('#ol-acepto').addEventListener('change', listo);
            $('#ol-encender').addEventListener('click', async () => {
                const est = $('#ol-cam-estado');
                try { await encender(); est.textContent = '✅ Encendidos'; est.style.color = '#2f9e44'; $('#ol-encender').hidden = true; }
                catch (e) { est.textContent = permisoTexto(e); est.style.color = '#e03131'; }
                listo();
            });
            if (!puedeGrabar()) { $('#ol-cam-estado').textContent = 'Este navegador no puede grabar: use Chrome, Edge o Firefox actualizados (o Safari 14.5 o más nuevo).'; $('#ol-cam-estado').style.color = '#e03131'; $('#ol-encender').disabled = true; }
        }
        $('#ol-empezar').addEventListener('click', () => {
            if (VIG) { if (!(Vig.stream && Vig.stream.active)) return; avisoVig('acepto'); empezarGrabacion(); }
            if (!seguir) encolar({tipo: 'inicio'});
            const z = $('#ol'); if (z.requestFullscreen && !document.fullscreenElement) z.requestFullscreen().catch(() => {});
            volverAJugar();
        });
    }
    // --- Vigilancia: cámara y micrófono encendidos y grabados (solo si el evento lo exige) ---------
    // Se graba en trozos independientes de ~30 s (se puede ver cada uno solo) y se suben al servidor.
    // Si la cámara o el micrófono se apagan, el juego se tapa hasta que se vuelvan a encender (el reloj sigue).
    const VIG = D.vigilancia;
    const Vig = {stream: null, rec: null, n: 0, cola: [], subiendo: false, apagada: false, parar: false};
    function avisoVig(tipo, motivo) {
        if (D.prueba || !U.grabacion) return;
        const f = new FormData(); f.append('tipo', tipo); f.append('t', Math.round(E.activo)); if (motivo) f.append('motivo', motivo);
        pedir(U.grabacion, {method: 'POST', headers: {'X-CSRFToken': U.csrf}, body: f}, 10000).catch(() => {});
    }
    const puedeGrabar = () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    function tipoVideo() {
        for (const t of ['video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4;codecs=avc1,mp4a', 'video/mp4']) {
            try { if (MediaRecorder.isTypeSupported(t)) return t; } catch (e) { /* sigue */ }
        }
        return '';
    }
    async function encender() {
        if (!puedeGrabar()) throw new Error('Este navegador no puede grabar. Use Chrome, Edge o Firefox actualizados (o Safari 14.5 o más nuevo).');
        if (Vig.stream && Vig.stream.active) return Vig.stream;
        Vig.stream = await navigator.mediaDevices.getUserMedia({video: {width: {ideal: 320}, height: {ideal: 240}, frameRate: {ideal: 10, max: 15}, facingMode: 'user'}, audio: true});
        Vig.stream.getTracks().forEach(t => t.addEventListener('ended', () => apagada('se apagó ' + (t.kind === 'video' ? 'la cámara' : 'el micrófono'))));
        espejo();
        return Vig.stream;
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
    function grabarTrozo() {
        if (Vig.parar || !Vig.stream || !Vig.stream.active) return;
        const tipo = tipoVideo(), partes = [], inicio = E.activo;
        let rec;
        try { rec = new MediaRecorder(Vig.stream, Object.assign({videoBitsPerSecond: 120000, audioBitsPerSecond: 32000}, tipo ? {mimeType: tipo} : {})); }
        catch (e) { rec = new MediaRecorder(Vig.stream); }
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
    function empezarGrabacion() { if (VIG && !Vig.rec) { Vig.parar = false; grabarTrozo(); } }
    function terminarGrabacion() { Vig.parar = true; if (Vig.rec && Vig.rec.state !== 'inactive') Vig.rec.stop(); setTimeout(() => { if (Vig.stream) Vig.stream.getTracks().forEach(t => t.stop()); const e = document.getElementById('ol-espejo'); if (e) e.remove(); }, 800); }
    function apagada(motivo) {
        if (!VIG || Vig.apagada || E.fase === 'fin' || E.fase === 'portada') return;
        Vig.apagada = true; avisoVig('corte', motivo);
        let capa2 = document.getElementById('ol-camara');
        if (!capa2) {
            capa2 = document.createElement('div'); capa2.id = 'ol-camara';
            capa2.style.cssText = 'position:absolute;inset:0;z-index:50;background:rgba(15,20,35,.92);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px;border-radius:18px';
            $('#ol').style.position = 'relative'; $('#ol').appendChild(capa2);
        }
        capa2.innerHTML = '<div style="font-size:2.5rem">📷🎤</div><h5 class="fw-bold">Se apagó la cámara o el micrófono</h5><p class="small mb-3">Este evento exige tenerlos encendidos. El reloj sigue corriendo: enciéndalos para seguir jugando.</p><button type="button" class="btn btn-warning btn-lg">Encender de nuevo</button><div class="small mt-2 text-warning ol-cam-error"></div>';
        capa2.hidden = false;
        capa2.querySelector('button').addEventListener('click', async () => {
            try {
                Vig.stream = null; await encender(); Vig.apagada = false; capa2.hidden = true; avisoVig('reanudo');
                if (Vig.rec && Vig.rec.state !== 'inactive') { try { Vig.rec.stop(); } catch (e) { /* sigue */ } } else { Vig.rec = null; empezarGrabacion(); }
            } catch (e) { capa2.querySelector('.ol-cam-error').textContent = permisoTexto(e); }
        });
    }
    function permisoTexto(e) {
        if (e && (e.name === 'NotAllowedError' || e.name === 'SecurityError')) return 'El navegador no dio permiso. Toque el candado 🔒 junto a la dirección, permita cámara y micrófono, y vuelva a intentar.';
        if (e && e.name === 'NotFoundError') return 'No se encontró cámara o micrófono en este equipo.';
        if (e && e.name === 'NotReadableError') return 'Otra aplicación está usando la cámara. Ciérrela y vuelva a intentar.';
        return (e && e.message) || 'No se pudo encender la cámara y el micrófono.';
    }
    // Revisa cada 2 s que sigan encendidos (si el sistema la apaga, el evento «ended» no siempre llega)
    setInterval(() => {
        if (!VIG || !Vig.stream || Vig.apagada || !['jugando', 'pregunta', 'descanso'].includes(E.fase)) return;
        if (!Vig.stream.active || Vig.stream.getTracks().some(t => t.readyState === 'ended')) apagada('se desconectó');
    }, 2000);

    // --- Actualizar: guarda, recarga la página y sigue donde iba (con otro reto) -----------------
    async function actualizar() {
        const b = $('#ol-actualizar'); if (b) { b.disabled = true; b.innerHTML = '<i class="fas fa-rotate fa-spin me-1"></i>Actualizando…'; }
        if (E.fase === 'jugando' || E.fase === 'pregunta') { E.reto = null; if (E.fase === 'pregunta') E.fase = 'jugando'; }
        guardar();
        if (VIG) {        // el trozo que se estaba grabando también se sube antes de recargar
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
        if (!VIG) return fn();
        encender().then(() => { empezarGrabacion(); avisoVig('reanudo'); fn(); })
                  .catch(() => { E.fase = E.fase === 'portada' ? 'jugando' : E.fase; fn(); Vig.apagada = false; apagada('no se pudo encender al volver'); });
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
