"""Resolve an explicitly delimited finite group against source-listed integer records."""
import re

import scope_resumption
from scope_application import normalize
from scope_discourse import scope_segments


# An annotation names the property in both languages and the two columns whose
# equality expresses it. Values come from the quoted data, not from an editor's
# per-member verdict. Positions throughout the packet and receipt are one-based.
_INTEGER = r"[+-]?[0-9]+"
_ROW = rf"\(\s*{_INTEGER}(?:\s*,\s*{_INTEGER})+\s*\)"
_TABLE = rf"{_ROW}(?:\s*,\s*{_ROW})*"
_NUMBER_NAMES = {
    "en": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
    "es": ["uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez"],
}


def _records(source):
    data = normalize(source).rstrip(".").rsplit(":", 1)[-1].strip()
    if not re.fullmatch(_TABLE, data):
        return []
    try:
        return [tuple(int(v) for v in re.findall(_INTEGER, row)) for row in re.findall(_ROW, data)]
    except ValueError:  # The interpreter can limit the length of decimal integers.
        return []


def validate(rule):
    if not isinstance(rule, dict) or set(rule) != {"kind", "source", "en", "es"} or rule["kind"] != "finite_group":
        raise ValueError("finite_group requires kind, source, en and es")
    if not isinstance(rule["source"], str):
        raise ValueError("finite_group requires a quoted sequence of integer records")
    records = _records(rule["source"])
    if not records or any(len(row) != len(records[0]) for row in records):
        raise ValueError("finite_group needs an ordered list of integer records of equal width")
    for lang in ("en", "es"):
        spec = rule[lang]
        if not isinstance(spec, dict) or set(spec) != {"property", "objects", "equal_columns"}:
            raise ValueError(f"{lang}: expected property, objects and equal_columns")
        if not isinstance(spec["property"], str) or not spec["property"].strip():
            raise ValueError(f"{lang}: expected a nonempty property")
        nouns = spec["objects"]
        if not isinstance(nouns, list) or not nouns or not all(isinstance(s, str) and s.strip() for s in nouns):
            raise ValueError(f"{lang}: expected literal object names")
        cols = spec["equal_columns"]
        if (not isinstance(cols, list) or len(cols) != 2
                or not all(type(i) is int and 1 <= i <= len(records[0]) for i in cols)
                or cols[0] == cols[1]):
            raise ValueError(f"{lang}: expected two distinct one-based column positions in the records")
    if rule["en"]["equal_columns"] != rule["es"]["equal_columns"]:
        raise ValueError("finite_group requires the same source columns in both editions")


def findings(sentence, rule, lang):
    # A finite check requires an active, source-attributed resumption.
    return []


def extension(sentence, rule, lang):
    detail = scope_resumption.extension(sentence, rule, lang)
    if detail is not None or rule[lang]["mode"] != "example":
        return detail
    noun = scope_resumption._aliases(rule[lang]["objects"])
    # In Spanish "cada una de las demás parejas" retains the quantified noun.
    # Require its end: "las demás parejas de una subcolección" restricts it.
    if lang == "es":
        group = rf"(?:para|a|en) (?:cada un[oa] de|cualquiera de|tod[oa]s) l[oa]s (?:demás|otr[oa]s) {noun}"
    else:
        group = rf"(?:for|to|in) (?:each|every|any)(?: one)? of the (?:other|remaining) {noun}"
    frame = rf"{scope_resumption._SUBJECT[lang]} {scope_resumption._ASSERT[lang]} (?P<group>{group}){scope_resumption._TAIL[lang]}[.!]?"
    match = re.fullmatch(frame, normalize(sentence), re.I)
    if match:
        return (f"possible transfer of example property '{rule[lang]['property']}' "
                f"to '{match['group']}' in '{match.group()}'.")
    return None


def _domain_positions(declaration, nouns, lang, records):
    words = _NUMBER_NAMES[lang]
    n = rf"(?P<count>[1-9][0-9]*|{'|'.join(words)})"
    if lang == "en":
        prefix = r"(?:for this comparison )?the reference group (?:consists of|contains|includes only) "
        first = rf"(?:only )?the (?P<side>first|last) {n} {nouns}"
        all_rows = rf"all {n} {nouns}"
        suffix = r"(?: in the (?:ordered )?list)?"
    else:
        prefix = r"(?:para esta comparación )?el grupo de referencia (?:comprende|contiene|incluye únicamente) "
        first = rf"(?:(?:solo|únicamente) )?l[oa]s {n} (?P<side>primer[oa]s|últim[oa]s) {nouns}"
        all_rows = rf"(?:tod[oa]s )?l[oa]s {n} {nouns}"
        suffix = r"(?: de la lista(?: ordenada)?)?"
    # Naming the records allows a non-contiguous selection. Values that occur
    # twice in the source do not identify individual positions by themselves.
    explicit = re.fullmatch(prefix + rf"(?P<members>{_TABLE})", declaration, re.I)
    if explicit:
        members = _records(explicit["members"])
        if len(set(members)) != len(members) or len(members) < 2:
            return None
        if any(records.count(member) != 1 for member in members):
            return None
        return [records.index(member) for member in members]
    size = len(records)
    for pattern in (first, all_rows):
        match = re.fullmatch(prefix + pattern + suffix, declaration, re.I)
        if not match:
            continue
        word = match["count"].lower()
        if word.isdigit():
            if len(word) > len(str(size)):
                return None
            count = int(word)
        elif word in words:
            count = words.index(word) + 1
        else:
            return None
        if not 2 <= count <= size:
            return None
        side = match.groupdict().get("side")
        if side is None and count != size:
            return None
        left = size - count if side and side.lower() in ("last", "últimas", "últimos") else 0
        return list(range(left, left + count))
    return None


