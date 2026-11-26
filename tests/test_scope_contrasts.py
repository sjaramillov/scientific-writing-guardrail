import copy
import unittest

from scope_contrasts import findings, validate


# Synthetic terminology is independent of the papers used for development.
# Each matched sentence has a control that reinstates scope or changes a role.
SAMPLES = [
    ("relaxed_condition",
     {"subject": "sample", "retained": "dry", "excluded": "contains salt"},
     {"subject": "muestra", "retained": "seca", "excluded": "contenga sal"},
     "This holds for each sample that is dry, even if it contains salt.",
     "Esto vale para cada muestra que sea seca, aunque contenga sal.",
     "This holds for each sample that is dry and contains no salt.",
     "Esto vale para cada muestra que sea seca y no contenga sal."),
    ("partial_sufficiency",
     {"condition": "symmetry", "conclusion": "convergence"},
     {"condition": "simetría", "conclusion": "convergencia"},
     "Convergence follows from symmetry alone.",
     "Por sí sola, la simetría garantiza la convergencia.",
     "Symmetry and coercivity guarantee convergence.",
     "La simetría y la coercividad garantizan la convergencia."),
    ("excluded_instance",
     {"actor": "classifier", "instance": "empty sample", "outcome": "label"},
     {"actor": "clasificador", "instance": "muestra vacía", "outcome": "etiqueta"},
     "The classifier produces a label even for an empty sample.",
     "El clasificador produce una etiqueta incluso para una muestra vacía.",
     "The classifier produces a warning even for an empty sample.",
     "El clasificador produce un aviso incluso para una muestra vacía."),
    ("strengthened_value",
     {"subject": "degree", "value": "4"},
     {"subject": "grado", "value": "4"},
     "The degree must be exactly 4.", "El grado debe ser exactamente 4.",
     "The degree is at most 4.", "El grado es a lo sumo 4."),
    ("discarded_condition",
     {"subject": "tubes", "condition": "sterile"}, {"subject": "tubos", "condition": "estériles"},
     "The result holds even without requiring the tubes to be sterile.",
     "El resultado se cumple incluso sin exigir que los tubos sean estériles.",
     "The result holds when the tubes are sterile.", "El resultado se cumple si los tubos son estériles."),
    ("unconditional_bound",
     {"condition": "calibration", "quantity": "errors", "limit": "2"},
     {"condition": "calibración", "quantity": "errores", "limit": "2"},
     "Without calibration, the paper guarantees infinitely many errors of size at most 2.",
     "Sin calibración, el artículo garantiza infinitos errores de tamaño a lo sumo 2.",
     "Without calibration, the paper guarantees infinitely many errors of size at most 10.",
     "Sin calibración, el artículo garantiza infinitos errores de tamaño a lo sumo 10."),
    ("eventual_bound",
     {"quantity": "residuals", "index": "step"}, {"quantity": "residuos", "index": "paso"},
     "Beyond a certain step, this bound covers all residuals.",
     "A partir de cierto paso, esta cota cubre todos los residuos.",
     "Beyond a certain step, this bound covers some residuals.",
     "A partir de cierto paso, esta cota cubre algunos residuos."),
    ("wider_domain",
     {"subject": "vector", "domain": "ambient space"}, {"subject": "vector", "domain": "espacio ambiente"},
     "This applies to every vector in the ambient space.",
     "Esto se cumple para todo vector en el espacio ambiente.",
     "This holds for every unit vector in the ambient space.",
     "Esto vale para todo vector unitario en el espacio ambiente."),
    ("distributed_uniqueness",
     {"member": "blocks", "object": "entry"}, {"member": "bloques", "object": "elemento"},
     "Each of the blocks has exactly one entry.",
     "Cada uno de los bloques tiene exactamente un elemento.",
     "All the blocks have exactly one common entry.",
     "Todos los bloques tienen exactamente un elemento común."),
]


def mapped(frame, en, es):
    data = {"kind": "contrast", "source": "frozen sample"}
    for lang, roles in [("en", en), ("es", es)]:
        data[lang] = {"frame": frame, "licensed": "source-supported relation",
                      "roles": {key: [term] for key, term in roles.items()}}
    return data


class TestScopeContrasts(unittest.TestCase):
    def test_bilingual_frames_bind_every_declared_role(self):
        for frame, en, es, bad_en, bad_es, ok_en, ok_es in SAMPLES:
            rule = mapped(frame, en, es)
            validate(rule)
            for lang, bad, ok, roles in [("en", bad_en, ok_en, en), ("es", bad_es, ok_es, es)]:
                with self.subTest(frame=frame, lang=lang):
                    alerts = findings(bad, rule, lang)
                    self.assertEqual(len(alerts), 1)
                    for role in roles:
                        self.assertIn(role + " '", alerts[0])
                    self.assertEqual(findings(ok, rule, lang), [])

    def test_derivation_is_directed_and_must_be_asserted(self):
        rule = mapped(*SAMPLES[1][:3])
        for lang, examples in [
            ("en", ["Convergence implies symmetry.", "Symmetry alone guarantees convergence?",
                    "The argument alone does not establish that symmetry implies convergence.",
                    "Symmetry guarantees convergence provided the operator is coercive."]),
            ("es", ["La convergencia implica la simetría.", "¿La simetría implica la convergencia?",
                    "Por sí solo, el argumento no acredita que la simetría implique la convergencia.",
                    "La simetría garantiza la convergencia bajo una condición de coercividad."]),
        ]:
            for sentence in examples:
                with self.subTest(sentence=sentence):
                    self.assertEqual(findings(sentence, rule, lang), [])

    def test_term_aliases_are_literal_and_variables_case_sensitive(self):
        rule = mapped("strengthened_value", {"subject": "F", "value": "2.5"},
                      {"subject": "F", "value": "2.5"})
        for lang, verb in [("en", "equals"), ("es", "equivale a")]:
            self.assertTrue(findings(f"F {verb} 2.5.", rule, lang))
            self.assertFalse(findings(f"f {verb} 2.5.", rule, lang))
            self.assertFalse(findings(f"F {verb} 2x5.", rule, lang))
            self.assertFalse(findings(f"F {verb} 12.5.", rule, lang))

    def test_sources_and_roles_are_required_in_both_editions(self):
        base = mapped(*SAMPLES[1][:3])
        for key, value in [("roles", {"conclusion": ["x"]}), ("roles", {"condition": [], "conclusion": ["x"]}),
                           ("licensed", " "), ("frame", "free regex")]:
            invalid = copy.deepcopy(base)
            invalid["es"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(invalid)
        for source in ["", None]:
            invalid = dict(base, source=source)
            with self.assertRaises(ValueError):
                validate(invalid)
        mismatched = dict(base, en=mapped(*SAMPLES[0][:3])["en"])
        with self.assertRaises(ValueError):
            validate(mismatched)
