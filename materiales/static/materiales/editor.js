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
    var MODOS = JSON.parse(document.getElementById('mm-modos').textContent || '{}');

    function cambiarModo(b, modo) {
        b.modo = modo;
        if ((modo === 'unica' || modo === 'varias') && !(b.opciones && b.opciones.length)) b.opciones = ['', '', '', ''];
        if (modo === 'varias' && !b.correctas) b.correctas = [];
        if (modo === 'completar' && !b.texto) b.texto = '';
        if (modo === 'corta' && !b.aceptadas) b.aceptadas = [];
        if (modo === 'emparejar' && !b.pares) b.pares = [['', ''], ['', ''], ['', '']];
        if (modo === 'ordenar' && !b.elementos) b.elementos = ['', '', ''];
        if (modo === 'clasificar' && !b.grupos) b.grupos = [{ nombre: '', elementos: [] }, { nombre: '', elementos: [] }];
        if (modo === 'abierta' && !b.lineas) b.lineas = 3;
    }

    function listaTexto(valores, ayuda, alCambiar, filas) {
        var t = el('textarea', { class: 'form-control form-control-sm', rows: String(filas || 4), placeholder: ayuda });
        t.value = (valores || []).join('\n');
        t.addEventListener('input', function () { alCambiar(t.value.split('\n').map(function (x) { return x.trim(); }).filter(Boolean)); cambio(); });
        return t;
    }

    // Lo que va debajo del enunciado según el tipo de pregunta
    var CUERPO = {
        unica: function (b) { return opcionesUI(b, false); },
        varias: function (b) { return opcionesUI(b, true); },
        vf: function (b) {
            var s2 = el('select', { class: 'form-select form-select-sm', style: 'width:auto' }, [
                el('option', { value: 'v', text: 'Es verdadera' }), el('option', { value: 'f', text: 'Es falsa' })]);
            s2.value = b.valor ? 'v' : 'f';
            s2.addEventListener('change', function () { b.valor = s2.value === 'v'; cambio(); });
            return el('div', { class: 'd-flex gap-2 align-items-center small' }, [el('span', { text: 'La afirmación' }), s2]);
        },
        completar: function (b) {
            var t = el('textarea', { class: 'form-control form-control-sm', rows: '3',
                placeholder: 'La capital de Colombia es [[Bogotá]] y el río más largo es el [[Magdalena|río Magdalena]].' });
            t.value = b.texto || '';
            t.addEventListener('input', function () { b.texto = t.value; cambio(); });
            var m = el('input', { type: 'checkbox', class: 'form-check-input', id: 'may-' + b.id });
            m.checked = !!b.mayusculas;
            m.addEventListener('change', function () { b.mayusculas = m.checked; cambio(); });
            return el('div', {}, [t, el('div', { class: 'small text-muted mt-1' }, [
                el('span', { html: 'Ponga cada espacio entre dobles corchetes: <b>[[respuesta]]</b>. Si vale de varias formas: <b>[[forma 1|forma 2]]</b>. ' }),
                el('span', { class: 'form-check d-inline-block ms-1' }, [m, el('label', { class: 'form-check-label', for: 'may-' + b.id, text: 'Exigir tildes y mayúsculas' })])])]);
        },
        numerica: function (b) {
            return el('div', { class: 'd-flex flex-wrap gap-2 align-items-center small' }, [
                el('span', { text: 'Respuesta' }), campo(b.respuesta, '3,5', function (v) { b.respuesta = v; }, 'form-control form-control-sm w-auto'),
                el('span', { text: 'Margen ±' }), campo(b.tolerancia, '0', function (v) { b.tolerancia = v; }, 'form-control form-control-sm w-auto'),
                el('span', { text: 'Unidad' }), campo(b.unidad, 'cm', function (v) { b.unidad = v; }, 'form-control form-control-sm w-auto')]);
        },
        corta: function (b) {
            return el('div', { class: 'small' }, [el('div', { class: 'text-muted', text: 'Respuestas que se aceptan (una por línea). Si el estudiante escribe otra cosa, usted la revisa.' }),
                listaTexto(b.aceptadas, 'fotosíntesis', function (v) { b.aceptadas = v; }, 2)]);
        },
        abierta: function (b) {
            var n = el('input', { type: 'number', min: '1', max: '20', class: 'form-control form-control-sm', style: 'width:70px' });
            n.value = b.lineas || 3;
            n.addEventListener('input', function () { b.lineas = Math.max(1, Math.min(20, +n.value || 3)); cambio(); });
            return el('div', { class: 'd-flex gap-2 align-items-center small text-muted' }, [el('span', { text: 'Líneas para responder' }), n,
                el('span', { text: '· la califica usted' })]);
        },
        emparejar: function (b) {
            var caja3 = el('div', { class: 'small' }, [el('div', { class: 'text-muted', text: 'Escriba cada pareja; al estudiante le salen en desorden.' })]);
            b.pares.forEach(function (par, i) {
                caja3.appendChild(el('div', { class: 'd-flex gap-1 my-1' }, [
                    campo(par[0], 'Concepto', function (v) { b.pares[i][0] = v; }),
                    el('span', { class: 'align-self-center', text: '↔' }),
                    campo(par[1], 'Su pareja', function (v) { b.pares[i][1] = v; }),
                    el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger', html: '&times;', title: 'Quitar',
                        onclick: function () { b.pares.splice(i, 1); cambio(); pintar(); } })]));
            });
            if (b.pares.length < 12) caja3.appendChild(el('button', { type: 'button', class: 'btn btn-sm btn-link', text: '+ pareja',
                onclick: function () { b.pares.push(['', '']); cambio(); pintar(); } }));
            return caja3;
        },
        ordenar: function (b) {
            return el('div', { class: 'small' }, [el('div', { class: 'text-muted', text: 'Escriba los pasos en el orden correcto, uno por línea; al estudiante le salen en desorden.' }),
                listaTexto(b.elementos, 'Lava los mangos\nCorta la pulpa\nLicúa', function (v) { b.elementos = v; }, 4)]);
        },
        clasificar: function (b) {
            var caja3 = el('div', { class: 'small' }, [el('div', { class: 'text-muted', text: 'Cada grupo con sus elementos separados por comas.' })]);
            b.grupos.forEach(function (g, i) {
                var elems = el('input', { type: 'text', class: 'form-control form-control-sm', placeholder: 'perro, gato, vaca' });
                elems.value = (g.elementos || []).join(', ');
                elems.addEventListener('input', function () { g.elementos = elems.value.split(',').map(function (x) { return x.trim(); }).filter(Boolean); cambio(); });
                caja3.appendChild(el('div', { class: 'd-flex gap-1 my-1' }, [
                    campo(g.nombre, 'Grupo', function (v) { g.nombre = v; }, 'form-control form-control-sm w-25'), elems,
                    el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger', html: '&times;', title: 'Quitar grupo',
                        onclick: function () { b.grupos.splice(i, 1); cambio(); pintar(); } })]));
            });
            if (b.grupos.length < 6) caja3.appendChild(el('button', { type: 'button', class: 'btn btn-sm btn-link', text: '+ grupo',
                onclick: function () { b.grupos.push({ nombre: '', elementos: [] }); cambio(); pintar(); } }));
            return caja3;
        }
    };

    function opcionesUI(b, varias) {
        var caja3 = el('div');
        var letras = 'ABCDEF';
        b.opciones = b.opciones || [];
        if (varias) b.correctas = b.correctas || [];
        b.opciones.forEach(function (op, i) {
            var marca = el('input', { type: varias ? 'checkbox' : 'radio', name: 'c-' + b.id, title: 'Respuesta correcta', class: 'form-check-input mt-0' });
            marca.checked = varias ? b.correctas.indexOf(i) >= 0 : b.correcta === i;
            marca.addEventListener('change', function () {
                if (varias) {
                    b.correctas = b.correctas.filter(function (x) { return x !== i; });
                    if (marca.checked) b.correctas.push(i);
                } else b.correcta = i;
                cambio();
            });
            caja3.appendChild(el('div', { class: 'mm-op' }, [marca, el('b', { text: letras[i] + '.' }),
                campo(op, 'Opción ' + letras[i], function (v) { b.opciones[i] = v; }, ''),
                el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger py-0', title: 'Quitar opción', html: '&times;',
                    onclick: function () {
                        b.opciones.splice(i, 1);
                        if (varias) b.correctas = b.correctas.filter(function (x) { return x !== i; }).map(function (x) { return x > i ? x - 1 : x; });
                        else if (b.correcta === i) b.correcta = null; else if (b.correcta > i) b.correcta--;
                        cambio(); pintar();
                    } })]));
        });
        caja3.appendChild(el('div', { class: 'd-flex gap-2 small' }, [
            b.opciones.length < 6 ? el('button', { type: 'button', class: 'btn btn-sm btn-link py-0', text: '+ opción',
                onclick: function () { b.opciones.push(''); cambio(); pintar(); } }) : null,
            el('span', { class: 'text-muted align-self-center', text: varias ? 'marque todas las correctas' : 'marque la correcta' })]));
        return caja3;
    }

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
        if (tipo === 'pregunta') { b.modo = 'unica'; b.puntos = 1; b.enunciado = ''; b.opciones = ['', '', '', '']; b.correcta = null; b.lineas = 0; b.imagen = null; }
        if (tipo === 'contexto') { b.titulo = ''; b.html = ''; b.imagen = null; b.ancho = 70; b.cubre = 0; }
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
            if (!b.modo) b.modo = (b.opciones && b.opciones.some(function (o) { return o; })) ? 'unica' : 'abierta';
            var caja2 = el('div');
            var sel = el('select', { class: 'form-select form-select-sm', style: 'width:auto', 'aria-label': 'Tipo de pregunta' });
            Object.keys(MODOS).forEach(function (k) { sel.appendChild(el('option', { value: k, text: MODOS[k] })); });
            sel.value = b.modo;
            sel.addEventListener('change', function () { cambiarModo(b, sel.value); cambio(); pintar(); });
            var pts = el('input', { type: 'number', min: '1', max: '100', class: 'form-control form-control-sm', style: 'width:70px', title: 'Puntos' });
            pts.value = b.puntos || 1;
            pts.addEventListener('input', function () { b.puntos = Math.max(1, Math.min(100, +pts.value || 1)); cambio(); });
            var ctl = el('input', { type: 'checkbox', class: 'form-check-input', id: 'ctl-' + b.id });
            ctl.checked = !!b.control;
            ctl.addEventListener('change', function () { b.control = ctl.checked; cambio(); });
            caja2.appendChild(el('div', { class: 'd-flex flex-wrap gap-2 align-items-center mb-1 small' }, [sel,
                el('span', { class: 'text-muted', text: 'Puntos' }), pts,
                el('span', { class: 'form-check ms-1' }, [ctl, el('label', { class: 'form-check-label text-muted', for: 'ctl-' + b.id, text: 'De control (no cuenta)' })])]));
            caja2.appendChild(editable(b.enunciado, b.modo === 'completar' ? 'Indicación (opcional): Completa con la palabra correcta' : 'Escriba la pregunta…', function (v) { b.enunciado = v; }, true));
            if (b.imagen && IMAGENES[b.imagen]) {
                caja2.appendChild(el('div', { class: 'mm-img text-center' }, [el('img', { src: IMAGENES[b.imagen], alt: 'Imagen de la pregunta', style: 'width:45%' }),
                    el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger', text: 'Quitar imagen', onclick: function () { b.imagen = null; cambio(); pintar(); } })]));
            }
            caja2.appendChild((CUERPO[b.modo] || CUERPO.abierta)(b));
            caja2.appendChild(el('div', { class: 'd-flex flex-wrap gap-2 align-items-center small mt-1' }, [
                el('button', { type: 'button', class: 'btn btn-sm btn-link py-0', text: 'Imagen para la pregunta',
                    onclick: function () { activo = b.id; destinoImagen = b; $('#mm-archivo').click(); } })]));
            return caja2;
        },
        contexto: function (b) {
            var cubre = el('input', { type: 'number', min: '0', max: '30', class: 'form-control form-control-sm', style: 'width:70px' });
            cubre.value = b.cubre || 0;
            cubre.addEventListener('input', function () { b.cubre = Math.max(0, Math.min(30, +cubre.value || 0)); cambio(); });
            var hijos = [el('div', { class: 'small fw-bold text-primary', text: 'Texto o imagen que comparten varias preguntas' }),
                campo(b.titulo, 'Título (opcional)', function (v) { b.titulo = v; }, 'form-control form-control-sm fw-bold text-center border-0')];
            if (b.imagen && IMAGENES[b.imagen]) {
                var img = el('img', { src: IMAGENES[b.imagen], alt: 'Imagen del texto', style: 'width:' + (b.ancho || 70) + '%' });
                var rango = el('input', { type: 'range', min: '10', max: '100', step: '5', class: 'form-range', style: 'max-width:200px' });
                rango.value = b.ancho || 70;
                rango.addEventListener('input', function () { b.ancho = +rango.value; img.style.width = b.ancho + '%'; cambio(); });
                hijos.push(el('div', { class: 'mm-img text-center' }, [img, el('div', {}, [rango]),
                    el('button', { type: 'button', class: 'btn btn-sm btn-link text-danger', text: 'Quitar imagen', onclick: function () { b.imagen = null; cambio(); pintar(); } })]));
            }
            hijos.push(editable(b.html, 'El texto, la receta, la biografía o la explicación de la gráfica…', function (v) { b.html = v; }));
            hijos.push(el('div', { class: 'd-flex flex-wrap gap-2 align-items-center small text-muted mt-1' }, [
                el('button', { type: 'button', class: 'btn btn-sm btn-link py-0', text: b.imagen ? 'Cambiar imagen' : 'Agregar imagen',
                    onclick: function () { activo = b.id; destinoImagen = b; $('#mm-archivo').click(); } }),
                el('span', { class: 'ms-auto', text: 'Preguntas que cubre (0 = hasta el siguiente texto o sección)' }), cubre]));
            return el('div', { class: 'border-start border-4 border-primary ps-2' }, hijos);
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
            destinoImagen = b && (b.tipo === 'pregunta' || b.tipo === 'contexto') && !b.imagen ? b : null;
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
    // Cuadernillo: portada y datos de la sesión
    var CAMPOS_CUAD = ['sesion', 'duracion', 'horario', 'aviso', 'fin'];
    CAMPOS_CUAD.forEach(function (k) {
        var c = $('#mm-c-' + k);
        if (!c) return;
        c.value = datos.opciones[k] || '';
        c.addEventListener('input', function () { datos.opciones[k] = c.value; cambio(); });
    });
    var portada = $('#mm-c-portada');
    if (portada) {
        portada.checked = !!datos.opciones.portada;
        portada.addEventListener('change', function () { datos.opciones.portada = portada.checked; cambio(); });
    }
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
    $$('.mm-guardar-antes').forEach(function (a) {
        a.addEventListener('click', function (e) { e.preventDefault(); var url = a.href; guardar().then(function () { location.href = url; }); });
    });
    $$('.mm-form-guardar').forEach(function (f) {
        f.addEventListener('submit', function (e) { e.preventDefault(); guardar().then(function () { f.submit(); }); });
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
