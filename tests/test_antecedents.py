"""Explicit links identify a particular occurrence and an earlier displayed claim."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import guardrail
from tests.test_scope import ROOT, SOURCE, force_packet, run_cli
from tests.test_scope_continuity import add_segment


def linked_packet(lang="es", *, target="C1", sentence=2, mention=None, text=None):
    packet = force_packet()
    packet["version"] = 3
    add_segment(packet, 2)
    add_segment(packet, 3)
    default_text = {
        "en": "We observe the spring. This holds in all cases.",
        "es": "Observamos el resorte. Esto vale en todos los casos.",
    }
    if mention is None:
        mention = {"en": "This", "es": "Esto"}[lang]
    part = packet["versions"][lang][2]
    part.update(text=default_text[lang] if text is None else text, new_paragraph=True,
                antecedents=[{"sentence": sentence, "mention": mention, "claim": target}])
    return packet


class AntecedentChecks(unittest.TestCase):
    def test_link_reaches_across_intervening_claim_and_paragraph_in_each_language(self):
        for lang in ("en", "es"):
            with self.subTest(lang=lang):
                packet = linked_packet(lang)
                issues = guardrail.check(SOURCE, packet)
                self.assertTrue(any(f"{lang}/C3" in x and "C1" in x for x in issues), issues)
                del packet["versions"][lang][2]["antecedents"]
                self.assertEqual(guardrail.check(SOURCE, packet), [])

    def test_linked_disclaimer_passes_and_receipt_identifies_the_occurrence(self):
        for lang, sentence, mention in (
            ("en", "We observe the spring. The theorem does not claim that this holds in all cases.", "this"),
            ("es", "Observamos el resorte. El teorema no afirma que esto valga en todos los casos.", "esto"),
        ):
            with self.subTest(lang=lang):
                p = linked_packet(lang, text=sentence, mention=mention)
                run = run_cli("check", p)
                self.assertEqual(run.returncode, 0, run.stdout)
                result = json.loads(run.stdout)
                self.assertEqual(result["resolved_antecedents"], [
                    {"language": lang, "from_claim": "C3", "sentence": 2, "mention": mention, "to_claim": "C1"}
                ])
                rendered = run_cli("render", p, "--language", lang, "--with-notes")
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                self.assertIn(sentence, rendered.stdout)
                self.assertNotIn("resolved_antecedents", rendered.stdout)

    def test_link_to_unclassified_scope_requires_review_for_a_generalization(self):
        p = linked_packet(target="C2")
        issues = guardrail.check(SOURCE, p)
        self.assertTrue(any("es/C3" in x and "C2" in x for x in issues), issues)
        p["versions"]["es"][2]["text"] = "Observamos el resorte. Esto describe la construcción."
        self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_annotating_a_different_mention_does_not_bind_the_generalization(self):
        p = linked_packet(mention="Eso", text="Observamos el resorte. Eso describe el ensayo, pero esto vale en todos los casos.")
        self.assertEqual(guardrail.check(SOURCE, p), [])
        p["versions"]["es"][2]["antecedents"][0]["mention"] = "esto"
        issues = guardrail.check(SOURCE, p)
        self.assertTrue(any("es/C3" in x and "C1" in x for x in issues), issues)

    def test_reference_order_comes_from_its_own_edition(self):
        p = linked_packet()
        p["versions"]["en"].reverse()
        self.assertTrue(guardrail.check(SOURCE, p))
        p["versions"]["es"].reverse()
        with self.assertRaises(guardrail.PacketError):
            guardrail.check(SOURCE, p)

    def test_two_disjoint_mentions_use_their_own_target_in_one_sentence(self):
        p = linked_packet(text="Observamos el resorte. Esto vale en todos los casos, pero eso vale en todos los casos.")
        p["versions"]["es"][2]["antecedents"].append({"sentence": 2, "mention": "eso", "claim": "C2"})
        run = run_cli("check", p)
        self.assertEqual(run.returncode, 1, run.stdout)
        r = json.loads(run.stdout)
        self.assertCountEqual(
            [(a["mention"], a["to_claim"]) for a in r["resolved_antecedents"]],
            [("Esto", "C1"), ("eso", "C2")],
        )
        issues = r["issues"]
        self.assertEqual(len(issues), 2, issues)
        self.assertTrue(any("esto vale" in i and "C1" in i and "C2" not in i for i in issues))
        self.assertTrue(any("eso vale" in i and "C2" in i and "C1" not in i for i in issues))

    def test_sentence_number_disambiguates_identical_mentions_in_two_sentences(self):
        p = linked_packet(text="Esto describe el resorte. Esto vale en todos los casos.")
        issues = guardrail.check(SOURCE, p)
        self.assertTrue(any("C1" in i and "es/C3" in i for i in issues), issues)
        p["versions"]["es"][2]["antecedents"][0]["sentence"] = 1
        self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_unknown_self_duplicate_and_overlapping_references_are_invalid(self):
        for target in ("C99", "C3"):
            with self.subTest(target=target), self.assertRaises(guardrail.PacketError):
                guardrail.check(SOURCE, linked_packet(target=target))
        for other in ("Esto", "Esto vale"):
            p = linked_packet()
            p["versions"]["es"][2]["antecedents"].append({"sentence": 2, "mention": other, "claim": "C2"})
            with self.subTest(other=other), self.assertRaises(guardrail.PacketError):
                guardrail.check(SOURCE, p)

    def test_invalid_index_and_reference_shape_are_input_errors(self):
        for row in (
            {"sentence": 0, "mention": "Esto", "claim": "C1"},
            {"sentence": True, "mention": "Esto", "claim": "C1"},
            {"sentence": "2", "mention": "Esto", "claim": "C1"},
            {"sentence": 2, "mention": "", "claim": "C1"},
            {"sentence": 2, "mention": "Esto"},
        ):
            p = linked_packet()
            p["versions"]["es"][2]["antecedents"] = [row]
            with self.subTest(row=row), self.assertRaises(guardrail.PacketError):
                guardrail.check(SOURCE, p)

    def test_unlocatable_edits_leave_no_resolved_reference_and_withhold_render(self):
        for p in [
            linked_packet(sentence=3),
            linked_packet(mention="Eso"),
            linked_packet(text="Observamos el resorte. Esto y Esto describen la construcción."),
            linked_packet(mention="Esto", text="Observamos el resorte. Estos casos son distintos."),
        ]:
            with self.subTest(segment=p["versions"]["es"][2]):
                check = run_cli("check", p)
                self.assertEqual(check.returncode, 1, check.stdout)
                self.assertEqual(json.loads(check.stdout)["resolved_antecedents"], [])
                render = run_cli("render", p, "--language", "es")
                self.assertEqual(render.returncode, 1)
                self.assertEqual(render.stdout, "")

    def test_older_packets_reject_links_and_keep_their_original_receipt_schema(self):
        for version in (1, 2):
            with self.subTest(version=version):
                p = linked_packet()
                p["version"] = version
                if version == 1:
                    del p["claims"][0]["existentials"]
                with self.assertRaises(guardrail.PacketError):
                    guardrail.check(SOURCE, p)
                del p["versions"]["es"][2]["antecedents"]
                run = run_cli("check", p)
                self.assertEqual(run.returncode, 0, run.stdout)
                self.assertNotIn("resolved_antecedents", json.loads(run.stdout))

    def test_prepare_selects_the_requested_schema(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "source.txt"
            source.write_bytes(SOURCE)
            for options, version in (([], 1), (["--with-scope"], 2), (["--with-antecedents"], 3)):
                with self.subTest(options=options):
                    result = subprocess.run([sys.executable, str(ROOT / "guardrail.py"), "prepare",
                                             *options, str(source)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["version"], version)
