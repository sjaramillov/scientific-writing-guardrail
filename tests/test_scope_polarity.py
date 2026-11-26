"""Minimal pairs for the English/Spanish denial-of-attribution exception."""

import unittest

from guardrail import check_existential
from scope_context import is_disclaimed


def decisions(text, phrase, lang):
    text, phrase = text.casefold(), phrase.casefold()
    matches = []
    offset = text.find(phrase)
    while offset != -1:
        end = offset + len(phrase)
        matches.append(is_disclaimed(text, offset, end, lang))
        offset = text.find(phrase, end)
    return matches


class ScopePolarityTests(unittest.TestCase):
    def test_open_indirect_question_at_the_start_of_the_clause(self):
        for lang, span, predicate, frames in (
            ("en", "every forest", "is pervasive", [
                "It is not known whether", "It remains an open question whether",
                "We don't yet know whether", "It is still unclear whether"]),
            ("es", "todo bosque", "es pervasivo", [
                "Se desconoce si", "Aún no se sabe si", "Sigue abierta la cuestión de si",
                "Sigue sin saberse si"]),
        ):
            for frame in frames:
                text = f"{frame} {span} {predicate}."
                with self.subTest(text=text):
                    self.assertEqual(decisions(text, span, lang), [True])

    def test_known_answers_external_negation_and_retractions_require_review(self):
        for lang, span, texts in (
            ("en", "every forest", [
                "It is known that every forest is pervasive.",
                "It is not unknown whether every forest is pervasive.",
                "It is false that it is not known whether every forest is pervasive.",
                "It is not known whether every forest is not pervasive.",
                "It is not known whether every forest is pervasive, but the answer is yes.",
                "It is unknown whether every forest is pervasive; the answer is affirmative.",
                "It is unknown whether every forest is pervasive. We now know that it is.",
                "It is unknown whether every forest is pervasive, but it is.",
                "It is unknown whether every forest is pervasive, but this has since been proved.",
                "It is unknown whether every forest is pervasive; yes.",
                "It is not known whether every forest is pervasive?",
            ]),
            ("es", "todo bosque", [
                "Se sabe que todo bosque es pervasivo.",
                "No se desconoce si todo bosque es pervasivo.",
                "Es falso que se desconoce si todo bosque es pervasivo.",
                "Se desconoce si todo bosque no es pervasivo.",
                "Se desconoce si todo bosque es pervasivo, pero ahora sabemos que sí.",
                "Se desconoce si todo bosque es pervasivo; la respuesta es afirmativa.",
                "Se desconoce si todo bosque es pervasivo. La respuesta es sí.",
                "Se desconoce si todo bosque es pervasivo, pero sí que lo es.",
                "Se desconoce si todo bosque es pervasivo. Sí.",
                "¿Se desconoce si todo bosque es pervasivo?",
            ]),
        ):
            for text in texts:
                with self.subTest(text=text):
                    self.assertEqual(decisions(text, span, lang), [False])

    def test_open_question_does_not_protect_later_quantifiers(self):
        for lang, span, text in (
            ("en", "every forest", "It is not known whether every forest is pervasive, but we show that every forest is pervasive."),
            ("en", "every forest", "It remains open whether every forest is pervasive. Every forest is pervasive."),
            ("es", "todo bosque", "Se desconoce si todo bosque es pervasivo, pero demostramos que todo bosque es pervasivo."),
            ("es", "todo bosque", "No sabemos si todo bosque es pervasivo. Todo bosque es pervasivo."),
        ):
            with self.subTest(text=text):
                self.assertEqual(decisions(text, span, lang), [True, False])

    def test_a_witness_under_uncertainty_is_insufficient(self):
        for lang, noun, witness, cases in (
            ("en", "force", "a specific force", [
                ("It is not known whether a specific force acts.", False),
                ("It is not known whether there exists a specific force.", False),
                ("It is not known whether a specific force does not act.", False),
                ("It remains open whether the construction uses a specific force.", False),
                ("It remains open whether the device works, but we construct a specific force.", True),
                ("It is unknown whether every force acts. We exhibit a specific force.", True),
            ]),
            ("es", "fuerza", "una fuerza específica", [
                ("Se desconoce si una fuerza específica actúa.", False),
                ("Se desconoce si existe una fuerza específica.", False),
                ("Se desconoce si una fuerza específica no actúa.", False),
                ("No se sabe si la construcción utiliza una fuerza específica.", False),
                ("Se desconoce si el dispositivo funciona, pero construimos una fuerza específica.", True),
                ("Se desconoce si toda fuerza actúa. Exhibimos una fuerza específica.", True),
            ]),
        ):
            terms = {"referents": [noun], "witnesses": [witness]}
            for text, expected_witness in cases:
                with self.subTest(text=text):
                    issues, found = check_existential(text.casefold(), terms, lang, "C1")
                    self.assertEqual(found is not None, expected_witness, issues)
                    if not expected_witness:
                        self.assertTrue(any("accepted existential wording missing" in s for s in issues), issues)
                    else:
                        self.assertEqual(issues, [])

    def test_isolation_qualifier_with_known_reporting_clauses(self):
        for lang, span, subject, report, qualifiers in [
            ("en", "every lens", "the argument", "does not establish that every lens works",
             ("on its own", "by itself", "taken in isolation")),
            ("es", "toda lente", "el argumento", "no acredita que toda lente funcione",
             ("por sí solo", "por sí mismo", "considerado aisladamente")),
        ]:
            for qualifier in qualifiers:
                for sentence in (
                    f"{qualifier}, {subject} {report}.",
                    f"{qualifier} {subject} {report}.",
                    f"{subject}, {qualifier}, {report}.",
                ):
                    with self.subTest(sentence=sentence):
                        self.assertEqual(decisions(sentence, span, lang), [True])

    def test_isolation_qualifier_does_not_reverse_an_assertion_or_escape_its_clause(self):
        cases = [
            ("es", "Por sí solo, el argumento acredita que toda lente funciona.", "toda lente", [False]),
            ("es", "Por sí solo, el argumento no solo acredita que toda lente funciona.", "toda lente", [False]),
            ("es", "Es falso que, por sí solo, el argumento no acredita que toda lente funcione.", "toda lente", [False]),
            ("es", "Por sí solo, el argumento no acredita que toda lente no funcione.", "toda lente", [False]),
            ("es", "Por sí solo, el argumento no acredita que toda lente funcione, pero mostramos que toda lente funciona.", "toda lente", [True, False]),
            ("en", "On its own, the argument establishes that every lens works.", "every lens", [False]),
            ("en", "On its own, the argument does not merely establish that every lens works.", "every lens", [False]),
            ("en", "It is false that, on its own, the argument does not establish that every lens works.", "every lens", [False]),
            ("en", "On its own, the argument does not establish that every lens never works.", "every lens", [False]),
            ("en", "On its own, the argument does not establish that every lens works, but we show that every lens works.", "every lens", [True, False]),
        ]
        for lang, sentence, span, expected in cases:
            with self.subTest(sentence=sentence):
                self.assertEqual(decisions(sentence, span, lang), expected)

    def test_reporting_verbs_in_either_language(self):
        families = [
            ("en", "any lens", [
                "The theorem does not claim that", "Our proof does not show that",
                "The article doesn't imply that", "The paper doesn’t establish that",
                "The authors do not assert that", "We do not conclude that",
                "The result makes no claim that",
            ]),
            ("es", "cualquier lente", [
                "El teorema no afirma que", "El estudio no demuestra que",
                "Esta prueba no establece que", "Los autores no sostienen que",
                "No se afirma que", "No podemos concluir que", "No afirmamos que",
            ]),
        ]
        for lang, phrase, frames in families:
            for frame in frames:
                with self.subTest(frame=frame):
                    self.assertEqual(decisions(f"{frame} {phrase} …", phrase, lang), [True])

    def test_referents_witnesses_and_anaphoric_candidates(self):
        for lang, text, span in [
            ("es", "El teorema no afirma que una lente cualquiera funcione.", "lente cualquiera"),
            ("en", "The theorem does not claim that a lens of any kind works.", "lens of any kind"),
            ("es", "No afirmamos que una lente concreta funcione.", "una lente concreta"),
            ("en", "We do not claim that a specific lens works.", "a specific lens"),
            ("es", "El teorema no afirma que esto valga para cualquier lente.", "cualquier lente"),
            ("en", "The theorem does not claim that this holds for every lens.", "every lens"),
            ("en", "The theorem does not claim that this holds in all cases.", "this holds in all cases"),
            ("es", "No afirmamos que esto valga en todos los casos.", "esto valga en todos los casos"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(decisions(text, span, lang), [True])

    def test_inference_limits_and_error_judgments_have_affirmative_controls(self):
        pairs = {
            "en": ("any lens", [
                ("It does not follow that", "It follows that"),
                ("It doesn't follow from this result that", "It follows from this result that"),
                ("We cannot conclude that", "We can conclude that"),
                ("One can't infer that", "One cannot deny that"),
                ("It would be a mistake to say that", "It would not be a mistake to say that"),
                ("It is unjustified to infer that", "It is unjustified to deny that"),
            ]),
            "es": ("cualquier lente", [
                ("De ello no se sigue que", "De ello se sigue que"),
                ("De este resultado tampoco se deduce que", "De este resultado se deduce que"),
                ("No cabe inferir que", "Cabe inferir que"),
                ("El artículo tampoco sostiene que", "El artículo tampoco niega que"),
                ("Sería un error decir que", "No sería un error decir que"),
                ("Es injustificado suponer que", "Es injustificado negar que"),
            ]),
        }
        for lang, (span, comparisons) in pairs.items():
            for deny, assert_ in comparisons:
                with self.subTest(denial=deny, assertion=assert_):
                    self.assertEqual(decisions(f"{deny} {span} …", span, lang), [True])
                    self.assertEqual(decisions(f"{assert_} {span} …", span, lang), [False])

    def test_changing_or_adding_a_negation_does_not_clear_a_claim(self):
        cases = {
            "en": ("every lens", [
                "The theorem claims that every lens works.",
                "Not every lens works.", "Every lens does not work.",
                "The paper does not deny that every lens works.",
                "The theorem does not merely claim that every lens works.",
                "The paper does not claim that every lens never works.",
                "It is false that the theorem does not claim that every lens works.",
                "It is not true that the theorem does not claim that every lens works.",
                "If the paper does not claim that every lens works, we will.",
                "The theorem does not claim that every lens works?",
                "The paper does not rule out the possibility that every lens works.",
                "The theorem does not claim that every lens works, but we do.",
            ]),
            "es": ("toda lente", [
                "El teorema afirma que toda lente funciona.",
                "No toda lente funciona.", "Toda lente no funciona.",
                "El artículo no niega que toda lente funcione.",
                "El artículo no solo afirma que toda lente funciona.",
                "El artículo no afirma que toda lente no funcione.",
                "Es falso que el teorema no afirma que toda lente funcione.",
                "Si el artículo no afirma que toda lente funciona, lo haremos nosotros.",
                "¿El teorema no afirma que toda lente funcione?",
                "No se descarta que toda lente funcione.",
                "El artículo no afirma que toda lente funcione, pero sí lo demuestra.",
            ]),
        }
        for lang, (span, texts) in cases.items():
            for text in texts:
                with self.subTest(text=text):
                    self.assertEqual(decisions(text, span, lang), [False])

    def test_disclaimer_is_local_to_the_matched_occurrence(self):
        for lang, text, phrase in [
            ("en", "Although the paper does not claim that every lens works, we show that every lens works.", "every lens"),
            ("es", "Aunque el artículo no afirma que toda lente funcione, demostramos que toda lente funciona.", "toda lente"),
            ("en", "The theorem does not claim that any lens works. Any lens works.", "any lens"),
            ("en", "The theorem does not claim that any lens fails, but any lens works.", "any lens"),
            ("es", "El teorema no afirma que cualquier lente funcione; en efecto, cualquier lente funciona.", "cualquier lente"),
            ("en", "The paper does not claim that every lens works and states that every lens suffices.", "every lens"),
            ("es", "El estudio no afirma que toda lente funcione y demuestra que toda lente basta.", "toda lente"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(decisions(text, phrase, lang), [True, False])

    def test_sentence_ending_before_the_clause_does_not_hide_the_denial(self):
        for lang, text, phrase in [
            ("en", "A particular lens works. The theorem does not claim that any lens works.", "any lens"),
            ("es", "Una lente particular funciona. El teorema no afirma que cualquier lente funcione.", "cualquier lente"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(decisions(text, phrase, lang), [True])
