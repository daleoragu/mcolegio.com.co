/*!
 * Salón Digital — envío de resultados
 * Pega este archivo (o su contenido) en tu actividad y llama a SalonDigital.enviar()
 * cuando el estudiante termine. Al subir el archivo, Salón Digital completa solo
 * las dos constantes de abajo.
 */
const ENDPOINT = '';      // Salón Digital lo completa al subir el archivo
const CLAVE_PANEL = '';   // Salón Digital lo completa al subir el archivo

const SalonDigital = (function () {
  const COLA = 'salon_cola';

  function leerCola() {
    try { return JSON.parse(localStorage.getItem(COLA) || '[]'); } catch (e) { return []; }
  }
  function escribirCola(lista) {
    try { localStorage.setItem(COLA, JSON.stringify(lista)); } catch (e) {}
  }

  async function mandar(datos) {
    const r = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(datos),
    });
    if (!r.ok) throw new Error('respuesta ' + r.status);
    return true;
  }

  /* Reintenta lo que quedó pendiente de una sesión anterior sin internet. */
  async function reintentar() {
    if (!ENDPOINT) return;
    const pendientes = leerCola();
    if (!pendientes.length) return;
    const quedan = [];
    for (const datos of pendientes) {
      try { await mandar(datos); } catch (e) { quedan.push(datos); }
    }
    escribirCola(quedan);
  }

  /*
   * Envía un resultado. Devuelve 'enviado', 'pendiente' o 'sin-endpoint'.
   * Nunca lanza error: si no hay internet, lo guarda para el próximo intento.
   */
  async function enviar(datos) {
    if (!ENDPOINT) return 'sin-endpoint';
    if (!datos.fecha) datos.fecha = new Date().toISOString();
    try {
      await mandar(datos);
      return 'enviado';
    } catch (e) {
      const pendientes = leerCola();
      pendientes.push(datos);
      escribirCola(pendientes);
      return 'pendiente';
    }
  }

  /*
   * Arma el objeto de resultado a partir de las preguntas y las respuestas.
   *
   *   preguntas: [{id, comp, apr, clave, expl}]
   *   marcadas : ['A', 'C', '—', ...]  en el mismo orden
   *   datos    : {ape, nom, gru, sede, nombrePrueba, segundos}
   */
  function armar(preguntas, marcadas, datos) {
    let ok = 0;
    const det = preguntas.map(function (q, i) {
      const marcada = marcadas[i] || '—';
      const acierto = marcada === q.clave;
      if (acierto) ok++;
      return {
        n: q.id, apr: q.apr || '', comp: q.comp || '',
        ac: acierto, marcada: marcada, clave: q.clave,
        expl: q.expl || '', intentos: q.intentos || 1, seg: q.seg || 0,
      };
    });

    const completo = ((datos.ape || '') + ' ' + (datos.nom || '')).replace(/\s+/g, ' ').trim();
    return {
      ape: datos.ape || '', nom: datos.nom || '', completo: completo,
      sede: datos.sede || '', gru: datos.gru || '',
      prueba: datos.prueba || 'p1',
      pruebaNombre: datos.nombrePrueba || document.title,
      fecha: new Date().toISOString(),
      ok: ok, total: preguntas.length,
      pct: Math.round((ok / preguntas.length) * 1000) / 10,
      seg: datos.segundos || 0,
      cambios: datos.cambios || 0,
      vez: datos.vez || 1,
      det: det,
    };
  }

  if (document.readyState !== 'loading') reintentar();
  else document.addEventListener('DOMContentLoaded', reintentar);

  return { enviar: enviar, armar: armar, reintentar: reintentar };
})();
