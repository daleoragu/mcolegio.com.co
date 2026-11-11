/* Chat flotante de Mis colegas (como el de Facebook), solo en el computador:
 *   · Botón redondo abajo a la derecha con el número de mensajes sin leer.
 *   · Al tocarlo, un panel con las conversaciones y los colegas (buscar, abrir un chat nuevo).
 *   · Cada chat se abre en una ventanita abajo (hasta 3); se puede minimizar a una barrita o cerrar.
 *   · Las ventanas abiertas se recuerdan al cambiar de página.
 * Usa las mismas rutas del chat de colegas (/chat/colegas/…). En el celular no aparece: allá se usa la página completa. */
(function () {
    'use strict';
    if (window.ChatFlotante || window.innerWidth < 992) return;
    const BASE = '/chat/colegas';
    const CLAVE = 'mc-chat-flotante';
    const MAX = 3;
    const $ = (s, r) => (r || document).querySelector(s);
    const esc = t => String(t == null ? '' : t).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
    let token = '';
    const csrf = () => { const m = document.cookie.match(/csrftoken=([^;]+)/); return m ? m[1] : token; };
    const pedir = (url, op) => fetch(url, Object.assign({credentials: 'same-origin', headers: {'X-Requested-With': 'fetch'}}, op || {}))
        .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });

    // --- Estilos ---------------------------------------------------------------------------
    const css = document.createElement('style');
    css.textContent = `
    .cf-boton { position:fixed; right:22px; bottom:22px; z-index:1080; width:58px; height:58px; border-radius:50%; border:0;
      background:linear-gradient(135deg,#2b5cbf,#1f3a68); color:#fff; box-shadow:0 6px 20px rgba(0,0,0,.28); cursor:pointer;
      display:flex; align-items:center; justify-content:center; transition:transform .15s; }
    .cf-boton:hover { transform:scale(1.07); }
    .cf-boton svg { width:28px; height:28px; }
    .cf-num { position:absolute; top:-3px; right:-3px; min-width:22px; height:22px; padding:0 6px; border-radius:11px; background:#e03131; color:#fff;
      font:700 12px/22px system-ui,sans-serif; text-align:center; box-shadow:0 0 0 2px #fff; }
    .cf-panel { position:fixed; right:22px; bottom:92px; z-index:1081; width:340px; height:min(520px,calc(100vh - 120px)); background:#fff; border-radius:16px;
      box-shadow:0 12px 40px rgba(0,0,0,.25); display:flex; flex-direction:column; overflow:hidden; font-family:system-ui,-apple-system,'Segoe UI',sans-serif; }
    .cf-panel header { padding:14px 16px 8px; display:flex; align-items:center; gap:8px; }
    .cf-panel header b { flex:1; font-size:1.35rem; color:#1f3a68; }
    .cf-ico { width:34px; height:34px; border-radius:50%; border:0; background:#eef1f6; color:#1f3a68; display:inline-flex; align-items:center;
      justify-content:center; cursor:pointer; text-decoration:none; font-size:15px; }
    .cf-ico:hover { background:#e2e8f2; }
    .cf-buscar { margin:0 14px 8px; border:0; background:#eef1f6; border-radius:20px; padding:8px 14px; outline:none; font-size:.92rem; }
    .cf-lista { flex:1; overflow-y:auto; padding:0 6px 8px; }
    .cf-sec { font:700 .72rem system-ui; color:#667085; text-transform:uppercase; letter-spacing:.04em; padding:10px 10px 4px; }
    .cf-fila { display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:10px; cursor:pointer; }
    .cf-fila:hover { background:#f2f4f8; }
    .cf-fila .t { flex:1; min-width:0; }
    .cf-fila .t b { display:block; font-size:.92rem; color:#1d2939; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .cf-fila .t span { display:block; font-size:.8rem; color:#667085; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .cf-fila.nuevo .t b, .cf-fila.nuevo .t span { color:#1d2939; font-weight:700; }
    .cf-fila .n { background:#2b5cbf; color:#fff; border-radius:10px; font:700 11px/18px system-ui; min-width:18px; padding:0 5px; text-align:center; }
    .cf-av { width:40px; height:40px; flex:0 0 40px; border-radius:50%; background:#dfe6f3; color:#1f3a68; display:flex; align-items:center;
      justify-content:center; font:700 15px system-ui; overflow:hidden; }
    .cf-av img { width:100%; height:100%; object-fit:cover; }
    .cf-av.grupo { background:#1f3a68; color:#fff; }
    .cf-av.ch { width:32px; height:32px; flex-basis:32px; font-size:13px; }
    .cf-vacio { text-align:center; color:#667085; font-size:.88rem; padding:30px 18px; }
    .cf-ventana { position:fixed; bottom:0; z-index:1079; width:328px; height:440px; background:#fff; border-radius:12px 12px 0 0;
      box-shadow:0 4px 24px rgba(0,0,0,.25); display:flex; flex-direction:column; font-family:system-ui,-apple-system,'Segoe UI',sans-serif; }
    .cf-ventana.min { height:48px; }
    .cf-ventana.min .cf-msgs, .cf-ventana.min form, .cf-ventana.min .cf-cerrado { display:none; }
    .cf-vcab { display:flex; align-items:center; gap:8px; padding:8px 8px 8px 10px; border-bottom:1px solid #e3e7ef; cursor:pointer; border-radius:12px 12px 0 0; }
    .cf-ventana.alerta .cf-vcab { background:#2b5cbf; }
    .cf-ventana.alerta .cf-vcab b { color:#fff; }
    .cf-vcab b { flex:1; min-width:0; font-size:.93rem; color:#1d2939; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .cf-vcab .cf-x { border:0; background:none; width:28px; height:28px; border-radius:50%; color:#2b5cbf; cursor:pointer; font-size:16px; line-height:1;
      display:inline-flex; align-items:center; justify-content:center; text-decoration:none; }
    .cf-vcab .cf-x:hover { background:#eef1f6; }
    .cf-msgs { flex:1; overflow-y:auto; padding:10px; background:#fff; }
    .cf-m { display:flex; margin:2px 0; }
    .cf-m.mio { justify-content:flex-end; }
    .cf-m .b { max-width:78%; padding:7px 11px; border-radius:16px; background:#eef1f6; color:#1d2939; font-size:.9rem; line-height:1.3; word-wrap:break-word; white-space:pre-wrap; }
    .cf-m.mio .b { background:#2b5cbf; color:#fff; }
    .cf-m .b small { display:block; font-size:.68rem; opacity:.7; margin-top:2px; }
    .cf-m .b i { opacity:.7; }
    .cf-m .b img { max-width:100%; border-radius:10px; display:block; margin-bottom:2px; }
    .cf-m .b a { color:inherit; }
    .cf-m .b audio { width:200px; height:34px; }
    .cf-autor { font:700 .7rem system-ui; color:#e3a226; margin:6px 0 1px 4px; }
    .cf-dia { text-align:center; font-size:.72rem; color:#98a2b3; margin:8px 0 4px; }
    .cf-ventana form { display:flex; gap:6px; padding:8px; border-top:1px solid #e3e7ef; align-items:flex-end; }
    .cf-ventana textarea { flex:1; border:0; background:#eef1f6; border-radius:18px; padding:8px 12px; resize:none; outline:none; font:inherit; font-size:.9rem;
      max-height:90px; height:36px; }
    .cf-ventana form button { width:36px; height:36px; border-radius:50%; border:0; background:none; color:#2b5cbf; cursor:pointer; flex:0 0 36px; }
    .cf-ventana form button:hover { background:#eef1f6; }
    .cf-ventana form button svg { width:20px; height:20px; }
    .cf-cerrado { padding:10px; font-size:.8rem; color:#667085; text-align:center; border-top:1px solid #e3e7ef; }
    `;
    document.head.appendChild(css);

    const ICONO = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.36 2 2 6.13 2 11.7c0 2.91 1.19 5.44 3.14 7.17.16.15.26.35.27.57l.05 1.78c.02.57.6.94 1.12.71l1.99-.88c.17-.07.36-.09.54-.04.91.25 1.88.39 2.89.39 5.64 0 10-4.13 10-9.7S17.64 2 12 2zm-1.06 12.52-2.43-2.6-4.75 2.6 5.22-5.54 2.49 2.6 4.69-2.6-5.22 5.54z"/></svg>';
    const ENVIAR = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z"/></svg>';
    const av = (foto, nombre, grupo, chico) => `<span class="cf-av${grupo ? ' grupo' : ''}${chico ? ' ch' : ''}">${grupo ? '👥' : foto ? `<img src="${esc(foto)}" alt="">` : esc((nombre || '?').trim().charAt(0).toUpperCase())}</span>`;

    // --- Estado guardado (ventanas abiertas) -----------------------------------------------------
    let guardado = {abiertas: []};
    try { guardado = JSON.parse(localStorage.getItem(CLAVE) || '{"abiertas":[]}'); } catch (e) { /* sin almacenamiento */ }
    const guardar = () => { try { localStorage.setItem(CLAVE, JSON.stringify({abiertas: ventanas.map(v => ({id: v.id, min: v.el.classList.contains('min')}))})); } catch (e) { /* nada */ } };

    // --- Botón y panel ------------------------------------------------------------------------------
    const boton = document.createElement('button');
    boton.type = 'button'; boton.className = 'cf-boton'; boton.title = 'Chats con mis colegas'; boton.setAttribute('aria-label', 'Chats con mis colegas');
    boton.innerHTML = ICONO + '<span class="cf-num" hidden></span>';
    document.body.appendChild(boton);
    let panel = null, datos = null;

    function numero(n) { const b = $('.cf-num', boton); b.textContent = n > 99 ? '99+' : n; b.hidden = !n; }
    function cargarLista() {
        return pedir(`${BASE}/mini/`).then(j => { datos = j; if (j.csrf) token = j.csrf; numero((j.n || 0) + (j.solicitudes || 0)); if (panel) pintarLista(); return j; }).catch(() => null);
    }
    function pintarLista() {
        const q = ($('.cf-buscar', panel).value || '').toLowerCase().trim();
        const lista = $('.cf-lista', panel);
        if (!datos) { lista.innerHTML = '<div class="cf-vacio">Cargando…</div>'; return; }
        const convs = datos.convs.filter(c => !q || c.titulo.toLowerCase().includes(q));
        const sin = datos.colegas.filter(c => !c.conv && (!q || c.nombre.toLowerCase().includes(q)));
        let h = '';
        if (datos.solicitudes) h += `<a class="cf-fila" href="${BASE}/?tab=solicitudes" style="text-decoration:none"><span class="cf-av" style="background:#fff3bf">🙋</span><span class="t"><b>${datos.solicitudes} solicitud${datos.solicitudes === 1 ? '' : 'es'} de colegas</b><span>Toque para responder</span></span></a>`;
        if (convs.length) h += '<div class="cf-sec">Chats</div>' + convs.map(c => `<div class="cf-fila${c.sin_leer ? ' nuevo' : ''}" data-conv="${c.id}">${av(c.foto, c.titulo, c.grupo)}
            <span class="t"><b>${esc(c.titulo)}</b><span>${esc(c.previa)}${c.cuando ? ' · ' + esc(c.cuando) : ''}</span></span>${c.sin_leer ? `<span class="n">${c.sin_leer}</span>` : ''}</div>`).join('');
        if (sin.length) h += '<div class="cf-sec">Colegas</div>' + sin.map(c => `<div class="cf-fila" data-usuario="${c.id}">${av(c.foto, c.nombre)}<span class="t"><b>${esc(c.nombre)}</b><span>Escríbale</span></span></div>`).join('');
        if (!h) h = q ? '<div class="cf-vacio">Nadie con ese nombre.</div>'
            : `<div class="cf-vacio">Todavía no tiene chats con colegas.<br><a href="${BASE}/?tab=buscar">Busque docentes</a> y agréguelos.</div>`;
        lista.innerHTML = h;
    }
    function abrirPanel() {
        if (panel) { cerrarPanel(); return; }
        panel = document.createElement('div'); panel.className = 'cf-panel';
        panel.innerHTML = `<header><b>Chats</b>
            <a class="cf-ico" href="${BASE}/grupo/nuevo/" title="Crear un grupo de docentes">👥</a>
            <a class="cf-ico" href="${BASE}/?tab=buscar" title="Agregar colegas">＋</a>
            <a class="cf-ico" href="${BASE}/" title="Abrir Mis colegas completo">⤢</a></header>
            <input class="cf-buscar" placeholder="Buscar en mis chats y colegas" aria-label="Buscar"><div class="cf-lista"></div>`;
        document.body.appendChild(panel);
        $('.cf-buscar', panel).addEventListener('input', pintarLista);
        $('.cf-lista', panel).addEventListener('click', e => {
            const f = e.target.closest('.cf-fila'); if (!f || f.tagName === 'A') return;
            if (f.dataset.conv) abrirVentana(+f.dataset.conv);
            else if (f.dataset.usuario) {
                const fd = new FormData(); fd.append('usuario', f.dataset.usuario);
                pedir(`${BASE}/mini/abrir/`, {method: 'POST', body: fd, headers: {'X-CSRFToken': csrf(), 'X-Requested-With': 'fetch'}}).then(j => j.ok && abrirVentana(j.id));
            }
            cerrarPanel();
        });
        pintarLista(); cargarLista();
        setTimeout(() => $('.cf-buscar', panel) && $('.cf-buscar', panel).focus(), 50);
    }
    function cerrarPanel() { if (panel) { panel.remove(); panel = null; } }
    boton.addEventListener('click', abrirPanel);
    document.addEventListener('click', e => { if (panel && !panel.contains(e.target) && !boton.contains(e.target)) cerrarPanel(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarPanel(); });

    // --- Ventanitas de chat ---------------------------------------------------------------------
    const ventanas = [];
    function ubicar() { ventanas.forEach((v, i) => { v.el.style.right = (96 + i * 340) + 'px'; }); }
    function burbuja(m, grupo, anterior) {
        let cont;
        if (m.eliminado) cont = '<i>Mensaje eliminado</i>';
        else if (m.tipo === 'foto') cont = `<a href="${esc(m.archivo)}" target="_blank" rel="noopener"><img src="${esc(m.archivo)}" alt="Foto" loading="lazy"></a>${esc(m.texto)}`;
        else if (m.tipo === 'voz') cont = `<audio controls preload="none" src="${esc(m.archivo)}"></audio>`;
        else if (m.tipo === 'doc') cont = `📄 <a href="${esc(m.archivo)}" target="_blank" rel="noopener">${esc(m.nombre || 'Documento')}</a>${m.texto ? '<br>' + esc(m.texto) : ''}`;
        else cont = esc(m.texto);
        let h = '';
        if (!anterior || anterior.dia !== m.dia) h += `<div class="cf-dia">${esc(m.dia)}</div>`;
        if (grupo && !m.mio && (!anterior || anterior.autor !== m.autor || anterior.mio)) h += `<div class="cf-autor">${esc(m.autor)}</div>`;
        return h + `<div class="cf-m${m.mio ? ' mio' : ''}" data-id="${m.id}"><div class="b">${cont}<small>${m.editado ? 'editado · ' : ''}${esc(m.hora)}</small></div></div>`;
    }
    function abrirVentana(id, minimizada) {
        let v = ventanas.find(x => x.id === id);
        if (v) { v.el.classList.remove('min', 'alerta'); $('textarea', v.el) && $('textarea', v.el).focus(); guardar(); return; }
        if (ventanas.length >= MAX) cerrarVentana(ventanas[0]);
        const el = document.createElement('div'); el.className = 'cf-ventana' + (minimizada ? ' min' : '');
        el.innerHTML = `<div class="cf-vcab"><span class="cf-av ch">…</span><b>Cargando…</b>
            <a class="cf-x cf-completo" href="${BASE}/c/${id}/" title="Abrir en grande (fotos, notas de voz y documentos)">⤢</a>
            <button type="button" class="cf-x cf-minimizar" title="Minimizar">–</button><button type="button" class="cf-x cf-cerrar" title="Cerrar">✕</button></div>
            <div class="cf-msgs"></div>
            <form autocomplete="off"><textarea rows="1" placeholder="Escriba un mensaje…" aria-label="Mensaje"></textarea><button type="submit" title="Enviar" aria-label="Enviar">${ENVIAR}</button></form>
            <div class="cf-cerrado" hidden></div>`;
        document.body.appendChild(el);
        v = {id, el, ultimo: 0, grupo: false, previo: null, timer: null};
        ventanas.push(v); ubicar(); guardar();
        $('.cf-vcab', el).addEventListener('click', e => {
            if (e.target.closest('.cf-cerrar')) { cerrarVentana(v); return; }
            if (e.target.closest('.cf-completo')) return;
            el.classList.toggle('min'); el.classList.remove('alerta'); guardar();
            if (!el.classList.contains('min')) { bajar(v); $('textarea', el).focus(); }
        });
        const ta = $('textarea', el), form = $('form', el);
        ta.addEventListener('input', () => { ta.style.height = '36px'; ta.style.height = Math.min(90, ta.scrollHeight) + 'px'; });
        ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
        form.addEventListener('submit', e => {
            e.preventDefault();
            const texto = ta.value.trim(); if (!texto) return;
            ta.value = ''; ta.style.height = '36px';
            pedir(`${BASE}/c/${id}/enviar/`, {method: 'POST', body: JSON.stringify({texto}),
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf(), 'X-Requested-With': 'fetch'}})
                .then(j => { if (j.ok) agregar(v, [j.mensaje]); })
                .catch(() => { ta.value = texto; alert('No se pudo enviar. Revise la conexión.'); });
        });
        pedir(`${BASE}/mini/c/${id}/`).then(j => {
            v.grupo = j.grupo;
            $('.cf-vcab .cf-av', el).outerHTML = av(j.foto, j.titulo, j.grupo, true);
            $('.cf-vcab b', el).textContent = j.titulo;
            permitir(v, j.puede_escribir);
            agregar(v, j.mensajes, true);
            v.listo = true;
            cargarLista();
        }).catch(() => cerrarVentana(v));
        v.timer = setInterval(() => sondear(v), 4000);
        if (!minimizada) setTimeout(() => ta.focus(), 50);
    }
    function permitir(v, si) {
        $('form', v.el).hidden = !si;
        const c = $('.cf-cerrado', v.el); c.hidden = si;
        c.textContent = v.grupo ? 'En este grupo solo escriben los moderadores.' : 'Ya no son colegas: no se pueden escribir.';
    }
    function bajar(v) { const m = $('.cf-msgs', v.el); m.scrollTop = m.scrollHeight; }
    function agregar(v, mensajes, inicio) {
        const caja = $('.cf-msgs', v.el);
        let nuevosAjenos = 0;
        mensajes.forEach(m => {
            if (m.id <= v.ultimo) return;
            caja.insertAdjacentHTML('beforeend', burbuja(m, v.grupo, v.previo));
            v.previo = m; v.ultimo = m.id;
            if (!m.mio) nuevosAjenos++;
        });
        if (inicio && !mensajes.length) caja.innerHTML = '<div class="cf-vacio">Salude a su colega 👋</div>';
        else if (caja.querySelector('.cf-vacio') && mensajes.length) caja.querySelector('.cf-vacio').remove();
        bajar(v);
        if (!inicio && nuevosAjenos && v.el.classList.contains('min')) v.el.classList.add('alerta');
    }
    function sondear(v) {
        if (document.hidden || !v.listo) return;
        pedir(`${BASE}/c/${v.id}/nuevos/?despues=${v.ultimo}`).then(j => {
            if (j.mensajes && j.mensajes.length) agregar(v, j.mensajes);
            (j.borrados || []).forEach(id => { const b = $(`.cf-m[data-id="${id}"] .b`, v.el); if (b) b.innerHTML = '<i>Mensaje eliminado</i>'; });
            // Mensajes de texto que su autor editó
            (j.editados || []).forEach(x => {
                const b = $(`.cf-m[data-id="${x.id}"] .b`, v.el);
                if (!b || b.querySelector('img, audio, a, i')) return;
                const hora = (($('small', b) || {}).textContent || '').replace(/^editado · /, '');
                b.innerHTML = `${esc(x.texto)}<small>editado · ${esc(hora)}</small>`;
            });
            permitir(v, j.puede_escribir);
        }).catch(() => {});
    }
    function cerrarVentana(v) {
        clearInterval(v.timer); v.el.remove();
        ventanas.splice(ventanas.indexOf(v), 1); ubicar(); guardar();
    }

    // --- Arranque: recupera las ventanas abiertas y cuenta lo sin leer ---------------------------
    (guardado.abiertas || []).slice(-MAX).forEach(x => abrirVentana(x.id, x.min));
    cargarLista();
    setInterval(() => { if (!document.hidden) cargarLista(); }, 20000);
    window.ChatFlotante = {abrir: abrirVentana};
})();
