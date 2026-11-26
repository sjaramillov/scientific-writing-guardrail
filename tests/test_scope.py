"""Regression tests for the optional bilingual existential-scope check."""

import copy
import json
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

import guardrail


ROOT = Path(__file__).resolve().parents[1]
SCOPE_CHECK = "declared_existential_scope_wording"
SOURCE = b"We construct a smooth force. The force balances the spring."


def force_packet():
    packet = guardrail.prepare(SOURCE)
    packet.update(version=2, audience="Bilingual editors", assistance="Synthetic test case")
    packet["claims"][0].update(
        status="reported", evidence="Teaching note, example 1",
        quote="The force balances the spring.",
        anchors=[{"source": "spring", "en": "spring", "es": "resorte"}],
        existentials=[{
            "source": "We construct a smooth force",
            "en": {
                "referents": ["smooth force", "force"],
                "witnesses": ["a smooth force", "one particular force"],
            },
            "es": {
                "referents": ["fuerza suave", "fuerza"],
                "witnesses": ["una fuerza suave", "una fuerza específica"],
            },
        }],
    )
    packet["versions"]["en"][0]["text"] = "For every trial, a smooth force balances the spring."
    packet["versions"]["es"][0]["text"] = "En cada ensayo, una fuerza suave equilibra el resorte."
    return packet


def run_cli(command, packet, *options):
    with tempfile.TemporaryDirectory() as directory:
        source_path = Path(directory) / "source.txt"
        packet_path = Path(directory) / "packet.json"
        source_path.write_bytes(SOURCE)
        packet_path.write_text(json.dumps(packet), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(ROOT / "guardrail.py"), command,
             str(source_path), str(packet_path), *options],
            capture_output=True, text=True,
        )


