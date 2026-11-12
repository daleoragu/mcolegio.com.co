/* Menú encadenado de la región: País → Departamento → Municipio (DANE · DIVIPOLA).
 * Los municipios salen del departamento escogido; con «Otro país» se escriben el país y la ciudad. */
(function () {
  'use strict';
  var nodo = document.getElementById('mm-regiones');
  if (!nodo) return;
  var R = JSON.parse(nodo.textContent);
  document.querySelectorAll('form').forEach(function (f) {
    var pais = f.querySelector('.mm-region-pais'), dep = f.querySelector('.mm-region-dep'),
        mun = f.querySelector('.mm-region-mun'), otro = f.querySelector('.mm-region-otro');
    if (!pais || !dep || !mun) return;
    function caja(el) { return el.closest('.mb-3') || el.parentNode; }
    function llenar() {
      var lista = R.municipios[dep.value] || [], antes = mun.value;
      mun.innerHTML = '';
      var o = document.createElement('option'); o.value = '';
      o.textContent = dep.value ? 'Escoja el municipio…' : 'Escoja primero el departamento';
      mun.appendChild(o);
      lista.forEach(function (m) { var x = document.createElement('option'); x.value = m[0]; x.textContent = m[1]; mun.appendChild(x); });
      mun.value = lista.some(function (m) { return m[0] === antes; }) ? antes : '';
      // Bogotá tiene un solo «municipio»: se escoge solo
      if (lista.length === 1) mun.value = lista[0][0];
      mun.disabled = !dep.value;
    }
    function verPais() {
      var colombia = pais.value !== 'otro';
      caja(dep).hidden = !colombia; caja(mun).hidden = !colombia;
      if (otro) caja(otro).hidden = colombia;
    }
    dep.addEventListener('change', llenar);
    pais.addEventListener('change', verPais);
    llenar(); verPais();
    f.addEventListener('submit', function () { mun.disabled = false; });
  });
})();
