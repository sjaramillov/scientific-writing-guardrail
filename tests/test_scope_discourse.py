"""Characterize the bounded restatement vocabulary and its normalized offsets."""
import unittest

import guardrail
from scope_discourse import scope_segments, universal_restatements
from tests.test_scope import SOURCE, force_packet


class SentenceSpans(unittest.TestCase):
    def test_spans_recover_exact_text_with_closing_punctuation(self):
        text = '  Existe un caso. «Esto vale en todos los casos.»  ¿Siempre?   Fin  '
        parts = [text[start:end] for start, end in scope_segments(text)]
        self.assertEqual(parts, ['Existe un caso.', '«Esto vale en todos los casos.»', '¿Siempre?', 'Fin'])

    def test_math_numbers_and_editorial_abbreviations_do_not_break_the_context(self):
        fragments = [
            'Usamos 0.52, p. ej. en el lema 1.1, y la Fig. 2.',
            'See Fig. 2 of Thm. 1.1 (e.g. at 0.5).',
        ]
        for first in fragments:
            with self.subTest(first=first):
                text = first + ' A second sentence.'
                self.assertEqual([text[a:b] for a, b in scope_segments(text)], [first, 'A second sentence.'])

    def test_space_only_or_unpunctuated_text(self):
        self.assertEqual(scope_segments('   '), [])
        self.assertEqual(scope_segments('  un ejemplo  '), [(2, 12)])
        self.assertEqual(scope_segments('one; another.'), [(0, 13)])


