/* Aula invertida: editor de preguntas sobre el video, como Edpuzzle.
 *
 * El docente ve el video (YouTube) con su línea de tiempo; pausa donde quiera, pulsa «Agregar pregunta aquí»,
 * escoge el tipo (opción múltiple, verdadero o falso, abierta), escribe la pregunta y sus puntos.
 * Las marcas quedan sobre la línea de tiempo; un clic en una marca lleva a ese minuto.
 * Todo se guarda en el campo oculto «preguntas_json» del formulario (el servidor lo valida).
 *
 * Cada editor: <div class="ie" data-prefijo="n"> con #ie-datos-<prefijo> (json_script con las preguntas actuales)
 * y el campo del enlace del video #inv-video-<prefijo>.
 */
(function () {
    'use strict';
    const TIPOS = {multiple: 'Opción múltiple', vf: 'Verdadero o falso', abierta: 'Abierta'};
    const editores = [];
    let apiLista = false;

    function minuto(s) {
        if (s === null || s === undefined || s === '') return 'Al final';
        s = Math.max(0, Math.floor(s));
        const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
        return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(x).padStart(2, '0');
    }
    function aSegundos(t) {
        t = (t || '').trim();
        if (!t) return null;
        if (!/^\d{1,2}(:\d{1,2}){0,2}$/.test(t)) return NaN;
        return t.split(':').reduce((a, b) => a * 60 + parseInt(b, 10), 0);
    }
    function idYoutube(url) {
        const m = (url || '').match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/|live\/))([\w-]{11})/);
        return m ? m[1] : '';
    }
    function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

    function Editor(raiz) {
        const pref = raiz.dataset.prefijo;
        const $ = sel => raiz.querySelector(sel);
        const datos = document.getElementById('ie-datos-' + pref);
        let preguntas = datos ? JSON.parse(datos.textContent || '[]') : [];
        if (!Array.isArray(preguntas)) preguntas = [];
        preguntas = preguntas.map(p => ({
            texto: p.texto, tipo: p.opciones && p.opciones.length ? (p.tipo === 'vf' ? 'vf' : 'multiple') : 'abierta',
            opciones: (p.opciones || []).map(o => ({texto: o.texto, correcta: !!o.correcta})),
            segundo: p.segundo === undefined ? null : p.segundo, puntos: p.puntos === undefined ? 1 : p.puntos,
        }));
        const campoVideo = document.getElementById('inv-video-' + pref);
        const oculto = $('[name=preguntas_json]');
        const form = raiz.closest('form');
        let reproductor = null, videoActual = '', editando = -1;

        // ------------------------------------------------------------ video
        function montar() {
            const id = idYoutube(campoVideo ? campoVideo.value : '');
            $('.ie-sin').classList.toggle('d-none', !!id);
            $('.ie-con').classList.toggle('d-none', !id);
            $('.ie-agregar').classList.toggle('d-none', !id);           // sin YouTube no hay minuto actual
            $('.ie-tiempo').classList.toggle('d-none', !id);
            $('.ie-final').textContent = id ? 'Pregunta al final' : 'Agregar pregunta';
            if (!id || id === videoActual || !apiLista) return;
            videoActual = id;
            if (reproductor && reproductor.loadVideoById) { reproductor.cueVideoById(id); return; }
            reproductor = new YT.Player('ie-yt-' + pref, {
                host: 'https://www.youtube-nocookie.com', videoId: id,
                playerVars: {rel: 0, playsinline: 1, modestbranding: 1},
                events: {onReady: () => setInterval(tic, 300)},
            });
        }
        function duracion() { return reproductor && reproductor.getDuration ? reproductor.getDuration() : 0; }
        function ahora() { return reproductor && reproductor.getCurrentTime ? reproductor.getCurrentTime() : 0; }
        function tic() {
            const d = duracion(), t = ahora();
            $('.ie-tiempo').textContent = minuto(t) + (d ? ' / ' + minuto(d) : '');
            $('.ie-agregar span').textContent = minuto(t);
            $('.ie-cabeza').style.left = d ? (t * 100 / d) + '%' : '0';
            if (d && !$('.ie-pista').dataset.dur) { $('.ie-pista').dataset.dur = d; pintar(); }
        }
        $('.ie-pista').addEventListener('click', ev => {
            const d = duracion(); if (!d || ev.target.closest('.ie-marca')) return;
            const r = ev.currentTarget.getBoundingClientRect();
            reproductor.seekTo(d * (ev.clientX - r.left) / r.width, true);
        });
        if (campoVideo) campoVideo.addEventListener('input', montar);

        // ------------------------------------------------------------ formulario de una pregunta
        const caja = $('.ie-form');
        function filaOpcion(o, k) {
            const d = document.createElement('div');
            d.className = 'd-flex align-items-center gap-2 mb-1 ie-op';
            d.innerHTML = '<input type="radio" class="form-check-input mt-0" name="ie-correcta-' + pref + '" title="Es la correcta">' +
                '<input type="text" class="form-control form-control-sm" maxlength="300" placeholder="Opción ' + 'ABCDEFGH'[k] + '">' +
                '<button type="button" class="btn btn-sm btn-link text-danger px-1" title="Quitar"><i class="far fa-trash-can"></i></button>';
            d.querySelector('input[type=text]').value = o.texto || '';
            d.querySelector('input[type=radio]').checked = !!o.correcta;
            d.querySelector('button').onclick = () => { d.remove(); };
            $('.ie-opciones').appendChild(d);
        }
        function verTipo() {
            const t = $('.ie-tipo').value;
            $('.ie-bloque-op').classList.toggle('d-none', t !== 'multiple');
            $('.ie-bloque-vf').classList.toggle('d-none', t !== 'vf');
        }
        $('.ie-tipo').addEventListener('change', verTipo);
        $('.ie-mas-op').onclick = () => { if ($('.ie-opciones').children.length < 8) filaOpcion({}, $('.ie-opciones').children.length); };
        function abrir(i, segundo) {
            editando = i;
            const p = i >= 0 ? preguntas[i] : {texto: '', tipo: 'multiple', opciones: [{}, {}, {}, {}], segundo: segundo, puntos: 1};
            if (reproductor && reproductor.pauseVideo) reproductor.pauseVideo();
            $('.ie-tipo').value = p.tipo;
            $('.ie-min').value = p.segundo === null || p.segundo === undefined ? '' : minuto(p.segundo);
            $('.ie-texto').value = p.texto || '';
            $('.ie-puntos').value = p.puntos;
            $('.ie-opciones').innerHTML = '';
            (p.tipo === 'multiple' ? p.opciones : [{}, {}, {}, {}]).forEach(filaOpcion);
            const vf = p.tipo === 'vf' ? (p.opciones[1] && p.opciones[1].correcta ? '1' : '0') : '0';
            raiz.querySelectorAll('.ie-vf').forEach(r => { r.checked = r.value === vf; });
            $('.ie-error').textContent = '';
            verTipo();
            caja.classList.remove('d-none');
            $('.ie-texto').focus();
        }
        function cerrar() { caja.classList.add('d-none'); editando = -1; }
        $('.ie-agregar').onclick = () => abrir(-1, reproductor ? Math.floor(ahora()) : null);
        $('.ie-final').onclick = () => abrir(-1, null);
        $('.ie-cancelar').onclick = cerrar;
        $('.ie-guardar').onclick = () => {
            const tipo = $('.ie-tipo').value, texto = $('.ie-texto').value.trim();
            const seg = aSegundos($('.ie-min').value);
            const puntos = parseFloat(($('.ie-puntos').value || '1').replace(',', '.'));
            const error = m => { $('.ie-error').textContent = m; };
            if (!texto) return error('Escriba la pregunta.');
            if (Number.isNaN(seg)) return error('El minuto va así: 2:30 (o vacío para dejarla al final).');
            if (!(puntos >= 0 && puntos <= 100)) return error('Los puntos van de 0 a 100.');
            let opciones = [];
            if (tipo === 'multiple') {
                opciones = Array.from(raiz.querySelectorAll('.ie-op')).map(d => ({
                    texto: d.querySelector('input[type=text]').value.trim(), correcta: d.querySelector('input[type=radio]').checked,
                })).filter(o => o.texto);
                if (opciones.length < 2) return error('Escriba al menos dos opciones.');
                if (!opciones.some(o => o.correcta)) return error('Marque cuál es la correcta (el círculo a la izquierda).');
            } else if (tipo === 'vf') {
                const c = raiz.querySelector('.ie-vf:checked');
                opciones = [{texto: 'Verdadero', correcta: !c || c.value === '0'}, {texto: 'Falso', correcta: !!c && c.value === '1'}];
            }
            const p = {texto: texto, tipo: tipo, opciones: opciones, segundo: seg, puntos: puntos};
            if (editando >= 0) preguntas[editando] = p; else preguntas.push(p);
            cerrar();
            pintar();
        };

        // ------------------------------------------------------------ lista y marcas
        function ordenar() { preguntas.sort((a, b) => (a.segundo === null) - (b.segundo === null) || (a.segundo || 0) - (b.segundo || 0)); }
        function pintar() {
            ordenar();
            const d = parseFloat($('.ie-pista').dataset.dur || 0);
            $('.ie-marcas').innerHTML = d ? preguntas.map((p, i) => p.segundo === null ? '' :
                '<button type="button" class="ie-marca ie-t-' + p.tipo + '" style="left:' + Math.min(100, p.segundo * 100 / d) + '%" data-i="' + i + '" title="' +
                esc(minuto(p.segundo) + ' · ' + p.texto) + '"></button>').join('') : '';
            $('.ie-lista').innerHTML = preguntas.length ? preguntas.map((p, i) =>
                '<li class="ie-item"><button type="button" class="btn btn-sm ie-ir" data-i="' + i + '">' + minuto(p.segundo) + '</button>' +
                '<div class="flex-grow-1" style="min-width:0"><span class="badge ie-b-' + p.tipo + '">' + TIPOS[p.tipo] + '</span> ' +
                '<span class="small text-muted">' + p.puntos + ' punto' + (p.puntos == 1 ? '' : 's') + '</span><div class="text-truncate">' + esc(p.texto) + '</div></div>' +
                '<button type="button" class="btn btn-sm btn-link ie-editar" data-i="' + i + '" title="Editar"><i class="fas fa-pen"></i></button>' +
                '<button type="button" class="btn btn-sm btn-link text-danger ie-borrar" data-i="' + i + '" title="Quitar"><i class="far fa-trash-can"></i></button></li>').join('')
                : '<li class="small text-muted">Todavía no hay preguntas. Reproduzca el video, páuselo donde quiera y pulse «Agregar pregunta aquí».</li>';
            const total = preguntas.reduce((a, p) => a + (+p.puntos || 0), 0);
            $('.ie-resumen').textContent = preguntas.length ? preguntas.length + ' pregunta' + (preguntas.length === 1 ? '' : 's') + ' · ' + total + ' puntos en total' : '';
            oculto.value = JSON.stringify(preguntas);
            const texto = form && form.querySelector('[name=preguntas]');
            if (texto) texto.required = !preguntas.length;
        }
        raiz.addEventListener('click', ev => {
            const b = ev.target.closest('[data-i]'); if (!b) return;
            const i = +b.dataset.i;
            if (b.classList.contains('ie-borrar')) { if (confirm('¿Quitar esta pregunta?')) { preguntas.splice(i, 1); pintar(); } }
            else if (b.classList.contains('ie-editar')) abrir(i);
            else if ((b.classList.contains('ie-ir') || b.classList.contains('ie-marca')) && reproductor && preguntas[i].segundo !== null) {
                reproductor.seekTo(preguntas[i].segundo, true); reproductor.pauseVideo();
                if (b.classList.contains('ie-marca')) abrir(i);
            }
        });
        pintar();
        this.montar = montar;
    }

    document.querySelectorAll('.ie').forEach(r => editores.push(new Editor(r)));
    if (!editores.length) return;
    const anterior = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = function () {
        apiLista = true;
        if (anterior) anterior();
        editores.forEach(e => e.montar());
    };
    editores.forEach(e => e.montar());
    if (!window.YT) {
        const api = document.createElement('script');
        api.src = 'https://www.youtube.com/iframe_api';
        document.head.appendChild(api);
    } else if (window.YT.Player) { apiLista = true; editores.forEach(e => e.montar()); }
})();
