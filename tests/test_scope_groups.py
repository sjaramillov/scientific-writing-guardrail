"""Directed counterfactuals for source-backed finite reference groups."""
import copy
import hashlib
import unittest

import guardrail
import scope_groups


DATA = "(-2,8,-2), (5,1,5), (9,0,9), (7,1,0)"
CATALOG = "Ordered observations: " + DATA + "."
QUOTE = "The first and last measurements of the first record (-2,8,-2) agree."
RAW = (CATALOG + "\n" + QUOTE).encode()
PROPERTIES = {"en": "outer measurements agree", "es": "medidas extremas coinciden"}
OBJECTS = {"en": ["record", "records"], "es": ["fila", "filas"]}
WITNESS = {"en": "Its outer measurements agree.", "es": "Sus medidas extremas coinciden."}
CLOSING = {"en": "This holds for each of the others.", "es": "Esto vale para cada una de las demás."}
NARROW = {"en": "the first three records", "es": "las tres primeras filas"}
WHOLE = {"en": "all four records", "es": "las cuatro filas"}
RESUMPTION = {"source": QUOTE, "kind": "resumption"}
GROUP = {"source": CATALOG, "kind": "finite_group"}
for language in ("en", "es"):
    RESUMPTION[language] = dict(mode="example", property=PROPERTIES[language],
                                objects=OBJECTS[language], parameters=[], witnesses=[WITNESS[language]])
    GROUP[language] = dict(property=PROPERTIES[language], objects=OBJECTS[language], equal_columns=[1, 3])


def passage(lang, domain=None, chosen="(-2,8,-2)"):
    group = domain or NARROW[lang]
    if lang == "en":
        body = (f"The ordered list is {DATA}. The reference group contains {group}. "
                'Here "the others" denotes only the other records in that group. '
                f"Choose the first record {chosen}.")
    else:
        body = (f"La lista ordenada es {DATA}. El grupo de referencia contiene {group}. "
                "Aquí «las demás» alude únicamente a las otras filas de dicho grupo. "
                f"Elegimos la primera fila {chosen}.")
    return body + " " + WITNESS[lang] + " " + CLOSING[lang]


def packet():
    return {"version": 6, "source_sha256": hashlib.sha256(RAW).hexdigest(),
            "audience": "Bilingual editors", "assistance": "Constructed software regression fixture.",
            "claims": [{"id": "C1", "quote": QUOTE, "evidence": "Ordered observations.",
                        "status": "observed", "anchors": [{"source": "(-2,8,-2)", "en": "(-2,8,-2)", "es": "(-2,8,-2)"}],
                        "scope_rules": copy.deepcopy([RESUMPTION, GROUP])}],
            "versions": {lang: [{"claim": "C1", "text": passage(lang)}] for lang in ("en", "es")}}


def check(item):
    audits, findings = [], []
    issues, _ = guardrail.evaluate(RAW, item, scope_findings=findings, scope_group_checks=audits)
    return issues, findings, audits


