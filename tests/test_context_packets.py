"""Bilingual end-to-end regression for the two version 5 context checks."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import guardrail
from tests.test_scope import ROOT, SOURCE, force_packet, run_cli
from tests.test_scope_continuity import add_segment
from tests.test_scope_hypotheses import RULE
from tests.test_scope_resumption import EXAMPLE, QUESTION


def fixture(*rules):
    p = force_packet()
    p["version"] = 5
    c = p["claims"][0]
    del c["existentials"]
    c["scope_rules"] = [dict(copy.deepcopy(r), source=c["quote"]) for r in rules]
    return p


class ContextPackets(unittest.TestCase):
    def test_scaffold_combines_flags_and_preserves_prior_versions(self):
        for flags, version, kinds in [
            (["--with-antecedents"], 3, []), (["--with-properties"], 4, ["relation"]),
            (["--with-context"], 5, ["resumption", "hypothesis"]),
            (["--with-properties","--with-context"], 5, ["relation","resumption","hypothesis"]),
        ]:
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp)/"source.txt"
                src.write_bytes(SOURCE)
                out = subprocess.check_output([sys.executable,"-B",str(ROOT/"guardrail.py"),"prepare",str(src),*flags])
                packet = json.loads(out)
                self.assertEqual(packet["version"],version)
                self.assertEqual([r["kind"] for r in packet["claims"][0].get("scope_rules", [])],kinds)

    def test_schema_and_source_are_checked_even_when_no_wording_matches(self):
        for r in (EXAMPLE, RULE):
            p = fixture(r)
            p["version"] = 4
            self.assertEqual(run_cli("check", p).returncode, 2)
            p["version"] = 5
            p["claims"][0]["scope_rules"][0]["source"] = "A missing quotation."
            self.assertEqual(run_cli("check",p).returncode, 1)
            del p["claims"][0]["scope_rules"][0]["en"]
            self.assertEqual(run_cli("check",p).returncode, 2)

    def test_local_example_and_open_question_keep_their_own_antecedent(self):
        for lang, rule, extension in (
            ("es", EXAMPLE, "Esto vale para todas las baldosas."),
            ("en", QUESTION, "This is guaranteed for every angle."),
        ):
            p = fixture(EXAMPLE,QUESTION)
            part = p["versions"][lang][0]
            part["text"] += " " + rule[lang]["witnesses"][0] + " " + extension
            receipt = json.loads(run_cli("check",p).stdout)
            row, = receipt["scope_findings"]
            self.assertEqual((row["kind"],row["rule_claim"],row["witness_sentence"],row["sentence"]),
                             ("resumption","C1",2,3))
            self.assertEqual(row["rule"], 1 if rule is EXAMPLE else 2)
            self.assertIn("declared_property_resumptions", receipt["checked"])
            self.assertFalse(any("hypothesis_removals" in k for k in receipt["checked"]))

    def test_explicit_link_can_cross_paragraphs_but_other_mentions_cannot(self):
        p = fixture(EXAMPLE)
        p["versions"]["en"][0]["text"] += " It has six sides."
        add_segment(p,2)
        part = p["versions"]["en"][1]
        part.update(text="We inspect the spring. This also holds for all tiles.",new_paragraph=True)
        self.assertEqual(guardrail.check(SOURCE,p),[])
        part["antecedents"]=[{"sentence":2,"claim":"C1","mention":"tiles"}]
        self.assertEqual(guardrail.check(SOURCE,p),[])
        part["antecedents"][0]["mention"]="This"
        r=json.loads(run_cli("check",p).stdout)
        f,=r["scope_findings"]
        self.assertEqual((f["claim"],f["rule_claim"],f["witness_sentence"]),("C2","C1",2))
        self.assertEqual(len(r["issues"]),1)

    def test_a_link_to_a_claim_with_two_witnessed_properties_does_not_select_one(self):
        p=fixture(EXAMPLE,QUESTION)
        p["versions"]["en"][0]["text"]+=" It has six sides. Would one index suffice?"
        add_segment(p,2)
        p["versions"]["en"][1].update(text="We observe the spring. This is guaranteed for every angle.",
                                      new_paragraph=True,antecedents=[{"sentence":2,"claim":"C1","mention":"This"}])
        self.assertEqual(guardrail.check(SOURCE,p),[])

    def test_direct_hypothesis_issue_is_attributed_to_its_sentence_only(self):
        p=fixture(RULE)
        p["versions"]["es"][0]["text"]+=" La estimación se cumple sin regularidad."
        r=json.loads(run_cli("check",p).stdout)
        f,=r["scope_findings"]
        self.assertEqual((f["kind"],f["language"],f["sentence"]),("hypothesis","es",2))
        self.assertNotIn("witness_sentence",f)
        self.assertEqual(run_cli("render",p,"--language","es").returncode,1)
        p["versions"]["es"][0]["text"]+=" La hipótesis aparece en la fuente."
        self.assertEqual(len(guardrail.check(SOURCE,p)),1)