class RestatementSpans(unittest.TestCase):
    def test_removing_restrictions_on_the_ambient_domain(self):
        for lang, phrases in [
            ('es', ['esto vale sin ninguna restricción sobre la clase ambiente',
                    'esta conclusión se cumple sin restricciones sobre el dominio de aplicación']),
            ('en', ['this holds without any restriction on the ambient class',
                    'this result applies without restrictions on the domain of application']),
        ]:
            for phrase in phrases:
                with self.subTest(lang=lang, phrase=phrase):
                    self.assertEqual(universal_restatements(phrase, lang), [(0, len(phrase))])

    def test_a_restriction_on_a_different_object_or_a_retained_hypothesis(self):
        for lang, phrases in [
            ('es', ['esto vale sin restricciones adicionales sobre la clase ambiente',
                    'esto vale sin ninguna restricción sobre la clase de etiquetas',
                    'esto vale sin ninguna restricción sobre la clase ambiente de las etiquetas',
                    'esto vale sin ninguna restricción sobre la clase ambiente, si el grafo es conexo',
                    'esto vale sin ninguna restricción sobre la clase ambiente si el grafo es conexo',
                    'esto no vale sin ninguna restricción sobre la clase ambiente']),
            ('en', ['this holds without further restrictions on the ambient class',
                    'this holds without any restriction on the label class',
                    'this holds without any restriction on the ambient class of labels',
                    'this holds without any restriction on the ambient class, if the graph is connected',
                    'this holds without any restriction on the ambient class if the graph is connected',
                    'this does not hold without any restriction on the ambient class']),
        ]:
            for phrase in phrases:
                with self.subTest(lang=lang, phrase=phrase):
                    self.assertEqual(universal_restatements(phrase, lang), [])

    def test_domain_removal_requires_context_and_obeys_the_reporting_clause(self):
        for lang, assertion, caution, correction in [
            ('es', 'Esto vale sin ninguna restricción sobre la clase ambiente.',
             'El argumento no acredita que esto valga sin ninguna restricción sobre la clase ambiente.',
             'El argumento no acredita que esto valga sin ninguna restricción sobre la clase ambiente, pero los autores sí.'),
            ('en', 'This holds without any restriction on the ambient class.',
             'The argument does not establish that this holds without any restriction on the ambient class.',
             'The argument does not establish that this holds without any restriction on the ambient class, but the authors do.'),
        ]:
            for text, expect_review in [(assertion, True), (caution, False), (correction, True)]:
                with self.subTest(lang=lang, text=text):
                    packet = force_packet()
                    packet['versions'][lang][0]['text'] += ' ' + text
                    issues = guardrail.check(SOURCE, packet)
                    self.assertEqual(len(issues), int(expect_review), issues)
                    if expect_review:
                        self.assertIn('universal restatement', issues[0])
                    del packet['claims'][0]['existentials']
                    self.assertEqual(guardrail.check(SOURCE, packet), [])
            with self.subTest(lang=lang, context='missing witness'):
                packet = force_packet()
                lead = {'es': 'Observamos el resorte.', 'en': 'We observe the spring.'}[lang]
                packet['versions'][lang][0]['text'] = lead + ' ' + assertion
                issues = guardrail.check(SOURCE, packet)
                self.assertEqual(len(issues), 1, issues)
                self.assertIn('accepted existential wording missing', issues[0])

    def test_explicit_universal_subject_predicate_and_domain(self):
        samples = {
            'es': ['la primera frase puede reforzarse a una afirmación universal',
                   'esto vale en todos los casos', 'este resultado se aplica a todos los casos',
                   'la conclusión se cumple para cada caso', 'esa parte. esto funciona sin excepción'],
            'en': ['the previous sentence can be strengthened to a universal statement',
                   'this holds in all cases', 'the result applies to every case',
                   'it works without exception', 'this conclusion has universal scope'],
        }
        for lang, phrases in samples.items():
            for phrase in phrases:
                with self.subTest(lang=lang, phrase=phrase):
                    self.assertTrue(universal_restatements(phrase, lang))

    def test_other_subjects_domains_and_restrictions(self):
        samples = {
            'es': ['la nota compara una afirmación universal con otra',
                   'esta observación se limita a ese conjunto',
                   'esto vale para todos sus puntos', 'esto vale para cada viscosidad positiva',
                   'esto vale en todos los casos examinados',
                   'esto vale en todos los casos de aquella muestra',
                   'esto no vale en todos los casos', 'la primera frase no puede generalizarse'],
            'en': ['the index defines a universal statement', 'this applies to all its points',
                   'this holds for every positive viscosity', 'this only holds for a particular choice',
                   'this is universally known', 'this holds in all cases examined',
                   'this applies in all cases in the chosen subset', 'this does not hold in all cases'],
        }
        for lang, phrases in samples.items():
            for phrase in phrases:
                with self.subTest(lang=lang, phrase=phrase):
                    self.assertEqual(universal_restatements(phrase, lang), [])

    def test_starts_at_the_subordinate_subject_for_polarity(self):
        for lang, prefix, phrase in [
            ('es', 'el teorema no afirma que ', 'esto valga en todos los casos'),
            ('es', 'el artículo no dice que ', 'este resultado se aplique a todos los casos'),
            ('en', 'the theorem does not claim that ', 'this holds in all cases'),
        ]:
            with self.subTest(phrase=phrase):
                text = prefix + phrase + '.'
                self.assertEqual(universal_restatements(text, lang), [(len(prefix), len(text) - 1)])

    def test_multiple_spans_allow_polarity_to_be_evaluated_for_each_clause(self):
        text = 'the authors do not claim that this holds in all cases, but it applies to every case.'
        self.assertEqual([text[a:b] for a, b in universal_restatements(text, 'en')],
                         ['this holds in all cases', 'it applies to every case'])

    def test_indifference_to_choice_and_arbitrary_pronoun(self):
        pairs = [
            ('es', 'la elección concreta resulta irrelevante', 'la elección concreta de notación resulta irrelevante'),
            ('es', 'la elección específica no importa', 'la elección específica no importa para la notación'),
            ('es', 'cualquiera de ellas funciona', 'cualquiera de ellas funciona, siempre que sea la elegida'),
            ('es', 'no importa cuál se elija', 'no importa cuál de las dos notaciones se elija'),
            ('en', 'the specific choice is irrelevant', 'the specific choice of font is irrelevant'),
            ('en', 'the particular choice makes no difference', 'the particular choice makes no difference to the label'),
            ('en', 'any of them would work', 'any of them would work, provided it was among those tested'),
            ('en', 'it does not matter which one is chosen', 'it does not matter which one is chosen as a label'),
        ]
        for lang, generalization, control in pairs:
            with self.subTest(generalization=generalization):
                self.assertEqual(universal_restatements(generalization, lang), [(0, len(generalization))])
                self.assertEqual(universal_restatements(control, lang), [])

    def test_description_equality_and_bare_plural_pronouns_leave_antecedent_open(self):
        for lang, phrase in [
            ('es', 'las dos descripciones son equivalentes'), ('es', 'todos cumplen la condición'),
            ('en', 'the descriptions are equivalent'), ('en', 'all of them are green'),
        ]:
            with self.subTest(phrase=phrase):
                self.assertEqual(universal_restatements(phrase, lang), [])


if __name__ == '__main__':
    unittest.main()
