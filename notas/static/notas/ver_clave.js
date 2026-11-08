/* Botón 👁 para ver u ocultar la contraseña en todos los campos de contraseña de la página. */
(function () {
  var OJO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  var TACHADO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 19c-7 0-11-7-11-7a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 7 11 7a18.5 18.5 0 0 1-2.16 3.19M1 1l22 22"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/></svg>';
  function preparar(inp) {
    if (inp.dataset.verClave) return;
    inp.dataset.verClave = '1';
    var caja = document.createElement('span');
    caja.style.cssText = 'position:relative;display:block;width:100%';
    inp.parentNode.insertBefore(caja, inp);
    caja.appendChild(inp);
    inp.style.paddingRight = '2.6rem';
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'ver-clave';
    b.setAttribute('aria-label', 'Mostrar contraseña');
    b.title = 'Mostrar contraseña';
    b.innerHTML = OJO;
    b.style.cssText = 'position:absolute;right:.35rem;top:50%;transform:translateY(-50%);border:0;background:transparent;' +
      'color:#6c757d;padding:.25rem .35rem;line-height:0;cursor:pointer;z-index:5';
    b.addEventListener('click', function () {
      var ver = inp.type === 'password';
      inp.type = ver ? 'text' : 'password';
      b.innerHTML = ver ? TACHADO : OJO;
      b.title = ver ? 'Ocultar contraseña' : 'Mostrar contraseña';
      b.setAttribute('aria-label', b.title);
      inp.focus();
    });
    caja.appendChild(b);
    // Al enviar el formulario se vuelve a ocultar (para que el navegador la guarde como contraseña)
    if (inp.form) inp.form.addEventListener('submit', function () { inp.type = 'password'; });
  }
  function todo() { document.querySelectorAll('input[type=password]').forEach(preparar); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', todo); else todo();
  window.verClave = todo;
})();
