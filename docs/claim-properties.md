# Qué afirma el texto y para qué casos vale

«Para cada tolerancia existe un umbral» permite elegir un umbral distinto en cada caso. «Un mismo umbral sirve para todas las tolerancias» exige más. Un editor puede declarar esta dependencia al revisar una traducción. Si el programa reconoce el cambio, le señala la frase que debe cotejar con el original.

| Si al leer te preguntas… | Ve a… | Versión mínima del paquete |
| --- | --- | --- |
| ¿Qué propiedad se afirma y de qué objeto? | [La propiedad y sus argumentos](#la-propiedad-y-sus-argumentos) | 4 |
| ¿Puedo elegir este valor antes de fijar el otro? | [El orden de las elecciones](#el-orden-de-las-elecciones) | 4 |
| ¿«Esto» vale para las mismas muestras? | [Seguir una propiedad entre frases](#seguir-una-propiedad-entre-frases) | 4 |
| ¿Se extiende un ejemplo o desaparece una hipótesis? | [Retomar una propiedad o suprimir una condición](#reglas-v5) | 5 |
| ¿La revisión presenta una condición como suficiente? | [Cuándo cambia el alcance](#reglas-v6) | 6 |
| ¿«Las demás» abarca la lista entera o una parte? | [Comprobar el grupo de referencia](#grupo-finito) | 6 |

Antes de declarar una regla, lee el teorema completo, el ejemplo o la figura. Identifica la propiedad demostrada, los objetos a los que se aplica y las cantidades que dependen de una elección anterior. Una cita literal breve te permitirá volver al pasaje que justifica esa lectura.

Para empezar una plantilla, usa el comando correspondiente a la revisión. Los tres se ejecutan desde la raíz del repositorio.

| Para revisar | Comando |
| --- | --- |
| Una propiedad, su dominio o sus parámetros | `python3 guardrail.py prepare private/source.txt --with-properties` |
| La referencia a otra frase o una hipótesis | `python3 guardrail.py prepare private/source.txt --with-context` |
| Un cambio de alcance | `python3 guardrail.py prepare private/source.txt --with-contrasts` |

Completa los campos del paquete y conserva las reglas pertinentes. Cada afirmación puede llevar una lista `scope_rules`. Cada regla incluye una cita literal en `source` y una declaración para cada idioma en `en` y `es`. Una lista vacía mantiene las comprobaciones anteriores. También se pueden seguir usando los paquetes de las versiones 1 a 3.

## La propiedad y sus argumentos

Imagina que los minimizadores de una función forman una curva que pasa por el origen. Hay otros minimizadores de la curva tan cerca del origen como se quiera. Llamar al origen «minimizador aislado» cambiaría el resultado.

Puedes registrar ese contraste con una regla `relation`. En este ejemplo didáctico, la cita en inglés debe aparecer en el archivo fuente.

```json
{
  "kind": "relation",
  "source": "The minimizers form a curve through the origin.",
  "en": {
    "frame": "classification",
    "subject": ["origin"], "predicate": ["minimizer"],
    "licensed": ["non-isolated"], "review": ["isolated"]
  },
  "es": {
    "frame": "classification",
    "subject": ["origen"], "predicate": ["minimizador"],
    "licensed": ["no aislado"], "review": ["aislado"]
  }
}
```

Tanto «El origen es un minimizador aislado» como *The origin is an isolated minimizer* activan la alerta. En «El otro punto es un minimizador aislado» cambia el sujeto. El programa busca las palabras declaradas en una construcción gramatical reconocible. Si necesitas comprobar que una expresión aparece en ambas versiones del pasaje, puedes registrarla además en `anchors`.

| Valor de `frame` | Qué conviene comparar | Ejemplo de la distinción |
| --- | --- | --- |
| `preservation` | La clase de los objetos de entrada y de salida. | «Cada S envía X a X» conserva la clase X. |
| `operator` | La operación que se aplica al sujeto. | La imagen y la preimagen de S pueden ser diferentes. |
| `domain` | El dominio en el que vale la afirmación. | «Todo S tiene la propiedad P en X» especifica dónde vale P. |
| `classification` | La característica atribuida al objeto. | Un minimizador puede ser aislado o no aislado. |
| `action` | El objeto al que se refiere una acción. | Afirmar que se demostró una conjetura exige identificar cuál. |

En `licensed` escribe la formulación que respalda la fuente. En `review`, las variantes que quieres señalar. Incluye las formas literales pertinentes en cada idioma. Si la prueba empieza con «sea un elemento arbitrario» y demuestra el resultado para todos los elementos de una clase, conserva ese alcance universal y declara la clase en el dominio.

## El orden de las elecciones

Si la fuente permite elegir un umbral **después** de fijar la tolerancia, declara los dos papeles por separado. El ejemplo usa `K` para el umbral y `ε` para la tolerancia.

```json
{
  "kind": "dependency",
  "source": "For each tolerance there exists a threshold.",
  "en": {"quantity": ["threshold"], "parameter": ["tolerance"], "quantity_symbols": ["K"], "parameter_symbols": ["ε"]},
  "es": {"quantity": ["umbral"], "parameter": ["tolerancia"], "quantity_symbols": ["K"], "parameter_symbols": ["ε"]}
}
```

*For each tolerance there exists a threshold* mantiene la posibilidad de elegir varios umbrales. *A single threshold works for every tolerance* activa la revisión porque exige uniformidad. Los símbolos distinguen mayúsculas y minúsculas.

Añade el campo opcional `limit_values` cuando fijar la cantidad mientras el parámetro se acerca a un valor concreto ampliaría la conclusión. Para el cero, por ejemplo, usa `["zero", "0"]` en inglés y `["cero", "0"]` en español. Comprueba también el intervalo indicado. Una cota uniforme sobre un intervalo restringido de tolerancias puede ser compatible con la fuente.

## Seguir una propiedad entre frases

La regla `application` vincula una propiedad con la clase de objetos para la que se ha establecido. En este ejemplo didáctico se observaron muestras metálicas. El campo `witnesses` contiene la frase afirmativa completa que presenta a la vez la clase y la propiedad.

```json
{
  "kind": "application",
  "source": "The metal samples conduct heat.",
  "en": {
    "property": "conduct heat", "objects": "metal samples",
    "witnesses": ["The metal samples conduct heat."], "extensions": ["samples"]
  },
  "es": {
    "property": "conducen el calor", "objects": "muestras metálicas",
    "witnesses": ["Las muestras metálicas conducen el calor."], "extensions": ["muestras"]
  }
}
```

Si la frase siguiente dice «Esto vale para todas las muestras» o *This holds for all samples*, la regla puede señalar la extensión. También reconoce algunas formulaciones que eliminan expresamente una restricción sobre la clase. Una frase intermedia o un nuevo párrafo interrumpe el enlace automático. Para señalar una referencia más distante, usa `antecedents` en el segmento y en el idioma correspondientes. Vincula el demostrativo que retoma la afirmación.

<a name="reglas-v5"></a>

## Retomar una propiedad o suprimir una condición

La versión 5 admite dos reglas adicionales en `scope_rules`. Si ya tienes un paquete, puedes trabajar sobre una copia, cambiar `version` a `5` y añadir las reglas que respalde la fuente.

### Una propiedad observada en un ejemplo

Supongamos que la fuente describe una baldosa marcada de seis lados. La traducción presenta la baldosa y añade «Tiene seis lados». La regla `resumption` permite identificar cuándo una frase posterior atribuye esa propiedad a otras baldosas.

```json
{
  "kind": "resumption", "source": "The marked tile has six sides.",
  "en": {"mode": "example", "property": "six sides", "witnesses": ["It has six sides."],
         "objects": ["tile", "tiles"], "parameters": ["colour", "edge length"]},
  "es": {"mode": "example", "property": "seis lados", "witnesses": ["Tiene seis lados."],
         "objects": ["baldosa", "baldosas"], "parameters": ["color", "longitud del borde"]}
}
```

*This last property holds for each of the others as well* puede extender la observación a otras baldosas. «Esto vale para todas las que tengan ese mismo color» hace depender la extensión del color. Para valorar cualquiera de las dos frases, identifica las baldosas a las que se refiere el texto. Un subgrupo definido previamente puede compartir la propiedad en todos sus miembros.

### Una pregunta abierta sobre uniformidad

Usa `"mode": "open_uniformity"` si el pasaje pregunta expresamente si una misma elección sirve para distintos valores de un parámetro. En `witnesses`, copia la pregunta completa con su puntuación. En `property`, reproduce la expresión que designa la cantidad que se propone fijar. En `parameters`, incluye los nombres de los parámetros que varían. La lista `objects` puede estar vacía.

Si la pregunta fue «¿Bastará un mismo índice para todos los ángulos?», la continuación *This is guaranteed for every angle* presenta la respuesta como establecida. Localizar la pregunta permite al editor juzgar el alcance de «esto».

En ambos usos, el programa busca en la oración inmediatamente anterior una frase que coincida con `witnesses` en ese idioma. Puede cruzar entre segmentos adyacentes del mismo párrafo. Un nuevo párrafo reinicia la búsqueda automática. Un enlace explícito sobre el demostrativo permite volver a una afirmación anterior en la que se haya encontrado la frase declarada. Cuando allí se retoman dos propiedades posibles, asignar un ID distinto a cada afirmación ayuda a identificar cuál se quiere recuperar.

### Una hipótesis que desaparece

Supongamos que un artículo establece una estimación del error para sistemas regulares. Con `hypothesis` puedes declarar el sujeto, la hipótesis, el dominio donde podrían imponerse otras condiciones y la conclusión.

```json
{
  "kind": "hypothesis", "source": "For regular systems the error estimate holds.",
  "en": {"subjects": ["system"], "hypotheses": ["regularity", "regular"],
         "domains": ["class"], "conclusions": ["error estimate"]},
  "es": {"subjects": ["sistema"], "hypotheses": ["regularidad", "regular"],
         "domains": ["clase"], "conclusions": ["estimación del error"]}
}
```

La comprobación puede señalar una frase que presenta la estimación como válida sin regularidad, o que descarta expresamente la regularidad y cualquier otra condición sobre la clase. La alerta invita a buscar qué respalda el resultado ampliado. Demostrar que otra hipótesis basta, o que la hipótesis original es necesaria, requiere un argumento matemático. Una omisión implícita o una paráfrasis indirecta puede pasar inadvertida.

<a name="reglas-v6"></a>

## Cuándo cambia el alcance

La regla `contrast` de la versión 6 permite declarar un cambio concreto que merece revisión. Imagina que un procedimiento de calibración garantiza la exactitud de instrumentos **secos y nivelados**. Si la edición afirma «La sequedad por sí sola garantiza la exactitud», ha convertido una de las condiciones en suficiente.

```json
{
  "kind": "contrast",
  "source": "The calibration guarantees accuracy for instruments that are both dry and level.",
  "en": {"frame": "partial_sufficiency", "licensed": "accuracy for dry and level instruments",
         "roles": {"condition": ["dryness"], "conclusion": ["accuracy"]}},
  "es": {"frame": "partial_sufficiency", "licensed": "exactitud para instrumentos secos y nivelados",
         "roles": {"condition": ["sequedad"], "conclusion": ["exactitud"]}}
}
```

Aquí `licensed` es un texto que resume el resultado respaldado. En `roles` se indican las expresiones que designan cada elemento en cada idioma. Al encontrar *Dryness alone guarantees accuracy* o la frase española equivalente, el recibo identifica la oración y los elementos que coincidieron. El editor comprueba si otra evidencia respalda la afirmación más fuerte. Si la frase dice «esta garantía», identifica a qué garantía se refiere dentro de la afirmación anotada. Elegir el contraste o un contraejemplo exige interpretar la fuente.

| Valor de `frame` | Cambio que se quiere revisar | Campos obligatorios de `roles` |
| --- | --- | --- |
| `relaxed_condition` | Se mantiene una restricción y se admiten casos antes excluidos. | `subject`, `retained`, `excluded` |
| `partial_sufficiency` | Se presenta una sola condición como suficiente. | `condition`, `conclusion` |
| `excluded_instance` | Se promete el resultado para un caso fuera del alcance declarado. | `instance`, `actor`, `outcome` |
| `strengthened_value` | Se exige un valor más específico que el respaldado. | `subject`, `value` |
| `discarded_condition` | Se afirma el resultado al eliminar una condición. | `subject`, `condition` |
| `unconditional_bound` | Una cota condicional pasa a ser incondicional. | `condition`, `quantity`, `limit` |
| `eventual_bound` | Una cota se extiende a todos los índices suficientemente grandes. | `quantity`, `index` |
| `wider_domain` | Se aplica una propiedad a una clase más amplia. | `subject`, `domain` |
| `distributed_uniqueness` | Una unicidad conjunta pasa a afirmarse para cada miembro por separado. | `member`, `object` |

<a name="grupo-finito"></a>

## A quiénes designa «las demás»

Considera esta lista de parejas. Elegimos la primera y queremos decir que las coordenadas de «las demás» también son iguales.

| Lista de la fuente | Grupo al que se refiere la frase | Resultado |
| --- | --- | --- |
| (1,1), (2,2), (1,2) | Las dos primeras parejas | La otra pareja es (2,2). Sus coordenadas coinciden. |
| (1,1), (2,2), (1,2) | La lista completa | La tercera pareja, (1,2), tiene coordenadas distintas. |

Combina una regla `finite_group` con una regla `resumption` en modo `example` dentro de la misma afirmación. Cita en `source` una lista ordenada de registros enteros del original congelado.

```json
{
  "kind": "finite_group",
  "source": "Ordered pairs: (1,1), (2,2), (1,2).",
  "en": {"property": "two coordinates are equal", "objects": ["pair", "pairs"], "equal_columns": [1, 2]},
  "es": {"property": "dos coordenadas son iguales", "objects": ["pareja", "parejas"], "equal_columns": [1, 2]}
}
```

Cada idioma debe usar el nombre de propiedad de su regla `resumption`. Los números de `equal_columns` deben ser los mismos en ambas ediciones y se cuentan desde uno. El editor verifica que la igualdad de esas columnas represente la propiedad que afirma el texto.

El pasaje debe reproducir la lista, delimitar el grupo, definir a quiénes designa «las demás», elegir un miembro y enunciar su propiedad. Así se puede cotejar la frase que la extiende al resto. En `scope_group_checks`, el recibo identifica el miembro elegido, las posiciones comprobadas y las que incumplen la igualdad. Todas las posiciones se cuentan desde uno en la lista original. Una selección ambigua, una lista sin verificar, un cálculo distinto de la igualdad o una manera poco habitual de definir el grupo pueden requerir revisión humana.

## Interpretar el recibo

El recibo privado identifica la lengua, la afirmación y la oración señalada. También registra qué regla coincidió, su posición en `scope_rules` y las palabras que activaron la alerta. Tanto las oraciones dentro de cada segmento como las posiciones de las reglas se numeran desde uno. En una referencia a una propiedad anterior, `rule_claim` y `witness_sentence` permiten volver a la afirmación y la oración donde se presentó. Si varias reglas de tipo `resumption` coinciden para el mismo antecedente, el programa deja abierta la elección.

La lista `issues` incluye el mismo aviso para quienes usan la línea de comandos. La copia de lectura contiene la prosa del autor. Un sinónimo imprevisto, un dominio sin declarar o una dependencia reformulada pueden pasar sin alerta. El cotejo científico con la fuente y la evaluación de qué entendió el lector requieren revisión humana.
