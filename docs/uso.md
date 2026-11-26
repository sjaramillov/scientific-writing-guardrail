# Cómo revisar un pasaje con la herramienta

Para trabajar con tu paper necesitas una copia del pasaje original, su versión, el lugar donde está su evidencia y las dos redacciones que quieres comparar. El archivo de trabajo se llama *paquete*. Es un JSON que conserva esas decisiones para que otra persona pueda repetir la revisión.

## Preparar la primera revisión

1. Crea la carpeta `private/` y guarda el pasaje original en `private/source.txt`, en UTF-8. Incluye los extractos de evidencia que necesites citar textualmente. Git ignora esta carpeta.
2. Crea una plantilla con el comando siguiente. Usa un nombre distinto para cada revisión porque la redirección `>` sobrescribe el archivo si ya existe.
3. Completa la plantilla con el público, las afirmaciones, la evidencia y el texto seguido de cada edición.

```sh
python3 guardrail.py prepare private/source.txt > private/borrador-v1.json
```

| Campo | Qué escribir |
| --- | --- |
| `audience` y `assistance` | Quién leerá el pasaje, qué necesita entender y qué asistencia editorial se utilizó. Registra herramienta, tarea y fecha cuando corresponda. |
| `id` y `status` | Un identificador como `C1` y el tipo de afirmación: observación (`observed`), resultado comunicado (`reported`), resultado formal (`formal`), interpretación (`interpretation`), plan (`planned`) o limitación (`limitation`). |
| `evidence` y `quote` | El documento, versión y sección, o el identificador de una ejecución, junto con una cita exacta del archivo fuente. El revisor usa el localizador para comprobar el respaldo científico. |
| `anchors` | Las expresiones que deben conservarse y su redacción esperada en cada idioma. Usa `"invariant": true` cuando deban ser idénticas. Dos literales numéricos se comparan exactamente. Si conviertes cifras en palabras, revisa tú la equivalencia. |
| `versions` | Un segmento por afirmación e idioma. Cada segmento admite varias oraciones. Puedes ordenar los segmentos según el idioma. Para empezar otro párrafo, usa `"new_paragraph": true`. |

La cita de la fuente debe coincidir tal como está escrita. Para buscar las expresiones protegidas, el programa respeta las mayúsculas y normaliza espacios y la representación Unicode de los caracteres. Si cambias el original, revisa las citas y guarda una nueva versión del paquete.

## Entender el recibo

```sh
python3 guardrail.py check private/source.txt private/borrador-v1.json > private/recibo-v1.json
```

| Si aparece… | Qué hacer |
| --- | --- |
| `ready_for_human_review` (salida 0) | Entrega el pasaje a un revisor. Queda por juzgar si la evidencia respalda la conclusión y si las dos versiones dicen lo mismo. |
| `revise` (salida 1) | Lee `issues`, localiza la afirmación y compara la frase con su fuente. Una alerta también puede deberse a una regla mal declarada. |
| `invalid_input` (salida 2) | Lee `error` y corrige los archivos o los campos que indica. |

El recibo identifica el comprobador y guarda las huellas SHA-256 de la fuente y del paquete. Permiten repetir el cotejo sobre los mismos bytes. Una afirmación omitida por completo del mapa puede pasar inadvertida. El estado de la evidencia lo declara el editor.

## Compartir una copia para revisión

```sh
python3 guardrail.py render private/source.txt private/borrador-v1.json --language es --with-notes
```

Usa `en` para leer la edición inglesa. Omite `--with-notes` si quieres solo el texto. Las notas muestran los identificadores de las afirmaciones, el estado de evidencia declarado y la huella del paquete. El campo opcional `public_doi` permite incluir un DOI que hayas decidido compartir. Escríbelo sin prefijo de URL y comprueba que remita a la fuente correcta.

El cuerpo del borrador se exporta como se redactó. Comprueba qué contiene antes de enviarlo. Los localizadores internos y las notas libres de asistencia permanecen en el paquete local. Si hay una incidencia, `render` devuelve el diagnóstico en lugar de la copia.

