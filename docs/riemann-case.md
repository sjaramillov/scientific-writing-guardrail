# Reading a machine-checked proof of the Riemann hypothesis

Evidence reviewed on 26 November 2026. This editorial case follows the published checks and one attempt at exposition. We did not rerun the proof.

In 1859 Bernhard Riemann posed a question about the zeros of the zeta function. On 20 November 2026 Levent Alpöge announced that he had found a proof with Claude. He released a Lean formalization and a short note. The note describes his part in finding the argument and the difficulty he still faced in explaining it. [Original problem and historical context](https://www.claymath.org/millennium/riemann-hypothesis/) · [Alpöge’s note, pp. 1–2](https://alpo.ge/remark.pdf)

## One statement at two reading levels

**English.** A zero of the Riemann zeta function is an input at which the function takes the value zero. Its zeros at the negative even integers are called trivial. Plot all the other zeros in the complex plane. Every one lies on the vertical line whose horizontal coordinate is exactly 1/2.

**Español.** Un cero de la función zeta de Riemann es un valor para el cual la función vale cero. Sus ceros en los enteros pares negativos se llaman triviales. Si situamos todos los demás ceros en el plano complejo, cada uno queda sobre la recta vertical cuya coordenada horizontal es exactamente 1/2.

**Technical statement.** For every nontrivial zero *s* of the Riemann zeta function, Re(*s*) = 1/2. Mathlib’s formal statement also explicitly excludes *s* = 1, where the classical zeta function has a pole and the library uses a conventional value. The English and Spanish renderings explain the classical statement. The formal definition is the place to recover that implementation detail. [Sutherland, “What was verified,” item 1](https://math.mit.edu/~drew/grh/)

## Reconstruct the evidence chain

1. **Identify the claim.** Read the opening of Alpöge’s note for the attribution, then locate the classical theorem and the separate results on Dirichlet L-functions in Sutherland’s list. Label each result with its actual domain. [Author’s note](https://alpo.ge/remark.pdf) · [Five formal statements](https://math.mit.edu/~drew/grh/)
2. **Identify what the reviewers certified.** On 21 November the Lean FRO and the Mathlib Initiative reported that both the formal statement of the classical Riemann hypothesis and its proof were correct. They describe independent comparisons with Mathlib’s formulation and checks of the exported proof. Attribute this conclusion to those reviewers. [Joint statement, checks 1–4](https://leanprover-community.github.io/blog/posts/riemann-hypothesis/)
3. **Identify what the reader must still supply.** Michael Rubinstein’s working guide, version 2 of 22 November, reduces its central inequality to thirteen hypotheses. The guide identifies what it takes from Lean and leaves those hypotheses without standalone proofs in the text. This is a limitation of that exposition. The formal result has its own verification record. [Rubinstein’s description of the guide](https://www.math.uwaterloo.ca/~mrubinst/alpoge_claude_grh/)
4. **Check the audience goal.** On 24 November Anurag Sahay, Will Sawin and Lior Silberman proposed a collaborative effort to explain the argument, connect it with the literature and identify ideas other mathematicians could reuse. These are concrete goals for an explanation beyond stating the theorem. [Authors’ Polymath proposal](https://terrytao.wordpress.com/2026/11/24/g-r-h-polymath/)

## Reader exercise

Give a bilingual reader the two explanations above and ask three questions without the source open. Does the statement cover the zero at −2? Could a nontrivial zero have real part 0.5001? Did Rubinstein’s guide prove all thirteen of its auxiliary hypotheses in prose?

The expected answers are **no** to all three, for different reasons. The first point is excluded by definition. The second violates an exact equality. For the third, the guide states its dependencies. A reader who can answer the first two has recovered the scope of the statement. Explaining how the proof establishes it is a separate task requiring the argument and its dependencies.
