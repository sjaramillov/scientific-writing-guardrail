"""Check declared source quotations, identifiers and literal expressions in EN/ES drafts."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


CHECKER_VERSION = "0.1.0"
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
    "grammar_and_reader_comprehension",
)


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


def contains_term(text, term):
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
    return bool(re.search(pattern, normalize(text)))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PacketError("Duplicate JSON property: " + key)
        result[key] = value
    return result


def prepare(raw):
    return {
        "version": 1, "source_sha256": digest(raw), "audience": "",
        "assistance": "", "claims": [{
            "id": "C1", "status": "", "evidence": "",
            "quote": raw.decode("utf-8").strip(),
            "anchors": [{"source": "", "en": "", "es": ""}],
        }],
        "versions": {lang: [{"claim": "C1", "text": ""}] for lang in LANGUAGES},
    }


def public_doi(claim):
    if "public_doi" not in claim:
        return None
    value = required_text(claim, "public_doi")
    if not PUBLIC_DOI.fullmatch(value) or any(
        part in {".", "..", ""} for part in value.split("/")
    ):
        raise PacketError("Expected a bare public DOI, for example 10.1234/example.1")
    return value


def check(raw, packet):
    source = raw.decode("utf-8")
    if not isinstance(packet, dict) or type(packet.get("version")) is not int or packet["version"] != 1:
        raise PacketError("Expected packet version 1")
    required_text(packet, "audience")
    required_text(packet, "assistance")
    issues = []
    if required_text(packet, "source_sha256") != digest(raw):
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
        raise PacketError("Version 1 requires en and es renderings")
    for lang in LANGUAGES:
        seen = set()
        for part in items(versions, lang):
            key = required_text(part, "claim")
            text = required_text(part, "text")
            if type(part.get("new_paragraph", False)) is not bool:
                raise PacketError(f"{lang}/{key}: new_paragraph must be true or false")
            if key not in claims or key in seen:
                raise PacketError(f"{lang}: unknown or repeated claim ID {key}")
            seen.add(key)
            for n, anchor in enumerate(claims[key]["anchors"], 1):
                if not contains_term(text, anchor[lang]):
                    issues.append(f"{lang}/{key} anchor {n}: protected expression missing.")
        for key in sorted(set(claims) - seen):
            issues.append(f"{lang}/{key}: claim missing.")
    return issues


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
    commands.add_parser("prepare", help="Start an incomplete EN/ES packet").add_argument("source", type=Path)
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
            result = prepare(raw)
            code = 0
        else:
            packet_bytes = args.packet.read_bytes()
            packet = json.loads(packet_bytes.decode("utf-8"), object_pairs_hook=unique_object)
            issues = check(raw, packet)
            if args.command == "render" and not issues:
                print(render_draft(packet, args.language, digest(packet_bytes), args.with_notes))
                return 0
            result = {"result": "revise" if issues else "ready_for_human_review",
                      "checker_version": CHECKER_VERSION, "checked": CHECKS,
                      "not_assessed": NOT_ASSESSED, "human_review": "pending", "source_sha256": digest(raw),
                      "packet_sha256": digest(packet_bytes), "issues": issues}
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
