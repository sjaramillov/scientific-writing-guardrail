"""Checks for the public teaching packet and the limits of literal preservation."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import guardrail


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "riemann" / "source.txt"
PACKET = SOURCE.with_name("packet.json")


class PacketChecks(unittest.TestCase):
    def setUp(self):
        self.raw = SOURCE.read_bytes()
        self.packet = json.loads(PACKET.read_text(encoding="utf-8"))

    def test_example_is_ready_for_review_with_matching_hashes(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "guardrail.py"), "check", str(SOURCE), str(PACKET)],
            capture_output=True, text=True, check=True,
        )
        result = json.loads(run.stdout)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["result"], "ready_for_human_review")
        self.assertEqual(result["human_review"], "pending")
        self.assertEqual(result["checker_version"], "0.1.0")
        self.assertIn("verbatim_quotes_in_source", result["checked"])
        self.assertIn("evidence_authenticity_or_support", result["not_assessed"])
        self.assertIn("semantic_equivalence_including_quantity_referents", result["not_assessed"])
        self.assertIn("grammar_and_reader_comprehension", result["not_assessed"])
        self.assertEqual(result["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(result["packet_sha256"], hashlib.sha256(PACKET.read_bytes()).hexdigest())

    def test_incomplete_scaffold_requires_an_editor(self):
        scaffold = guardrail.prepare(self.raw)
        self.assertEqual(scaffold["source_sha256"], self.packet["source_sha256"])
        with self.assertRaises(guardrail.PacketError):
            guardrail.check(self.raw, scaffold)

    def test_structural_fields_are_required(self):
        for key, bad_value in [("version", True), ("audience", ""), ("assistance", None),
                               ("claims", []), ("versions", {"en": []})]:
            with self.subTest(key=key):
                packet = dict(self.packet, **{key: bad_value})
                with self.assertRaises(guardrail.PacketError):
                    guardrail.check(self.raw, packet)
        self.packet["claims"][0]["status"] = "peer-approved-by-model"
        with self.assertRaises(guardrail.PacketError):
            guardrail.check(self.raw, self.packet)

    def test_bytes_change_even_when_all_claims_survive(self):
        issues = guardrail.check(self.raw + b"\n", self.packet)
        self.assertEqual(issues, ["Source SHA-256 differs from the frozen source."])

    def test_each_declared_quantity_and_qualifier_needs_its_expression(self):
        changes = [
            ("en", "every", "some"),
            ("en", "nontrivial", "trivial"),
            ("en", "1/2", "1/20"),
            ("es", "cada", "algún"),
            ("es", "no trivial", "trivial"),
            ("es", "exactamente", "aproximadamente"),
        ]
        for lang, protected, replacement in changes:
            with self.subTest(lang=lang, protected=protected):
                packet = copy.deepcopy(self.packet)
                part = packet["versions"][lang][0]
                part["text"] = part["text"].replace(protected, replacement)
                issues = guardrail.check(self.raw, packet)
                self.assertEqual(len(issues), 1, issues)
                self.assertIn(f"{lang}/C1", issues[0])

    def test_a_claim_missing_from_one_language_is_flagged(self):
        self.packet["versions"]["es"].pop()
        self.assertIn("es/C3: claim missing.", guardrail.check(self.raw, self.packet))

    def test_numbers_have_exact_signs_precision_and_boundaries(self):
        for text, term in [("−1/2", "1/2"), ("12.5%", "5%"), ("1/20", "1/2")]:
            with self.subTest(text=text, term=term):
                self.assertFalse(guardrail.contains_term(text, term))
        self.assertTrue(guardrail.contains_term("The estimate was 12.5.", "12.5"))

    def test_numeric_alias_rejected_even_without_explicit_invariant(self):
        anchor = next(a for a in self.packet["claims"][0]["anchors"] if a["source"] == "1/2")
        anchor.pop("invariant")
        anchor["es"] = "2/3"
        part = self.packet["versions"]["es"][0]
        part["text"] = part["text"].replace("1/2", "2/3")
        self.assertTrue(any("fixed literal changed" in issue
                            for issue in guardrail.check(self.raw, self.packet)))

    def test_symbolic_ids_can_be_declared_invariant(self):
        anchor = next(a for a in self.packet["claims"][1]["anchors"] if a["source"] == "Lean FRO")
        anchor.update(invariant=True, es="FRO2")
        part = self.packet["versions"]["es"][1]
        part["text"] = part["text"].replace("Lean FRO", "FRO2")
        self.assertTrue(any("fixed literal changed" in issue
                            for issue in guardrail.check(self.raw, self.packet)))

    def test_render_emits_only_the_requested_checked_draft(self):
        for lang, title in [("en", "Draft for human review"), ("es", "Borrador para revisión humana")]:
            with self.subTest(language=lang):
                run = subprocess.run(
                    [sys.executable, str(ROOT / "guardrail.py"), "render", str(SOURCE), str(PACKET),
                     "--language", lang], capture_output=True, text=True, check=True,
                )
                body = " ".join(p["text"] for p in self.packet["versions"][lang])
                self.assertEqual(run.stdout, title + "\n\n" + body + "\n")
                self.assertEqual(run.stderr, "")

    def test_shareable_draft_uses_claim_markers_statuses_and_paragraphs(self):
        self.packet["versions"]["es"][1]["new_paragraph"] = True
        rendered = guardrail.render_draft(self.packet, "es", "digest", True)
        self.assertIn("[C1]\n\n", rendered)
        self.assertIn("[C2] reportado", rendered)
        self.assertIn("registro de asistencia editorial", rendered)
        self.assertNotIn(self.packet["assistance"], rendered)
        self.assertNotIn(self.packet["claims"][0]["evidence"], rendered)
        self.assertIn("SHA-256 · digest", rendered)

    def test_external_notes_only_publish_explicit_doi_in_both_languages(self):
        self.packet["assistance"] = "Private working group: EXAMPLE-17"
        self.packet["audience"] = "unpublished reviewer list"
        self.packet["internal_notes"] = "fictional reviewer contact"
        for claim in self.packet["claims"]:
            claim["evidence"] = "/private/synthetic/worksheet and DOI 10.1234/private.1"
            claim["internal_notes"] = "fictional embargo"
        self.packet["claims"][0]["public_doi"] = "10.1234/example.1"
        with tempfile.TemporaryDirectory() as private_dir:
            packet = Path(private_dir) / "packet.json"
            packet.write_text(json.dumps(self.packet), encoding="utf-8")
            for lang in ("en", "es"):
                with self.subTest(language=lang):
                    run = subprocess.run(
                        [sys.executable, str(ROOT / "guardrail.py"), "render", str(SOURCE), str(packet),
                         "--language", lang, "--with-notes"], capture_output=True, text=True, check=True,
                    )
                    self.assertIn("[C1] formal · https://doi.org/10.1234/example.1", run.stdout)
                    self.assertIn(hashlib.sha256(packet.read_bytes()).hexdigest(), run.stdout)
                    self.assertEqual(run.stderr, "")
                    for internal in ("EXAMPLE-17", "unpublished reviewer", "fictional", "/private/", "10.1234/private.1"):
                        self.assertNotIn(internal, run.stdout)

    def test_public_doi_rejects_free_text_urls_and_private_metadata(self):
        for value in (None, "", "/private/private.txt", "https://doi.org/10.1234/name",
                      "10.1234/public\nprivate notes", "10.1234/item?reviewer=private", "10.1234/../private"):
            with self.subTest(value=value):
                self.packet["claims"][0]["public_doi"] = value
                with self.assertRaises(guardrail.PacketError):
                    guardrail.check(self.raw, self.packet)

    def test_v1_receipt_does_not_assess_which_noun_a_number_modifies(self):
        raw = b"The register contains 12 records from 3 sites."
        packet = guardrail.prepare(raw)
        packet.update(audience="Bilingual reviewers", assistance="Fictional worked example")
        packet["claims"][0].update(status="reported", evidence="Synthetic register",
                                   anchors=[{"source": n, "en": n, "es": n} for n in ("12", "3")])
        packet["versions"]["en"][0]["text"] = raw.decode()
        packet["versions"]["es"][0]["text"] = "El registro contiene 3 registros de 12 sitios."
        self.assertEqual(guardrail.check(raw, packet), [])
        self.assertIn("semantic_equivalence_including_quantity_referents", guardrail.NOT_ASSESSED)

    def test_render_withholds_text_when_an_anchor_is_missing(self):
        self.packet["versions"]["en"][0]["text"] = "Only this sentence survives."
        with tempfile.TemporaryDirectory() as private_dir:
            invalid = Path(private_dir) / "revision.json"
            invalid.write_text(json.dumps(self.packet), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(ROOT / "guardrail.py"), "render", str(SOURCE), str(invalid),
                 "--language", "en"], capture_output=True, text=True, check=False,
            )
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stdout, "")
        self.assertEqual(json.loads(run.stderr)["result"], "revise")

    def test_quote_must_be_present_in_frozen_source(self):
        self.packet["claims"][0]["quote"] += " Extra material."
        self.assertIn("C1: verbatim source passage missing.", guardrail.check(self.raw, self.packet))

    def test_duplicate_claim_ids_and_duplicate_renderings_are_invalid(self):
        for target in [self.packet["claims"], self.packet["versions"]["es"]]:
            with self.subTest(field=list(target[0])):
                target.append(copy.deepcopy(target[0]))
                with self.assertRaises(guardrail.PacketError):
                    guardrail.check(self.raw, self.packet)
                target.pop()

    def test_cli_rejects_duplicate_json_properties_before_checking(self):
        with tempfile.TemporaryDirectory() as private_dir:
            invalid = Path(private_dir) / "duplicate.json"
            invalid.write_text('{"version":1,"version":1}', encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(ROOT / "guardrail.py"), "check", str(SOURCE), str(invalid)],
                capture_output=True, text=True, check=False,
            )
        result = json.loads(run.stdout)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(result["result"], "invalid_input")
        self.assertIn("Duplicate JSON property", result["error"])

    def test_false_prose_can_preserve_all_anchors(self):
        # The negation changes the meaning while retaining all protected terms.
        part = self.packet["versions"]["en"][0]
        part["text"] = part["text"].replace("The theorem says that", "The theorem denies that")
        self.assertIn("denies", part["text"])
        self.assertEqual(guardrail.check(self.raw, self.packet), [])


if __name__ == "__main__":
    unittest.main()
