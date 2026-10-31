/* Mis materiales · editor por bloques.
 * El documento vive en `datos` ({bloques, opciones}); cada cambio se guarda solo al servidor.
 * Las imágenes se pegan (Ctrl+V), se arrastran o se suben: van a la nube de la plataforma.
 */
(function () {
    'use strict';
    var CFG = window.MM;
    var datos = JSON.parse(document.getElementById('mm-contenido').textContent || '{}');
    var IMAGENES = JSON.parse(document.getElementById('mm-imagenes').textContent || '{}');
    var NUBE = JSON.parse(document.getElementById('mm-nube-config').textContent || '{}');
    datos.bloques = datos.bloques || [];
    datos.opciones = Object.assign({ columnas: 1, letra: 11, modo: 'normal', nombre_estudiante: true, datos: true }, datos.opciones || {});

    var $ = function (s, r) { return (r || document).querySelector(s); };
    var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
    var caja = $('#mm-bloques');
    var activo = null;            // id del bloque marcado: lo nuevo se agrega debajo
    var ESTILOS = { recuerda: 'Recuerda', reto: 'Reto', vocabulario: 'Vocabulario', nota: 'Nota' };

    function id() { return Math.random().toString(36).slice(2, 10); }
    function el(tag, attrs, hijos) {
        var e = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (k) {
            if (k === 'text') e.textContent = attrs[k];
            else if (k === 'html') e.innerHTML = attrs[k];
            else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), attrs[k]);
            else e.setAttribute(k, attrs[k]);
        });
        (hijos || []).forEach(function (h) { if (h) e.appendChild(h); });
        return e;
    }
    function estado(t, mal) { var s = $('#mm-estado'); s.textContent = t; s.style.color = mal ? '#b02a37' : ''; }

    // -------------------------------------------------------------------
    // Guardar solo
    // -------------------------------------------------------------------
    var temporizador = null, guardando = false, pendiente = false;
    function cambio() {
        estado('Cambios sin guardar…');
        clearTimeout(temporizador);
        temporizador = setTimeout(guardar, 1200);
    }
    function guardar() {
        if (guardando) { pendiente = true; return Promise.resolve(); }
        guardando = true;
        estado('Guardando…');
        var cuerpo = {
            titulo: $('#mm-titulo').value, area: $('#mm-area').value, grado: $('#mm-grado').value,
            periodo: $('#mm-periodo').value, contenido: datos
        };
        return fetch(CFG.guardar, {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf }, body: JSON.stringify(cuerpo)
        }).then(function (r) { return r.json(); }).then(function (j) {
            estado(j.ok ? 'Todo guardado' : (j.error || 'No se pudo guardar'), !j.ok);
        }).catch(function () { estado('Sin conexión: se guardará al volver', true); pendiente = true; })
            .then(function () {
                guardando = false;
                if (pendiente) { pendiente = false; setTimeout(guardar, 800); }
            });
    }
    ['#mm-titulo', '#mm-area', '#mm-grado', '#mm-periodo'].forEach(function (s) { $(s).addEventListener('input', cambio); });
    window.addEventListener('beforeunload', function (e) {
        if ($('#mm-estado').textContent !== 'Todo guardado') { e.preventDefault(); e.returnValue = ''; }
    });

    // -------------------------------------------------------------------
    // Bloques
    // -------------------------------------------------------------------
    function nuevo(tipo) {
        var b = { id: id(), tipo: tipo };
        if (tipo === 'texto') b.html = '';
        if (tipo === 'titulo') { b.texto = ''; b.nivel = 1; }
        if (tipo === 'seccion') { b.titulo = ''; b.indicacion = ''; }
        if (tipo === 'recuadro') { b.estilo = 'recuerda'; b.titulo = 'Recuerda'; b.html = ''; }
        if (tipo === 'tabla') { b.filas = [['', '', ''], ['', '', '']]; b.encabezado = true; }
        if (tipo === 'lineas') b.n = 4;
        if (tipo === 'pregunta') { b.enunciado = ''; b.opciones = ['', '', '', '']; b.correcta = null; b.lineas = 0; b.imagen = null; }
        return b;
    }
    function indice(bid) { for (var i = 0; i < datos.bloques.length; i++) if (datos.bloques[i].id === bid) return i; return -1; }
    function insertar(b) {
        var i = activo ? indice(activo) : -1;
        datos.bloques.splice(i < 0 ? datos.bloques.length : i + 1, 0, b);
        activo = b.id;
        pintar();
        cambio();
        var nodo = caja.querySelector('[data-id="' + b.id + '"] .mm-edit, [data-id="' + b.id + '"] input');
        if (nodo) nodo.focus();
    }

    function editable(valor, ayuda, alCambiar, plano) {
        var e = el('div', { contenteditable: 'true', class: 'mm-edit', 'data-ayuda': ayuda });
        if (plano) e.textContent = valor || ''; else e.innerHTML = valor || '';
        e.addEventListener('input', function () { alCambiar(plano ? e.textContent : e.innerHTML); cambio(); });
        return e;
    }
    function campo(valor, ayuda, alCambiar, clase) {
        var i = el('input', { type: 'text', class: clase || 'form-control form-control-sm', placeholder: ayuda });
        i.value = valor || '';
        i.addEventListener('input', function () { alCambiar(i.value); cambio(); });
        return i;
    }

    var DIBUJAR = {
        titulo: function (b) {
            var sel = el('select', { class: 'form-select form-select-sm', style: 'width:auto' }, [
                el('option', { value: '1', text: 'Título' }), el('option', { value: '2', text: 'Subtítulo' })]);
            sel.value = String(b.nivel || 1);
            sel.addEventListener('change', function () { b.nivel = +sel.value; cambio(); pintar(); });
            var t = campo(b.texto, 'Escriba el título', function (v) { b.texto = v; },
                          'form-control border-0 fw-bold ' + (b.nivel === 2 ? 'fs-6' : 'fs-5'));
            return el('div', { class: 'd-flex gap-2 align-items-center' }, [t, sel]);
        },
        seccion: function (b) {
            return el('div', {}, [
                el('div', { class: 'mm-seccion' }, [campo(b.titulo, 'Nombre de la sección (Ej.: 1. Exploración)', function (v) { b.titulo = v; },
                                                          'form-control form-control-sm bg-transparent border-0 text-white fw-bold')]),
                campo(b.indicacion, 'Indicación corta (opcional)', function (v) { b.indicacion = v; }, 'form-control form-control-sm border-0 fst-italic')]);
        },
        texto: function (b) { return editable(b.html, 'Escriba aquí…', function (v) { b.html = v; }); },
        imagen: function (b) {
            var img = el('img', { src: IMAGENES[b.imagen] || '', alt: b.pie || 'Imagen', style: 'width:' + (b.ancho || 60) + '%' });
            var rango = el('input', { type: 'range', min: '10', max: '100', step: '5', class: 'form-range', style: 'max-width:200px' });
            rango.value = b.ancho || 60;
            rango.addEventListener('input', function () { b.ancho = +rango.value; img.style.width = b.ancho + '%'; cambio(); });
            return el('div', { class: 'mm-img text-center' }, [img,
                el('div', { class: 'd-flex gap-2 align-items-center justify-content-center mt-1 small text-muted' }, [el('span', { text: 'Tamaño' }), rango]),
                campo(b.pie, 'Pie de imagen (opcional)', function (v) { b.pie = v; }, 'form-control form-control-sm border-0 text-center fst-italic')]);
        },
        tabla: function (b) {
            var t = el('table', { class: 'mm-tabla mx-auto' });
            b.filas.forEach(function (fila, i) {
                var tr = el('tr');
                fila.forEach(function (valor, j) {
                    var td = el('td', { contenteditable: 'true', style: i === 0 && b.encabezado ? 'font-weight:700;background:#e8eef9' : '' });
                    td.textContent = valor;
                    td.addEventListener('input', function () { b.filas[i][j] = td.textContent; cambio(); });
                    tr.appendChild(td);
                });
                t.appendChild(tr);
            });
            function boton(texto, f) { return el('button', { type: 'button', class: 'btn btn-sm btn-link py-0', text: texto, onclick: function () { f(); cambio(); pintar(); } }); }
            var enc = el('input', { type: 'checkbox', class: 'form-check-input', id: 'enc-' + b.id });
            enc.checked = !!b.encabezado;
            enc.addEventListener('change', function () { b.encabezado = enc.checked; cambio(); pintar(); });
            return el('div', {}, [t, el('div', { class: 'd-flex flex-wrap gap-1 justify-content-center small' }, [
                boton('+ fila', function () { b.filas.push(b.filas[0].map(function () { return ''; })); }),
                boton('− fila', function () { if (b.filas.length > 1) b.filas.pop(); }),
                boton('+ columna', function () { if (b.filas[0].length < 8) b.filas.forEach(function (f) { f.push(''); }); }),
                boton('− columna', function () { if (b.filas[0].length > 1) b.filas.forEach(function (f) { f.pop(); }); }),
                el('span', { class: 'form-check ms-2' }, [enc, el('label', { class: 'form-check-label', for: 'enc-' + b.id, text: 'Primera fila de títulos' })])])]);
        },
        recuadro: function (b) {
            var sel = el('select', { class: 'form-select form-select-sm', style: 'width:auto' });
            Object.keys(ESTILOS).forEach(function (k) { sel.appendChild(el('option', { value: k, text: ESTILOS[k] })); });
            sel.value = b.estilo;
            sel.addEventListener('change', function () {
                if (b.titulo === ESTILOS[b.estilo]) b.titulo = ESTILOS[sel.value];
                b.estilo = sel.value; cambio(); pintar();
            });
            return el('div', { class: 'mm-recuadro ' + b.estilo }, [
                el('div', { class: 'd-flex gap-2 align-items-center mb-1' }, [
                    campo(b.titulo, 'Título del recuadro', function (v) { b.titulo = v; }, 'form-control form-control-sm fw-bold bg-transparent border-0'), sel]),
                editable(b.html, 'Contenido del recuadro…', function (v) { b.html = v; })]);
        },
        lineas: function (b) {
            var n = el('input', { type: 'number', min: '1', max: '30', class: 'form-control form-control-sm', style: 'width:80px' });
            n.value = b.n;
            n.addEventListener('input', function () { b.n = Math.max(1, Math.min(30, +n.value || 1)); cambio(); pintar(); });
            var lineas = el('div');
            for (var k = 0; k < Math.min(b.n, 30); k++) lineas.appendChild(el('div', { class: 'mm-linea' }));
            return el('div', {}, [el('div', { class: 'd-flex gap-2 align-items-center small text-muted mb-1' }, [el('span', { text: 'Líneas para responder' }), n]), lineas]);
        },
        pregunta: function (b) {
            var caja2 = el('div');
            caja2.appendChild(editable(b.enunciado, 'Escriba la pregunta…', function (v) { b.enunciado = v; }, true));
            if (b.imagen && IMAGENES[b.imagen]) {
                caja2.appendChild(el('div', { class: 'mm-img text-center' }, [el('img', { src: IMAGENES[b.imagen], alt: 'Imagen de la pregunta', style: 'width:45%' }),
                    el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger', text: 'Quitar imagen', onclick: function () { b.imagen = null; cambio(); pintar(); } })]));
            }
            var letras = 'ABCDEF';
            b.opciones.forEach(function (op, i) {
                var radio = el('input', { type: 'radio', name: 'c-' + b.id, title: 'Respuesta correcta', class: 'form-check-input mt-0' });
                radio.checked = b.correcta === i;
                radio.addEventListener('change', function () { b.correcta = i; cambio(); });
                caja2.appendChild(el('div', { class: 'mm-op' }, [radio, el('b', { text: letras[i] + '.' }),
                    campo(op, 'Opción ' + letras[i], function (v) { b.opciones[i] = v; }, ''),
                    el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger py-0', title: 'Quitar opción', html: '&times;',
                        onclick: function () { b.opciones.splice(i, 1); if (b.correcta === i) b.correcta = null; else if (b.correcta > i) b.correcta--; cambio(); pintar(); } })]));
            });
            var lin = el('input', { type: 'number', min: '0', max: '20', class: 'form-control form-control-sm', style: 'width:70px' });
            lin.value = b.lineas || 0;
            lin.addEventListener('input', function () { b.lineas = Math.max(0, Math.min(20, +lin.value || 0)); cambio(); });
            caja2.appendChild(el('div', { class: 'd-flex flex-wrap gap-2 align-items-center small mt-1' }, [
                b.opciones.length < 6 ? el('button', { type: 'button', class: 'btn btn-sm btn-link py-0', text: '+ opción',
                    onclick: function () { b.opciones.push(''); cambio(); pintar(); } }) : null,
                el('button', { type: 'button', class: 'btn btn-sm btn-link py-0', text: 'Imagen para la pregunta',
                    onclick: function () { activo = b.id; destinoImagen = b; $('#mm-archivo').click(); } }),
                el('span', { class: 'text-muted ms-auto', text: 'Líneas para responder' }), lin,
                el('span', { class: 'text-muted', text: b.opciones.length ? '· marque la correcta' : '· pregunta abierta' })]));
            return caja2;
        },
        separador: function () { return el('div', { class: 'text-center text-muted small', html: '— separador —' }); },
        salto: function () { return el('div', { class: 'text-center text-muted small', html: '<i class="fas fa-scissors"></i> Aquí empieza una página nueva' }); }
    };

    function herramientas(b, i) {
        function boton(icono, titulo, f) {
            return el('button', { type: 'button', title: titulo, 'aria-label': titulo, html: '<i class="' + icono + '"></i>', onclick: function (ev) { ev.stopPropagation(); f(); } });
        }
        return el('div', { class: 'mm-herr' }, [
            boton('fas fa-arrow-up', 'Subir', function () { if (i > 0) { datos.bloques.splice(i - 1, 0, datos.bloques.splice(i, 1)[0]); cambio(); pintar(); } }),
            boton('fas fa-arrow-down', 'Bajar', function () { if (i < datos.bloques.length - 1) { datos.bloques.splice(i + 1, 0, datos.bloques.splice(i, 1)[0]); cambio(); pintar(); } }),
            boton('far fa-copy', 'Duplicar', function () { var c = JSON.parse(JSON.stringify(b)); c.id = id(); datos.bloques.splice(i + 1, 0, c); cambio(); pintar(); }),
            boton('far fa-trash-can', 'Eliminar', function () { datos.bloques.splice(i, 1); if (activo === b.id) activo = null; cambio(); pintar(); })]);
    }

    function pintar() {
        caja.innerHTML = '';
        var n = 0;
        datos.bloques.forEach(function (b, i) {
            if (!DIBUJAR[b.tipo]) return;
            var nodo = el('div', { class: 'mm-bloque' + (activo === b.id ? ' activo' : ''), 'data-id': b.id });
            if (b.tipo === 'pregunta') { n++; nodo.appendChild(el('div', { class: 'small fw-bold text-primary', text: 'Pregunta ' + n })); }
            nodo.appendChild(herramientas(b, i));
            nodo.appendChild(DIBUJAR[b.tipo](b));
            nodo.addEventListener('focusin', function () { marcar(b.id); });
            nodo.addEventListener('mousedown', function () { marcar(b.id); });
            caja.appendChild(nodo);
        });
    }
    function marcar(bid) {
        if (activo === bid) return;
        activo = bid;
        $$('.mm-bloque', caja).forEach(function (x) { x.classList.toggle('activo', x.getAttribute('data-id') === bid); });
    }

    $$('#mm-agregar [data-nuevo]').forEach(function (b) {
        b.addEventListener('click', function () {
            var tipo = b.getAttribute('data-nuevo');
            if (tipo === 'imagen') { destinoImagen = null; $('#mm-archivo').click(); return; }
            insertar(nuevo(tipo));
        });
    });
    $$('[data-cmd]').forEach(function (b) {
        b.addEventListener('mousedown', function (e) { e.preventDefault(); });
        b.addEventListener('click', function () { document.execCommand(b.getAttribute('data-cmd'), false, null); });
    });

    // -------------------------------------------------------------------
    // Imágenes: pegar, arrastrar o subir
    // -------------------------------------------------------------------
    var destinoImagen = null;     // una pregunta, si la imagen es para ella
    function subirImagen(archivo) {
        estado('Subiendo imagen…');
        var f = new FormData();
        f.append('imagen', archivo, archivo.name || 'pegada.png');
        return fetch(CFG.imagen, { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': CFG.csrf }, body: f })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (!j.ok) { estado(j.error || 'No se pudo subir la imagen', true); return; }
                IMAGENES[j.id] = j.url;
                if (j.nube) {
                    $('#mm-nube-texto') && ($('#mm-nube-texto').textContent = j.nube.usado_mb + ' MB de ' + j.nube.cuota_mb + ' MB');
                }
                if (destinoImagen) { destinoImagen.imagen = j.id; destinoImagen = null; pintar(); cambio(); }
                else { var b = nuevo('imagen'); b.imagen = j.id; b.ancho = 60; b.pie = ''; insertar(b); }
            }).catch(function () { estado('No se pudo subir la imagen', true); });
    }
    function imagenesDe(lista) {
        return Array.prototype.filter.call(lista || [], function (f) { return f && f.type && f.type.indexOf('image/') === 0; });
    }
    $('#mm-archivo').addEventListener('change', function () {
        var archivos = imagenesDe(this.files);
        archivos.reduce(function (p, f) { return p.then(function () { return subirImagen(f); }); }, Promise.resolve());
        this.value = '';
    });
    document.addEventListener('paste', function (e) {
        var cd = e.clipboardData;
        if (!cd) return;
        var archivos = [];
        Array.prototype.forEach.call(cd.items || [], function (it) { if (it.kind === 'file' && it.type.indexOf('image/') === 0) archivos.push(it.getAsFile()); });
        if (archivos.length) {
            e.preventDefault();
            var b = activo && datos.bloques[indice(activo)];
            destinoImagen = b && b.tipo === 'pregunta' && !b.imagen ? b : null;
            archivos.reduce(function (p, f) { return p.then(function () { return subirImagen(f); }); }, Promise.resolve());
            return;
        }
        // Texto pegado de Word o de internet: solo el texto, sin estilos ajenos.
        if (e.target && e.target.isContentEditable) {
            e.preventDefault();
            document.execCommand('insertText', false, cd.getData('text/plain'));
        }
    });
    var hoja = $('#mm-hoja');
    hoja.addEventListener('dragover', function (e) { e.preventDefault(); hoja.classList.add('mm-soltar'); });
    hoja.addEventListener('dragleave', function () { hoja.classList.remove('mm-soltar'); });
    hoja.addEventListener('drop', function (e) {
        hoja.classList.remove('mm-soltar');
        var archivos = imagenesDe(e.dataTransfer && e.dataTransfer.files);
        if (!archivos.length) return;
        e.preventDefault();
        destinoImagen = null;
        archivos.reduce(function (p, f) { return p.then(function () { return subirImagen(f); }); }, Promise.resolve());
    });

    // -------------------------------------------------------------------
    // Acomodar: modo, columnas, letra
    // -------------------------------------------------------------------
    function pintarOpciones() {
        var o = datos.opciones;
        $$('#mm-modo [data-modo]').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-modo') === o.modo); });
        $$('#mm-columnas [data-col]').forEach(function (b) { b.classList.toggle('active', +b.getAttribute('data-col') === +o.columnas); });
        $('#mm-letra').value = o.letra; $('#mm-letra-v').textContent = o.letra;
        $('#mm-datos').checked = o.datos !== false; $('#mm-nombre').checked = o.nombre_estudiante !== false;
        var pub = $('#mm-publicar [name=modo]'); if (pub) pub.value = o.modo;
    }
    $$('#mm-modo [data-modo]').forEach(function (b) { b.addEventListener('click', function () { datos.opciones.modo = b.getAttribute('data-modo'); pintarOpciones(); cambio(); }); });
    $$('#mm-columnas [data-col]').forEach(function (b) { b.addEventListener('click', function () { datos.opciones.columnas = +b.getAttribute('data-col'); pintarOpciones(); cambio(); }); });
    $('#mm-letra').addEventListener('input', function () { datos.opciones.letra = +this.value; pintarOpciones(); cambio(); });
    $('#mm-datos').addEventListener('change', function () { datos.opciones.datos = this.checked; cambio(); });
    $('#mm-nombre').addEventListener('change', function () { datos.opciones.nombre_estudiante = this.checked; cambio(); });

    $('#mm-contar').addEventListener('click', function () {
        var out = $('#mm-paginas');
        out.textContent = 'Contando…';
        guardar().then(function () { return fetch(CFG.paginas, { credentials: 'same-origin' }); })
            .then(function (r) { return r.json(); })
            .then(function (p) {
                out.innerHTML = '';
                out.appendChild(el('div', { text: 'Normal: ' + p.normal + ' · Compacto: ' + p.compacto + ' · Máximo ahorro: ' + p.maximo + ' página(s)' }));
                var copias = el('input', { type: 'number', min: '1', max: '200', value: '35', class: 'form-control form-control-sm d-inline-block', style: 'width:70px' });
                var res = el('div', { class: 'fw-semibold mt-1' });
                function calcular() {
                    var c = Math.max(1, +copias.value || 1);
                    var ahorro = (p.normal - p.maximo) * c;
                    res.textContent = ahorro > 0 ? 'Con máximo ahorro se ahorran ' + ahorro + ' hojas para ' + c + ' copias.' : 'Ya está en el mínimo de páginas.';
                }
                copias.addEventListener('input', calcular);
                out.appendChild(el('div', { class: 'mt-1' }, [el('span', { text: 'Copias: ' }), copias]));
                out.appendChild(res);
                calcular();
            }).catch(function () { out.textContent = 'No se pudo contar.'; });
    });

    // -------------------------------------------------------------------
    // Vista previa, descargas y nube del docente
    // -------------------------------------------------------------------
    $('#mm-ver').addEventListener('click', function () {
        guardar().then(function () {
            $('#mm-previa-marco').src = CFG.pdf + '?t=' + Date.now();
            if (window.bootstrap) new bootstrap.Modal($('#mm-previa')).show(); else window.open(CFG.pdf, '_blank');
        });
    });
    ['#mm-pdf', '#mm-word'].forEach(function (s) {
        $(s).addEventListener('click', function (e) {
            e.preventDefault();
            var url = this.href;
            guardar().then(function () { location.href = url; });
        });
    });
    var formPub = $('#mm-publicar');
    if (formPub) formPub.addEventListener('submit', function (e) {
        e.preventDefault();
        guardar().then(function () { formPub.submit(); });
    });

    var NOMBRE_NUBE = { google: 'Google Drive', onedrive: 'OneDrive' };
    var CARPETA = 'mcolegio-materiales';
    var esperando = null;
    function token(p) {
        try { var t = JSON.parse(sessionStorage.getItem('cu-token-' + p) || 'null'); return t && t.expira > Date.now() ? t.token : null; }
        catch (e) { return null; }
    }
    function recibirPermiso(d) {
        if (!d || (d.tipo !== 'token' && d.tipo !== 'error')) return;
        if (d.tipo === 'error') { estado('No se conectó ' + NOMBRE_NUBE[d.proveedor] + ': ' + d.error, true); return; }
        try { sessionStorage.setItem('cu-token-' + d.proveedor, JSON.stringify({ token: d.token, expira: d.expira })); } catch (e) {}
        if (esperando) { var f = esperando; esperando = null; f(); }
    }
    try { new BroadcastChannel('mcolegio-nube').onmessage = function (ev) { recibirPermiso(ev.data); }; } catch (e) {}
    window.addEventListener('message', function (ev) { if (ev.origin === location.origin) recibirPermiso(ev.data); });
    function api(url, opciones, p) {
        opciones = opciones || {};
        opciones.headers = Object.assign({ Authorization: 'Bearer ' + token(p) }, opciones.headers || {});
        return fetch(url, opciones).then(function (r) {
            if (!r.ok) throw new Error(NOMBRE_NUBE[p] + ' respondió ' + r.status);
            return r;
        });
    }
    function carpetaGoogle() {
        var q = encodeURIComponent("name='" + CARPETA + "' and mimeType='application/vnd.google-apps.folder' and trashed=false");
        return api('https://www.googleapis.com/drive/v3/files?q=' + q + '&fields=files(id)', {}, 'google')
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.files && d.files.length) return d.files[0].id;
                return api('https://www.googleapis.com/drive/v3/files?fields=id', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: CARPETA, mimeType: 'application/vnd.google-apps.folder' })
                }, 'google').then(function (r) { return r.json(); }).then(function (f) { return f.id; });
            });
    }
    function subir(p, blob, nombre) {
        if (p === 'google') {
            return carpetaGoogle().then(function (carpeta) {
                var cuerpo = new FormData();
                cuerpo.append('metadata', new Blob([JSON.stringify({ name: nombre, parents: [carpeta] })], { type: 'application/json' }));
                cuerpo.append('file', blob);
                return api('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id', { method: 'POST', body: cuerpo }, 'google');
            });
        }
        return api('https://graph.microsoft.com/v1.0/me/drive/root:/' + CARPETA + '/' + encodeURIComponent(nombre) +
                   ':/content?@microsoft.graph.conflictBehavior=rename',
                   { method: 'PUT', headers: { 'Content-Type': blob.type || 'application/octet-stream' }, body: blob }, 'onedrive');
    }
    function guardarEnNube(p, formato) {
        if (!token(p)) {
            esperando = function () { guardarEnNube(p, formato); };
            window.open(CFG.ayudante.replace('PROV', p), 'mm-nube', 'width=520,height=680');
            estado('Conecte su ' + NOMBRE_NUBE[p] + ' en la ventana que se abrió…');
            return;
        }
        var url = formato === 'word' ? CFG.word : CFG.pdf + '?descargar=1';
        var nombre = ($('#mm-titulo').value || 'material').replace(/[\\/:*?"<>|]/g, '').slice(0, 60) + (formato === 'word' ? '.docx' : '.pdf');
        estado('Guardando en ' + NOMBRE_NUBE[p] + '…');
        guardar().then(function () { return fetch(url, { credentials: 'same-origin' }); })
            .then(function (r) { if (!r.ok) throw new Error('No se pudo generar el archivo'); return r.blob(); })
            .then(function (blob) { return subir(p, blob, nombre); })
            .then(function () { estado('Copia guardada en ' + NOMBRE_NUBE[p] + ' · carpeta ' + CARPETA); })
            .catch(function (e) { estado(e.message, true); });
    }
    $$('[data-nube]').forEach(function (b) {
        b.addEventListener('click', function () { guardarEnNube(b.getAttribute('data-nube'), b.getAttribute('data-formato')); });
    });

    pintarOpciones();
    pintar();
})();
