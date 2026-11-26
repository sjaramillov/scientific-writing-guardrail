"""Minimal role-preserving pairs outside the five evaluation papers."""
import copy
import unittest

import scope_relations as relations


def packet(frame, en, es):
    roles = ("subject", "predicate", "licensed", "review")
    return {"kind": "relation", "source": "Teaching example.",
            "en": dict(frame=frame, **dict(zip(roles, ([term] for term in en)))),
            "es": dict(frame=frame, **dict(zip(roles, ([term] for term in es))))}


class RelationChecks(unittest.TestCase):
    def pairs(self, rule, en, es):
        relations.validate(rule)
        for lang, (conflict, controls) in (("en", en), ("es", es)):
            with self.subTest(lang=lang, text=conflict):
                findings = relations.findings(conflict, rule, lang)
                self.assertEqual(len(findings), 1, findings)
                self.assertIn(rule[lang]["licensed"][0], findings[0])
                for role in ("subject", "predicate", "review"):
                    self.assertIn(rule[lang][role][0], findings[0])
            for text in controls:
                with self.subTest(lang=lang, text=text):
                    self.assertEqual(relations.findings(text, rule, lang), [])

    def test_operator_and_argument_cannot_exchange_roles(self):
        rule = packet("operator", ("sample", "stable", "mean", "median"),
                      ("muestra", "estable", "media", "mediana"))
        self.pairs(rule, (
            "The median of a sample is stable.",
            ["The mean of a sample is stable.", "The median of a signal is stable.",
             "The median of a sample is variable.", "Is the median of a sample stable?",
             "The theorem does not claim that the median of a sample is stable.",
             "The median of a sample is stable if its distribution is symmetric.",
             "A sample of the median is stable."]), (
            "La mediana de una muestra es estable.",
            ["La media de una muestra es estable.", "La mediana de una señal es estable.",
             "La mediana de una muestra es variable.", "¿Es estable la mediana de una muestra?",
             "La mediana de una muestra es estable si su distribución es simétrica."]))

    def test_preservation_binds_both_arguments_to_declared_class(self):
        rule = packet("preservation", ("transform", "maps", "segments", "disks"),
                      ("transformación", "envía", "segmentos", "discos"))
        self.pairs(rule, (
            "Every transform maps disks to disks.",
            ["Every transform maps disks to segments.", "Every transform maps segments to disks.",
             "Every transform maps segments to segments.", "This transform maps disks to disks."]), (
            "Toda transformación envía discos a discos.",
            ["Toda transformación envía segmentos a discos.", "Toda transformación envía discos a segmentos.",
             "Toda transformación envía segmentos a segmentos.", "Esta transformación envía discos a discos."]))

    def test_qualifies_predicate_only_for_declared_object(self):
        rule = packet("classification", ("root", "solution", "local", "global"),
                      ("raíz", "solución", "local", "global"))
        self.pairs(rule, (
            "The root is a global solution.",
            ["The root is a local solution.", "Its derivative is a global solution.",
             "It is unknown whether the root is a global solution.", "The root is not a global solution.",
             "For another problem, the root is a global solution."]), (
            "La raíz es una solución global.",
            ["La raíz es una solución local.", "La derivada es una solución global.",
             "Se desconoce si la raíz es una solución global.", "La raíz no es una solución global.",
             "Para otro problema, la raíz es una solución global."]))

    def test_assumption_and_postposed_restriction_are_not_unqualified_assertions(self):
        rule = packet("classification", ("root", "solution", "local", "global"),
                      ("raíz", "solución", "local", "global"))
        for lang, texts in [("en", ["By assumption, the root is a global solution.",
                                    "The root is a global solution, but only under the extra condition."]),
                            ("es", ["Por hipótesis, la raíz es una solución global.",
                                    "La raíz es una solución global, pero solo bajo la condición adicional."])]:
            for text in texts:
                with self.subTest(text=text):
                    self.assertEqual(relations.findings(text, rule, lang), [])
        self.assertTrue(relations.findings("That remains open, but the root is a global solution.", rule, "en"))
        self.assertTrue(relations.findings("Eso queda abierto, pero la raíz es una solución global.", rule, "es"))

    def test_domain_requires_universal_subject_and_the_right_predicate(self):
        rule = packet("domain", ("series", "convergent", "the unit disk", "all of space"),
                      ("serie", "convergente", "el disco unidad", "todo el espacio"))
        self.pairs(rule, (
            "Every series is convergent in all of space.",
            ["Every series is bounded in all of space.", "Some series are convergent in all of space.",
             "Every series is convergent in the unit disk.", "It is unknown whether every series is convergent in all of space."]), (
            "Toda serie es convergente en todo el espacio.",
            ["Toda serie es acotada en todo el espacio.", "Toda serie es convergente en el disco unidad.",
             "Hay una serie convergente en todo el espacio.", "Se desconoce si toda serie es convergente en todo el espacio."]))

    def test_action_requires_declared_actor_verb_and_object(self):
        rule = packet("action", ("test", "establishes", "uniqueness", "existence"),
                      ("ensayo", "establece", "unicidad", "existencia"))
        self.pairs(rule, (
            "The test establishes existence.",
            ["The test establishes uniqueness.", "The construction establishes existence.",
             "The test considers existence.", "If the test establishes existence, we can stop."]), (
            "El ensayo establece la existencia.",
            ["El ensayo establece la unicidad.", "La construcción establece la existencia.",
             "El ensayo presupone la existencia.", "Si el ensayo establece la existencia, podemos parar."]))

    def test_symbol_case_and_punctuation_are_literal(self):
        rule = packet("action", ("f", "preserves", "mass", "P(x)"),
                      ("f", "conserva", "masa", "P(x)"))
        for lang, verb in [("en", "preserves"), ("es", "conserva")]:
            self.assertTrue(relations.findings(f"f {verb} P(x).", rule, lang))
            for text in [f"F {verb} P(x).", f"f {verb} p(x).", f"f {verb} Px."]:
                self.assertEqual(relations.findings(text, rule, lang), [])

    def test_rule_validation(self):
        base = packet("classification", ("root", "solution", "local", "global"),
                      ("raíz", "solución", "local", "global"))
        for field, value in [("frame", []), ("frame", "unsupported"), ("subject", []),
                             ("review", True), ("predicate", [" "]), ("licensed", ["GLOBAL"])]:
            candidate = copy.deepcopy(base)
            candidate["en"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                relations.validate(candidate)
        candidate = copy.deepcopy(base)
        candidate["es"]["frame"] = "domain"
        with self.assertRaises(ValueError):
            relations.validate(candidate)


if __name__ == "__main__":
    unittest.main()