class GroupTests(unittest.TestCase):
    def test_witness_subset_and_counterexample_are_computed_in_both_editions(self):
        for lang in ("en", "es"):
            for domain, expected, failures in [(NARROW[lang], [2, 3], []), (WHOLE[lang], [2, 3, 4], [4]),
                                               ("(-2,8,-2), (9,0,9)", [3], []),
                                               ("(-2,8,-2), (7,1,0)", [4], [4])]:
                with self.subTest(lang=lang, domain=domain):
                    item = packet()
                    item["versions"][lang][0]["text"] = passage(lang, domain)
                    issues, findings, audits = check(item)
                    audit, = [a for a in audits if a["language"] == lang]
                    self.assertEqual((audit["selected_member"], audit["checked_members"], audit["failing_members"]),
                                     (1, expected, failures))
                    self.assertEqual(audit["equal_columns"], [1, 3])
                    self.assertEqual(audit["supported"], not failures)
                    self.assertEqual(len(issues), bool(failures))
                    self.assertEqual(len(findings), bool(failures))

    def test_unsupported_members_and_unbound_context_retain_alert(self):
        for lang in ("en", "es"):
            text = passage(lang)
            binding = {'en': '"the others"', 'es': '«las demás»'}[lang]
            cases = [
                text.replace(binding, "X"),
                text.replace("(5,1,5)", "(5,1,6)"),
                passage(lang, "(-2,8,-2), (9,0,10)"),
                passage(lang, "(-2,8,-2), (-2,8,-2)"),
                passage(lang, "the first 50 records" if lang == "en" else "las 50 primeras filas"),
                passage(lang, chosen="(9,0,9)"),
                text.replace(CLOSING[lang], "This holds for all records." if lang == "en" else "Esto vale para todas las filas."),
            ]
            for candidate in cases:
                with self.subTest(lang=lang, candidate=candidate):
                    item = packet()
                    item["versions"][lang][0]["text"] = candidate
                    issues, findings, audits = check(item)
                    self.assertEqual([f["language"] for f in findings], [lang])
                    self.assertFalse(any(a["language"] == lang for a in audits))
                    self.assertTrue(issues)

    def test_last_block_witness_is_itself_checked(self):
        for lang, domain, selected in [("en", "the last two records", "first record (9,0,9)"),
                                       ("es", "las dos últimas filas", "primera fila (9,0,9)")]:
            text = passage(lang, domain, "(9,0,9)")
            last = "last record (7,1,0)" if lang == "en" else "última fila (7,1,0)"
            item = packet()
            item["versions"][lang][0]["text"] = text.replace(selected, last)
            issues, _, audits = check(item)
            audit, = [a for a in audits if a["language"] == lang]
            self.assertFalse(audit["selected_member_satisfies"])
            self.assertFalse(audit["supported"])
            self.assertEqual(audit["failing_members"], [])
            self.assertTrue(issues)

    def test_missing_source_ambiguous_mapping_or_other_property_cannot_license_pass(self):
        for reason in ("changed-source", "ambiguous", "wrong-property", "unverified-source"):
            with self.subTest(reason=reason):
                item = packet()
                rules = item["claims"][0]["scope_rules"]
                if reason == "changed-source":
                    rules[1]["source"] = "Other inventory: " + DATA
                elif reason == "ambiguous":
                    rules.append(copy.deepcopy(rules[1]))
                elif reason == "wrong-property":
                    for lang in ("en", "es"):
                        rules[1][lang]["property"] = "other"
                else:
                    item["source_sha256"] = "0" * 64
                issues, findings, audits = check(item)
                self.assertEqual(len(findings), 2)
                self.assertTrue(issues)
                self.assertFalse(audits)

    def test_explicit_cross_paragraph_link_does_not_borrow_the_local_group(self):
        item = packet()
        second = dict(copy.deepcopy(item["claims"][0]), id="C2")
        item["claims"].append(second)
        for lang in ("en", "es"):
            # Both claims have the same label; the link explicitly points to C1.
            item["versions"][lang][0]["text"] = passage(lang).removesuffix(CLOSING[lang])
            item["versions"][lang].append({"claim": "C2", "new_paragraph": True, "text": passage(lang),
                                           "antecedents": [{"sentence": 6, "mention": CLOSING[lang].split()[0], "claim": "C1"}]})
        issues, findings, audits = check(item)
        self.assertEqual(len(issues), 2)
        self.assertEqual([(f["claim"], f["rule_claim"]) for f in findings], [("C2", "C1")] * 2)
        self.assertFalse(audits)

    def test_paragraph_break_inside_a_part_prevents_reusing_the_old_binding(self):
        for lang in ("en", "es"):
            item = packet()
            item["versions"][lang][0]["text"] = passage(lang).replace(" " + WITNESS[lang], "\n\n" + WITNESS[lang])
            _, findings, audits = check(item)
            self.assertEqual([f["language"] for f in findings], [lang])
            self.assertFalse(any(a["language"] == lang for a in audits))

    def test_quantified_declared_noun_and_retained_restrictions(self):
        for lang, whole, subset in [
            ("en", "This holds for each of the remaining records.", "This holds for each of the remaining records in the sample."),
            ("es", "Esto vale para cada una de las demás filas.", "Esto vale para cada una de las demás filas de la muestra."),
        ]:
            item = packet()
            for text, expected in [(subset, False), (whole, True)]:
                with self.subTest(lang=lang, text=text):
                    item["versions"][lang][0]["text"] = passage(lang).replace(CLOSING[lang], text)
                    issues, findings, audits = check(item)
                    self.assertEqual(bool(issues), expected)
                    self.assertEqual(bool(findings), expected)
                    self.assertFalse(any(a["language"] == lang for a in audits))

    def test_the_closing_pronoun_must_match_its_definition(self):
        cases = [("en", '"the others"', '"the other"'),
                 ("en", '"the others"', '"others"'),
                 ("es", "«las demás»", "«los demás»"),
                 ("es", "cada una de las demás", "cada uno de los demás"),
                 ("es", "cada una de las demás", "cada uno de las demás"),
                 ("es", "a las otras filas", "a los otros filas")]
        for lang, old, new in cases:
            with self.subTest(lang=lang, new=new):
                item = packet()
                item["versions"][lang][0]["text"] = passage(lang).replace(old, new)
                _, findings, audits = check(item)
                self.assertEqual([f["language"] for f in findings], [lang])
                self.assertFalse(any(a["language"] == lang for a in audits))

    def test_rule_validates_shape_dimensions_and_bilingual_agreement(self):
        scope_groups.validate(GROUP)
        for columns in ([0, 3], [1, 4], [True, 3], [1, 1], [1], [1, 2]):
            with self.subTest(columns=columns), self.assertRaises(ValueError):
                invalid = copy.deepcopy(GROUP)
                invalid["es"]["equal_columns"] = columns
                scope_groups.validate(invalid)
        for source in ("a finite set", "(1,2), (1,2,3)", "(1,2), ..."):
            with self.subTest(source=source), self.assertRaises(ValueError):
                scope_groups.validate(dict(GROUP, source=source))
