"""Anaphoric scope changes should preserve object, parameter, and question status."""
import copy
import unittest

import scope_resumption as res


EXAMPLE = {
    "kind": "resumption", "source": "The chosen tile has six sides.",
    "en": {"mode": "example", "property": "six sides", "objects": ["tile", "tiles"],
           "parameters": ["colour", "edge length"], "witnesses": ["It has six sides."]},
    "es": {"mode": "example", "property": "seis lados", "objects": ["baldosa", "baldosas"],
           "parameters": ["color", "longitud del borde"], "witnesses": ["Tiene seis lados."]},
}
QUESTION = {
    "kind": "resumption", "source": "Whether one index works is open.",
    "en": {"mode": "open_uniformity", "property": "one index", "objects": [],
           "parameters": ["angle", "angles", "θ"], "witnesses": ["Would one index suffice?"]},
    "es": {"mode": "open_uniformity", "property": "un único índice", "objects": [],
           "parameters": ["ángulo", "ángulos", "θ"], "witnesses": ["¿Bastaría un único índice?"]},
}


class ResumptionTests(unittest.TestCase):
    def test_modes_have_meaningful_roles_and_complete_witnesses(self):
        for rule in (EXAMPLE, QUESTION):
            res.validate(rule)
        for field, value in (("mode", []), ("objects", []), ("property", None), ("parameters", [""]),
                             ("witnesses", ["Would it have six sides?"]),
                             ("witnesses", ["It has six sides. Another tile was observed."]),
                             ("witnesses", ["The tile has five sides."])):
            rule = copy.deepcopy(EXAMPLE)
            rule["en"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                res.validate(rule)
        rule = copy.deepcopy(QUESTION)
        rule["es"]["parameters"] = []
        with self.assertRaises(ValueError):
            res.validate(rule)
        rule = copy.deepcopy(EXAMPLE)
        rule["en"] = QUESTION["en"]
        with self.assertRaises(ValueError):
            res.validate(rule)

    def test_witness_preserves_question_mark_mathematical_case_and_literal_property(self):
        self.assertTrue(res.witnessed("It  has six sides", EXAMPLE, "en"))
        self.assertFalse(res.witnessed("It has six sides?", EXAMPLE, "en"))
        self.assertFalse(res.witnessed("We suppose it has six sides.", EXAMPLE, "en"))
        self.assertTrue(res.witnessed("¿Bastari\u0301a un único índice?", QUESTION, "es"))
        self.assertFalse(res.witnessed("¿Bastaría un único índice.", QUESTION, "es"))
        rule = copy.deepcopy(EXAMPLE)
        rule["en"].update(property="R", witnesses=["R has six sides."])
        res.validate(rule)
        self.assertFalse(res.witnessed("r has six sides.", rule, "en"))

    def test_example_members_and_matching_declared_features(self):
        for lang, samples in (
            ("en", ["This holds for every one of them with that same colour and edge length.",
                    "That property also applies to all of the others.", "This is valid for every other tile.",
                    "This last property holds for each of the others as well.",
                    "This applies to all tiles with the same edge length."]),
            ("es", ["Esto se cumple para todos los que compartan ese mismo color y esa misma longitud del borde.",
                    "Esta última propiedad se cumple también en cada una de las demás.",
                    "La misma propiedad vale para todas las demás baldosas.",
                    "Ese resultado se aplica a cada baldosa con el mismo color."]),
        ):
            for text in samples:
                with self.subTest(text=text):
                    detail = res.extension(text, EXAMPLE, lang)
                    self.assertIsNotNone(detail)
                    self.assertIn(EXAMPLE[lang]["property"], detail)
                    self.assertIn(EXAMPLE[lang]["objects"][0], detail)
                    self.assertIn(text, detail)

    def test_example_preserves_retained_domains_and_other_roles(self):
        for lang, samples in (
            ("en", ["This only holds for the tile just constructed.", "This holds for all of its sides.",
                    "This holds for all tiles in the displayed sample.",
                    "This applies to all of them with the same edge length and material.",
                    "This holds for every tile, provided it is regular.",
                    "Does this hold for all the other tiles?", "This holds for all tiles?",
                    "It is unknown whether this holds for all tiles.", "The previous estimate holds for all tiles.",
                    "This does not apply to every other tile.", "This holds for all tiles except the central one.",
                    "This is valid for every angle.", "This is valid for every tile if it is regular."]),
            ("es", ["Esto solo vale para la baldosa que acabamos de construir.", "Esto vale para todos sus vértices.",
                    "Esto vale para todas las baldosas de la muestra.", "Esto vale para todas las baldosas salvo una.",
                    "Esto vale para todos los que tengan ese mismo color y ese mismo radio.",
                    "Esto se cumple para todas las baldosas si son regulares.",
                    "¿Esto se cumple para las demás baldosas?", "Esto no se cumple para todas las demás.",
                    "El argumento no demuestra que esto se cumpla en cada una de las demás."]),
        ):
            for text in samples:
                with self.subTest(text=text):
                    self.assertIsNone(res.extension(text, EXAMPLE, lang))

    def test_question_to_guarantee_mentions_the_actual_parameter(self):
        for lang, samples in (
            ("en", ["This is guaranteed in all cases, however small the angle.",
                    "That conclusion holds for every value of the angle.", "This holds regardless of the angle.",
                    "This holds for all angles.", "This is true for every θ."]),
            ("es", ["Esto está garantizado en todos los casos, por pequeño que sea el ángulo.",
                    "Este resultado vale para cada valor del ángulo.",
                    "Eso se cumple independientemente del ángulo.", "Esto es cierto para todos los ángulos."]),
        ):
            for text in samples:
                with self.subTest(text=text):
                    detail = res.extension(text, QUESTION, lang)
                    self.assertIsNotNone(detail)
                    self.assertIn(QUESTION[lang]["property"], detail)
                    self.assertIn(text, detail)

    def test_no_guarantee_for_other_parameter_restricted_range_or_open_question(self):
        for lang, samples in (
            ("en", ["This is true for every angle we measured.", "This holds for each angle, if sufficiently small.",
                    "This is guaranteed in all cases, however small the radius.", "This might hold for every angle.",
                    "This does not hold for every angle.", "If this holds for every angle, the proof is complete.",
                    "This is true for each angle under the initial conditions.", "This holds for every Θ."]),
            ("es", ["Esto está garantizado para cada ángulo mayor que 0,2.", "Esto podría valer para cada ángulo.",
                    "Esto se cumple para cada ángulo, salvo cuando es recto.", "Esto vale para cada ángulo?",
                    "Esto vale para todos los casos, por pequeño que sea el radio.",
                    "Esto se cumple en todos los casos de la tabla."]),
        ):
            for text in samples:
                with self.subTest(text=text):
                    self.assertIsNone(res.extension(text, QUESTION, lang))

    def test_modes_do_not_invent_a_missing_group_or_parameter(self):
        self.assertIsNone(res.extension("This is true for every angle.", EXAMPLE, "en"))
        self.assertIsNone(res.extension("Esto se cumple para todos los demás.", QUESTION, "es"))
        self.assertIsNone(res.extension("This holds for every one of them with the same unknown feature.", EXAMPLE, "en"))
