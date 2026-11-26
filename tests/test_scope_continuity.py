"""End-to-end invariants for scientific wordings in a bounded reading context."""

import copy
import unittest

from tests.test_scope import SOURCE, force_packet, run_cli
import guardrail


def add_segment(packet, number):
    key = f"C{number}"
    packet["claims"].append({
        "id": key, "status": "reported", "quote": "The force balances the spring.",
        "evidence": "Teaching note", "anchors": [{"source": "spring", "en": "spring", "es": "resorte"}],
    })
    for lang, text in (("en", "We observe the spring."), ("es", "Observamos el resorte.")):
        packet["versions"][lang].append({"claim": key, "text": text})


class ScopeContinuityChecks(unittest.TestCase):
    # Each cell of this finite grid has an expected result defined by the
    # assertion or disclaimer. Typography and sentence order are varied
    # independently. No NLP output supplies the expected labels.
    def test_bilingual_edit_grid(self):
        language_pairs = {
            "en": ("The theorem does not claim that any smooth force works.",
                   "The theorem claims that any smooth force works.",
                   "This holds in all cases."),
            "es": ("El teorema no afirma que cualquier fuerza suave funcione.",
                   "El teorema afirma que cualquier fuerza suave funciona.",
                   "Esto vale en todos los casos."),
        }
        for lang, (caveat, overclaim, restatement) in language_pairs.items():
            for first, second, expect_alert in (
                (caveat, caveat, False), (overclaim, caveat, True),
                (caveat, overclaim, True), (caveat, restatement, True),
            ):
                for case in (str.upper, str.lower):
                    for space in (" ", "  ", "\n"):
                        with self.subTest(lang=lang, first=first, second=second, case=case, space=space):
                            p = force_packet()
                            s = p["versions"][lang][0]
                            s["text"] += " " + case(first + " " + second).replace(" ", space)
                            self.assertEqual(bool(guardrail.check(SOURCE, p)), expect_alert)

    def test_cross_claim_uses_display_order_and_names_source_and_location(self):
        p = force_packet()
        add_segment(p, 2)
        s = p["versions"]["es"][1]
        s["text"] = "Esto vale en todos los casos. " + s["text"]
        issues = guardrail.check(SOURCE, p)
        self.assertEqual(len(issues), 1, issues)
        self.assertIn("es/C2 sentence 1", issues[0])
        self.assertIn("C1 existential", issues[0])
        p["versions"]["es"].reverse()
        self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_lookback_ends_at_paragraph_unscoped_sentence_or_intervening_claim(self):
        original = force_packet()
        add_segment(original, 2)
        add_segment(original, 3)
        for index, new_paragraph, text in [
            (1, True, "This holds in all cases. We observe the spring."),
            (1, False, "We observe the spring. This holds in all cases."),
            (2, False, "This holds in all cases. We observe the spring."),
        ]:
            with self.subTest(index=index, new_paragraph=new_paragraph, text=text):
                p = copy.deepcopy(original)
                p["versions"]["en"][index].update(text=text, new_paragraph=new_paragraph)
                self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_multiple_possible_antecedents_reported_together_in_one_language(self):
        p = force_packet()
        raw = SOURCE + b" We chose one spring."
        p["source_sha256"] = guardrail.digest(raw)
        p["claims"][0]["existentials"].append({
            "source": "We chose one spring.", "en": {"referents": ["spring"], "witnesses": ["one spring"]},
            "es": {"referents": ["resorte"], "witnesses": ["un resorte"]},
        })
        for lang, more in (("es", "Se eligió un resorte."), ("en", "We chose one spring.")):
            p["versions"][lang][0]["text"] += " " + more
        add_segment(p, 2)
        p["versions"]["es"][1]["text"] = "Esto vale en todos los casos. Observamos el resorte."
        issues = guardrail.check(raw, p)
        self.assertEqual(len(issues), 1, issues)
        for name in ("C1 existential 1", "C1 existential 2"):
            self.assertIn(name, issues[0])

    def test_disclaimer_is_not_a_positive_witness_and_a_later_witness_counts(self):
        p = force_packet()
        s = p["versions"]["en"][0]
        s["text"] = "The theorem does not claim that a smooth force balances the spring."
        self.assertTrue(any("accepted existential wording missing" in i for i in guardrail.check(SOURCE, p)))
        s["text"] += " We construct a smooth force that balances the spring."
        self.assertEqual(guardrail.check(SOURCE, p), [])

    def test_cli_render_only_emits_the_accepted_text(self):
        p = force_packet()
        p["versions"]["es"][0]["text"] += " El teorema no afirma que cualquier fuerza suave funcione."
        good = run_cli("render", p, "--language", "es")
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn("no afirma", good.stdout)
        p["versions"]["es"][0]["text"] += " La primera frase puede reforzarse a una afirmación universal."
        bad = run_cli("render", p, "--language", "es")
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(bad.stdout, "")
        self.assertIn("universal restatement", bad.stderr)
