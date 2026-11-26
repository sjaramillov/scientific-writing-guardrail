"""Recognize bounded affirmative extensions of a previously identified proposition."""
import re

from scope_application import literal, normalize
from scope_discourse import scope_segments


def validate(rule):
    if not isinstance(rule, dict) or set(rule) != {"kind", "source", "en", "es"}:
        raise ValueError("resumption requires kind, source, en and es")
    if rule["kind"] != "resumption" or not isinstance(rule["source"], str) or not rule["source"].strip():
        raise ValueError("resumption requires a nonempty source quotation")
    for lang in ("en", "es"):
        spec = rule[lang]
        if not isinstance(spec, dict) or set(spec) != {"mode", "property", "objects", "parameters", "witnesses"}:
            raise ValueError(f"{lang}: expected mode, property, objects, parameters and witnesses")
        mode = spec["mode"]
        if mode not in ("example", "open_uniformity"):
            raise ValueError(f"{lang}: unknown resumption mode")
        if not isinstance(spec["property"], str) or not spec["property"].strip():
            raise ValueError(f"{lang}: expected the property stated or asked about")
        for field in ("witnesses", "objects", "parameters"):
            items = spec[field]
            if not isinstance(items, list) or not all(isinstance(v, str) and v.strip() for v in items):
                raise ValueError(f"{lang}: expected literal phrases in {field}")
        if not spec["witnesses"] or not spec["objects" if mode == "example" else "parameters"]:
            raise ValueError(f"{lang}: a witness and the relevant object or parameter are required")
        for text in spec["witnesses"]:
            text = normalize(text)
            if len(scope_segments(text)) != 1 or not re.search(literal(spec["property"]), text):
                raise ValueError(f"{lang}: each witness must be one sentence containing the exact property")
            if mode == "example" and text.endswith("?"):
                raise ValueError(f"{lang}: example mode needs an affirmative witness")
    if rule["en"]["mode"] != rule["es"]["mode"]:
        raise ValueError("both languages must declare the same resumption mode")


def witnessed(sentence, rule, lang):
    # The question mark and mathematical letter case can change what was said.
    sentence = normalize(sentence).rstrip(".")
    return any(sentence == normalize(text).rstrip(".") for text in rule[lang]["witnesses"])


_SUBJECT = {
    "en": r"(?:(?:this|that)(?: (?:(?:last|latter|same|previous) )?(?:property|claim|result|conclusion|statement))?|the same (?:property|result|conclusion))",
    "es": r"(?:esto|eso|lo anterior|(?:esta|esa) (?:(?:última|misma|anterior) )?(?:propiedad|afirmación|conclusión)|la (?:última|misma|anterior) (?:propiedad|afirmación|conclusión)|(?:este|ese) (?:mismo )?resultado)",
}
_ASSERT = {
    "en": r"(?:(?:also )?(?:holds|applies|works|is (?:true|valid|guaranteed))|remains (?:true|valid))",
    "es": r"(?:(?:también )?(?:se cumple|se aplica|vale|rige|funciona|es (?:ciert[oa]|válid[oa])|está garantizad[oa])(?: también)?)",
}
_TAIL = {"en": r"(?: as well| too)?", "es": r"(?: también)?"}


def _aliases(words):
    # Match mathematical identifiers and controlled terms exactly. Only the
    # surrounding grammar uses case-insensitive comparisons.
    return "(?-i:" + "|".join(re.escape(normalize(w)) for w in words) + ")"


def _sample_domain(spec, lang):
    obj = _aliases(spec["objects"])
    if lang == "en":
        all_objects = rf"(?:all (?:the )?|every |each |any )(?:other )?{obj}"
        others = (r"(?:(?:all|both)(?: of)? (?:them|the others)|(?:every|each|any)(?: one)? of "
                  r"(?:them|the others)|(?:all|each of|any of) the remaining ones)")
        candidates = rf"(?:{all_objects}|{others})"
        if spec["parameters"]:
            feature = _aliases(spec["parameters"])
            same = r"(?:(?:the|that|those|these) same |matching )"
            # All named matching features are checked. Extra restrictions or
            # undeclared roles keep the assertion outside this grammar.
            qualifiers = rf" with {same}{feature}(?: and (?:{same})?{feature})*"
            candidates = rf"{candidates}(?:{qualifiers})?"
        return rf"(?:for|to|in) {candidates}"
    quant = r"(?:tod[oa]s l[oa]s |tod[oa] |cada |cualquier )"
    others = r"(?:tod[oa]s (?:ell[oa]s|l[oa]s demás)|(?:cada un[oa] de|cualquiera de) (?:ell[oa]s|l[oa]s demás))"
    candidates = rf"(?:{quant}(?:demás )?{obj}|{others})"
    if spec["parameters"]:
        feature = _aliases(spec["parameters"])
        same = r"(?:(?:es[ea]s?|l[ao]s?|el) mism[oa]s? )"
        shared = rf"{same}{feature}(?: y (?:{same})?{feature})*"
        relative = rf"tod[oa]s (?:l[oa]s|aquell[oa]s) que (?:tengan|compartan) {shared}"
        candidates = rf"(?:{candidates}(?: con {shared})?|{relative})"
    return rf"(?:para|a|en) {candidates}"


def _uniform_domain(spec, lang):
    param = _aliases(spec["parameters"])
    if lang == "en":
        every = rf"(?:for|at) (?:all|every|each|any) (?:values? of (?:the )?)?{param}"
        unrestricted = rf"(?:however (?:small|large) (?:the )?{param}|regardless of (?:the (?:size|value) of )?(?:the )?{param})"
        return rf"(?:{every}|(?:(?:in|for) (?:all (?:possible )?cases|every case),? )?{unrestricted})"
    every = rf"(?:para|con) (?:cada|cualquier|todas las|todos los|tod[oa]) (?:valor(?:es)? (?:de (?:la )?|del ))?{param}"
    unrestricted = (rf"(?:por (?:pequeñ[oa]|grande) que sea (?:el |la )?{param}|"
                    rf"(?:con independencia|independientemente) (?:de (?:la )?|del ){param})")
    return rf"(?:{every}|(?:(?:en|para) (?:todos los casos|cada caso),? )?{unrestricted})"


def extension(sentence, rule, lang):
    """Candidate only; the caller must have resolved this sentence's antecedent."""
    spec = rule[lang]
    domain = _sample_domain(spec, lang) if spec["mode"] == "example" else _uniform_domain(spec, lang)
    statement = rf"{_SUBJECT[lang]} {_ASSERT[lang]} (?P<domain>{domain}){_TAIL[lang]}[.!]?"
    m = re.fullmatch(statement, normalize(sentence), re.IGNORECASE)
    if not m:
        return None
    if spec["mode"] == "example":
        return (f"possible transfer of example property '{spec['property']}' on '{spec['objects'][0]}' "
                f"to '{m['domain']}' in '{m.group()}'.")
    return (f"possible affirmative answer to the declared open question about '{spec['property']}' "
            f"across parameter scope '{m['domain']}' in '{m.group()}'.")
