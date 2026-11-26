# Cómo leer la demostración de la hipótesis de Riemann verificada en Lean

Este caso está dirigido a lectores que quieren entender qué afirma la hipótesis de Riemann y qué se verificó. El 26 de noviembre de 2026 revisamos las comprobaciones publicadas de la primera formalización y una guía que intentaba explicar el argumento. La verificación informática que se describe a continuación es la que realizaron los equipos citados.

En 1859, Bernhard Riemann planteó una pregunta sobre los ceros de la función zeta. El 20 de noviembre de 2026, Levent Alpöge anunció que había encontrado una demostración con Claude. Publicó la formalización en Lean y una nota en la que explicó qué parte del argumento había desarrollado personalmente y qué le quedaba por comprender para poder explicarlo. [Problema original y contexto histórico](https://www.claymath.org/millennium/riemann-hypothesis/) · [Nota de Alpöge, pp. 1–2](https://alpo.ge/remark.pdf)

## El enunciado en dos idiomas

**Español.** Un cero de la función zeta de Riemann es un valor para el cual la función vale cero. Sus ceros en los enteros pares negativos se llaman triviales. Si situamos todos los demás ceros en el plano complejo, cada uno queda sobre la recta vertical cuya coordenada horizontal es exactamente 1/2.

**Inglés.** A zero of the Riemann zeta function is an input at which the function takes the value zero. Its zeros at the negative even integers are called trivial. Plot all the other zeros in the complex plane. Every one lies on the vertical line whose horizontal coordinate is exactly 1/2.

**Enunciado técnico.** Para todo cero no trivial *s* de la función zeta de Riemann, Re(*s*) = 1/2. Las dos explicaciones anteriores se refieren a la función clásica. En *s* = 1, esa función tiene un polo. La biblioteca Mathlib asigna un valor por convención en ese punto, por lo que su enunciado formal excluye también *s* = 1 de forma explícita. [Enunciado formal recogido por Sutherland, punto 1 de «What was verified»](https://math.mit.edu/~drew/grh/)

## Qué comprobaron los matemáticos

1. **¿Qué resultado anunció Alpöge?** Su nota identifica su participación y la de Claude. La lista de Andrew Sutherland permite localizar por separado la hipótesis clásica y los resultados sobre funciones *L* de Dirichlet. Al citar cualquiera de ellos, conviene precisar a qué función se refiere. [Nota del autor](https://alpo.ge/remark.pdf) · [Cinco enunciados formales](https://math.mit.edu/~drew/grh/)
2. **¿Qué verificaron los revisores?** El 21 de noviembre, Lean FRO y la iniciativa Mathlib certificaron el enunciado formal de la hipótesis clásica y su demostración. Dos herramientas independientes compararon el enunciado demostrado con el de Mathlib. Varios verificadores comprobaron además la prueba exportada. [Comunicado conjunto, comprobaciones 1–4](https://leanprover-community.github.io/blog/posts/riemann-hypothesis/)
3. **¿Qué pasos puede reconstruir quien lee la guía?** En la versión 2, del 22 de noviembre, Michael Rubinstein redujo la desigualdad central de la prueba a trece hipótesis auxiliares. Indicó qué resultados tomó de la formalización en Lean. Las demostraciones completas de esas trece hipótesis quedaron pendientes en el texto de la guía. [Descripción de la guía por Rubinstein](https://www.math.uwaterloo.ca/~mrubinst/alpoge_claude_grh/)
4. **¿Qué explicación buscaba la comunidad?** El 24 de noviembre, Anurag Sahay, Will Sawin y Lior Silberman propusieron un proyecto colaborativo para explicar el argumento, relacionarlo con la bibliografía y extraer ideas que otros matemáticos pudieran reutilizar. [Propuesta de los autores para el proyecto Polymath](https://terrytao.wordpress.com/2026/11/24/g-r-h-polymath/)

## Ejercicio de lectura

Pide a una persona bilingüe que lea los dos enunciados y el párrafo sobre la guía de Rubinstein. Después, con las fuentes cerradas, formula las siguientes preguntas.

1. ¿Está incluido el cero en −2 en la afirmación sobre la recta?
2. ¿Podría un cero no trivial tener parte real igual a 0,5001?
3. ¿Presenta la guía de Rubinstein una demostración en prosa de cada una de sus trece hipótesis auxiliares?

**Clave para quien facilita la lectura.** La respuesta esperada a las tres preguntas es «no». El cero en −2 es trivial. El valor 0,5001 incumple la igualdad exacta con 1/2. La guía declara las trece hipótesis de las que depende su argumento y deja pendiente demostrarlas por completo en ese texto. Las dos primeras respuestas permiten comprobar si se entendió el enunciado. Para explicar cómo se demuestra hace falta reconstruir el argumento y los resultados de los que depende.
