# Ponderación de periodos y presentación del boletín

Cuatro cambios en el módulo de colegios. Todos **apagados por defecto**, salvo el
cuarto: ningún colegio ve nada distinto hasta que lo active en su configuración.

---

## Instalación

```bash
python manage.py makemigrations notas
python manage.py migrate
python manage.py check
```

Son campos nuevos con valor por defecto, así que la migración no toca ningún dato
existente. Pero **antes de subir a producción**, compara boletines (ver abajo).

Todo se configura en **Configuración de Calificaciones**, la pantalla que ya existía.

---

## 1. Cada periodo vale un porcentaje

Antes la nota del año era el promedio simple de los periodos, calculado en dos
sitios distintos que podían desincronizarse. Ahora los dos llaman a
`notas/boletin/ponderacion.py`, que es el único lugar donde vive la fórmula.

- **Apagado** (por defecto): todos los periodos pesan igual. El resultado es
  idéntico al de antes.
- **Encendido**: cada periodo usa su `peso_porcentual`, que se edita en la misma
  pantalla de configuración.

Si los porcentajes no suman 100 —por una digitación—, el sistema reparte
proporcionalmente igual y te avisa al guardar. Nunca multiplica las notas por un
número raro.

## 2. Qué pasa cuando faltan notas

Con la ponderación encendida, promediar periodos incompletos no significa nada.
Por eso, cuando falta la nota de algún periodo:

- La definitiva del año **no se calcula**: queda en blanco.
- El boletín trae la lista de periodos faltantes en `materia.periodos_faltantes`.
- La sábana marca la celda con un `!` naranja y el detalle al pasar el mouse.

Es el caso del estudiante que llega a mitad de año y cuyas notas anteriores se
suben tarde: el administrador las carga y la definitiva aparece sola.

Hay un interruptor aparte para los colegios que no ponderan pero igual quieren
esta regla. La ponderación lo activa por su cuenta.

**La columna acumulada de la sábana es la excepción**: ahí sí se calcula con lo
que haya, porque es un avance del año en curso y no la nota final.

## 3. Nota mínima necesaria en el último periodo

En la fila acumulada de la sábana, cada asignatura muestra qué nota necesita el
estudiante en el último periodo para no reprobar el año. Se calcula contra el
piso de la escala BÁSICO del colegio, y respeta los pesos de cada periodo.

| Lo que ves | Qué significa |
|---|---|
| `↑4,8` | Necesita 4,8 en el último periodo |
| `↑∞` en rojo | Ya no alcanza ni con la nota máxima |
| nada | Ya aprobó, o faltan notas anteriores y no se puede proyectar |

Solo aparece mientras el último periodo no tenga nota.

## 4. Nombres de las tres columnas

`SER`, `SABER` y `HACER` estaban escritos a mano en la plantilla del boletín.
Ahora salen de la configuración del colegio, una sola vez para todo el colegio.
Los campos que tenía `Materia` siguen ahí pero no se usan en el boletín: un
encabezado de tabla no puede mostrar nombres distintos por asignatura.

## 5. Área con una sola asignatura

Antes, un área con una sola materia dibujaba dos filas con la misma nota: la del
área y la de la asignatura. Ahora se unen en una sola, que lleva el nombre del
área y las notas de la asignatura.

Afecta al boletín de periodo, al boletín final, a la sábana en pantalla y a la
sábana en Excel. **Está encendido por defecto**, porque es lo que pediste; se
apaga en la configuración si algún colegio quiere el formato anterior.

---

## Antes de subirlo a producción

Esto cambia la aritmética de los boletines. Un error aquí llega a las familias
como una nota equivocada. Haz esta comprobación:

1. En local, **sin activar nada**, genera el boletín y la sábana de un curso con
   notas reales y guárdalos.
2. Compáralos con los que produce la versión actual en producción. Deben ser
   idénticos, cifra por cifra. Si no lo son, algo quedó mal y hay que mirarlo
   antes de seguir.
3. Solo entonces activa la ponderación en un colegio y revisa que las notas
   cambien como esperas.

El paso 2 es el que importa: comprueba que lo que ya funcionaba sigue funcionando.
