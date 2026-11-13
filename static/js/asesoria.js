/* Asesoría docente: recorrido guiado por la página y modo «¿Qué es esto?».
 * Las guías vienen del servidor (notas/asesoria.py) en el JSON #asesoria-datos. */
(function () {
    'use strict';
    const datosEl = document.getElementById('asesoria-datos');
    if (!datosEl) return;
    const D = JSON.parse(datosEl.textContent);
    const $ = id => document.getElementById(id);
    const boton = $('as-boton'), panel = $('as-panel');
    const CLAVE = 'mc-asesoria-visto:' + (D.vista || '');
    const normal = t => (t || '').replace(/\s+/g, ' ').trim().toLowerCase();

    function visible(el) {
        if (!el || el.closest('#as-panel')) return false;
        const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
    }
    // Busca el elemento del paso: por selector, por texto (el más pequeño que lo contenga) o por ambos
    function buscar(p) {
        const raiz = p.en ? document.querySelector(p.en) : document;
        if (!raiz) return null;
        if (p.s && !p.c) return [...raiz.querySelectorAll(p.s)].find(visible) || null;
        const cand = [...raiz.querySelectorAll(p.s || 'h1,h2,h3,h4,h5,h6,a,button,label,th,summary,b,strong,.fw-semibold,.fw-bold')].filter(visible);
        const t = normal(p.c);
        const con = cand.filter(el => normal(el.textContent).includes(t));
        con.sort((a, b) => normal(a.textContent).length - normal(b.textContent).length);
        return con[0] || null;
    }

    // --- Panel -------------------------------------------------------------------------------------------
    const guia = D.guia;
    $('as-titulo').textContent = guia ? guia.titulo : 'Esta página';
    $('as-resumen').textContent = guia ? guia.resumen
        : 'Esta página todavía no tiene recorrido. Use «¿Qué es esto?» para que le explique cada botón, o mire el mapa para ubicarse.';
    const mapa = $('as-mapa');
    D.mapa.forEach(m => {
        const li = document.createElement('li');
        const b = document.createElement('b'); b.textContent = m.t; li.appendChild(b);
        li.appendChild(document.createTextNode(m.x));
        if (m.url) { const a = document.createElement('a'); a.href = m.url; a.textContent = ' Ir allá →'; li.appendChild(document.createElement('br')); li.appendChild(a); }
        mapa.appendChild(li);
    });
    function pasosDisponibles() {
        const vistos = new Set(), lista = [];
        (guia ? guia.pasos : []).forEach(p => {
            const el = buscar(p);
            if (el && !vistos.has(el)) { vistos.add(el); lista.push({p, el}); }
        });
        return lista;
    }
    function abrirPanel() {
        const n = pasosDisponibles().length;
        const rec = $('as-recorrido');
        rec.disabled = !n;
        $('as-npasos').textContent = n ? `${n} paso${n === 1 ? '' : 's'}: le muestro qué es cada cosa.` : 'Esta página no tiene recorrido todavía.';
        panel.hidden = false; boton.classList.remove('as-nuevo');
        try { localStorage.setItem(CLAVE, '1'); } catch (e) { /* sin almacenamiento */ }
        (n ? rec : $('as-quees')).focus();
    }
    function cerrarPanel() { panel.hidden = true; boton.focus(); }
    boton.addEventListener('click', () => (panel.hidden ? abrirPanel() : cerrarPanel()));
    $('as-cerrar').addEventListener('click', cerrarPanel);
    try { if (guia && !localStorage.getItem(CLAVE)) boton.classList.add('as-nuevo'); } catch (e) { /* nada */ }

    // --- Recorrido ---------------------------------------------------------------------------------------
    let pasos = [], i = 0, foco = null, burbuja = null;
    function limpiar() { foco && foco.remove(); burbuja && burbuja.remove(); foco = burbuja = null; document.removeEventListener('keydown', teclas); window.removeEventListener('resize', ubicar); window.removeEventListener('scroll', ubicar, true); }
    function teclas(ev) {
        if (ev.key === 'Escape') { limpiar(); boton.focus(); }
        else if (ev.key === 'ArrowRight') mostrar(i + 1);
        else if (ev.key === 'ArrowLeft') mostrar(i - 1);
    }
    function ubicar() {
        if (!foco || !pasos[i]) return;
        const r = pasos[i].el.getBoundingClientRect(), m = 6;
        Object.assign(foco.style, {left: r.left - m + 'px', top: r.top - m + 'px', width: r.width + 2 * m + 'px', height: r.height + 2 * m + 'px'});
        const bw = burbuja.offsetWidth, bh = burbuja.offsetHeight, vw = innerWidth, vh = innerHeight;
        let top = r.bottom + 14;
        if (top + bh > vh - 8) top = r.top - bh - 14;
        if (top < 8) top = Math.min(vh - bh - 8, Math.max(8, r.top + 14));
        const left = Math.min(vw - bw - 12, Math.max(12, r.left + r.width / 2 - bw / 2));
        Object.assign(burbuja.style, {left: left + 'px', top: top + 'px'});
    }
    function mostrar(k) {
        if (k < 0 || k >= pasos.length) return;
        i = k;
        const {p, el} = pasos[i];
        el.scrollIntoView({block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
        if (!foco) {
            foco = document.createElement('div'); foco.className = 'as-foco';
            burbuja = document.createElement('div'); burbuja.className = 'as-burbuja'; burbuja.setAttribute('role', 'dialog'); burbuja.setAttribute('aria-live', 'polite');
            document.body.append(foco, burbuja);
            document.addEventListener('keydown', teclas); window.addEventListener('resize', ubicar); window.addEventListener('scroll', ubicar, true);
        }
        burbuja.innerHTML = '';
        const t = document.createElement('b'); t.textContent = p.t;
        const x = document.createElement('p'); x.textContent = p.x;
        const nav = document.createElement('div'); nav.className = 'as-nav';
        const cuenta = document.createElement('span'); cuenta.textContent = `${i + 1} de ${pasos.length}`;
        nav.appendChild(cuenta);
        if (i > 0) { const a = document.createElement('button'); a.type = 'button'; a.className = 'as-ant'; a.textContent = 'Atrás'; a.onclick = () => mostrar(i - 1); nav.appendChild(a); }
        const s = document.createElement('button'); s.type = 'button';
        if (i < pasos.length - 1) { s.className = 'as-sig'; s.textContent = 'Siguiente'; s.onclick = () => mostrar(i + 1); }
        else { s.className = 'as-fin'; s.textContent = '¡Listo!'; s.onclick = () => { limpiar(); boton.focus(); }; }
        nav.appendChild(s);
        const salir = document.createElement('button'); salir.type = 'button'; salir.className = 'as-fin'; salir.textContent = 'Salir'; salir.onclick = () => { limpiar(); boton.focus(); };
        if (i < pasos.length - 1) nav.appendChild(salir);
        burbuja.append(t, x, nav);
        ubicar(); setTimeout(ubicar, 350);
        s.focus({preventScroll: true});
    }
    $('as-recorrido').addEventListener('click', () => {
        pasos = pasosDisponibles();
        if (!pasos.length) return;
        panel.hidden = true; limpiar(); mostrar(0);
    });

    // --- ¿Qué es esto? -----------------------------------------------------------------------------------
    let aviso = null, marco = null;
    function rotulo(el) {
        return (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '').replace(/\s+/g, ' ').trim();
    }
    function explicar(el) {
        const r = rotulo(el), n = normal(r), t = normal(el.getAttribute('title'));
        // 1) el paso de la guía de esta página que señala este mismo elemento
        const paso = (guia ? guia.pasos : []).find(p => { const e = buscar(p); return e && (e === el || e.contains(el) || el.contains(e)); });
        if (paso) return {t: paso.t, x: paso.x};
        // 2) el glosario
        const clave = Object.keys(D.glosario).sort((a, b) => b.length - a.length).find(k => n.includes(k) || (t && t.includes(k)));
        if (clave) return {t: r.slice(0, 60) || clave, x: D.glosario[clave]};
        // 3) lo que dice el propio botón
        if (el.getAttribute('title') && normal(el.getAttribute('title')) !== n) return {t: r.slice(0, 60), x: el.getAttribute('title')};
        return {t: r.slice(0, 60) || 'Esta parte', x: 'Todavía no tengo una explicación para esto. Si tiene dudas, escríbanos desde la Sala de Profesores y la agregamos.'};
    }
    function objetivo(ev) {
        const el = ev.target.closest('a,button,input,select,textarea,label,th,h1,h2,h3,h4,h5,h6,[title],.card,.mm-tarjeta,.au-tarjeta');
        return el && !el.closest('.as-quees-aviso,.as-burbuja,#as-panel,#as-boton') ? el : null;
    }
    function sobre(ev) {
        const el = objetivo(ev); if (!el) return;
        const r = el.getBoundingClientRect();
        Object.assign(marco.style, {left: r.left - 3 + 'px', top: r.top - 3 + 'px', width: r.width + 6 + 'px', height: r.height + 6 + 'px', display: 'block'});
    }
    function toque(ev) {
        if (ev.target.closest('.as-quees-aviso,.as-burbuja')) return;
        const el = objetivo(ev);
        ev.preventDefault(); ev.stopPropagation();
        if (!el) return;
        const e = explicar(el);
        pasos = [{p: e, el}]; i = 0;
        burbuja && burbuja.remove(); foco && foco.remove(); foco = burbuja = null;
        mostrar(0);
        burbuja.querySelector('.as-nav span').textContent = 'Toque otra cosa o Salir';
    }
    function salirQuees() {
        document.body.classList.remove('as-quees');
        document.removeEventListener('click', toque, true); document.removeEventListener('mouseover', sobre, true);
        document.removeEventListener('keydown', escQuees);
        aviso && aviso.remove(); marco && marco.remove(); aviso = marco = null; limpiar(); boton.focus();
    }
    function escQuees(ev) { if (ev.key === 'Escape') salirQuees(); }
    $('as-quees').addEventListener('click', () => {
        panel.hidden = true; limpiar();
        document.body.classList.add('as-quees');
        aviso = document.createElement('div'); aviso.className = 'as-quees-aviso'; aviso.setAttribute('role', 'status');
        aviso.innerHTML = '<span>Toque cualquier botón o sección y le explico qué es.</span>';
        const fin = document.createElement('button'); fin.type = 'button'; fin.textContent = 'Terminar'; fin.onclick = salirQuees;
        aviso.appendChild(fin);
        marco = document.createElement('div'); marco.className = 'as-marco'; marco.style.display = 'none';
        document.body.append(aviso, marco);
        setTimeout(() => { document.addEventListener('click', toque, true); document.addEventListener('mouseover', sobre, true); }, 0);
        document.addEventListener('keydown', escQuees);
    });
})();
