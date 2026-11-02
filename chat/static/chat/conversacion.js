/* Conversación del chat (colegio y Mi Salón Virtual). La página trae su configuración en #ch-config. */
(function () {
  if (!document.getElementById('ch-config')) return;
  var muro = document.getElementById('ch-muro'), form = document.getElementById('ch-form'), caja = document.getElementById('ch-texto');
  var botonEnviar = document.getElementById('ch-enviar'), mic = document.getElementById('ch-mic'), entradaFoto = document.getElementById('ch-foto');
  var CFG = JSON.parse(document.getElementById('ch-config').textContent);
  var token = document.querySelector('#ch-token [name=csrfmiddlewaretoken]').value;
  var URL_NUEVOS = CFG.nuevos, URL_ENVIAR = CFG.enviar, URL_ACCION = CFG.accion;
  var fotoElegida = null;

  function ultimo() { var x = muro.querySelectorAll('.ch-msg[data-id]'); return x.length ? +x[x.length - 1].getAttribute('data-id') : 0; }
  function abajo() { muro.scrollTop = muro.scrollHeight; }
  function cuerpoDe(m) {
    var c = document.createElement('div'); c.className = 'b';
    if (CFG.autores && !m.mio) { var au = document.createElement('b'); au.className = 'ch-autor'; au.textContent = m.autor; c.appendChild(au); }
    var hora = document.createElement('span'); hora.className = 'ch-hora'; hora.textContent = m.hora;
    if (m.eliminado) { c.appendChild(document.createTextNode('Mensaje eliminado')); c.appendChild(hora); return c; }
    if (m.tipo === 'foto' && m.archivo) { var i = document.createElement('img'); i.src = m.archivo; i.alt = 'Foto'; i.loading = 'lazy'; i.onload = function () { if (cercaDelFinal(200)) abajo(); }; c.appendChild(i); }
    if (m.tipo === 'voz' && m.archivo) { var a = document.createElement('audio'); a.controls = true; a.preload = 'metadata'; a.src = m.archivo; c.appendChild(a); }
    if (m.tipo === 'doc' && m.archivo) c.appendChild(tarjetaDoc(m.nombre || 'Documento', (m.peso_txt || '') + ' · Descargar', m.archivo));
    if (m.texto) { var s = document.createElement('span'); s.className = 'ch-pie'; s.textContent = m.texto; c.appendChild(s); }
    c.appendChild(hora);
    return c;
  }
  function claseDoc(nombre) {
    var n = (nombre || '').toLowerCase();
    if (/\.pdf$/.test(n)) return ['pdf', 'PDF'];
    if (/\.(xls|xlsx|ods)$/.test(n)) return ['xls', 'XLS'];
    if (/\.(ppt|pptx|odp)$/.test(n)) return ['ppt', 'PPT'];
    return ['doc', 'DOC'];
  }
  function tarjetaDoc(nombre, detalle, url) {
    var t = document.createElement(url ? 'a' : 'span'); t.className = 'ch-docu';
    if (url) { t.href = url; t.target = '_blank'; t.rel = 'noopener'; t.title = 'Descargar'; }
    var k = claseDoc(nombre), ico = document.createElement('span'); ico.className = 'ico ' + k[0]; ico.textContent = k[1];
    var txt = document.createElement('span'); txt.className = 'txt';
    var b = document.createElement('b'); b.textContent = nombre; var sm = document.createElement('small'); sm.textContent = detalle;
    txt.appendChild(b); txt.appendChild(sm); t.appendChild(ico); t.appendChild(txt);
    return t;
  }
  function pesoTxt(n) { return n >= 1048576 ? (n / 1048576).toFixed(1).replace('.', ',') + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB'; }
  function dibujar(m) {
    if (muro.querySelector('.ch-msg[data-id="' + m.id + '"]')) return;
    var d = document.createElement('div');
    d.className = 'ch-msg' + (m.mio ? ' mio' : '') + (m.eliminado ? ' borrado' : '');
    d.setAttribute('data-id', m.id);
    var dias = muro.querySelectorAll('.ch-dia');
    var ultimoDia = dias.length ? dias[dias.length - 1].getAttribute('data-dia') : '';
    if (m.dia && m.dia !== ultimoDia) {
      var sep = document.createElement('div'); sep.className = 'ch-dia'; sep.setAttribute('data-dia', m.dia);
      var sp = document.createElement('span'); sp.textContent = m.dia; sep.appendChild(sp); muro.appendChild(sep);
    }
    var acc = document.createElement('div'); acc.className = 'm';
    if (m.puede_borrar) { var x = document.createElement('button'); x.type = 'button'; x.className = 'ch-borrar'; x.setAttribute('data-id', m.id); x.textContent = 'Borrar'; acc.appendChild(x); }
    if (CFG.reportar && !m.mio && !m.eliminado) { var r = document.createElement('button'); r.type = 'button'; r.className = 'ch-reportar'; r.setAttribute('data-id', m.id); r.textContent = 'Reportar'; acc.appendChild(r); }
    d.appendChild(cuerpoDe(m)); d.appendChild(acc);
    muro.appendChild(d);
  }
  function borradoEnPantalla(id) {
    var d = muro.querySelector('.ch-msg[data-id="' + id + '"]');
    if (!d || d.classList.contains('borrado')) return;
    d.classList.add('borrado'); var b = d.querySelector('.b'); var h = b.querySelector('.ch-hora'); var au = b.querySelector('.ch-autor');
    b.innerHTML = ''; if (au) b.appendChild(au); b.appendChild(document.createTextNode('Mensaje eliminado')); if (h) b.appendChild(h);
    d.querySelectorAll('button').forEach(function (x) { x.remove(); });
  }
  function cercaDelFinal(px) { return muro.scrollHeight - muro.scrollTop - muro.clientHeight < (px || 80); }
  function traer() {
    fetch(URL_NUEVOS + '?despues=' + ultimo(), { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (j) {
      var cerca = cercaDelFinal();
      (j.mensajes || []).forEach(dibujar);
      (j.borrados || []).forEach(borradoEnPantalla);
      if (form && 'puede_escribir' in j) { form.classList.toggle('d-none', !j.puede_escribir); if (rapidas) rapidas.classList.toggle('d-none', !j.puede_escribir); var ce = document.getElementById('ch-cerrado'); if (ce) ce.classList.toggle('d-none', !!j.puede_escribir); }
      if ((j.mensajes || []).length && cerca) abajo();
    }).catch(function () {});
  }
  function mandar(datos, alFallar) {
    var opciones = { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': token } };
    if (datos instanceof FormData) opciones.body = datos;
    else { opciones.headers['Content-Type'] = 'application/json'; opciones.body = JSON.stringify(datos); }
    botonEnviar.disabled = true;
    return fetch(URL_ENVIAR, opciones).then(function (r) { return r.json(); }).then(function (j) {
      botonEnviar.disabled = false;
      if (j.ok) { dibujar(j.mensaje); abajo(); } else { alFallar(); alert(j.error || 'No se envió.'); }
    }).catch(function () { botonEnviar.disabled = false; alFallar(); alert('Sin conexión: no se envió.'); });
  }

  // Botón de enviar o micrófono, como en WhatsApp: con texto o foto se envía; vacío, se graba.
  var rapidas = document.getElementById('ch-rapidas');
  if (rapidas) rapidas.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    mandar({ texto: b.textContent.trim() }, function () {});
  });
  function alternar() {
    if (rapidas && form && !form.classList.contains('d-none')) rapidas.classList.toggle('d-none', !!(caja.value.trim() || fotoElegida));
    if (!mic) return;
    var hayAlgo = caja.value.trim() || fotoElegida;
    botonEnviar.classList.toggle('d-none', !hayAlgo);
    mic.classList.toggle('d-none', !!hayAlgo);
  }
  function crecer() { caja.style.height = 'auto'; caja.style.height = Math.min(caja.scrollHeight, 120) + 'px'; }
  if (caja) {
    caja.addEventListener('input', function () { crecer(); alternar(); });
    caja.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey && window.matchMedia('(pointer:fine)').matches) { e.preventDefault(); form.requestSubmit(); }
    });
  }
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    var texto = caja.value.trim();
    if (fotoElegida) {
      var f = new FormData(); f.append('archivo', fotoElegida); f.append('texto', texto);
      if (esDocumento) f.append('tipo', 'doc');
      var guardada = fotoElegida, eraDoc = esDocumento; quitarFoto(); caja.value = ''; crecer(); alternar();
      mandar(f, function () { elegirFoto(guardada, eraDoc); caja.value = texto; alternar(); });
      return;
    }
    if (!texto) return;
    caja.value = ''; crecer(); alternar();
    mandar({ texto: texto }, function () { caja.value = texto; alternar(); });
  });

  // Fotos
  var previa = document.getElementById('ch-previa');
  var esDocumento = false, entradaDoc = document.getElementById('ch-doc');
  function elegirFoto(archivo, doc) {
    fotoElegida = archivo; esDocumento = !!doc;
    var img = document.getElementById('ch-previa-img'), pd = document.getElementById('ch-previa-doc');
    img.classList.toggle('d-none', esDocumento); pd.classList.toggle('d-none', !esDocumento);
    if (esDocumento) { pd.replaceWith(tarjetaDoc(archivo.name, pesoTxt(archivo.size))); document.querySelector('#ch-previa .ch-docu').id = 'ch-previa-doc'; }
    else img.src = URL.createObjectURL(archivo);
    previa.classList.remove('d-none'); alternar(); caja.focus();
  }
  function quitarFoto() { fotoElegida = null; esDocumento = false; if (entradaFoto) entradaFoto.value = ''; if (entradaDoc) entradaDoc.value = ''; previa.classList.add('d-none'); alternar(); }
  if (entradaDoc) entradaDoc.addEventListener('change', function () {
    var a = entradaDoc.files[0]; if (!a) return;
    if (!/\.(pdf|docx?|xlsx?|pptx?|odt|ods|odp|txt)$/i.test(a.name)) { alert('Ese tipo de archivo no se puede enviar. Sirven PDF, Word, Excel, PowerPoint y texto.'); entradaDoc.value = ''; return; }
    if (a.size > 15 * 1024 * 1024) { alert('El documento pasa de 15 MB.'); entradaDoc.value = ''; return; }
    elegirFoto(a, true);
  });
  if (entradaFoto) entradaFoto.addEventListener('change', function () {
    var a = entradaFoto.files[0]; if (!a) return;
    if (!/^image\//.test(a.type)) { alert('Escoja una imagen.'); return; }
    if (a.size > 10 * 1024 * 1024) { alert('La foto pasa de 10 MB.'); return; }
    elegirFoto(a);
  });
  var quitar = document.getElementById('ch-quitar-foto'); if (quitar) quitar.addEventListener('click', quitarFoto);

  // Notas de voz
  var grabando = document.getElementById('ch-grabando'), cajaTexto = document.getElementById('ch-caja'), reloj = document.getElementById('ch-reloj');
  var grabadora = null, partes = [], inicio = 0, tic = null, limite = null, cancelada = false;
  function mmss(s) { return Math.floor(s / 60) + ':' + ('0' + Math.floor(s % 60)).slice(-2); }
  function modoGrabando(si) {
    grabando.classList.toggle('d-none', !si); cajaTexto.classList.toggle('d-none', si);
    document.querySelectorAll('.ch-clip').forEach(function (clip) { clip.style.setProperty('display', si ? 'none' : '', 'important'); });
    mic.innerHTML = si ? '<i class="fas fa-paper-plane"></i>' : '<i class="fas fa-microphone"></i>';
    mic.setAttribute('aria-label', si ? 'Enviar la nota de voz' : 'Grabar nota de voz');
  }
  if (mic) {
    if (!(navigator.mediaDevices && window.MediaRecorder)) { mic.remove(); mic = null; alternar(); botonEnviar.classList.remove('d-none'); }
    else {
      alternar();
      mic.addEventListener('click', function () {
        if (grabadora && grabadora.state === 'recording') { cancelada = false; grabadora.stop(); return; }
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (flujo) {
          partes = []; cancelada = false;
          grabadora = new MediaRecorder(flujo);
          grabadora.ondataavailable = function (ev) { if (ev.data.size) partes.push(ev.data); };
          grabadora.onstop = function () {
            clearInterval(tic); clearTimeout(limite);
            flujo.getTracks().forEach(function (p) { p.stop(); });
            modoGrabando(false);
            var segundos = Math.round((Date.now() - inicio) / 1000);
            if (cancelada || segundos < 1 || !partes.length) return;
            var tipo = (grabadora.mimeType || 'audio/webm').split(';')[0];
            var ext = tipo.indexOf('mp4') >= 0 ? 'm4a' : tipo.indexOf('ogg') >= 0 ? 'ogg' : 'webm';
            var f = new FormData();
            f.append('archivo', new File([new Blob(partes, { type: tipo })], 'voz.' + ext, { type: tipo }));
            f.append('duracion', segundos);
            mandar(f, function () {});
          };
          grabadora.start();
          inicio = Date.now(); reloj.textContent = '0:00'; modoGrabando(true);
          tic = setInterval(function () { reloj.textContent = mmss((Date.now() - inicio) / 1000); }, 500);
          limite = setTimeout(function () { if (grabadora.state === 'recording') grabadora.stop(); }, 300000);
        }).catch(function () { alert('No se pudo usar el micrófono. Revise el permiso del navegador.'); });
      });
      document.getElementById('ch-cancelar').addEventListener('click', function () {
        if (grabadora && grabadora.state === 'recording') { cancelada = true; grabadora.stop(); }
      });
    }
  }

  // Ver la foto en grande, borrar y reportar
  var visor = document.getElementById('ch-visor');
  visor.addEventListener('click', function () { visor.classList.add('d-none'); });
  document.querySelectorAll('.ch-ver-foto').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); visor.querySelector('img').src = a.getAttribute('data-src'); visor.classList.remove('d-none'); });
  });
  muro.addEventListener('click', function (e) {
    var img = e.target.closest('.b img');
    if (img) { visor.querySelector('img').src = img.src; visor.classList.remove('d-none'); return; }
    var b = e.target.closest('button'); if (!b) return;
    var id = b.getAttribute('data-id');
    if (b.classList.contains('ch-borrar')) {
      if (!confirm('¿Borrar este mensaje? Quedará como «mensaje eliminado».')) return;
      var f = new FormData(); f.append('accion', 'borrar'); f.append('mensaje', id);
      fetch(URL_ACCION, { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': token, 'X-Requested-With': 'fetch' }, body: f })
        .then(function () { borradoEnPantalla(id); });
    } else if (b.classList.contains('ch-reportar')) {
      var motivo = prompt('¿Qué tiene de malo este mensaje? Lo revisan los directivos del colegio.');
      if (!motivo || !CFG.reportar) return;
      var rf = document.getElementById('ch-reporte');
      rf.action = CFG.reportar.replace('ID', id); rf.motivo.value = motivo; rf.submit();
    }
  });
  abajo();
  setTimeout(abajo, 400);
  setInterval(function () { if (!document.hidden) traer(); }, 5000);
})();
