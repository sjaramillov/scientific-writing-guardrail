"""Version 4 from prepare/check/render, including bilingual evidence for a restatement."""
import copy
import json
import unittest

import guardrail
from tests.test_scope import SOURCE, force_packet, run_cli
from tests.test_scope_continuity import add_segment


WITNESS = {"en": "The spring supports blue loads.", "es": "El resorte sostiene cargas azules."}
EXTENSION = {"en": "This works for all red loads.", "es": "Esto funciona para todas las cargas rojas."}


def application():
    return {
        "kind": "application", "source": "The force balances the spring.",
        "en": {"property": "supports", "objects": "blue loads", "witnesses": [WITNESS["en"]],
               "extensions": ["red loads"]},
        "es": {"property": "sostiene", "objects": "cargas azules", "witnesses": [WITNESS["es"]],
               "extensions": ["cargas rojas"]},
    }


def sample():
    p = force_packet()
    p["version"] = 4
    del p["claims"][0]["existentials"]
    p["claims"][0]["scope_rules"] = [application()]
    for lang in WITNESS:
        p["versions"][lang][0]["text"] = WITNESS[lang]
    return p


class PropertyPackets(unittest.TestCase):
    def test_prepare_keeps_other_versions_and_combines_selected_features(self):
        for scope, links, props, version in ((False, False, False, 1), (True, False, False, 2),
                                              (False, True, False, 3), (False, False, True, 4),
                                              (True, True, True, 4)):
            p = guardrail.prepare(SOURCE, with_scope=scope, with_antecedents=links, with_properties=props)
            self.assertEqual(p["version"], version)
            self.assertEqual("antecedents" in p["versions"]["es"][0], links)
            self.assertEqual("existentials" in p["claims"][0], scope or links)
            self.assertEqual("scope_rules" in p["claims"][0], props)
        self.assertEqual(guardrail.check(SOURCE, sample()), [])

    def test_rule_version_shape_mismatch_and_source_mismatch(self):
        for version in (1, 2, 3):
            p = sample()
            p["version"] = version
            with self.assertRaises(guardrail.PacketError):
                guardrail.check(SOURCE, p)
        for bad in (None, {}, [None], [{}], [dict(application(), kind="unsupported")]):
            p = sample()
            p["claims"][0]["scope_rules"] = bad
            self.assertEqual(run_cli("check", p).returncode, 2)
        p = sample()
        p["claims"][0]["scope_rules"][0]["source"] = "Unsupported extract."
        self.assertTrue(any("source wording missing" in i for i in guardrail.check(SOURCE, p)))

    def test_wrong_scope_setup_is_invalid(self):
        for override in ({"extensions": ["BLUE loads"]}, {"witnesses": ["Supports items."]},
                         {"objects": ""}, {"extensions": "loads"}, {"property": []}):
            p = sample()
            p["claims"][0]["scope_rules"][0]["en"].update(override)
            with self.assertRaises(guardrail.PacketError):
                guardrail.check(SOURCE, p)

    def test_asserted_property_and_licensed_domain_appear_in_private_receipt(self):
        for lang, text in EXTENSION.items():
            p = sample()
            p["versions"][lang][0]["text"] += " " + text
            run = run_cli("check", p)
            self.assertEqual(run.returncode, 1)
            receipt = json.loads(run.stdout)
            self.assertEqual(receipt["scope_rule_count"], 1)
            row, = receipt["scope_findings"]
            self.assertEqual((row["language"], row["claim"], row["rule_claim"], row["rule"], row["sentence"]),
                             (lang, "C1", "C1", 1, 2))
            spec = application()[lang]
            for term in (spec["objects"], spec["extensions"][0], spec["property"]):
                self.assertIn(term, row["detail"])
            self.assertEqual(run_cli("render", p, "--language", lang).returncode, 1)
            rendered = run_cli("render", sample(), "--language", lang, "--with-notes")
            self.assertEqual(rendered.returncode, 0)
            self.assertNotIn("extensions", rendered.stdout)

    def test_uses_recent_affirmative_witness_for_this_object_and_direction_only(self):
        for lang, before, after in (
            ("en", "We ask whether the spring supports blue loads.", EXTENSION["en"]),
            ("en", WITNESS["en"]+" The spring is long.", EXTENSION["en"]),
            ("en", WITNESS["en"], "This works for all red loads if calibrated."),
            ("en", WITNESS["en"], "This works for all blue loads."),
            ("es", "Se desconoce si el resorte sostiene cargas azules.", EXTENSION["es"]),
            ("es", WITNESS["es"], "Esto funciona para todas las cargas rojas, si se calibra."),
        ):
            p = sample()
            p["versions"][lang][0]["text"] = before + " " + after
            self.assertEqual(guardrail.check(SOURCE, p), [], (before, after))

    def test_cross_segment_reading_order_and_paragraph_boundary(self):
        p = sample()
        add_segment(p, 2)
        part = p["versions"]["es"][1]
        part["text"] = EXTENSION["es"] + " Observamos el resorte."
        self.assertTrue(guardrail.check(SOURCE, p))
        part["new_paragraph"] = True
        self.assertEqual(guardrail.check(SOURCE, p), [])
        part["antecedents"] = [{"sentence": 1, "mention": "Esto", "claim": "C1"}]
        self.assertTrue(guardrail.check(SOURCE, p))

    def test_exact_distant_link_overrides_local_property_after_unicode_casefold(self):
        p = sample()
        add_segment(p, 2)
        add_segment(p, 3)
        part = p["versions"]["en"][2]
        part.update(text="The spring is marked Straße. " + EXTENSION["en"], new_paragraph=True,
                    antecedents=[{"sentence": 2, "mention": "This", "claim": "C1"}])
        run = json.loads(run_cli("check", p).stdout)
        self.assertEqual(len(run["scope_findings"]), 1)
        row = run["scope_findings"][0]
        self.assertEqual((row["claim"], row["rule_claim"]), ("C3", "C1"))
        part["antecedents"][0]["claim"] = "C2"
        self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_annotating_an_object_instead_of_the_subject_cannot_transfer_property(self):
        p = sample()
        add_segment(p, 2)
        part = p["versions"]["en"][1]
        part.update(text=EXTENSION["en"]+" We observe the spring.", new_paragraph=True,
                    antecedents=[{"sentence": 1, "mention": "red loads", "claim": "C1"}])
        self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_witness_and_new_domain_respect_case_sensitive_mathematical_names(self):
        p = sample()
        spec = p["claims"][0]["scope_rules"][0]["en"]
        spec.update(property="supports", objects="loads in V", witnesses=["The spring supports loads in V."],
                    extensions=["loads in U"])
        for witness, extension, alerts in (
            ("The spring supports loads in V.", "This works for all loads in U.", True),
            ("The spring supports loads in v.", "This works for all loads in U.", False),
            ("The spring supports loads in V.", "This works for all loads in u.", False),
        ):
            p["versions"]["en"][0]["text"] = witness + " " + extension
            self.assertEqual(bool(guardrail.check(SOURCE, p)), alerts)

    def test_metadata_only_v4_does_not_change_legacy_decision(self):
        p = force_packet()
        q = copy.deepcopy(p)
        q["version"] = 4
        q["claims"][0]["scope_rules"] = []
        self.assertEqual(guardrail.check(SOURCE, p), guardrail.check(SOURCE, q))
        receipt = json.loads(run_cli("check", q).stdout)
        self.assertEqual((receipt["scope_rule_count"], receipt["scope_findings"]), (0, []))
        self.assertNotIn("declared_scope_relations_and_dependencies", receipt["checked"])
