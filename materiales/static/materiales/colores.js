/* Selector de color de los documentos (Mi encabezado y el editor): muestras y un color libre. */
window.MMColores = {
    iniciar: function (id, actual, alCambiar) {
        var caja = document.getElementById(id);
        if (!caja) return;
        var libre = caja.querySelector('input[type=color]');
        function marcar(c) {
            var hay = false;
            caja.querySelectorAll('.mm-color[data-color]').forEach(function (b) {
                var on = b.dataset.color.toLowerCase() === c.toLowerCase(); b.classList.toggle('on', on); hay = hay || on;
            });
            var l = caja.querySelector('.mm-color.libre');
            l.classList.toggle('on', !hay); if (!hay) l.style.setProperty('--c', c);
            libre.value = c;
        }
        caja.querySelectorAll('.mm-color[data-color]').forEach(function (b) {
            b.addEventListener('click', function () { marcar(b.dataset.color); alCambiar(b.dataset.color); });
        });
        libre.addEventListener('input', function () { marcar(libre.value); alCambiar(libre.value); });
        marcar(actual || '#1f3a68');
        return {poner: marcar};
    },
    /* La regla de color que corresponde a un área (o grado): [{area, color}] */
    regla: function (reglas, texto) {
        function c(t) { return (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').trim(); }
        var t = c(texto);
        if (!t) return null;
        for (var i = 0; i < (reglas || []).length; i++) {
            var k = c(reglas[i].area);
            if (k && (t.indexOf(k) >= 0 || k.indexOf(t) >= 0)) return reglas[i].color;
        }
        return null;
    }
};
