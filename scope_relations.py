"""Check explicit predicate/argument contrasts declared by a bilingual editor."""
import re
import unicodedata


_FRAMES = {"preservation", "operator", "domain", "classification", "action"}
_ROLES = ("subject", "predicate", "licensed", "review")


def _normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def _literal(text):
    # Preserve individual variable names in slots, including f/F and δ/Δ.
    # Longer scientific names and ordinary prose follow normal case folding.
    pieces = re.split(r"(?<!\w)([^\W\d_])(?!\w)", _normalize(text))
    return "".join(f"(?-i:{re.escape(part)})" if i % 2 else re.escape(part.casefold())
                   for i, part in enumerate(pieces))


def validate(rule):
    if not isinstance(rule, dict) or set(rule) != {"kind", "source", "en", "es"}:
        raise ValueError("A relation rule requires kind, source, en and es")
    if rule["kind"] != "relation" or not isinstance(rule["source"], str) or not rule["source"].strip():
        raise ValueError("Expected a relation with a nonempty source quotation")
    for lang in ("en", "es"):
        terms = rule[lang]
        if not isinstance(terms, dict) or set(terms) != {"frame", *_ROLES}:
            raise ValueError(f"{lang}: expected frame, subject, predicate, licensed and review")
        if not isinstance(terms["frame"], str) or terms["frame"] not in _FRAMES:
            raise ValueError(f"{lang}: unknown relation frame")
        for role in _ROLES:
            values = terms[role]
            if (not isinstance(values, list) or not values
                    or not all(isinstance(s, str) and s.strip() for s in values)):
                raise ValueError(f"{lang}: {role} requires nonempty literal phrases")
        licensed = {_literal(v) for v in terms["licensed"]}
        if any(_literal(v) in licensed for v in terms["review"]):
            raise ValueError(f"{lang}: the same value cannot be both licensed and under review")
    if rule["en"]["frame"] != rule["es"]["frame"]:
        raise ValueError("Both editions must use the same relation frame")


# Generic connective, article and agreement slots. A frame consumes the whole
# assertion: if a condition, another subject or a reporting denial intervenes,
# we cannot safely bind these roles. Unknown constructions are left to review.
_INTRO = {
    "en": r"(?:(?:in particular|therefore|thus|hence|consequently|in fact),? |by (?!assumption\b|hypothesis\b|supposition\b|contradiction\b)[\w-]+, )?",
    "es": r"(?:(?:en particular|por tanto|por lo tanto|por consiguiente|así pues|así|de hecho),? |por (?!hipótesis\b|suposición\b|contradicción\b)[\w-]+, )?",
}
_DET = {"en": r"(?:(?:the|a|an) )?", "es": r"(?:(?:el|la|los|las|un|una|unos|unas) )?"}
_ALL = {"en": r"(?:every|each|all|any) ", "es": r"(?:tod[oa]s?|cada|cualquier) "}
_COPULA = {"en": r"(?:is|are)", "es": r"(?:es|son)"}
_ADVERB = {"en": r"(?:(?:also|therefore|thus|necessarily) )?",
           "es": r"(?:(?:también|por tanto|necesariamente|así) )?"}
# Keep a trailing restriction attached to the assertion it qualifies.
_CLAUSE = {
    "en": re.compile(r"(?:;|,\s*(?:but|yet|whereas|however)\b)"
                     r"(?!\s*(?:but\s+)?(?:only|if|when|assuming|under|except|provided|unless)\b)\s*", re.I),
    "es": re.compile(r"(?:;|,\s*(?:pero|mientras que|sin embargo)\b)"
                     r"(?!\s*(?:pero\s+)?(?:s[oó]lo|solamente|únicamente|si|cuando|salvo|suponiendo|bajo)\b)\s*", re.I),
}



def _slot(name, terms):
    words = sorted({_normalize(v) for v in terms[name]}, key=len, reverse=True)
    return "(?P<" + name + ">" + "|".join(_literal(v) for v in words) + ")"


def _frame(terms, lang):
    subject, predicate, value = (_slot(role, terms) for role in ("subject", "predicate", "review"))
    det, universal, copula, adverb = _DET[lang], _ALL[lang], _COPULA[lang], _ADVERB[lang]
    frame = terms["frame"]
    if frame == "preservation":
        # Both arguments must come from the same review class. Synonyms and
        # singular/plural renderings can differ between input and output.
        destination = value.replace("(?P<review>", "(?P<destination>", 1)
        preposition = "(?:to|into)" if lang == "en" else "a"
        return (rf"{universal}{det}{subject} {adverb}{predicate} {adverb}{det}{value} "
                rf"{preposition} {det}{destination}")
    if frame == "operator":
        prep = "of " if lang == "en" else "(?:de |del )"
        return rf"{det}{value} {prep}{det}{subject} {copula} {adverb}{predicate}"
    if frame == "domain":
        prep = "(?:in|over|on)" if lang == "en" else "(?:en|sobre)"
        return rf"{universal}{det}{subject} {copula} {adverb}{predicate} {prep} {det}{value}"
    if frame == "classification":
        complement = rf"{value} {predicate}" if lang == "en" else rf"{predicate} {value}"
        return rf"{det}{subject} {copula} {adverb}{det}{complement}"
    outcome = "(?:in the negative|in the affirmative)" if lang == "en" else "en sentido (?:negativo|afirmativo)"
    return rf"{det}{subject} {adverb}{predicate} {adverb}(?:{outcome} )?{det}{value}(?: {outcome})?"


def findings(sentence, rule, lang):
    """Return evidence for intact assertions matching a declared role contrast."""
    terms = rule[lang]
    pattern = _INTRO[lang] + _frame(terms, lang)
    issues = []
    for clause in _CLAUSE[lang].split(_normalize(sentence)):
        clause = clause.strip().rstrip(".!…").rstrip()
        match = re.fullmatch(pattern, clause, re.I)
        if match:
            fields = match.groupdict()
            destination = (f" to '{fields['destination']}'" if "destination" in fields else "")
            issues.append(
                f"relation {terms['frame']}: subject '{fields['subject']}', predicate '{fields['predicate']}', "
                f"review value '{fields['review']}'{destination}; editor-declared comparison "
                f"'{terms['licensed'][0]}'. Matched '{match.group()}'."
            )
    return issues
