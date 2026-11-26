# ¿Se entiende el resultado y hasta dónde llega?

Dale el pasaje a una persona del público previsto. Con el texto delante, pídele que explique **qué se demostró, cómo se llegó a ese resultado y qué conclusión queda abierta**. La respuesta permite descubrir, por ejemplo, si entendió una condición que la redacción hacía fácil pasar por alto. El proyecto tiene pruebas del programa. La evaluación con lectores sigue pendiente.

## Qué detectó el programa

En la versión de desarrollo `0.2.0.dev5`, el programa detectó las **24 de 24 alteraciones** usadas para ajustar las reglas. Al probarlo en tres artículos nuevos con las reglas ya fijadas, detectó **0 de 12** en español y **0 de 12** en inglés. En esa misma prueba, las falsas alarmas fueron **0 de 12** pasajes fieles en cada idioma. Las traducciones forman parejas y las etiquetas editoriales siguen pendientes de revisión científica humana.

Para repetir una comparación, conserva la misma fuente y el mismo texto bilingüe al cambiar la versión del programa. Anota el idioma, la frase exacta, el objeto al que se refiere y la respuesta esperada **antes** de ver el resultado. Compara una cautela fiel con una generalización sobre el mismo objeto. Prueba por separado qué ocurre al empezar otra afirmación, cambiar de párrafo o interponer otro sujeto. Conserva los casos ambiguos para que se discutan.

Muestra cuántos errores pasaron entre los errores introducidos y cuántos textos fieles recibieron avisos entre los textos fieles. Guarda el primer resultado. Separa los ejemplos usados para corregir una regla de los pasajes nuevos, reservados antes de probarla. Para estudiar si las mejoras se trasladan a otras disciplinas, pide a especialistas bilingües que evalúen esos pasajes sin conocer los avisos del programa.

## Cómo probar el texto con lectores

**Elige los pasajes.** Usa dos pasajes independientes, A y B, parecidos en longitud, dificultad y género. Guarda el original y la revisión de cada uno con sus versiones. Compara en un solo idioma y con un público definido. Para evaluar una traducción al inglés, compárala con una versión de referencia en inglés que haya pasado una revisión técnica. Una persona bilingüe coteja ambas con el original español. Así evitas atribuir a la edición una diferencia de dominio del idioma.

**Revisa primero la fidelidad.** Un especialista localiza la evidencia de cada afirmación central y coteja cifras, unidades, procedencia, condiciones, pasos de la inferencia, términos, citas e incertidumbre. Registra su decisión (respaldada, cambiada, omitida o sin resolver), el pasaje de la fuente y la razón. Corrige cualquier denominador alterado, negación invertida, hipótesis omitida o conclusión sin respaldo. Un segundo especialista resuelve los desacuerdos. El recibo identifica la revisión exacta que se examinó. La validez de la investigación requiere evaluar su evidencia.

**Alterna el orden de lectura.** Un piloto de ocho lectores podría asignar dos a cada secuencia. Cada persona ve una sola versión de cada pasaje. Oculta cuál es la revisión, mantén las mismas preguntas y condiciones para ambas versiones y espera hasta el final para comentar las respuestas.

| Secuencia | Primera lectura | Segunda lectura |
| --- | --- | --- |
| 1 | A original | B revisado |
| 2 | B revisado | A original |
| 3 | A revisado | B original |
| 4 | B original | A revisado |

**Puntúa las respuestas.** Antes de convocar a los lectores, un especialista redacta cuatro preguntas con su clave. Cada pregunta aborda un aspecto del pasaje.

| Qué quieres recuperar | Pregunta orientativa |
| --- | --- |
| Resultado | ¿Qué encontraron los autores? |
| Método o inferencia decisiva | ¿Qué observación o paso permite llegar a ese resultado? |
| Supuesto | ¿Qué condición se necesita para sostener la conclusión? |
| Límite | ¿Qué pregunta queda abierta? |

Cada lector responde con sus propias palabras y puede consultar el texto. Dos evaluadores, sin conocer la versión, puntúan cada respuesta con **0** (incorrecta), **1** (parcialmente respaldada) o **2** (completa). Conserva los desacuerdos y cómo se resolvieron. Aparte, pide al lector que marque un término desconocido, un referente ambiguo o un salto de razonamiento y que valore lo fácil que fue seguir el argumento. Un editor de lengua registra los cambios concretos de gramática y cohesión. El tiempo de lectura aporta un dato descriptivo.

