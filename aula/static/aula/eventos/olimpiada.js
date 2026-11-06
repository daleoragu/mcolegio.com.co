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
    function limpiarZona() { if (motor && motor.destruir) motor.destruir(); motor = null; actual = null; $('#ol-zona').innerHTML = ''; }
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
            const preguntas = propio ? propio.preguntas.slice().sort(() => Math.random() - .5).slice(0, 3) : operaciones(3);
            $('#ol-reto-detalle').textContent = `Responda bien ${Math.min(2, preguntas.length)} de ${preguntas.length}.`;
            $('#ol-instrucciones').textContent = def.instrucciones || '';
            const cv = document.createElement('canvas'); cv.className = 'ol-motor'; zona.appendChild(cv);
            motor = Gamificacion.iniciar({lienzo: cv, tipo, preguntas, segundos: 20, minutos: 2, jugadores: 1, ritmo: (D.ritmo || {})[juego] || 1, tema: propio ? propio.titulo : '',
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
        $('#ol-q').textContent = q.texto;
        q.opciones.forEach((t, k) => {
            const b = document.createElement('button'); b.type = 'button'; b.className = 'ol-op'; b.textContent = 'ABCDEFGH'[k] + ') ' + t;
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
        if (E.bloque >= C.bloques) { E.fase = 'fin'; encolar({tipo: 'fin'}); guardar(); return mostrarFin(); }
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
              <div class="text-center"><button class="btn au-oro btn-lg" id="ol-empezar">${seguir ? 'Seguir' : '¡Empezar!'}</button></div>`);
        $('#ol-empezar').addEventListener('click', () => {
            if (!seguir) encolar({tipo: 'inicio'});
            const z = $('#ol'); if (z.requestFullscreen && !document.fullscreenElement) z.requestFullscreen().catch(() => {});
            volverAJugar();
        });
    }
    // --- Actualizar: guarda, recarga la página y sigue donde iba (con otro reto) -----------------
    async function actualizar() {
        const b = $('#ol-actualizar'); if (b) { b.disabled = true; b.innerHTML = '<i class="fas fa-rotate fa-spin me-1"></i>Actualizando…'; }
        if (E.fase === 'jugando' || E.fase === 'pregunta') { E.reto = null; if (E.fase === 'pregunta') E.fase = 'jugando'; }
        guardar();
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
    if (E.fase === 'fin') mostrarFin();
    else if (E.fase === 'descanso') mostrarDescanso();
    else if (E.fase === 'pregunta') preguntar();
    else if (vieneDeActualizar && E.fase === 'jugando') { aviso('Listo: siga donde iba.'); volverAJugar(); }
    else mostrarPortada();
    enviar();
    window.olimpiada = {estado: () => E};
    if (D.prueba) Object.assign(window.olimpiada, {superado, finDeBloque});      // solo en la prueba del organizador
})();
