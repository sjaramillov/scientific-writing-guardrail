"""Check declared source quotations, identifiers and literal expressions in EN/ES drafts."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
import scope_application
import scope_contrasts
import scope_dependencies
import scope_groups
import scope_hypotheses
import scope_relations
import scope_resumption
from scope_context import is_disclaimed, is_unasserted_witness
from scope_discourse import scope_segments, universal_restatements


CHECKER_VERSION = "0.2.0"
CONTEXT_TYPES = {"application": scope_application, "resumption": scope_resumption}
SCOPE_TYPES = {**CONTEXT_TYPES, "relation": scope_relations, "dependency": scope_dependencies,
               "hypothesis": scope_hypotheses, "contrast": scope_contrasts, "finite_group": scope_groups}
LANGUAGES = ("en", "es")
STATUSES = {"observed", "reported", "formal", "interpretation", "planned", "limitation"}
NUMERIC_LITERAL = re.compile(r"[+−-]?\d+(?:[.,]\d+)?(?:/\d+)?(?:%|‰)?")
# External notes accept bare DOIs in this conservative ASCII syntax. Other
# citations and URLs can still be kept in the private evidence field.
PUBLIC_DOI = re.compile(r"10\.[0-9]{4,9}/[-._;()/:a-zA-Z0-9]+")
CHECKS = (
    "frozen_source_sha256",
    "verbatim_quotes_in_source",
    "declared_claim_ids_in_both_editions",
    "declared_anchors_in_quotes_and_editions",
    "fixed_literal_equality",
)
NOT_ASSESSED = (
    "completeness_of_the_claim_map",
    "evidence_authenticity_or_support",
    "semantic_equivalence_including_quantity_referents",
    "logical_scope_beyond_declared_wording",
    "grammar_and_reader_comprehension",
)

# These forms must touch a declared noun phrase. In particular, "todo el"
# usually refers to the whole selected object, so it is absent here.
UNIVERSAL_PREFIX = {
    "en": r"(?:any(?: given)?|all(?: possible)?|each|every|arbitrary)",
    "es": r"(?:cualquier|cada|todo|toda|todos(?: los)?|todas(?: las)?)",
}
UNIVERSAL_SUFFIX = {
    "en": r"(?:whatsoever|of any kind)",
    "es": r"(?:cualquiera|cualesquiera|arbitrari[oa]s?)",
}


class PacketError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def required_text(obj, key):
    if not isinstance(obj, dict) or not isinstance(obj.get(key), str) or not obj[key].strip():
        raise PacketError(f"Expected nonempty text for {key}")
    return obj[key]


def items(obj, key):
    if not isinstance(obj, dict) or not isinstance(obj.get(key), list) or not obj[key]:
        raise PacketError(f"Expected a nonempty list for {key}")
    return obj[key]


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def term_pattern(term):
    # Interior punctuation, case, mathematical symbols and unit prefixes matter.
    token = normalize(term)
    pattern = re.escape(token)
    if token[0].isalnum() or token[0] == "_":
        pattern = r"(?<!\w)" + pattern
    if token[0].isdigit():
        pattern = r"(?<![+−.,/\-])" + pattern
    if token[-1].isalnum() or token[-1] == "_":
        pattern += r"(?!\w)"
    if token[-1].isdigit():
        pattern += r"(?![.,/]\d|[%‰])"
    return pattern


def contains_term(text, term):
    return bool(re.search(term_pattern(term), normalize(text)))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PacketError("Duplicate JSON property: " + key)
        result[key] = value
    return result


def prepare(raw, with_scope=False, with_antecedents=False, with_properties=False, with_context=False,
            with_contrasts=False):
    packet = {
        "version": 2 if with_scope else 1, "source_sha256": digest(raw), "audience": "",
        "assistance": "", "claims": [{
            "id": "C1", "status": "", "evidence": "",
            "quote": raw.decode("utf-8").strip(),
            "anchors": [{"source": "", "en": "", "es": ""}],
        }],
        "versions": {lang: [{"claim": "C1", "text": ""}] for lang in LANGUAGES},
    }
    if with_antecedents:
        packet["version"] = 3
        for parts in packet["versions"].values():
            parts[0]["antecedents"] = []
    if with_scope or with_antecedents:
        packet["claims"][0]["existentials"] = [{
            "source": "",
            **{lang: {"referents": [""], "witnesses": [""]} for lang in LANGUAGES},
        }]
    if with_properties:
        packet["version"] = 4
        packet["claims"][0]["scope_rules"] = [{
            "kind": "relation", "source": "",
            **{lang: {"frame": "classification", "subject": [""], "predicate": [""],
                      "licensed": [""], "review": [""]} for lang in LANGUAGES},
        }]
    if with_context:
        packet["version"] = 5
        for parts in packet["versions"].values():
            parts[0].setdefault("antecedents", [])
        rules = packet["claims"][0].setdefault("scope_rules", [])
        rules.extend([
            {"kind": "resumption", "source": "",
             **{lang: {"mode": "example", "property": "", "witnesses": [""],
                       "objects": [""], "parameters": []} for lang in LANGUAGES}},
            {"kind": "hypothesis", "source": "",
             **{lang: {"subjects": [""], "hypotheses": [""], "domains": [""],
                       "conclusions": [""]} for lang in LANGUAGES}},
        ])
    if with_contrasts:
        packet["version"] = 6
        rules = packet["claims"][0].setdefault("scope_rules", [])
        rules.append({"kind": "contrast", "source": "",
                      **{lang: {"frame": "partial_sufficiency", "licensed": "",
                                "roles": {"condition": [""], "conclusion": [""]}}
                         for lang in LANGUAGES}})
    return packet


def existential_rules(claim, version):
    if "existentials" not in claim:
        return []
    key = claim["id"]
    rules = claim["existentials"]
    if version < 2 or not isinstance(rules, list):
        raise PacketError(f"{key}: existentials requires a list in packet version 2 or later")
    for n, rule in enumerate(rules, 1):
        where = f"{key} existential {n}"
        if not isinstance(rule, dict) or set(rule) != {"source", *LANGUAGES}:
            raise PacketError(f"{where}: expected source, en and es")
        required_text(rule, "source")
        for lang in LANGUAGES:
            terms = rule[lang]
            if not isinstance(terms, dict) or set(terms) != {"referents", "witnesses"}:
                raise PacketError(f"{lang}/{where}: expected referents and witnesses")
            for field in ("referents", "witnesses"):
                if not all(isinstance(t, str) and t.strip() for t in items(terms, field)):
                    raise PacketError(f"{lang}/{where}: expected nonempty phrases in {field}")
            for witness in terms["witnesses"]:
                if not any(contains_term(witness.casefold(), ref.casefold()) for ref in terms["referents"]):
                    raise PacketError(f"{lang}/{where}: each witness must contain a declared referent")
    return rules


def check_existential(folded, terms, lang, where):
    # Match complete literal noun phrases, including their modifiers. Never
    # scan an arbitrary window that might reach a different noun or clause.
    refs = sorted({normalize(ref).casefold() for ref in terms["referents"]}, key=len, reverse=True)
    noun = "(?:" + "|".join(re.escape(ref) for ref in refs) + ")"
    conflict = rf"(?<!\w)(?:{UNIVERSAL_PREFIX[lang]} {noun}|{noun} {UNIVERSAL_SUFFIX[lang]})(?!\w)"
    issues = []
    for match in re.finditer(conflict, folded):
        if not is_disclaimed(folded, match.start(), match.end(), lang):
            issues.append(f"{where}: possible universal wording '{match.group()}'; review scope and polarity.")
    # A disclaimer cannot supply the only evidence that the draft still
    # states the existential. Retain its first accepted endpoint for lookback.
    witnesses = (
        m.end() for w in terms["witnesses"]
        for m in re.finditer(term_pattern(w.casefold()), folded)
        if not is_unasserted_witness(folded, m.start(), m.end(), lang)
    )
    first_witness_end = min(witnesses, default=None)
    if first_witness_end is None:
        issues.append(f"{where}: accepted existential wording missing for '{terms['referents'][0]}'.")
    return issues, first_witness_end


def resolve_antecedents(part, folded, sentences, earlier, lang, version):
    links = {}
    issues = []
    if "antecedents" not in part:
        return links, issues
    where = f"{lang}/{part['claim']}"
    if version < 3 or not isinstance(part["antecedents"], list):
        raise PacketError(f"{where}: antecedents requires a list in packet version 3 or later")
    for ref in part["antecedents"]:
        if not isinstance(ref, dict) or set(ref) != {"sentence", "mention", "claim"}:
            raise PacketError(f"{where}: expected sentence, mention and claim for each antecedent")
        target = required_text(ref, "claim")
        mention = required_text(ref, "mention")
        number = ref["sentence"]
        if type(number) is not int or number < 1:
            raise PacketError(f"{where}: sentence must be a positive integer")
        if target not in earlier:
            raise PacketError(f"{where}: antecedent {target} must be an earlier claim in the {lang} edition")
        if number > len(sentences):
            issues.append(f"{where}: sentence {number} for antecedent {target} is missing.")
            continue
        start, end = sentences[number - 1]
        matches = list(re.finditer(term_pattern(mention.casefold()), folded[start:end]))
        if len(matches) != 1:
            issues.append(f"{where} sentence {number}: expected one occurrence of '{mention}' for {target}, found {len(matches)}.")
            continue
        left, right = matches[0].span()
        span = (start + left, start + right)
        if any(span[0] < b and a < span[1] for a, b in links):
            raise PacketError(f"{where} sentence {number}: overlapping antecedent annotations")
        links[span] = {"language": lang, "from_claim": part["claim"], "sentence": number,
                       "mention": mention, "to_claim": target}
    return links, issues


def check_discourse(folded, sentences, lang, key, current_rules, previous_rules, links, earlier, covered=()):
    issues = []
    for number, (start, end) in enumerate(sentences, 1):
        if number in covered:
            continue
        sentence = folded[start:end]
        for left, right in universal_restatements(sentence, lang):
            # Use reading order in the chosen edition. The first sentence can
            # refer back one claim, until it introduces a new scoped object.
            candidates = [rule for rule, pos in current_rules if pos <= start + left]
            if number == 1 and not candidates:
                candidates = previous_rules
            if is_disclaimed(sentence, left, right, lang):
                continue
            # Only a link on the subject of this particular restatement can
            # replace automatic lookback. A second pronoun keeps its own scope.
            for (a, b), ref in links.items():
                if a == start + left and b <= start + right:
                    target = ref["to_claim"]
                    candidates = earlier[target] or [f"{target} (confirm scope; no accepted existential witness)"]
                    break
            if candidates:
                issues.append(
                    f"{lang}/{key} sentence {number}: possible universal restatement "
                    f"'{sentence[left:right]}'; compare with {', '.join(candidates)}."
                )
    return issues


def public_doi(claim):
    if "public_doi" not in claim:
        return None
    value = required_text(claim, "public_doi")
    if not PUBLIC_DOI.fullmatch(value) or any(
        part in {".", "..", ""} for part in value.split("/")
    ):
        raise PacketError("Expected a bare public DOI, for example 10.1234/example.1")
    return value


def declared_scope(claim, version):
    if "scope_rules" not in claim:
        return []
    rules = claim["scope_rules"]
    if version < 4 or not isinstance(rules, list):
        raise PacketError(f"{claim['id']}: scope_rules requires a list in packet version 4 or later")
    for number, rule in enumerate(rules, 1):
        where = f"{claim['id']} scope rule {number}"
        if not isinstance(rule, dict) or set(rule) != {"kind", "source", *LANGUAGES}:
            raise PacketError(f"{where}: expected kind, source, en and es")
        kind = required_text(rule, "kind")
        required_text(rule, "source")
        if kind not in SCOPE_TYPES:
            raise PacketError(f"{where}: unknown rule kind '{kind}'")
        if version < 5 and kind in ("resumption", "hypothesis"):
            raise PacketError(f"{where}: {kind} requires packet version 5")
        if version < 6 and kind in ("contrast", "finite_group"):
            raise PacketError(f"{where}: {kind} requires packet version 6")
        try:
            SCOPE_TYPES[kind].validate(rule)
        except ValueError as e:
            raise PacketError(f"{where}: {e}") from e
    return rules


def scope_in_segment(text, key, lang, rules, links, earlier, previous, *, version, source_verified,
                     group_checks=None):
    """Evaluate direct assertions and narrowly bounded references in reading order."""
    findings, witnessed, covered = [], {}, set()
    normalized = normalize(text)
    groups = []
    if version >= 6 and not re.search(r"\n[^\S\n]*\n|\u2029", text):
        groups = [r for r in rules if r["kind"] == "finite_group" and source_verified(r)]
    fold_offset = 0
    for number, (start, end) in enumerate(scope_segments(normalized), 1):
        sentence = normalized[start:end]
        lower = sentence.casefold()
        # Antecedent offsets refer to the folded edition. Mathematical symbols
        # for dependencies retain their case in the original sentence.
        folded_start = start + fold_offset
        fold_offset += len(lower) - len(sentence)
        current = []
        evidence = []
        for ordinal, rule in enumerate(rules, 1):
            kind = rule["kind"]
            if kind in CONTEXT_TYPES:
                if CONTEXT_TYPES[kind].witnessed(sentence, rule, lang):
                    item = (key, ordinal, rule, number)
                    current.append(item)
                    witnessed[ordinal] = item
            else:
                for detail in SCOPE_TYPES[kind].findings(sentence, rule, lang):
                    evidence.append((key, ordinal, kind, detail, None))
        # The application grammar starts at the anaphoric subject. A link on
        # another word in the sentence cannot change that subject's antecedent.
        target = next((ref["to_claim"] for (a, b), ref in links.items()
                       if a == folded_start), None)
        candidates = previous if target is None else earlier.get(target, ())
        # A reference to a claim carrying two different witnessed properties
        # cannot select which of those properties the pronoun resumes.
        ambiguous = sum(item[2]["kind"] == "resumption" for item in candidates) > 1
        for owner, ordinal, rule, witness_number in candidates:
            kind = rule["kind"]
            if kind == "resumption" and ambiguous:
                continue
            handler = scope_groups if version >= 6 and kind == "resumption" else CONTEXT_TYPES[kind]
            detail = handler.extension(sentence, rule, lang)
            if detail:
                if (groups and kind == "resumption" and owner == key and target is None
                        and witness_number == number - 1 and source_verified(rule)):
                    audit = scope_groups.resolve(normalized[:start], sentence, rule, lang, groups)
                    if audit is not None:
                        if group_checks is not None:
                            group_checks.append(dict(audit, language=lang, claim=key, rule=ordinal,
                                                     sentence=number, witness_sentence=witness_number))
                        if audit["supported"]:
                            covered.add(number)
                            continue
                        failed = audit["failing_members"]
                        if not audit["selected_member_satisfies"]:
                            failed = [audit["selected_member"], *failed]
                        detail += f" Source positions failing the equality: {failed}."
                evidence.append((owner, ordinal, kind, detail, witness_number))
                covered.add(number)
        for owner, ordinal, kind, detail, witness_number in evidence:
            finding = {"language": lang, "claim": key, "sentence": number,
                       "rule_claim": owner, "rule": ordinal, "kind": kind, "detail": detail}
            if kind == "resumption":
                finding["witness_sentence"] = witness_number
            findings.append(finding)
        previous = current
    return findings, list(witnessed.values()), previous, covered


def evaluate(raw, packet, *, scope_findings=None, scope_group_checks=None):
    source = raw.decode("utf-8")
    if not isinstance(packet, dict) or type(packet.get("version")) is not int or packet["version"] not in (1, 2, 3, 4, 5, 6):
        raise PacketError("Expected packet version 1, 2, 3, 4, 5 or 6")
    required_text(packet, "audience")
    required_text(packet, "assistance")
    issues = []
    resolved = []
    source_intact = required_text(packet, "source_sha256") == digest(raw)
    if not source_intact:
        issues.append("Source SHA-256 differs from the frozen source.")
    claims = {}
    for claim in items(packet, "claims"):
        key = required_text(claim, "id")
        if not re.fullmatch(r"C[1-9][0-9]*", key) or key in claims:
            raise PacketError("Expected unique claim IDs such as C1")
        if required_text(claim, "status") not in STATUSES:
            raise PacketError(f"{key}: unknown evidence status")
        required_text(claim, "evidence")
        public_doi(claim)
        quote = required_text(claim, "quote")
        if quote not in source:
            issues.append(f"{key}: verbatim source passage missing.")
        for n, rule in enumerate(existential_rules(claim, packet["version"]), 1):
            if rule["source"] not in source:
                issues.append(f"{key} existential {n}: verbatim source wording missing.")
        for n, rule in enumerate(declared_scope(claim, packet["version"]), 1):
            if rule["source"] not in source:
                issues.append(f"{key} scope rule {n}: verbatim source wording missing.")
        for n, anchor in enumerate(items(claim, "anchors"), 1):
            original = required_text(anchor, "source")
            if set(anchor) - {"source", "en", "es", "invariant"}:
                raise PacketError(f"{key} anchor {n}: unknown anchor property")
            invariant = anchor.get("invariant", False)
            if type(invariant) is not bool:
                raise PacketError(f"{key} anchor {n}: invariant must be true or false")
            if not contains_term(quote, original):
                issues.append(f"{key} anchor {n}: source term missing from quote.")
            for lang in LANGUAGES:
                target = required_text(anchor, lang)
                numeric_pair = NUMERIC_LITERAL.fullmatch(original) and NUMERIC_LITERAL.fullmatch(target)
                if (invariant or numeric_pair) and target != original:
                    issues.append(f"{lang}/{key} anchor {n}: fixed literal changed.")
        claims[key] = claim
    versions = packet.get("versions")
    if not isinstance(versions, dict) or set(versions) != set(LANGUAGES):
        raise PacketError("Expected en and es renderings")
    for lang in LANGUAGES:
        earlier = {}
        earlier_applications = {}
        previous_applications = []
        previous_rules = []
        for part in items(versions, lang):
            key = required_text(part, "claim")
            text = required_text(part, "text")
            if type(part.get("new_paragraph", False)) is not bool:
                raise PacketError(f"{lang}/{key}: new_paragraph must be true or false")
            if key not in claims or key in earlier:
                raise PacketError(f"{lang}: unknown or repeated claim ID {key}")
            for n, anchor in enumerate(claims[key]["anchors"], 1):
                if not contains_term(text, anchor[lang]):
                    issues.append(f"{lang}/{key} anchor {n}: protected expression missing.")
            current_rules = []
            folded = normalize(text).casefold()
            for n, rule in enumerate(claims[key].get("existentials", []), 1):
                label = f"{key} existential {n} ({rule[lang]['referents'][0]})"
                findings, witness_end = check_existential(folded, rule[lang], lang, f"{lang}/{label}")
                issues.extend(findings)
                if witness_end is not None:
                    current_rules.append((label, witness_end))
            if part.get("new_paragraph"):
                previous_rules = []
                previous_applications = []
            rules = claims[key].get("scope_rules", [])
            if current_rules or previous_rules or "antecedents" in part or rules or previous_applications:
                sentences = scope_segments(folded)
                links, problems = resolve_antecedents(part, folded, sentences, earlier, lang, packet["version"])
                issues.extend(problems)
                resolved.extend(links.values())
                covered = ()
                if packet["version"] >= 4:
                    found, earlier_applications[key], previous_applications, covered = scope_in_segment(
                        text, key, lang, rules, links, earlier_applications, previous_applications,
                        version=packet["version"], source_verified=lambda r: source_intact and r["source"] in source,
                        group_checks=scope_group_checks)
                    if scope_findings is not None:
                        scope_findings.extend(found)
                    for f in found:
                        issues.append(f"{lang}/{key} sentence {f['sentence']}: {f['rule_claim']} "
                                      f"{f['kind']} rule {f['rule']}: {f['detail']}")
                issues.extend(check_discourse(folded, sentences, lang, key, current_rules, previous_rules, links, earlier, covered))
            previous_rules = [label for label, _ in current_rules]
            earlier[key] = previous_rules
        for key in sorted(set(claims) - earlier.keys()):
            issues.append(f"{lang}/{key}: claim missing.")
    return issues, resolved


def check(raw, packet):
    return evaluate(raw, packet)[0]


def render_draft(packet, lang, packet_hash, with_notes):
    title, evidence, review_note = {
        "en": ("Draft for human review", "Evidence status assigned by the editor",
               "Ask the editor for the evidence and editorial assistance record using the claim ID and packet hash."),
        "es": ("Borrador para revisión humana", "Estado de la evidencia asignado por el editor",
               "Solicita al editor la evidencia y el registro de asistencia editorial con el identificador de la afirmación y la huella del paquete."),
    }[lang]
    paragraphs = []
    for part in packet["versions"][lang]:
        phrase = part["text"].strip()
        if with_notes:
            phrase += " [" + part["claim"] + "]"
        if not paragraphs or part.get("new_paragraph"):
            paragraphs.append(phrase)
        else:
            paragraphs[-1] += " " + phrase
    if with_notes:
        spanish_status = {
            "observed": "observado", "reported": "reportado", "formal": "formal",
            "interpretation": "interpretación", "planned": "planificado", "limitation": "limitación",
        }
        notes = [evidence]
        for claim in packet["claims"]:
            status = claim["status"] if lang == "en" else spanish_status[claim["status"]]
            line = f"[{claim['id']}] {status}"
            doi = public_doi(claim)
            if doi:
                line += " · https://doi.org/" + doi
            notes.append(line)
        paragraphs.extend(["\n".join(notes), review_note, "SHA-256 · " + packet_hash])
    return "\n\n".join([title] + paragraphs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=CHECKER_VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    scaffold = commands.add_parser("prepare", help="Start an incomplete EN/ES packet")
    scaffold.add_argument("source", type=Path)
    scaffold.add_argument("--with-scope", action="store_true", help="Start a version 2 packet with an existential rule")
    scaffold.add_argument("--with-antecedents", action="store_true", help="Start a version 3 packet with scope and reference annotations")
    scaffold.add_argument("--with-properties", action="store_true", help="Start a version 4 packet with a property and object rule")
    scaffold.add_argument("--with-context", action="store_true", help="Start a version 5 packet with resumption and hypothesis rules")
    scaffold.add_argument("--with-contrasts", action="store_true", help="Start a version 6 packet with a scoped claim contrast")
    validate = commands.add_parser("check", help="Check a packet against the original source bytes")
    validate.add_argument("source", type=Path)
    validate.add_argument("packet", type=Path)
    render = commands.add_parser("render", help="Read a checked draft as plain text")
    render.add_argument("source", type=Path)
    render.add_argument("packet", type=Path)
    render.add_argument("--language", required=True, choices=LANGUAGES)
    render.add_argument("--with-notes", action="store_true",
                        help="Add claim IDs, assigned statuses, explicitly public DOIs and the packet hash")
    args = parser.parse_args(argv)
    try:
        raw = args.source.read_bytes()
        if not raw.decode("utf-8").strip():
            raise PacketError("Source is empty")
        if args.command == "prepare":
            result = prepare(raw, with_scope=args.with_scope, with_antecedents=args.with_antecedents,
                             with_properties=args.with_properties, with_context=args.with_context,
                             with_contrasts=args.with_contrasts)
            code = 0
        else:
            packet_bytes = args.packet.read_bytes()
            packet = json.loads(packet_bytes.decode("utf-8"), object_pairs_hook=unique_object)
            findings = []
            group_checks = []
            issues, resolved = evaluate(raw, packet, scope_findings=findings, scope_group_checks=group_checks)
            if args.command == "render" and not issues:
                print(render_draft(packet, args.language, digest(packet_bytes), args.with_notes))
                return 0
            rule_count = sum(len(claim.get("existentials", [])) for claim in packet["claims"])
            checks = CHECKS
            if rule_count:
                checks += ("declared_existential_scope_wording", "local_disclaimer_wording",
                           "bounded_universal_restatements")
            if any(part.get("antecedents") for parts in packet["versions"].values() for part in parts):
                checks += ("editor_declared_antecedent_links",)
            scope_count = sum(len(c.get("scope_rules", [])) for c in packet["claims"])
            if scope_count:
                checks += ("declared_scope_relations_and_dependencies",)
            context_kinds = {r["kind"] for c in packet["claims"] for r in c.get("scope_rules", [])}
            if "resumption" in context_kinds:
                checks += ("declared_property_resumptions",)
            if "hypothesis" in context_kinds:
                checks += ("declared_hypothesis_removals",)
            if "contrast" in context_kinds:
                checks += ("declared_claim_contrasts",)
            if "finite_group" in context_kinds:
                checks += ("declared_finite_group_equalities",)
            result = {"result": "revise" if issues else "ready_for_human_review",
                      "checker_version": CHECKER_VERSION, "checked": checks, "existential_scope_rules": rule_count,
                      "not_assessed": NOT_ASSESSED, "human_review": "pending", "source_sha256": digest(raw),
                      "packet_sha256": digest(packet_bytes), "issues": issues}
            if packet["version"] >= 3:
                result["resolved_antecedents"] = resolved
            if packet["version"] >= 4:
                result.update(scope_rule_count=scope_count, scope_findings=findings)
            if packet["version"] >= 6:
                result["scope_group_checks"] = group_checks
            code = int(bool(issues))
    except (OSError, ValueError, RecursionError) as error:
        result = {"result": "invalid_input", "checker_version": CHECKER_VERSION, "checked": [],
                  "not_assessed": NOT_ASSESSED, "human_review": "pending", "error": str(error)}
        code = 2
    stream = sys.stderr if args.command == "render" else sys.stdout
    print(json.dumps(result, indent=2, ensure_ascii=False), file=stream)
    return code


if __name__ == "__main__":
    sys.exit(main())
