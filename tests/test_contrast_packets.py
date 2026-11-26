"""Integration checks for registering, checking and exporting a v6 claim contrast."""
import copy
import json
import unittest

import guardrail
from tests.test_scope import SOURCE, force_packet, run_cli


def packet():
    p = force_packet()
    p["version"] = 6
    rule = {
        "kind": "contrast", "source": p["claims"][0]["quote"],
        "en": {"frame": "partial_sufficiency", "licensed": "the designated force balances this spring",
               "roles": {"condition": ["smoothness"], "conclusion": ["balance"]}},
        "es": {"frame": "partial_sufficiency", "licensed": "la fuerza especificada equilibra este resorte",
               "roles": {"condition": ["suavidad"], "conclusion": ["equilibrio"]}},
    }
    p["claims"][0]["scope_rules"] = [rule]
    return p


class ContrastPackets(unittest.TestCase):
    def test_scaffold(self):
        p = guardrail.prepare(SOURCE, with_context=True, with_contrasts=True)
        self.assertEqual(p["version"], 6)
        self.assertEqual([r["kind"] for r in p["claims"][0]["scope_rules"]],
                         ["resumption", "hypothesis", "contrast"])

    def test_version_gate_and_source(self):
        p = packet()
        p["version"] = 5
        with self.assertRaisesRegex(guardrail.PacketError, "version 6"):
            guardrail.check(SOURCE, p)
        p["version"] = 6
        p["claims"][0]["scope_rules"][0]["source"] = "unquoted assertion"
        self.assertIn("verbatim source wording missing", " ".join(guardrail.check(SOURCE, p)))

    def test_alert_locations_and_human_review(self):
        for lang, sentence in [("en", "Smoothness alone guarantees balance."),
                               ("es", "La suavidad por sí sola garantiza el equilibrio.")]:
            with self.subTest(lang=lang):
                p = packet()
                p["versions"][lang][0]["text"] += " " + sentence
                check = run_cli("check", p)
                self.assertEqual(check.returncode, 1)
                receipt = json.loads(check.stdout)
                finding, = receipt["scope_findings"]
                self.assertEqual((finding["language"], finding["sentence"], finding["kind"]),
                                 (lang, 2, "contrast"))
                self.assertEqual(receipt["human_review"], "pending")
                self.assertEqual(receipt["scope_group_checks"], [])
                self.assertIn("declared_claim_contrasts", receipt["checked"])
                self.assertEqual(run_cli("render", p, "--language", lang).returncode, 1)

    def test_faithful_copy_and_legacy_receipt(self):
        p = packet()
        original = p["versions"]["en"][0]["text"]
        self.assertIn(original, run_cli("render", p, "--language", "en").stdout)
        legacy = copy.deepcopy(p)
        legacy["version"] = 5
        legacy["claims"][0].pop("scope_rules")
        self.assertNotIn("scope_group_checks", json.loads(run_cli("check", legacy).stdout))
