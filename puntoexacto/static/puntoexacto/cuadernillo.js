/* PuntoExacto · escribir el examen.
 *
 * El texto (preguntas, opciones, respuesta correcta) se guarda en la plataforma
 * y actualiza la clave. Las imágenes NO: se suben a la nube del docente (Google
 * Drive u OneDrive) directamente desde este navegador, y se guarda una copia
 * aquí mismo (IndexedDB) para trabajar rápido. Al pedir el Word o el PDF se
 * mandan junto con la petición y el servidor las usa solo para armar el archivo.
 */
(function () {
    'use strict';
    var CFG = window.CUADERNILLO;
    var NUBE = JSON.parse(document.getElementById('cu-nube-config').textContent);
    var datos = JSON.parse(document.getElementById('cu-contenido').textContent);
    var LETRAS = 'ABCDEFGHIJ';
    var MIN_OP = 2, MAX_OP = 6;
    var NOMBRE_NUBE = { google: 'Google Drive', onedrive: 'OneDrive', local: 'este navegador' };
    var CARPETA = 'mcolegio-examenes';

    var $ = function (s, r) { return (r || document).querySelector(s); };
    var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
    function azar(n) {
        var a = new Uint8Array(n || 8); crypto.getRandomValues(a);
        return Array.prototype.map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join('');
    }
    function el(tag, attrs, hijos) {
        var e = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (k) {
            if (k === 'class') e.className = attrs[k];
            else if (k === 'text') e.textContent = attrs[k];
            else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), attrs[k]);
            else e.setAttribute(k, attrs[k]);
        });
        (hijos || []).forEach(function (h) { if (h) e.appendChild(h); });
        return e;
    }

    // -----------------------------------------------------------------------
    // Copia local de las imágenes (IndexedDB)
    // -----------------------------------------------------------------------
    var bd = new Promise(function (ok) {
        try {
            var r = indexedDB.open('mcolegio-cuadernillo', 1);
            r.onupgradeneeded = function () { r.result.createObjectStore('imagenes'); };
            r.onsuccess = function () { ok(r.result); };
            r.onerror = function () { ok(null); };
        } catch (e) { ok(null); }
    });
    function bdGuardar(id, blob) {
        return bd.then(function (db) {
            if (!db) return;
            return new Promise(function (ok) {
                var tx = db.transaction('imagenes', 'readwrite');
                tx.objectStore('imagenes').put(blob, id);
                tx.oncomplete = ok; tx.onerror = ok;
            });
        });
    }
    function bdLeer(id) {
        return bd.then(function (db) {
            if (!db) return null;
            return new Promise(function (ok) {
                var r = db.transaction('imagenes').objectStore('imagenes').get(id);
                r.onsuccess = function () { ok(r.result || null); };
                r.onerror = function () { ok(null); };
            });
        });
    }

    // -----------------------------------------------------------------------
    // La nube del docente
    // -----------------------------------------------------------------------
    function disponible(p) { return p === 'local' || !!NUBE[p]; }
    var nube = {
        proveedor: (function () {
            var g = null;
            try { g = localStorage.getItem('cu-nube'); } catch (e) {}
            return disponible(g) ? g : (disponible(NUBE.sugerida) ? NUBE.sugerida : 'local');
        })()
    };
    function token(p) {
        try {
            var t = JSON.parse(sessionStorage.getItem('cu-token-' + p) || 'null');
            return t && t.expira > Date.now() ? t.token : null;
        } catch (e) { return null; }
    }
    function recibirPermiso(d) {
        if (!d || (d.tipo !== 'token' && d.tipo !== 'error')) return;
        if (d.tipo === 'error') { estado('No se conectó ' + NOMBRE_NUBE[d.proveedor] + ': ' + d.error, true); return; }
        try { sessionStorage.setItem('cu-token-' + d.proveedor, JSON.stringify({ token: d.token, expira: d.expira })); } catch (e) {}
        pintarNube();
        subirPendientes();
        pintar();
    }
    try { new BroadcastChannel('mcolegio-nube').onmessage = function (ev) { recibirPermiso(ev.data); }; } catch (e) {}
    window.addEventListener('message', function (ev) { if (ev.origin === location.origin) recibirPermiso(ev.data); });

    function conectar(p) {
        window.open(CFG.ayudante.replace('PROV', p), 'cu-nube', 'width=520,height=680');
    }

    function api(url, opciones, p) {
        opciones = opciones || {};
        opciones.headers = Object.assign({ Authorization: 'Bearer ' + token(p) }, opciones.headers || {});
        return fetch(url, opciones).then(function (r) {
            if (r.status === 401) {
                try { sessionStorage.removeItem('cu-token-' + p); } catch (e) {}
                pintarNube();
                throw new Error('El permiso de ' + NOMBRE_NUBE[p] + ' venció: conéctela otra vez.');
            }
            if (!r.ok) throw new Error(NOMBRE_NUBE[p] + ' respondió ' + r.status);
            return r;
        });
    }

    // Google Drive (permiso drive.file: la plataforma solo ve lo que ella misma creó)
    function carpetaGoogle() {
        var guardada = null;
        try { guardada = localStorage.getItem('cu-gcarpeta'); } catch (e) {}
        if (guardada) return Promise.resolve(guardada);
        var q = encodeURIComponent("name='" + CARPETA + "' and mimeType='application/vnd.google-apps.folder' and trashed=false");
        return api('https://www.googleapis.com/drive/v3/files?q=' + q + '&fields=files(id)', {}, 'google')
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.files && d.files.length) return d.files[0].id;
                return api('https://www.googleapis.com/drive/v3/files?fields=id', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: CARPETA, mimeType: 'application/vnd.google-apps.folder' })
                }, 'google').then(function (r) { return r.json(); }).then(function (f) { return f.id; });
            })
            .then(function (id) { try { localStorage.setItem('cu-gcarpeta', id); } catch (e) {} return id; });
    }
    function subirGoogle(blob, nombre) {
        return carpetaGoogle().then(function (carpeta) {
            var meta = { name: nombre, parents: [carpeta] };
            var cuerpo = new FormData();
            cuerpo.append('metadata', new Blob([JSON.stringify(meta)], { type: 'application/json' }));
            cuerpo.append('file', blob);
            return api('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',
                       { method: 'POST', body: cuerpo }, 'google');
        }).then(function (r) { return r.json(); }).then(function (f) { return f.id; });
    }
    function bajarGoogle(ref) {
        return api('https://www.googleapis.com/drive/v3/files/' + encodeURIComponent(ref) + '?alt=media', {}, 'google')
            .then(function (r) { return r.blob(); });
    }
    // OneDrive (Office 365 institucional o cuenta personal)
    function subirOneDrive(blob, nombre) {
        var url = 'https://graph.microsoft.com/v1.0/me/drive/root:/' + CARPETA + '/' + encodeURIComponent(nombre) +
                  ':/content?@microsoft.graph.conflictBehavior=rename';
        return api(url, { method: 'PUT', headers: { 'Content-Type': blob.type || 'application/octet-stream' }, body: blob }, 'onedrive')
            .then(function (r) { return r.json(); }).then(function (f) { return f.id; });
    }
    function bajarOneDrive(ref) {
        return api('https://graph.microsoft.com/v1.0/me/drive/items/' + encodeURIComponent(ref) +
                   '?select=id,@microsoft.graph.downloadUrl', {}, 'onedrive')
            .then(function (r) { return r.json(); })
            .then(function (d) { return fetch(d['@microsoft.graph.downloadUrl']); })
            .then(function (r) { if (!r.ok) throw new Error('OneDrive no entregó la imagen'); return r.blob(); });
    }
    function subirANube(p, blob, nombre) { return p === 'google' ? subirGoogle(blob, nombre) : subirOneDrive(blob, nombre); }
    function bajarDeNube(img) { return img.proveedor === 'google' ? bajarGoogle(img.ref) : bajarOneDrive(img.ref); }

    function pintarNube() {
        var caja = $('#cu-nube');
        caja.innerHTML = '';
        caja.appendChild(el('span', { text: 'Imágenes en:' }));
        var sel = el('select', { class: 'form-select form-select-sm', style: 'width:auto' });
        ['onedrive', 'google', 'local'].forEach(function (p) {
            if (!disponible(p)) return;
            var o = el('option', { value: p, text: p === 'local' ? 'Solo este navegador' : NOMBRE_NUBE[p] });
            if (p === nube.proveedor) o.selected = true;
            sel.appendChild(o);
        });
        sel.addEventListener('change', function () {
            nube.proveedor = sel.value;
            try { localStorage.setItem('cu-nube', sel.value); } catch (e) {}
            pintarNube(); subirPendientes();
        });
        caja.appendChild(sel);
        if (nube.proveedor !== 'local') {
            if (token(nube.proveedor)) {
                caja.appendChild(el('span', { class: 'pe-chip pe-ok', text: 'Conectado' }));
            } else {
                caja.appendChild(el('button', { type: 'button', class: 'btn btn-sm btn-outline-primary',
                    text: 'Conectar ' + NOMBRE_NUBE[nube.proveedor], onclick: function () { conectar(nube.proveedor); } }));
            }
        }
        var pend = pendientes().length;
        if (pend && nube.proveedor !== 'local') {
            caja.appendChild(el('span', { class: 'pe-chip pe-media',
                text: pend + ' imagen' + (pend > 1 ? 'es' : '') + ' solo en este navegador' }));
        }
        if (!NUBE.google && !NUBE.onedrive) {
            caja.appendChild(el('span', { class: 'cu-ayuda', text: '(la conexión con Drive u OneDrive aún no está activada en la plataforma)' }));
        }
    }

    // -----------------------------------------------------------------------
    // Imágenes
    // -----------------------------------------------------------------------
    var urls = {};          // id -> objectURL
    var buscando = {};      // id -> promesa

    function todasLasImagenes() {
        var lista = [];
        datos.items.forEach(function (it) {
            (it.imagenes || []).forEach(function (i) { lista.push(i); });
            (it.opciones || []).forEach(function (o) { if (o.imagen) lista.push(o.imagen); });
        });
        return lista;
    }
    function pendientes() { return todasLasImagenes().filter(function (i) { return i.proveedor === 'local'; }); }

    function obtener(img) {
        if (buscando[img.id]) return buscando[img.id];
        buscando[img.id] = bdLeer(img.id).then(function (blob) {
            if (blob) return blob;
            if (img.proveedor === 'local' || !token(img.proveedor)) return null;
            return bajarDeNube(img).then(function (b) { bdGuardar(img.id, b); return b; });
        }).catch(function () { return null; }).then(function (b) {
            if (!b) delete buscando[img.id];
            return b;
        });
        return buscando[img.id];
    }

    function reducir(archivo) {
        // Máximo 1400 px de ancho: suficiente para imprimir y liviano para la nube.
        return new Promise(function (ok, mal) {
            var im = new Image();
            im.onload = function () {
                var esc = Math.min(1, 1400 / im.naturalWidth);
                var c = document.createElement('canvas');
                c.width = Math.round(im.naturalWidth * esc); c.height = Math.round(im.naturalHeight * esc);
                var cx = c.getContext('2d');
                var png = archivo.type === 'image/png' || archivo.type === 'image/gif';
                if (!png) { cx.fillStyle = '#fff'; cx.fillRect(0, 0, c.width, c.height); }
                cx.drawImage(im, 0, 0, c.width, c.height);
                URL.revokeObjectURL(im.src);
                c.toBlob(function (b) {
                    if (png && b && b.size > 700000) {
                        cx.globalCompositeOperation = 'destination-over'; cx.fillStyle = '#fff'; cx.fillRect(0, 0, c.width, c.height);
                        c.toBlob(ok, 'image/jpeg', 0.88);
                    } else ok(b);
                }, png ? 'image/png' : 'image/jpeg', 0.88);
            };
            im.onerror = function () { mal(new Error('No es una imagen')); };
            im.src = URL.createObjectURL(archivo);
        });
    }

    function agregarImagen(archivo, ponerEn) {
        if (!archivo || !/^image\//.test(archivo.type)) return;
        estado('Preparando imagen…');
        reducir(archivo).then(function (blob) {
            var ext = blob.type === 'image/png' ? 'png' : 'jpg';
            var img = { id: 'im' + azar(8), proveedor: 'local', ref: '',
                        nombre: (CFG.titulo || 'examen').replace(/[^\w\-]+/g, '_').slice(0, 40) + '_' + azar(3) + '.' + ext,
                        ancho: 60 };
            return bdGuardar(img.id, blob).then(function () {
                ponerEn(img);
                pintar(); programarGuardado();
                if (nube.proveedor !== 'local' && token(nube.proveedor)) return subirUna(img, blob);
                if (nube.proveedor !== 'local') estado('Imagen guardada en este navegador. Conecte ' + NOMBRE_NUBE[nube.proveedor] + ' para subirla.');
            });
        }).catch(function (e) { estado(e.message, true); });
    }

    function subirUna(img, blob) {
        var p = nube.proveedor;
        img._subiendo = true; pintar();
        return subirANube(p, blob, img.nombre).then(function (ref) {
            img.proveedor = p; img.ref = ref; delete img._subiendo;
            pintar(); pintarNube(); programarGuardado();
        }).catch(function (e) { delete img._subiendo; pintar(); estado(e.message, true); });
    }

    var subiendoPendientes = false;
    function subirPendientes() {
        if (subiendoPendientes || nube.proveedor === 'local' || !token(nube.proveedor)) return;
        var lista = pendientes();
        if (!lista.length) return;
        subiendoPendientes = true;
        estado('Subiendo ' + lista.length + ' imagen(es) a ' + NOMBRE_NUBE[nube.proveedor] + '…');
        lista.reduce(function (cadena, img) {
            return cadena.then(function () { return bdLeer(img.id).then(function (b) { return b ? subirUna(img, b) : null; }); });
        }, Promise.resolve()).then(function () { subiendoPendientes = false; estado('Imágenes en ' + NOMBRE_NUBE[nube.proveedor] + '.'); });
    }

    function vistaImagen(img, quitar, compacta) {
        var caja = el('div', { class: 'cu-img' });
        var cont = el('div', { class: 'falta', text: 'Cargando…' });
        caja.appendChild(cont);
        if (img._subiendo) caja.appendChild(el('span', { class: 'sube', text: 'subiendo…' }));
        obtener(img).then(function (blob) {
            if (blob) {
                if (!urls[img.id]) urls[img.id] = URL.createObjectURL(blob);
                cont.replaceWith(el('img', { src: urls[img.id], alt: img.nombre || '', class: compacta ? 'cu-mini' : '' }));
            } else if (img.proveedor !== 'local') {
                cont.textContent = 'Conecte ' + NOMBRE_NUBE[img.proveedor] + ' para ver esta imagen.';
            } else {
                cont.textContent = 'Esta imagen quedó en otro navegador. Abra el respaldo del examen.';
            }
        });
        var acciones = el('div', { class: 'acciones' });
        if (!compacta) {
            var tam = el('select', { title: 'Tamaño al imprimir' });
            [[30, 'Pequeña'], [45, 'Mediana'], [60, 'Grande'], [100, 'Ancho completo']].forEach(function (t) {
                var o = el('option', { value: t[0], text: t[1] });
                if (+img.ancho === t[0]) o.selected = true;
                tam.appendChild(o);
            });
            if (![30, 45, 60, 100].includes(+img.ancho)) tam.value = 60;
            tam.addEventListener('change', function () { img.ancho = +tam.value; programarGuardado(); });
            acciones.appendChild(tam);
        }
        acciones.appendChild(el('span', { class: 'ms-auto pe-gris', title: 'Dónde está',
            text: img.proveedor === 'local' ? '💻' : (img.proveedor === 'google' ? 'Drive' : 'OneDrive') }));
        acciones.appendChild(el('button', { type: 'button', class: 'btn btn-link btn-sm text-danger p-0', title: 'Quitar',
            text: '✕', onclick: quitar }));
        caja.appendChild(acciones);
        return caja;
    }

    var destinoArchivo = null;
    $('#cu-archivo').addEventListener('change', function (ev) {
        var f = ev.target.files[0];
        if (f && destinoArchivo) agregarImagen(f, destinoArchivo);
        ev.target.value = '';
    });
    function elegirImagen(ponerEn) { destinoArchivo = ponerEn; $('#cu-archivo').click(); }

    // -----------------------------------------------------------------------
    // Pintar el examen
    // -----------------------------------------------------------------------
    function nuevaPregunta() {
        var ops = [];
        for (var i = 0; i < Math.max(MIN_OP, Math.min(MAX_OP, CFG.opciones || 4)); i++) ops.push({ texto: '', imagen: null });
        return { id: 'i' + azar(6), tipo: 'pregunta', enunciado: '', imagenes: [], opciones: ops, correcta: '' };
    }
    function crecer(t) { t.style.height = 'auto'; t.style.height = (t.scrollHeight + 2) + 'px'; }

    function areaTexto(valor, alCambiar, filas, ph) {
        var t = el('textarea', { class: 'form-control', rows: filas || 2, placeholder: ph || '' });
        t.value = valor || '';
        t.addEventListener('input', function () { alCambiar(t.value); crecer(t); programarGuardado(); });
        setTimeout(function () { crecer(t); }, 0);
        return t;
    }

    function pegarImagenes(t, ponerEn) {
        t.addEventListener('paste', function (ev) {
            var items = (ev.clipboardData || {}).items || [];
            for (var i = 0; i < items.length; i++) {
                if (items[i].kind === 'file' && /^image\//.test(items[i].type)) {
                    ev.preventDefault();
                    agregarImagen(items[i].getAsFile(), ponerEn);
                }
            }
        });
    }

    function mover(i, d) {
        var j = i + d;
        if (j < 0 || j >= datos.items.length) return;
        var x = datos.items[i]; datos.items[i] = datos.items[j]; datos.items[j] = x;
        pintar(); programarGuardado();
    }

    function botonCab(icono, titulo, accion) {
        return el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary', title: titulo,
                              onclick: accion }, [el('i', { class: 'fas ' + icono })]);
    }

    function pintarItem(it, idx, numero) {
        var caja = el('div', { class: 'cu-item' + (it.tipo === 'texto' ? ' texto' : '') + (it.tipo === 'pregunta' && !it.correcta ? ' cu-sin' : ''),
                               id: 'item-' + it.id });
        var acc = el('div', { class: 'ms-auto d-flex gap-1' }, [
            botonCab('fa-image', 'Agregar imagen', function () { elegirImagen(function (img) { it.imagenes.push(img); }); }),
            botonCab('fa-arrow-up', 'Subir', function () { mover(idx, -1); }),
            botonCab('fa-arrow-down', 'Bajar', function () { mover(idx, 1); }),
            botonCab('fa-trash', 'Eliminar', function () {
                var vacio = it.tipo === 'texto' ? !it.texto : (!it.enunciado && it.opciones.every(function (o) { return !o.texto; }));
                if (!vacio && !confirm('¿Eliminar ' + (it.tipo === 'texto' ? 'este texto' : 'la pregunta ' + numero) + '?')) return;
                datos.items.splice(idx, 1); pintar(); programarGuardado();
            })
        ]);
        caja.appendChild(el('div', { class: 'cu-cab' }, [
            el('span', { class: 'cu-num', text: it.tipo === 'texto' ? '' : numero + '.' }),
            it.tipo === 'texto' ? el('span', { class: 'fw-semibold', text: 'Texto o lectura' }) : null,
            it.tipo === 'texto' ? el('span', { class: 'cu-ayuda', text: '· acompaña a las preguntas que vienen después' }) : null,
            acc
        ]));
        var campo = it.tipo === 'texto' ? 'texto' : 'enunciado';
        var t = areaTexto(it[campo], function (v) { it[campo] = v; }, it.tipo === 'texto' ? 4 : 2,
                          it.tipo === 'texto' ? 'Lectura, tabla o situación…' : 'Escriba la pregunta (puede pegar una imagen con Ctrl+V)');
        pegarImagenes(t, function (img) { it.imagenes.push(img); });
        caja.appendChild(t);
        if (it.imagenes.length) {
            caja.appendChild(el('div', { class: 'cu-imgs' }, it.imagenes.map(function (img, k) {
                return vistaImagen(img, function () { it.imagenes.splice(k, 1); pintar(); programarGuardado(); });
            })));
        }
        if (it.tipo === 'texto') return caja;

        it.opciones.forEach(function (op, j) {
            var letra = LETRAS[j];
            var b = el('button', { type: 'button', class: 'letra' + (it.correcta === letra ? ' ok' : ''), text: letra,
                                   title: it.correcta === letra ? 'Respuesta correcta' : 'Marcar como correcta' });
            b.addEventListener('click', function () {
                it.correcta = it.correcta === letra ? '' : letra; pintar(); programarGuardado();
            });
            var ta = areaTexto(op.texto, function (v) { op.texto = v; }, 1, 'Opción ' + letra);
            pegarImagenes(ta, function (img) { img.ancho = 40; op.imagen = img; });
            var imgBtn = op.imagen
                ? vistaImagen(op.imagen, function () { op.imagen = null; pintar(); programarGuardado(); }, true)
                : el('button', { type: 'button', class: 'btn btn-sm btn-link cu-op-img', title: 'Imagen como opción',
                                 onclick: function () { elegirImagen(function (img) { img.ancho = 40; op.imagen = img; }); } }, [el('i', { class: 'far fa-image' })]);
            caja.appendChild(el('div', { class: 'cu-op' }, [b, ta, imgBtn]));
        });
        var pie = el('div', { class: 'd-flex align-items-center gap-2 mt-2' });
        pie.appendChild(el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary', text: '− opción',
            disabled: it.opciones.length <= MIN_OP ? 'disabled' : null,
            onclick: function () {
                if (it.opciones.length <= MIN_OP) return;
                var ult = it.opciones[it.opciones.length - 1];
                if ((ult.texto || ult.imagen) && !confirm('La última opción tiene contenido. ¿Quitarla?')) return;
                it.opciones.pop();
                if (it.correcta && LETRAS.indexOf(it.correcta) >= it.opciones.length) it.correcta = '';
                pintar(); programarGuardado();
            } }));
        pie.appendChild(el('button', { type: 'button', class: 'btn btn-sm btn-outline-secondary', text: '+ opción',
            disabled: it.opciones.length >= MAX_OP ? 'disabled' : null,
            onclick: function () { if (it.opciones.length < MAX_OP) { it.opciones.push({ texto: '', imagen: null }); pintar(); programarGuardado(); } } }));
        if (!it.correcta) pie.appendChild(el('span', { class: 'pe-mal small ms-2', text: 'Toque la letra de la respuesta correcta.' }));
        caja.appendChild(pie);
        return caja;
    }

    function pintar() {
        var cont = $('#cu-items');
        var y = window.scrollY;
        cont.innerHTML = '';
        var n = 0;
        datos.items.forEach(function (it, idx) {
            if (it.tipo === 'pregunta') n++;
            // Los botones "disabled: null" no deben quedar deshabilitados.
            cont.appendChild(pintarItem(it, idx, n));
        });
        $$('button[disabled="null"]', cont).forEach(function (b) { b.removeAttribute('disabled'); });
        window.scrollTo(0, y);
    }

    // -----------------------------------------------------------------------
    // Ajustes generales
    // -----------------------------------------------------------------------
    var instr = $('#cu-instrucciones');
    instr.value = datos.instrucciones || '';
    instr.addEventListener('input', function () { datos.instrucciones = instr.value; programarGuardado(); });
    $$('#cu-nombre input').forEach(function (r) {
        r.checked = r.value === datos.nombre;
        r.addEventListener('change', function () { datos.nombre = r.value; programarGuardado(); });
    });
    $$('#cu-columnas input').forEach(function (r) {
        r.checked = String(r.value) === String(datos.columnas);
        r.addEventListener('change', function () { datos.columnas = +r.value; programarGuardado(); });
    });
    $('#cu-mas-pregunta').addEventListener('click', function () {
        var p = nuevaPregunta(); datos.items.push(p); pintar(); programarGuardado();
        var t = $('#item-' + p.id + ' textarea'); if (t) { t.focus(); t.scrollIntoView({ block: 'center' }); }
    });
    $('#cu-mas-texto').addEventListener('click', function () {
        var x = { id: 'i' + azar(6), tipo: 'texto', texto: '', imagenes: [] };
        datos.items.push(x); pintar(); programarGuardado();
        var t = $('#item-' + x.id + ' textarea'); if (t) { t.focus(); t.scrollIntoView({ block: 'center' }); }
    });

    // -----------------------------------------------------------------------
    // Guardar
    // -----------------------------------------------------------------------
    function estado(texto, mal) {
        var e = $('#cu-estado'); e.textContent = texto; e.className = 'cu-estado' + (mal ? ' mal' : '');
    }
    function limpioParaGuardar() {
        return JSON.parse(JSON.stringify(datos, function (k, v) { return k.charAt(0) === '_' ? undefined : v; }));
    }
    var reloj = null, cambios = false, enCurso = null;
    function programarGuardado() {
        cambios = true;
        estado('Cambios sin guardar…');
        clearTimeout(reloj);
        reloj = setTimeout(guardar, 1500);
    }
    function guardar() {
        clearTimeout(reloj);
        if (enCurso) return enCurso.then(function () { return cambios ? guardar() : null; });
        cambios = false;
        estado('Guardando…');
        enCurso = fetch(CFG.guardar, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf },
            body: JSON.stringify({ contenido: limpioParaGuardar() })
        }).then(function (r) { if (!r.ok) throw new Error('No se pudo guardar (' + r.status + ')'); return r.json(); })
          .then(function (d) {
              var t = 'Guardado ' + d.hora + ' · ' + d.preguntas + ' preguntas · clave al día';
              if (d.sin_correcta && d.sin_correcta.length) {
                  t += ' · sin respuesta: ' + d.sin_correcta.slice(0, 8).join(', ') + (d.sin_correcta.length > 8 ? '…' : '');
              }
              if (d.formas_ajustadas && d.formas_ajustadas.length) t += ' · se ajustó la forma ' + d.formas_ajustadas.join(', ');
              estado(t, !!(d.sin_correcta && d.sin_correcta.length));
          })
          .catch(function (e) { cambios = true; estado(e.message + '. Se reintenta al seguir escribiendo.', true); })
          .then(function () { enCurso = null; });
        return enCurso;
    }
    $('#cu-guardar').addEventListener('click', guardar);
    window.addEventListener('beforeunload', function (ev) { if (cambios) { ev.preventDefault(); ev.returnValue = ''; } });

    // -----------------------------------------------------------------------
    // Word y PDF
    // -----------------------------------------------------------------------
    $$('[data-formato]').forEach(function (b) {
        b.addEventListener('click', function () { generar(b.dataset.formato, b); });
    });
    function generar(formato, boton) {
        var antes = boton.innerHTML;
        boton.disabled = true; boton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Armando…';
        var faltan = [];
        guardar().then(function () {
            var unicas = {};
            todasLasImagenes().forEach(function (i) { unicas[i.id] = i; });
            var ids = Object.keys(unicas);
            return Promise.all(ids.map(function (id) {
                return obtener(unicas[id]).then(function (b) { if (!b) faltan.push(unicas[id]); return [id, b]; });
            }));
        }).then(function (pares) {
            if (faltan.length && !confirm(faltan.length + ' imagen(es) no están disponibles en este momento (conecte su nube o abra el respaldo). ¿Armar el archivo sin ellas?')) {
                throw new Error('cancelado');
            }
            var fd = new FormData();
            fd.append('formato', formato);
            fd.append('nombre', datos.nombre);
            var pf = $('#cu-por-forma');
            fd.append('por_forma', pf && !pf.checked ? '0' : '1');
            pares.forEach(function (p) { if (p[1]) fd.append('img_' + p[0], p[1], p[0]); });
            return fetch(CFG.generar, { method: 'POST', headers: { 'X-CSRFToken': CFG.csrf }, body: fd });
        }).then(function (r) {
            if (!r.ok) return r.text().then(function (t) { throw new Error(t.slice(0, 200) || ('Error ' + r.status)); });
            var cd = r.headers.get('Content-Disposition') || '';
            var m = /filename="([^"]+)"/.exec(cd);
            return r.blob().then(function (blob) {
                var a = el('a', { href: URL.createObjectURL(blob), download: m ? m[1] : ('examen.' + formato) });
                document.body.appendChild(a); a.click(); a.remove();
                setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
            });
        }).catch(function (e) { if (e.message !== 'cancelado') estado(e.message, true); })
          .then(function () { boton.disabled = false; boton.innerHTML = antes; });
    }

    // -----------------------------------------------------------------------
    // Respaldo: el examen con sus imágenes en un archivo
    // -----------------------------------------------------------------------
    function aDataURL(blob) {
        return new Promise(function (ok) { var r = new FileReader(); r.onload = function () { ok(r.result); }; r.readAsDataURL(blob); });
    }
    $('#cu-respaldo').addEventListener('click', function () {
        var imgs = {};
        Promise.all(todasLasImagenes().map(function (i) {
            return obtener(i).then(function (b) { return b ? aDataURL(b).then(function (d) { imgs[i.id] = d; }) : null; });
        })).then(function () {
            var archivo = new Blob([JSON.stringify({ tipo: 'mcolegio-cuadernillo', version: 1, examen: CFG.examen,
                titulo: CFG.titulo, contenido: limpioParaGuardar(), imagenes: imgs })], { type: 'application/json' });
            var a = el('a', { href: URL.createObjectURL(archivo),
                              download: (CFG.titulo || 'examen').replace(/[^\w\-]+/g, '_') + '_respaldo.json' });
            document.body.appendChild(a); a.click(); a.remove();
        });
    });
    $('#cu-abrir-respaldo').addEventListener('change', function (ev) {
        var f = ev.target.files[0]; ev.target.value = '';
        if (!f) return;
        f.text().then(function (txt) {
            var r = JSON.parse(txt);
            if (r.tipo !== 'mcolegio-cuadernillo') throw new Error('Ese archivo no es un respaldo de examen.');
            var ids = Object.keys(r.imagenes || {});
            return Promise.all(ids.map(function (id) {
                return fetch(r.imagenes[id]).then(function (x) { return x.blob(); }).then(function (b) { return bdGuardar(id, b); });
            })).then(function () {
                buscando = {};
                if (r.contenido && confirm('Se recuperaron ' + ids.length + ' imagen(es). ¿Reemplazar también las preguntas por las del respaldo («' + (r.titulo || '') + '»)?')) {
                    datos = r.contenido; pintar(); guardar();
                } else { pintar(); }
                estado('Respaldo abierto: ' + ids.length + ' imagen(es) en este navegador.');
                subirPendientes();
            });
        }).catch(function (e) { estado(e.message || 'No se pudo abrir el respaldo.', true); });
    });

    // -----------------------------------------------------------------------
    if (!datos.items.length) datos.items.push(nuevaPregunta());
    pintarNube();
    pintar();
    subirPendientes();
})();
