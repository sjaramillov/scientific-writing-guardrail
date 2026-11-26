"""Dependency rules should bind the asserted quantity and its own parameter."""

import copy
import unicodedata
import unittest

import scope_dependencies as dep


RULE = {
    "kind": "dependency", "source": "given a radius choose a threshold",
    "en": {"quantity": ["threshold"], "parameter": ["radius", "radii"],
           "quantity_symbols": ["K(r)"], "parameter_symbols": ["r"]},
    "es": {"quantity": ["umbral"], "parameter": ["radio", "radios"],
           "quantity_symbols": ["K(r)"], "parameter_symbols": ["r"]},
}


class DependencyTests(unittest.TestCase):
    def test_schema_requires_two_distinguishable_roles_in_both_editions(self):
        dep.validate(RULE)
        for field, value in (("quantity", "threshold"), ("quantity", [4]), ("quantity", ["  "]),
                             ("parameter", ["threshold"]), ("parameter", ["k(R)"]),
                             ("parameter_symbols", ["K(r)"]), ("other", [])):
            rule = copy.deepcopy(RULE)
            rule["en"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                dep.validate(rule)
        for malformed in ([RULE], {}, {**RULE, "es": []}, {**RULE, "source": " "}):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                dep.validate(malformed)

    def test_aliases_may_be_words_or_exact_symbol_forms(self):
        rule = copy.deepcopy(RULE)
        rule["en"] = {"quantity": [], "parameter": [], "quantity_symbols": ["R"], "parameter_symbols": ["r"]}
        dep.validate(rule)
        self.assertTrue(dep.findings("R does not depend on r.", rule, "en"))
        self.assertFalse(dep.findings("r does not depend on R.", rule, "en"))
        rule["en"]["quantity_symbols"] = []
        with self.assertRaises(ValueError):
            dep.validate(rule)

    def test_universal_choice_binds_each_declared_role(self):
        for lang, sentences in [
            ("en", ["A single threshold is sufficient for every radius.",
                    "The same threshold works for all radii.",
                    "One common threshold suffices for each value of the radius."]),
            ("es", ["Basta un solo umbral para cualquier radio.",
                    "El mismo umbral sirve para todos los radios.",
                    "Un único umbral basta para cada valor del radio."]),
        ]:
            for sentence in sentences:
                with self.subTest(sentence=sentence):
                    alerts = dep.findings(sentence, RULE, lang)
                    self.assertEqual(len(alerts), 1)
                    self.assertIn("quantity", alerts[0])
                    self.assertIn("parameter", alerts[0])

    def test_reducing_or_varying_a_parameter_with_quantity_fixed(self):
        for lang, text, cue in [
            ("en", "Once selected, K(r) remains fixed while r varies.", "while r varies"),
            ("es", "Una vez elegido, K(r) puede mantenerse fijo a medida que r disminuye.", "que r disminuye"),
        ]:
            with self.subTest(lang=lang):
                alert, = dep.findings(text, RULE, lang)
                self.assertIn("'K(r)'", alert)
                self.assertIn("'r'", alert)
                self.assertIn(cue, alert)

    def test_explicit_limit_must_match_the_declared_endpoint(self):
        rule = copy.deepcopy(RULE)
        rule["en"]["limit_values"] = ["zero", "0"]
        rule["es"]["limit_values"] = ["cero", "0"]
        dep.validate(rule)
        for lang, ends, restricted in (
            ("en", ["K(r) remains fixed as r tends to zero.", "K(r) remains fixed as r approaches 0."],
             ["K(r) remains fixed as r tends to one.", "K(r) remains fixed as r approaches 0.5.",
              "K(r) remains fixed as r varies between 0.5 and 0.9.",
              "K(r) remains fixed as r decreases by at most 0.01."]),
            ("es", ["K(r) permanece fijo cuando r tiende a cero.", "K(r) permanece fijo cuando r se aproxima a 0."],
             ["K(r) permanece fijo cuando r tiende a uno.", "K(r) permanece fijo cuando r se aproxima a 0,5.",
              "K(r) permanece fijo cuando r varía entre 0,5 y 0,9.",
              "K(r) permanece fijo cuando r disminuye a lo sumo 0,01."]),
        ):
            for text in ends:
                with self.subTest(text=text):
                    self.assertTrue(dep.findings(text, rule, lang))
                    self.assertFalse(dep.findings(text, RULE, lang))
            for text in restricted:
                with self.subTest(text=text):
                    self.assertFalse(dep.findings(text, rule, lang))

    def test_preserves_trailing_restrictions_and_postposed_disclaimers(self):
        for lang, texts in [
            ("en", ["A single threshold is sufficient for every radius, apart from radii below one half.",
                    "The threshold is independent of the radius, assuming a constant input.",
                    "The threshold is independent of the radius, a statement we do not assert.",
                    "The threshold is independent of the radius, but only under this assumption.",
                    "The threshold is independent of the radius; only for a fixed input."]),
            ("es", ["Basta un solo umbral para cualquier radio, salvo los menores que un medio.",
                    "El umbral es independiente del radio, suponiendo una entrada constante.",
                    "El umbral es independiente del radio, afirmación que no sostenemos.",
                    "El umbral es independiente del radio, pero solo bajo esta condición.",
                    "El umbral es independiente del radio; solo para una entrada fija."]),
        ]:
            for text in texts:
                with self.subTest(text=text):
                    self.assertFalse(dep.findings(text, RULE, lang))

    def test_explicit_independence_or_uniformity_is_an_assertion(self):
        for lang, text in [
            ("en", "The threshold does not depend on the radius."),
            ("en", "The threshold is uniform in the radius."),
            ("en", "The threshold can be chosen independently of the radius."),
            ("en", "We can choose a threshold uniformly in the radius."),
            ("es", "El umbral no depende del radio."),
            ("es", "El umbral es uniforme respecto al radio."),
            ("es", "El umbral puede elegirse independientemente del radio."),
            ("es", "Podemos elegir el umbral uniformemente en el radio."),
        ]:
            with self.subTest(text=text):
                self.assertTrue(dep.findings(text, RULE, lang))

    def test_faithful_cautious_conditional_and_unrelated_statements_pass(self):
        for lang, sentences in [
            ("en", ["For every radius there is a threshold.", "The threshold may depend on the radius.",
                    "A single threshold is not sufficient for every radius.",
                    "It remains unknown whether a single threshold works for every radius.",
                    "If the threshold is independent of the radius, a simplification follows.",
                    "The threshold is independent of the radius, provided the sample is uniform.",
                    "K(r) remains fixed when r is held fixed.", "Is the threshold independent of the radius?",
                    "The radius is independent of the threshold.", "The threshold is independent of the radius measurement.",
                    "One threshold suffices for every radius selected in this experiment.",
                    "The threshold is sufficient. Every radius was tested.",
                    "K(r) is the threshold; the duration is independent of the radius."]),
            ("es", ["Para cada radio existe un umbral.", "El umbral puede depender del radio.",
                    "Un solo umbral no basta para cualquier radio.",
                    "Sigue abierta la cuestión de si un solo umbral sirve para cada radio.",
                    "Si el umbral es independiente del radio, se simplifica la expresión.",
                    "El umbral es independiente del radio, siempre que la muestra sea uniforme.",
                    "K(r) permanece fijo cuando r se mantiene fijo.", "¿Es el umbral independiente del radio?",
                    "El radio no depende del umbral.", "El umbral no depende del radio térmico residual.",
                    "Un solo umbral sirve para cada radio elegido en el experimento.",
                    "K(r) es el umbral; la duración no depende del radio."]),
        ]:
            for sentence in sentences:
                with self.subTest(sentence=sentence):
                    self.assertFalse(dep.findings(sentence, RULE, lang))

    def test_external_caution_does_not_hide_a_new_clausal_assertion(self):
        for lang, text in [
            ("en", "We make no claim about uniformity, but the same threshold works for every radius."),
            ("es", "Dejamos abierta la cuestión de la uniformidad, pero el mismo umbral basta para todo radio."),
        ]:
            with self.subTest(lang=lang):
                self.assertTrue(dep.findings(text, RULE, lang))

    def test_symbols_do_not_match_different_case_suffixes_or_variable_names(self):
        for phrase in ["k(r) remains fixed as r varies.", "K(r) remains fixed as R varies.",
                       "K(r)′ remains fixed as r varies.", "K(r) remains fixed as r₁ varies.",
                       "K(r) remains fixed as radius_squared varies.", "K(r) remains fixed as r′ varies."]:
            with self.subTest(phrase=phrase):
                self.assertFalse(dep.findings(phrase, RULE, "en"))

    def test_unicode_word_aliases_match_nfc_and_not_larger_words(self):
        rule = copy.deepcopy(RULE)
        rule["es"]["parameter"] = ["presión"]
        text = unicodedata.normalize("NFD", "El umbral no depende de la presión.")
        self.assertTrue(dep.findings(text, rule, "es"))
        self.assertFalse(dep.findings("El umbral no depende de la sobrepresión.", rule, "es"))
