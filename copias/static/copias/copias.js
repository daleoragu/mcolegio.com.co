/* Copia de seguridad: arma el .zip en el servidor y lo sube a Google Drive u OneDrive con el permiso
 * de la persona (el permiso se pide en una ventanita y no pasa por el servidor), o lo descarga. */
(function () {
  'use strict';
  var CFG = JSON.parse(document.getElementById('cp-config').textContent);
  var token = document.querySelector('#cp-token [name=csrfmiddlewaretoken]').value;
  var boton = document.getElementById('cp-hacer'), estado = document.getElementById('cp-estado');
  var barra = document.getElementById('cp-barra'), relleno = barra.querySelector('div');
  var CARPETA = 'mcolegio · copias de seguridad', CONSERVAR = 4;
  var NOMBRE = { google: 'Google Drive', onedrive: 'OneDrive', descarga: 'este dispositivo' };

  function decir(texto, error) { estado.textContent = texto; estado.className = 'cp-estado small mt-2' + (error ? ' text-danger' : ''); }
  function avance(p) { barra.classList.remove('d-none'); relleno.style.width = Math.max(3, Math.min(100, p)) + '%'; }
  function destino() { var r = document.querySelector('input[name=destino]:checked'); return r ? r.value : CFG.destino; }
  function conMedios() { var c = document.getElementById('cp-medios'); return c ? c.checked : CFG.medios; }

  // --- Permiso de la nube (mismo canal que usan PuntoExacto y Mis materiales) ---
  function permiso(p) {
    try { var t = JSON.parse(sessionStorage.getItem('cp-token-' + p) || 'null'); return t && t.expira > Date.now() ? t.token : null; }
    catch (e) { return null; }
  }
  var esperando = null;
  function recibir(d) {
    if (!d || !esperando || d.proveedor !== esperando.p) return;
    if (d.tipo === 'token') {
      try { sessionStorage.setItem('cp-token-' + d.proveedor, JSON.stringify({ token: d.token, expira: d.expira })); } catch (e) {}
      var ok = esperando.ok; esperando = null; ok(d.token);
    } else if (d.tipo === 'error') { var no = esperando.no; esperando = null; no(new Error(d.error)); }
  }
  try { new BroadcastChannel('mcolegio-nube').onmessage = function (ev) { recibir(ev.data); }; } catch (e) {}
  window.addEventListener('message', function (ev) { if (ev.origin === location.origin) recibir(ev.data); });
  function pedirPermiso(p) {
    var ya = permiso(p);
    if (ya) return Promise.resolve(ya);
    var ventana = window.open(CFG.ayudante.replace('PROV', p), 'cp-nube', 'width=520,height=680');
    if (!ventana) return Promise.reject(new Error('El navegador bloqueó la ventana para conectar ' + NOMBRE[p] + '. Permita las ventanas emergentes e intente de nuevo.'));
    return new Promise(function (ok, no) { esperando = { p: p, ok: ok, no: no }; });
  }
  function api(p, url, op) {
    op = op || {};
    op.headers = Object.assign({ Authorization: 'Bearer ' + permiso(p) }, op.headers || {});
    return fetch(url, op).then(function (r) {
      if (r.status === 401) { try { sessionStorage.removeItem('cp-token-' + p); } catch (e) {} throw new Error('El permiso de ' + NOMBRE[p] + ' venció. Intente de nuevo.'); }
      if (!r.ok) throw new Error(NOMBRE[p] + ' respondió ' + r.status + '.');
      return r;
    });
  }

  // --- Google Drive (permiso drive.file: solo ve lo que la plataforma creó) ---
  function carpetaGoogle() {
    var q = encodeURIComponent("name='" + CARPETA + "' and mimeType='application/vnd.google-apps.folder' and trashed=false");
    return api('google', 'https://www.googleapis.com/drive/v3/files?q=' + q + '&fields=files(id)').then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.files && d.files.length) return d.files[0].id;
        return api('google', 'https://www.googleapis.com/drive/v3/files?fields=id', { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: CARPETA, mimeType: 'application/vnd.google-apps.folder' }) }).then(function (r) { return r.json(); }).then(function (f) { return f.id; });
      });
  }
  function subirGoogle(blob) {
    return carpetaGoogle().then(function (carpeta) {
      var meta = JSON.stringify({ name: CFG.nombre, parents: [carpeta], mimeType: 'application/zip' });
      return api('google', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id', {
        method: 'POST', headers: { 'Content-Type': 'application/json; charset=UTF-8', 'X-Upload-Content-Type': 'application/zip' }, body: meta
      }).then(function (r) {
        var destino = r.headers.get('Location');
        if (destino) return enviarConAvance('PUT', destino, blob, {});
        var cuerpo = new FormData();          // sin la dirección de subida: en una sola petición
        cuerpo.append('metadata', new Blob([meta], { type: 'application/json' }));
        cuerpo.append('file', blob);
        return api('google', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id', { method: 'POST', body: cuerpo });
      }).then(function () { return limpiarGoogle(carpeta); });
    });
  }
  function limpiarGoogle(carpeta) {
    var q = encodeURIComponent("'" + carpeta + "' in parents and trashed=false and name contains 'mcolegio-copia-'");
    return api('google', 'https://www.googleapis.com/drive/v3/files?q=' + q + '&orderBy=createdTime desc&fields=files(id)&pageSize=50')
      .then(function (r) { return r.json(); })
      .then(function (d) { return Promise.all((d.files || []).slice(CONSERVAR).map(function (f) {
        return api('google', 'https://www.googleapis.com/drive/v3/files/' + f.id, { method: 'DELETE' }).catch(function () {});
      })); }).catch(function () {});
  }

  // --- OneDrive (sesión de subida por partes: sirve para archivos grandes) ---
  function subirOneDrive(blob) {
    var ruta = encodeURIComponent(CARPETA) + '/' + encodeURIComponent(CFG.nombre);
    return api('onedrive', 'https://graph.microsoft.com/v1.0/me/drive/root:/' + ruta + ':/createUploadSession', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item: { '@microsoft.graph.conflictBehavior': 'rename' } })
    }).then(function (r) { return r.json(); }).then(function (s) {
      var PARTE = 320 * 1024 * 32, total = blob.size, inicio = 0;      // 10 MB, múltiplo de 320 KB
      function siguiente() {
        if (inicio >= total) return Promise.resolve();
        var fin = Math.min(inicio + PARTE, total);
        return fetch(s.uploadUrl, { method: 'PUT', headers: { 'Content-Range': 'bytes ' + inicio + '-' + (fin - 1) + '/' + total },
          body: blob.slice(inicio, fin) }).then(function (r) {
            if (!r.ok && r.status !== 202) throw new Error('OneDrive respondió ' + r.status + '.');
            inicio = fin; avance(50 + 50 * inicio / total); return siguiente();
          });
      }
      return siguiente();
    }).then(limpiarOneDrive);
  }
  function limpiarOneDrive() {
    return api('onedrive', 'https://graph.microsoft.com/v1.0/me/drive/root:/' + encodeURIComponent(CARPETA) + ':/children?$select=id,name,createdDateTime&$top=100')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var copias = (d.value || []).filter(function (f) { return f.name.indexOf('mcolegio-copia-') === 0; })
          .sort(function (a, b) { return a.createdDateTime < b.createdDateTime ? 1 : -1; });
        return Promise.all(copias.slice(CONSERVAR).map(function (f) {
          return api('onedrive', 'https://graph.microsoft.com/v1.0/me/drive/items/' + f.id, { method: 'DELETE' }).catch(function () {});
        }));
      }).catch(function () {});
  }

  function enviarConAvance(metodo, url, blob, cabeceras) {
    return new Promise(function (ok, no) {
      var x = new XMLHttpRequest();
      x.open(metodo, url);
      Object.keys(cabeceras).forEach(function (k) { x.setRequestHeader(k, cabeceras[k]); });
      x.upload.onprogress = function (e) { if (e.lengthComputable) avance(50 + 50 * e.loaded / e.total); };
      x.onload = function () { x.status < 300 ? ok() : no(new Error('La nube respondió ' + x.status + '.')); };
      x.onerror = function () { no(new Error('Se cortó la conexión mientras subía la copia.')); };
      x.send(blob);
    });
  }

  function armar() {
    decir('Preparando su copia… puede tardar un poco.');
    avance(10);
    return fetch(CFG.generar + '?medios=' + (conMedios() ? '1' : '0'), { credentials: 'same-origin' }).then(function (r) {
      if (!r.ok) throw new Error('No se pudo preparar la copia (' + r.status + ').');
      return r.blob();
    }).then(function (b) { avance(50); return b; });
  }

  function registrar(p, blob) {
    return fetch(CFG.hecha, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
      body: JSON.stringify({ destino: p, peso: blob.size }) }).then(function (r) { return r.json(); }).then(function (j) {
        var mb = (blob.size / 1024 / 1024).toFixed(1).replace('.', ',');
        document.getElementById('cp-ultima').textContent = j.ultima + ' · ' + (p === 'descarga' ? 'Descargar al dispositivo' : NOMBRE[p]) + ' · ' + mb + ' MB';
      });
  }

  boton.addEventListener('click', function () {
    var p = destino();
    boton.disabled = true;
    var listo;
    if (p === 'descarga') {
      listo = armar().then(function (blob) {
        var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = CFG.nombre;
        document.body.appendChild(a); a.click(); a.remove();
        avance(100); return registrar(p, blob).then(function () { decir('Listo: la copia se descargó.'); });
      });
    } else {
      var conPermiso = pedirPermiso(p);          // la ventanita se abre con el toque, antes de esperar nada
      var archivo = armar();
      listo = Promise.all([conPermiso, archivo]).then(function (r) {
        decir('Subiendo a ' + NOMBRE[p] + '…');
        return (p === 'google' ? subirGoogle(r[1]) : subirOneDrive(r[1])).then(function () {
          avance(100); return registrar(p, r[1]);
        }).then(function () { decir('Listo: la copia quedó en ' + NOMBRE[p] + ', en la carpeta «' + CARPETA + '».'); });
      });
    }
    listo.catch(function (e) { decir(e.message || 'No se pudo hacer la copia.', true); barra.classList.add('d-none'); })
      .then(function () { boton.disabled = false; });
  });
})();