## Proteger el alcance de una afirmación

Imagina que para cada temperatura se construyó **una muestra**. Puede ser una muestra distinta para cada temperatura. Decir que funciona **cualquier muestra** amplía el resultado. La plantilla `--with-scope` permite declarar qué expresión introduce la muestra elegida.

```json
{
  "source": "For each temperature there exists a sample",
  "en": {"referents": ["sample"], "witnesses": ["a particular sample", "there exists a sample"]},
  "es": {"referents": ["muestra"], "witnesses": ["una muestra concreta", "existe una muestra"]}
}
```

Añade la regla a la lista `existentials` de la afirmación. Elige nombres y formas en singular o plural que realmente figuren en el pasaje. «El teorema no afirma que cualquier muestra funcione» limita lo demostrado. «El teorema afirma que cualquier muestra funciona» lo extiende. Una pregunta abierta tampoco sirve como prueba de que existe esa muestra. Revisa el enunciado fuente antes de marcar como existencial un objeto arbitrario en la demostración de un teorema universal.

Tras una mención aceptada, el programa reconoce algunas generalizaciones en la misma afirmación y en la primera oración de la siguiente dentro del mismo párrafo. Un cambio de párrafo o una afirmación intermedia sin esa regla interrumpe la búsqueda automática. El recibo indica la lengua, la afirmación, la oración y los posibles antecedentes.

## Indicar qué significa «esto»

Puedes vincular una mención con una afirmación anterior mediante la plantilla `--with-antecedents`. En esta edición española, la segunda oración del segmento `C3` retoma lo que se construyó en `C1`.

```json
{
  "claim": "C3",
  "text": "Volvamos al resultado de la construcción. Esto vale en todos los casos.",
  "new_paragraph": true,
  "antecedents": [{"sentence": 2, "mention": "Esto", "claim": "C1"}]
}
```

Cuenta las oraciones desde 1 dentro del segmento. La mención debe aparecer una sola vez en esa oración. La búsqueda ignora las mayúsculas y normaliza los espacios. El destino debe preceder a la mención en ese idioma. Declara los enlaces de la edición inglesa por separado y evita que se solapen. Si hay dos antecedentes plausibles, nombra en el propio texto cuál importa al lector.

En el ejemplo, el aviso vincula «en todos los casos» con `C1`. El recibo guarda el vínculo en `resolved_antecedents`. Si quitas o duplicas la mención, el comprobador pide revisar el enlace. Las anotaciones de vínculos quedan fuera de la copia que lee el revisor.

## Elegir una plantilla

Añade la opción a `python3 guardrail.py prepare private/source.txt`. Elige las reglas que respalde tu fuente y elimina los campos de ejemplo que no necesites.

| Formato | Opción | Qué añade |
| --- | --- | --- |
| 1 | Sin opción | Citas, expresiones y cifras protegidas. |
| 2 | `--with-scope` | Diferencia entre afirmar que existe un objeto y afirmar algo de todos. |
| 3 | `--with-antecedents` | Enlaces entre una mención y la afirmación que retoma. |
| 4 | `--with-properties` | Propiedades, dominios y dependencia de parámetros. |
| 5 | `--with-context` | Extensiones de una propiedad y eliminación explícita de hipótesis. |
| 6 | `--with-contrasts` | Contrastes declarados entre afirmaciones. El formato también admite cotejar un grupo finito con una lista de enteros de la fuente. |

En `scope_findings` puedes ver la oración y la regla que generó el aviso. Cuando se comprueba una igualdad entre columnas, `scope_group_checks` identifica los miembros del grupo que se cotejaron. [Ejemplos de propiedades y grupos](claim-properties.md)

Para reproducir las pruebas del programa desde la raíz del repositorio, ejecuta `python3 -m unittest discover -s tests -v`. Para evaluar un pasaje con especialistas y lectores, consulta el [protocolo de evaluación](evidence-and-evaluation.md).