**Decide qué revisar.** Informa cuántas afirmaciones recibieron aprobación, cuántas faltaban y cuántas siguen en disputa, con sus denominadores. Presenta los resultados de comprensión por pasaje, secuencia y versión, junto con el número de lectores, las preguntas sin responder y los malentendidos que se repiten. Una puntuación de **0 a 8** resume las respuestas de una persona a un pasaje. Las dos lecturas de la misma persona están emparejadas. Este piloto sirve para descubrir fallos y evaluar la viabilidad del estudio. La comprensión en otros públicos, la retención a largo plazo y la corrección formal de una prueba requieren evaluaciones propias.

| Qué ocurrió | Decisión editorial |
| --- | --- |
| Cambió una premisa, falta respaldo o una cita apunta a otra cosa. | Devuelve el pasaje al autor con la ubicación en la fuente. Corrige y vuelve a comprobar la fidelidad antes de la prueba con lectores. |
| El contenido es fiel, pero varios lectores pierden el mismo supuesto o paso. | Reescribe esa explicación y pruébala con lectores nuevos. Conserva el enunciado técnico. |
| La revisión técnica respalda el texto y los lectores reconstruyen el resultado y sus límites. | Un editor identificado puede aprobar esa versión para ese público. Informa los resultados observados, los desacuerdos y las limitaciones. |
| Falta el dictamen científico o la prueba con lectores. | Deja pendiente la evaluación correspondiente. Registra por separado lo que cotejó el programa. |

## Estudios que motivan estas decisiones

- **Preguntar por el contenido.** En un estudio en línea en inglés, 150 participantes dieron valoraciones parecidas de claridad y coherencia a resúmenes biomédicos escritos por personas y por modelos. Respondieron mejor las preguntas de comprensión tras leer los escritos por personas. De ahí que el piloto recoja por separado las respuestas sobre el método y los límites, y la impresión de claridad. [Guo y colaboradores, 2026](https://doi.org/10.1016/j.jbi.2026.105038)
- **Vigilar las generalizaciones.** Peters y Chin-Yee examinaron 4900 resúmenes de diez modelos. Al comparar resúmenes generados con resúmenes de divulgación escritos por personas, obtuvieron una razón de momios (*odds ratio*) de 4,85 para las generalizaciones amplias, con un intervalo de confianza del 95 % de 3,06 a 7,70. La estimación corresponde a esos modelos, instrucciones, textos y definición de generalización. En una revisión, comprueba población o dominio, supuestos, cuantificadores, fuerza de la evidencia y excepciones después de editar y de traducir. [Peters y Chin-Yee, 2025](https://doi.org/10.1098/rsos.241776)
- **Abrir cada cita.** Walters y Wilder comprobaron 636 referencias en 84 revisiones de literatura generadas sobre 42 temas. En aquel experimento de 2023, el 55 % de las referencias de GPT-3.5 y el 18 % de las de GPT-4 eran inventadas. También hallaron datos bibliográficos erróneos en referencias a trabajos reales. Comprueba la identidad del trabajo en la editorial o el repositorio y lee el pasaje citado. La replicación independiente exige evidencia adicional. [Walters y Wilder, 2023](https://doi.org/10.1038/s41598-023-41032-5)
- **Revisar en el idioma de destino.** Ramírez-Castañeda encuestó a 49 colombianos hispanohablantes que cursaban o habían completado un doctorado en ciencias biológicas. Describieron dificultades para leer y escribir en inglés y el tiempo que les exigía. Son experiencias declaradas por una muestra pequeña. El estudio se centró en las barreras lingüísticas. Conserva el original, coteja los términos y matices de ambos idiomas y convoca a lectores que usen la lengua de destino. [Ramírez-Castañeda, 2020](https://doi.org/10.1371/journal.pone.0238372)

Registra durante la edición cada herramienta, su versión si la conoces, la fecha, los pasajes afectados, para qué se usó y quién los revisó. Consulta las normas de la revista antes del envío. Pensoft, por ejemplo, pide a los autores declarar el uso de IA al presentar el manuscrito. [Política editorial de Pensoft](https://pensoft.net/editorial-policies)
