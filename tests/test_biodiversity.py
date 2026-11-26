"""Check the teaching passage and its two intentionally different failure modes."""
import copy
import json
import unittest
from pathlib import Path

import guardrail


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "biodiversity"


class BiodiversityExample(unittest.TestCase):
    def setUp(self):
        self.source = (EXAMPLE / "source.txt").read_bytes()
        self.packet = json.loads((EXAMPLE / "packet.json").read_text(encoding="utf-8"))

    def test_example_checks_and_each_edition_explains_the_limitation(self):
        self.assertEqual(guardrail.check(self.source, self.packet), [])
        for lang, expected in (("en", "species"), ("es", "especies")):
            with self.subTest(language=lang):
                result = guardrail.render_draft(self.packet, lang, "test-hash", True)
                self.assertIn(expected, result)
                self.assertIn("[C1]", result)
                self.assertIn("[C2]", result)

    def test_missing_count_is_reported(self):
        part = self.packet["versions"]["es"][0]
        part["text"] = part["text"].replace("12", "13")
        issues = guardrail.check(self.source, self.packet)
        self.assertTrue(any("es/C1" in issue for issue in issues))

    def test_reversed_counts_require_semantic_review(self):
        changed = copy.deepcopy(self.packet)
        part = changed["versions"]["es"][0]
        part["text"] = part["text"].replace("12 registros", "3 registros").replace("3 parcelas", "12 parcelas")
        self.assertNotEqual(part["text"], self.packet["versions"]["es"][0]["text"])
        self.assertEqual(guardrail.check(self.source, changed), [])
