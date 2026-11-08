/* Mis materiales · trabajo en equipo: invitar docentes (buscar por nombre y área), permisos, quitar,
 * quién más tiene abierto el material y aviso cuando otro docente guarda cambios. */
(function () {
    'use strict';
    var CFG = window.MM, $ = function (s) { return document.querySelector(s); };
    if (!CFG || !CFG.equipo) return;
    var panel = $('#mm-equipo'), lista = $('#mm-equipo-lista'), res = $('#mm-equipo-resultados');
    function esc(t) { var d = document.createElement('div'); d.textContent = t == null ? '' : t; return d.innerHTML; }
    function post(datos) {
        var f = new FormData(); Object.keys(datos).forEach(function (k) { f.append(k, datos[k]); });
        return fetch(CFG.equipo, { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': CFG.csrf }, body: f })
            .then(function (r) { return r.json(); });
    }
    function pintarEquipo(eq) {
        $('#mm-equipo-n').textContent = eq.length || '';
        if (!eq.length) { lista.innerHTML = '<div class="small text-muted">Todavía no hay nadie más en este material.</div>'; return; }
        lista.innerHTML = eq.map(function (c) {
            var acciones = CFG.rol === 'dueno'
                ? '<select class="form-select form-select-sm d-inline-block w-auto mm-eq-perm" data-c="' + c.id + '"><option value="editar"' + (c.permiso === 'editar' ? ' selected' : '') + '>Puede editar</option><option value="ver"' + (c.permiso === 'ver' ? ' selected' : '') + '>Solo puede ver</option></select> ' +
                  '<button type="button" class="btn btn-sm btn-link text-danger p-0 ms-1 mm-eq-quitar" data-c="' + c.id + '" title="Quitar del equipo">Quitar</button>'
                : '<span class="text-muted">' + (c.permiso === 'editar' ? 'Puede editar' : 'Solo ver') + '</span>';
            return '<div class="d-flex align-items-center gap-2 border-bottom py-1 small"><i class="fas fa-user text-muted"></i><b class="flex-grow-1">' + esc(c.nombre) + '</b>' +
                (c.estado === 'pendiente' ? '<span class="badge text-bg-light">invitado, sin responder</span>' : '<span class="badge text-bg-success">en el equipo</span>') + acciones + '</div>';
        }).join('');
    }
    function cargar(params) {
        var u = CFG.equipo + (params ? '?' + new URLSearchParams(params).toString() : '');
        return fetch(u, { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (j) {
            pintarEquipo(j.equipo);
            var sel = $('#mm-eq-area');
            if (sel && j.areas && sel.options.length === 1) j.areas.forEach(function (a) { var o = document.createElement('option'); o.value = a; o.textContent = a; sel.appendChild(o); });
            if (params) {
                res.innerHTML = j.encontrados.length ? j.encontrados.map(function (u) {
                    return '<div class="d-flex align-items-center gap-2 border-bottom py-1"><span class="flex-grow-1"><b>' + esc(u.nombre) + '</b>' + (u.area ? ' <span class="text-muted">· ' + esc(u.area) + '</span>' : '') + '</span>' +
                        '<button type="button" class="btn btn-sm btn-outline-primary mm-eq-invitar" data-u="' + u.id + '"><i class="fas fa-user-plus me-1"></i>Invitar</button></div>';
                }).join('') : '<div class="text-muted">No hay docentes con esa búsqueda' + (CFG.colegio ? '.' : '. En el plan individual solo aparecen sus colegas.') + '</div>';
            }
        });
    }
    var espera = null;
    function buscar(todos) {
        var p = { q: $('#mm-eq-q').value, area: $('#mm-eq-area').value };
        if (todos) p.todos = 1;
        if (!p.q && !p.area && !todos) { res.innerHTML = ''; return; }
        cargar(p);
    }
    $('#mm-equipo-abrir').addEventListener('click', function () { panel.hidden = !panel.hidden; if (!panel.hidden) cargar(); });
    $('#mm-equipo-cerrar').addEventListener('click', function () { panel.hidden = true; });
    if ($('#mm-eq-q')) {
        $('#mm-eq-q').addEventListener('input', function () { clearTimeout(espera); espera = setTimeout(function () { buscar(false); }, 300); });
        $('#mm-eq-area').addEventListener('change', function () { buscar(false); });
        $('#mm-eq-todos').addEventListener('click', function () { buscar(true); });
    }
    panel.addEventListener('click', function (e) {
        var b = e.target.closest('.mm-eq-invitar, .mm-eq-quitar');
        if (!b) return;
        var datos = b.classList.contains('mm-eq-invitar') ? { accion: 'invitar', usuario: b.dataset.u, permiso: $('#mm-eq-permiso').value }
                                                          : { accion: 'quitar', colaborador: b.dataset.c };
        if (datos.accion === 'quitar' && !confirm('¿Quitar a este docente del material?')) return;
        b.disabled = true;
        post(datos).then(function (j) {
            if (!j.ok) { alert(j.error || 'No se pudo.'); b.disabled = false; return; }
            pintarEquipo(j.equipo);
            if (datos.accion === 'invitar') b.closest('div').remove();
        });
    });
    panel.addEventListener('change', function (e) {
        var s = e.target.closest('.mm-eq-perm');
        if (s) post({ accion: 'permiso', colaborador: s.dataset.c, permiso: s.value }).then(function (j) { if (j.ok) pintarEquipo(j.equipo); });
    });

    // Quién más lo tiene abierto y si otro docente guardó cambios
    function aviso(texto) { $('#mm-conflicto-texto').textContent = texto; $('#mm-conflicto').hidden = false; }
    window.addEventListener('mm-conflicto', function (e) { aviso(e.detail.error); });
    function sondear() {
        if (document.hidden) return;
        fetch(CFG.estado, { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (j) {
            var p = j.presentes || [];
            $('#mm-presentes').innerHTML = p.length ? '<i class="fas fa-circle" style="font-size:.5rem"></i> También aquí: ' + esc(p.join(', ')) : '';
            if (j.version > CFG.version && j.editado_por_otro) {
                CFG.version = j.version;
                if (CFG.soloVer) aviso(j.editado_por + ' actualizó el material. Recargue para ver la versión nueva.');
                else { CFG.bloqueado = true; aviso(j.editado_por + ' guardó cambios en este material. Recargue para verlos antes de seguir editando.'); }
            }
        }).catch(function () {});
    }
    sondear(); setInterval(sondear, 15000);

    // Solo ver: nada se puede cambiar
    if (CFG.soloVer) {
        document.querySelectorAll('#mm-hoja [contenteditable], #mm-hoja input, #mm-hoja textarea, #mm-hoja select, #mm-titulo, #mm-area, #mm-grado, #mm-periodo')
            .forEach(function (el) { if (el.isContentEditable) el.contentEditable = 'false'; else el.disabled = true; });
        var ag = $('#mm-agregar'); if (ag) ag.hidden = true;
        var hoja = $('#mm-hoja'); if (hoja) hoja.classList.add('mm-solo-ver');
    }
})();
