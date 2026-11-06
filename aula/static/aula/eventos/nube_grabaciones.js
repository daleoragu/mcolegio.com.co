/* Copia las grabaciones de un evento a la nube del organizador (Google Drive u OneDrive).
 * El permiso lo da el organizador en una ventanita (/nube/<proveedor>/, el mismo de la copia de seguridad)
 * y la subida va directo de su navegador a su nube: el permiso no pasa por el servidor.
 * Quedan en «mcolegio · grabaciones / <evento> / <participante>». Opcional: borrarlas del servidor al terminar.
 *
 *   botones con data-nube="google|onedrive" y data-pid (vacío = todo el evento) dentro de .ng-panel
 */
(function () {
  'use strict';
  const CFG = JSON.parse(document.getElementById('ng-config').textContent);
  const RAIZ = 'mcolegio · grabaciones', NOMBRE = {google: 'Google Drive', onedrive: 'OneDrive'};

  // --- Permiso (mismo canal que la copia de seguridad: BroadcastChannel «mcolegio-nube») ---
  function permiso(p) {
    try { const t = JSON.parse(sessionStorage.getItem('cp-token-' + p) || 'null'); return t && t.expira > Date.now() ? t.token : null; } catch (e) { return null; }
  }
  let esperando = null;
  function recibir(d) {
    if (!d || !esperando || d.proveedor !== esperando.p) return;
    if (d.tipo === 'token') {
      try { sessionStorage.setItem('cp-token-' + d.proveedor, JSON.stringify({token: d.token, expira: d.expira})); } catch (e) { /* sin almacenamiento */ }
      const ok = esperando.ok; esperando = null; ok(d.token);
    } else if (d.tipo === 'error') { const no = esperando.no; esperando = null; no(new Error(d.error)); }
  }
  try { new BroadcastChannel('mcolegio-nube').onmessage = ev => recibir(ev.data); } catch (e) { /* navegador viejo */ }
  window.addEventListener('message', ev => { if (ev.origin === location.origin) recibir(ev.data); });
  function pedirPermiso(p) {
    const ya = permiso(p);
    if (ya) return Promise.resolve(ya);
    const v = window.open(CFG.ayudante.replace('PROV', p), 'cp-nube', 'width=520,height=680');
    if (!v) return Promise.reject(new Error('El navegador bloqueó la ventana para conectar ' + NOMBRE[p] + '. Permita las ventanas emergentes e intente de nuevo.'));
    return new Promise((ok, no) => { esperando = {p, ok, no}; });
  }
  async function api(p, url, op) {
    op = op || {};
    op.headers = Object.assign({Authorization: 'Bearer ' + permiso(p)}, op.headers || {});
    const r = await fetch(url, op);
    if (r.status === 401) { try { sessionStorage.removeItem('cp-token-' + p); } catch (e) { /* nada */ } throw new Error('El permiso de ' + NOMBRE[p] + ' venció. Intente de nuevo.'); }
    if (!r.ok) throw new Error(NOMBRE[p] + ' respondió ' + r.status + '.');
    return r;
  }

  // --- Google Drive: carpetas anidadas (permiso drive.file: solo ve lo que crea la plataforma) ---
  const carpetasG = {};
  async function carpetaGoogle(nombre, padre) {
    const k = (padre || 'root') + '/' + nombre;
    if (carpetasG[k]) return carpetasG[k];
    const esc = nombre.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    const q = encodeURIComponent(`name='${esc}' and mimeType='application/vnd.google-apps.folder' and trashed=false` + (padre ? ` and '${padre}' in parents` : ''));
    const d = await (await api('google', 'https://www.googleapis.com/drive/v3/files?q=' + q + '&fields=files(id)')).json();
    if (d.files && d.files.length) return (carpetasG[k] = d.files[0].id);
    const f = await (await api('google', 'https://www.googleapis.com/drive/v3/files?fields=id', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(Object.assign({name: nombre, mimeType: 'application/vnd.google-apps.folder'}, padre ? {parents: [padre]} : {}))})).json();
    return (carpetasG[k] = f.id);
  }
  async function subirGoogle(ruta, nombre, blob) {
    let padre = null;
    for (const c of ruta) padre = await carpetaGoogle(c, padre);
    const cuerpo = new FormData();
    cuerpo.append('metadata', new Blob([JSON.stringify({name: nombre, parents: [padre]})], {type: 'application/json'}));
    cuerpo.append('file', blob);
    await api('google', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id', {method: 'POST', body: cuerpo});
  }
  // --- OneDrive: por ruta (crea las carpetas solo); trozos pequeños, una sola petición ---
  async function subirOneDrive(ruta, nombre, blob) {
    const camino = ruta.concat([nombre]).map(encodeURIComponent).join('/');
    await api('onedrive', `https://graph.microsoft.com/v1.0/me/drive/root:/${camino}:/content?@microsoft.graph.conflictBehavior=replace`,
              {method: 'PUT', headers: {'Content-Type': blob.type || 'video/webm'}, body: blob});
  }

  async function servidor(datos) {
    const r = await fetch(CFG.nube, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf}, body: JSON.stringify(datos)});
    return r.json();
  }

  async function copiar(boton) {
    const panel = boton.closest('.ng-panel'), estado = panel.querySelector('.ng-estado'), barra = panel.querySelector('.ng-barra');
    const p = boton.dataset.nube, pid = boton.dataset.pid || '', borrar = (panel.querySelector('.ng-borrar') || {}).checked;
    const decir = (t, mal) => { estado.textContent = t; estado.className = 'ng-estado small mt-1 ' + (mal ? 'text-danger' : 'text-success'); };
    if (borrar && !confirm('Cuando cada trozo quede en ' + NOMBRE[p] + ' se borrará de la plataforma. ¿Seguir?')) return;
    panel.querySelectorAll('button').forEach(b => { b.disabled = true; });
    try {
      decir('Conectando ' + NOMBRE[p] + '…');
      await pedirPermiso(p);
      const lista = await (await fetch(CFG.nube + (pid ? '?pid=' + pid : ''), {credentials: 'same-origin'})).json();
      const todos = [];
      lista.personas.forEach(x => x.trozos.forEach(t => todos.push({x, t})));
      const faltan = todos.filter(o => o.t.nube !== p);
      if (!todos.length) { decir('No hay grabaciones para copiar.'); return; }
      let hechos = 0, listos = todos.filter(o => o.t.nube === p).map(o => o.t.id);
      if (barra) barra.hidden = false;
      for (const {x, t} of faltan) {
        decir(`Copiando ${hechos + 1} de ${faltan.length} a ${NOMBRE[p]}… (${x.nombre})`);
        const blob = await (await fetch(t.url, {credentials: 'same-origin'})).blob();
        const ruta = [RAIZ, lista.evento, x.nombre + (x.de ? ' - ' + x.de : '')];
        if (p === 'google') await subirGoogle(ruta, t.archivo, blob); else await subirOneDrive(ruta, t.archivo, blob);
        await servidor({accion: 'marcar', nube: p, ids: [t.id]});
        listos.push(t.id); hechos += 1;
        if (barra) barra.firstElementChild.style.width = (100 * hechos / faltan.length) + '%';
      }
      let fin = `Listo: ${todos.length} trozo(s) en ${NOMBRE[p]}, en la carpeta «${RAIZ} / ${lista.evento}».`;
      if (borrar && listos.length) {
        const r = await servidor({accion: 'borrar', ids: listos});
        fin += ` Se borraron ${r.n} de la plataforma.`;
      }
      decir(fin);
      if (borrar) setTimeout(() => location.reload(), 2500);
    } catch (e) {
      decir((e && e.message) || 'No se pudo copiar. Intente de nuevo: lo que ya quedó en la nube no se vuelve a subir.', true);
    } finally {
      panel.querySelectorAll('button').forEach(b => { b.disabled = false; });
    }
  }
  document.querySelectorAll('.ng-panel [data-nube]').forEach(b => b.addEventListener('click', () => copiar(b)));
})();