class ExistentialScopeChecks(unittest.TestCase):
    def test_prepare_only_creates_a_scope_scaffold_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.txt"
            source_path.write_bytes(SOURCE)
            for options, expected in [([], 1), (["--with-scope"], 2)]:
                with self.subTest(options=options):
                    run = subprocess.run(
                        [sys.executable, str(ROOT / "guardrail.py"), "prepare", *options, str(source_path)],
                        capture_output=True, text=True, check=True,
                    )
                    packet = json.loads(run.stdout)
                    self.assertEqual(packet["version"], expected)
                    self.assertEqual("existentials" in packet["claims"][0], expected == 2)
                    with self.assertRaises(guardrail.PacketError):
                        guardrail.check(SOURCE, packet)

    def test_each_approved_witness_passes_with_other_quantified_subjects(self):
        packet = force_packet()
        self.assertEqual(guardrail.check(SOURCE, packet), [])
        packet["versions"]["en"][0]["text"] = "In every trial one particular force balances the spring."
        packet["versions"]["es"][0]["text"] = "En cualquier ensayo una fuerza específica equilibra el resorte."
        self.assertEqual(guardrail.check(SOURCE, packet), [])

    def test_prefix_or_postfix_universal_is_reported_even_when_witness_survives(self):
        conflicting = [
            ("es", "Luego sirve una fuerza suave cualquiera."),
            ("es", "Luego sirve cualquier fuerza suave."),
            ("en", "Then any smooth force works."),
            ("en", "Then every force works."),
        ]
        for lang, added in conflicting:
            with self.subTest(lang=lang, added=added):
                packet = force_packet()
                packet["versions"][lang][0]["text"] += " " + added
                issues = guardrail.check(SOURCE, packet)
                self.assertTrue(any(f"{lang}/C1" in issue for issue in issues), issues)

    def test_whole_set_and_any_selection_are_distinct_from_every_set(self):
        raw = b"We exhibit an infinite set of points."
        packet = force_packet()
        packet["source_sha256"] = guardrail.digest(raw)
        packet["claims"][0].update(
            quote=raw.decode(),
            anchors=[{"source": "points", "en": "points", "es": "puntos"}],
            existentials=[{
                "source": "We exhibit an infinite set",
                "en": {"referents": ["infinite set"], "witnesses": ["an infinite set"]},
                "es": {"referents": ["conjunto infinito"], "witnesses": ["un conjunto infinito"]},
            }],
        )
        packet["versions"]["en"][0]["text"] = (
            "We exhibit an infinite set of points. Any selection may be smaller than the whole set."
        )
        packet["versions"]["es"][0]["text"] = (
            "Existe un conjunto infinito de puntos. Cualquier selección puede ser menor que todo el conjunto infinito."
        )
        self.assertEqual(guardrail.check(raw, packet), [])
        for lang, generalization in [
            ("es", "Esto se cumple para todo conjunto infinito."),
            ("en", "This holds for every infinite set."),
        ]:
            with self.subTest(lang=lang):
                changed = copy.deepcopy(packet)
                changed["versions"][lang][0]["text"] += " " + generalization
                issues = guardrail.check(raw, changed)
                self.assertTrue(any(f"{lang}/C1" in issue for issue in issues), issues)

    def test_missing_target_witness_is_reported_without_a_universal_marker(self):
        packet = force_packet()
        packet["versions"]["en"][0]["text"] = "The spring is balanced."
        issues = guardrail.check(SOURCE, packet)
        self.assertTrue(any("en/C1" in issue for issue in issues), issues)

    def test_normalized_scope_terms_remain_distinct_from_literal_anchors(self):
        packet = force_packet()
        variant = unicodedata.normalize("NFD", "UNA  FUERZA ESPECÍFICA")
        packet["versions"]["es"][0]["text"] = f"{variant} equilibra el resorte."
        self.assertEqual(guardrail.check(SOURCE, packet), [])
        packet["versions"]["es"][0]["text"] += " Funciona CUALQUIER   FUERZA."
        issues = guardrail.check(SOURCE, packet)
        self.assertTrue(any("es/C1" in issue for issue in issues), issues)

    def test_source_witness_is_checked_against_the_full_frozen_source(self):
        packet = force_packet()
        rule = packet["claims"][0]["existentials"][0]
        self.assertNotIn(rule["source"], packet["claims"][0]["quote"])
        self.assertEqual(guardrail.check(SOURCE, packet), [])
        rule["source"] = "we construct a smooth force"
        issues = guardrail.check(SOURCE, packet)
        self.assertTrue(any("C1" in issue for issue in issues), issues)

    def test_malformed_scope_data_is_rejected(self):
        packet = force_packet()
        rule = packet["claims"][0]["existentials"][0]
        for bad in [None, "en", {}, True,
                    {"referents": [], "witnesses": ["a force"]},
                    {"referents": ["force"], "witnesses": []},
                    {"referents": ["force"], "witnesses": ["an enforcer"]},
                    {"referents": "force", "witnesses": ["a force"]},
                    {"referents": ["force"], "witnesses": [False]}]:
            with self.subTest(bad=bad):
                rule["en"] = bad
                with self.assertRaises(guardrail.PacketError):
                    guardrail.check(SOURCE, packet)

    def test_version_one_rejects_the_reserved_field(self):
        packet = force_packet()
        packet["version"] = 1
        with self.assertRaises(guardrail.PacketError):
            guardrail.check(SOURCE, packet)

    def test_receipt_only_lists_scope_check_when_rules_were_used(self):
        packet = force_packet()
        rules = packet["claims"][0].pop("existentials")
        for version, count in [(1, 0), (2, 0), (2, 1)]:
            with self.subTest(version=version, rules=count):
                packet["version"] = version
                if count:
                    packet["claims"][0]["existentials"] = rules
                run = run_cli("check", packet)
                self.assertEqual(run.returncode, 0, run.stdout)
                result = json.loads(run.stdout)
                self.assertEqual(result["human_review"], "pending")
                self.assertEqual(result["existential_scope_rules"], count)
                self.assertEqual(SCOPE_CHECK in result["checked"], bool(count))
        packet["claims"][0]["existentials"] = []
        self.assertEqual(guardrail.check(SOURCE, packet), [])

    def test_rejected_scope_change_withholds_render_in_both_languages(self):
        packet = force_packet()
        packet["versions"]["es"][0]["text"] += " Esto vale para una fuerza cualquiera."
        check = run_cli("check", packet)
        self.assertEqual(check.returncode, 1, check.stdout)
        receipt = json.loads(check.stdout)
        self.assertEqual(receipt["result"], "revise")
        self.assertTrue(any("es/C1" in issue for issue in receipt["issues"]), receipt)
        for language in ("en", "es"):
            with self.subTest(language=language):
                render = run_cli("render", packet, "--language", language)
                self.assertEqual(render.returncode, 1, render.stderr)
                self.assertEqual(render.stdout, "")
                self.assertEqual(json.loads(render.stderr), receipt)


if __name__ == "__main__":
    unittest.main()
