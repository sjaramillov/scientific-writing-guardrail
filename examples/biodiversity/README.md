# Cómo leer un inventario ficticio de biodiversidad

Un editor de historia natural quiere saber qué cuenta el inventario y si esos datos permiten estimar cuántas especies hay. Las cifras y los textos de este ejercicio se inventaron con fines didácticos.

Desde la raíz del repositorio, ejecuta estos comandos para comprobar el pasaje y leer las copias de revisión en español e inglés.

```sh
python3 guardrail.py check examples/biodiversity/source.txt examples/biodiversity/packet.json
python3 guardrail.py render examples/biodiversity/source.txt examples/biodiversity/packet.json --language es --with-notes
python3 guardrail.py render examples/biodiversity/source.txt examples/biodiversity/packet.json --language en --with-notes
```

Las dos versiones deben explicar que cada fila corresponde a una observación. Varias observaciones podrían describir el mismo organismo. El inventario carece de determinaciones de especies, de modo que con estos registros no se puede deducir la riqueza de especies. Al comprobar el ejemplo, el programa debe devolver `ready_for_human_review`, una lista de incidencias vacía y la revisión humana pendiente. Las notas de la copia identifican las dos afirmaciones para que el editor pueda consultar sus registros locales.

## Prueba con dos cambios

1. **Cambia una cifra.** Copia el archivo `packet.json` a tu directorio de trabajo y conserva la fuente original. En el texto español de la afirmación C1, sustituye «12» por «13». Vuelve a ejecutar `check` usando la ruta a tu copia del paquete. Debe terminar con el código 1 e indicar que falta una expresión protegida en la versión española de C1.
2. **Intercambia lo que cuenta cada cifra.** Empieza con otra copia del paquete original. En el mismo texto español, intercambia «12» y «3». Ahora el texto atribuye 3 registros a 12 parcelas. Las dos cifras y los dos sustantivos siguen presentes, de modo que el cotejo literal puede pasar incluso con el resultado invertido.

Para comprobar si la edición transmite el diseño, pregunta al lector «¿Cuántas parcelas se muestrearon?» y «¿Qué representa cada fila?». Quien revise sus respuestas puede contrastarlas con las 3 parcelas y los 12 registros de la fuente. Las pruebas automatizadas del proyecto reproducen las dos modificaciones. La copia con notas también reproduce el texto de la edición, que conviene leer antes de compartirlo.
