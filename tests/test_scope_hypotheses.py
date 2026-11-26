"""Paired claims distinguish loss of an assumption from an alternative proof."""
import copy
import unittest

from scope_hypotheses import findings, validate


RULE = {
    "kind": "hypothesis",
    "source": "For every admissible system with the regularity property the estimate holds.",
    "en": {
        "subjects": ["system", "systems"],
        "hypotheses": ["regularity", "regular"],
        "domains": ["class", "domain"],
        "conclusions": ["error estimate", "estimate"],
    },
    "es": {
        "subjects": ["sistema", "sistemas"],
        "hypotheses": ["regularidad", "regular"],
        "domains": ["clase", "dominio"],
        "conclusions": ["estimación del error", "estimación"],
    },
}


class HypothesisChecks(unittest.TestCase):
    def test_schema_requires_both_editions_and_the_declared_roles(self):
        validate(RULE)
        for bad in (None, {"kind": "hypothesis"}, {**RULE, "source": "  "},
                    {**RULE, "en": None}, {**RULE, "es": {"subjects": ["object"]}}):
            with self.subTest(rule=bad), self.assertRaises(ValueError):
                validate(bad)
        for key in RULE["es"]:
            for value in ([], "papel", [""], ["x", False]):
                r = copy.deepcopy(RULE)
                r["es"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate(r)

    def test_blanket_release_names_condition_subject_and_domain(self):
        for lang, wording, roles in (
            ("en", "Thus the system need not have regularity, even in the absence of any other hypothesis on its class.",
             ("system", "regularity", "class", "error estimate")),
            ("es", "Así, el sistema puede carecer de regularidad incluso si no se supone nada más sobre su clase.",
             ("sistema", "regularidad", "clase", "estimación del error")),
            ("en", "The systems may lack regularity even without any other restrictions on their domain.",
             ("systems", "regularity", "domain", "error estimate")),
            ("es", "El sistema no tiene por qué ser regular, sin ninguna otra restricción sobre su dominio.",
             ("sistema", "regular", "dominio", "estimación del error")),
        ):
            with self.subTest(wording=wording):
                result, = findings(wording, RULE, lang)
                for value in roles:
                    self.assertIn(f"'{value}'", result)

    def test_named_conclusion_and_condition_belong_to_the_same_assertion(self):
        for lang, assertion, terms in (
            ("en", "The error estimate still holds even without assuming regularity.", ("error estimate", "regularity")),
            ("en", "The estimate applies even when the system lacks regularity.", ("estimate", "system", "regularity")),
            ("es", "La estimación del error se cumple incluso sin exigir regularidad.", ("estimación del error", "regularidad")),
            ("es", "La estimación se mantiene incluso si el sistema no es regular.", ("estimación", "sistema", "regular")),
        ):
            with self.subTest(assertion=assertion):
                result, = findings(assertion, RULE, lang)
                for v in terms:
                    self.assertIn(f"'{v}'", result)

    def test_retained_conditions_and_other_proofs_stay_with_the_claim(self):
        for lang, controls in (
            ("en", ["The system need not have regularity.",
                    "The system need not have regularity if it is symmetric.",
                    "The system may lack regularity without all other assumptions on its class.",
                    "The system may lack regularity without any other assumption on its class, provided it is bounded.",
                    "In a symmetric class the error estimate holds without regularity.",
                    "The estimate still holds without assuming regularity, but only under symmetry.",
                    "The estimate holds even without any further regularity.",
                    "The estimate holds without assuming regularity except at zero."]),
            ("es", ["El sistema puede carecer de regularidad.",
                    "El sistema puede carecer de regularidad si es simétrico.",
                    "El sistema puede carecer de regularidad incluso si no se supone nada más sobre su clase, siempre que sea acotado.",
                    "En la clase simétrica la estimación del error se cumple sin regularidad.",
                    "La estimación del error se cumple sin regularidad, pero solo bajo simetría.",
                    "La estimación se mantiene sin exigir más regularidad.",
                    "La estimación se mantiene sin regularidad salvo en cero."]),
        ):
            for control in controls:
                with self.subTest(control=control):
                    self.assertEqual(findings(control, RULE, lang), [])

    def test_explicitly_dispensable_condition_in_both_argument_orders(self):
        for lang, examples in (
            ("en", ["The error estimate does not require regularity.",
                    "Regularity is unnecessary for the error estimate.",
                    "Regularity is not required for the estimate."]),
            ("es", ["La estimación del error no requiere regularidad.",
                    "La regularidad es innecesaria para la estimación del error.",
                    "La estimación no necesita regularidad."]),
        ):
            for statement in examples:
                with self.subTest(statement=statement):
                    self.assertEqual(len(findings(statement, RULE, lang)), 1)

    def test_dispensability_is_bound_to_exact_named_requirement_and_conclusion(self):
        for lang, controls in (
            ("en", ["Regularity is unnecessary for notation.",
                    "The error estimate does not require additional regularity.",
                    "Regularity is unnecessary for the estimate if the systems are symmetric.",
                    "The estimate does not require regularity of the comparison map.",
                    "The paper never says that regularity is unnecessary for the estimate.",
                    "The estimate requires regularity.",
                    "‘Regularity is unnecessary for the estimate.’"]),
            ("es", ["La regularidad es innecesaria para la notación.",
                    "La estimación del error no requiere regularidad adicional.",
                    "La regularidad es innecesaria para la estimación siempre que el sistema sea simétrico.",
                    "La estimación no requiere regularidad de la aplicación de comparación.",
                    "Es falso que la estimación no requiera regularidad.",
                    "La estimación requiere regularidad.",
                    "«La regularidad es innecesaria para la estimación»."]),
        ):
            for statement in controls:
                with self.subTest(statement=statement):
                    self.assertEqual(findings(statement, RULE, lang), [])

    def test_epistemic_scope_and_polarity_do_not_become_assertions(self):
        for lang, controls in (
            ("en", ["It is not known whether the estimate holds without regularity.",
                    "The article does not claim that the estimate holds without regularity.",
                    "Does the estimate hold without regularity?",
                    "The estimate holds without regularity?",
                    "“The estimate holds without regularity.”",
                    "Assume that the estimate holds without regularity.",
                    "If the estimate holds without regularity, the rate follows."]),
            ("es", ["Se desconoce si la estimación se mantiene sin regularidad.",
                    "El artículo no afirma que la estimación se mantenga sin regularidad.",
                    "¿La estimación se mantiene sin regularidad?",
                    "«La estimación se mantiene sin regularidad».",
                    "Supóngase que la estimación se mantiene sin regularidad.",
                    "Si la estimación se mantiene sin regularidad, obtenemos la tasa."]),
        ):
            for control in controls:
                with self.subTest(control=control):
                    self.assertEqual(findings(control, RULE, lang), [])

    def test_other_subject_condition_domain_or_conclusion_does_not_trigger(self):
        for lang, controls in (
            ("en", ["The model may lack regularity without any other assumption on its domain.",
                    "The system may lack stability without any other assumption on its domain.",
                    "The system may lack regularity without any other assumption on its scale.",
                    "The estimate holds even when the model lacks regularity.",
                    "The pointwise bound holds without regularity."]),
            ("es", ["El modelo puede carecer de regularidad sin ninguna otra hipótesis sobre su clase.",
                    "El sistema puede carecer de estabilidad sin ninguna otra hipótesis sobre su clase.",
                    "El sistema puede carecer de regularidad sin ninguna otra hipótesis sobre su escala.",
                    "La estimación se cumple incluso si el modelo carece de regularidad.",
                    "La cota puntual se cumple sin regularidad."]),
        ):
            for control in controls:
                with self.subTest(control=control):
                    self.assertEqual(findings(control, RULE, lang), [])

    def test_variables_in_roles_remain_case_sensitive_and_patterns_are_literal(self):
        r = copy.deepcopy(RULE)
        r["en"].update(subjects=["map F"], hypotheses=["P(x)"], domains=["class"])
        text = "The map F may lack P(x) without any other assumption on its class."
        self.assertEqual(len(findings(text, r, "en")), 1)
        for change in (text.replace("map F", "map f"), text.replace("P(x)", "p(x)"),
                       text.replace("P(x)", "Px")):
            with self.subTest(change=change):
                self.assertEqual(findings(change, r, "en"), [])