def _checked(prefix, closing, rule, lang, spec, records):
    # Require the full local binding in a single segment. A new selection,
    # intervening sentence, or changed listing invalidates this proof.
    spans = scope_segments(prefix)
    if len(spans) < 5:
        return None
    listing, domain, reference, selection, witness = [
        normalize(prefix[a:b]).removesuffix(".") for a, b in spans[-5:]
    ]
    shared_names = sorted(set(spec["objects"]) & set(rule[lang]["objects"]))
    if not shared_names or not scope_resumption.witnessed(witness, rule, lang):
        return None
    nouns = scope_resumption._aliases(shared_names)
    if lang == "en":
        listing_start = r"(?:the|our) ordered list is "
        referent = rf"(?:here )?[“\"](?P<pronoun>the others)[”\"] (?:means|denotes) (?:precisely |only )?the other {nouns} in (?:that|the reference) group"
        chosen = rf"(?:select|choose|we select|we choose) the (?P<side>first|last) {nouns} (?P<record>{_ROW})"
        quantified = r"(?:for|to|in) (?:each(?: one)? of|every one of|all(?: of)?) (?P<pronoun>the others)"
    else:
        listing_start = r"(?:la|nuestra) lista ordenada es "
        referent = (rf'(?:aquí )?[«"](?P<pronoun>l(?P<gender>[oa])s demás)[»"] (?:se refiere|alude) '
                    rf"(?:exclusivamente |únicamente )?a l(?P=gender)s otr(?P=gender)s {nouns} "
                    r"de (?:ese grupo|dicho grupo|el grupo de referencia)")
        chosen = rf"(?:seleccionamos|elegimos|seleccionemos|elijamos) (?:el|la) (?P<side>primer[oa]?|últim[oa]) {nouns} (?P<record>{_ROW})"
        quantified = (r"(?:para|a|en) (?:(?:cada una de|todas) (?=las demás)|"
                      r"(?:cada uno de|todos) (?=los demás)|cualquiera de )(?P<pronoun>l[oa]s demás)")
    final = rf"{scope_resumption._SUBJECT[lang]} {scope_resumption._ASSERT[lang]} {quantified}{scope_resumption._TAIL[lang]}[.!]?"
    closing_match = re.fullmatch(final, normalize(closing), re.I)
    binding = re.fullmatch(referent, reference, re.I)
    if not closing_match or not binding or closing_match["pronoun"].casefold() != binding["pronoun"].casefold():
        return None
    table = re.fullmatch(listing_start + rf"(?P<data>{_TABLE})", listing, re.I)
    selected = re.fullmatch(chosen, selection, re.I)
    indices = _domain_positions(domain, nouns, lang, records)
    if not table or _records(table["data"]) != records or not selected or indices is None:
        return None
    chosen_index = indices[-1] if selected["side"].lower() in ("last", "última", "último") else indices[0]
    if _records(selected["record"]) != [records[chosen_index]]:
        return None
    left, right = (n - 1 for n in spec["equal_columns"])
    other_indices = [n for n in indices if n != chosen_index]
    failures = [n for n in other_indices if records[n][left] != records[n][right]]
    witness_true = records[chosen_index][left] == records[chosen_index][right]
    return {"supported": witness_true and not failures, "property": spec["property"],
            "equal_columns": spec["equal_columns"], "group_size": len(indices),
            "selected_member": chosen_index + 1, "selected_member_satisfies": witness_true,
            "checked_members": [n + 1 for n in other_indices], "failing_members": [n + 1 for n in failures]}


def resolve(prefix, sentence, rule, lang, rules):
    """Resolve a bare 'the others' only with a unique local finite proof.

    The caller must already have matched the resumption, checked its source,
    and limited prefix to the same segment and paragraph as its witness.
    """
    if rule[lang]["mode"] != "example":
        return None
    candidates = [r for r in rules if r["kind"] == "finite_group"
                  and normalize(r[lang]["property"]) == normalize(rule[lang]["property"])]
    if len(candidates) != 1:
        return None
    group = candidates[0]
    return _checked(prefix, sentence, rule, lang, group[lang], _records(group["source"]))
