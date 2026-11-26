"""Check an explicitly or locally resumed property against its declared domain."""
import re
import unicodedata


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def literal(phrase):
    return r"(?<!\w)" + re.escape(normalize(phrase)) + r"(?!\w)"


def validate(rule):
    for lang in ("en", "es"):
        spec = rule[lang]
        if not isinstance(spec, dict) or set(spec) != {"property", "objects", "witnesses", "extensions"}:
            raise ValueError("application requires property, objects, witnesses and extensions")
        for field in ("property", "objects"):
            if not isinstance(spec[field], str) or not spec[field].strip():
                raise ValueError(f"{lang}: application requires a nonempty {field}")
        for field in ("witnesses", "extensions"):
            values = spec[field]
            if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
                raise ValueError(f"{lang}: application requires a nonempty list of {field}")
        if any(normalize(v).casefold() == normalize(spec["objects"]).casefold() for v in spec["extensions"]):
            raise ValueError(f"{lang}: licensed and extended object classes overlap")
        for witness in spec["witnesses"]:
            if not all(re.search(literal(spec[k]), normalize(witness), re.I) for k in ("property", "objects")):
                raise ValueError(f"{lang}: each witness must include the declared property and object class")


# Witnesses start an affirmative sentence. Their full wording includes the
# licensed object class, which avoids binding a bare property in a question,
# an attribution denial or a discussion of a different object.
def witnessed(sentence, rule, lang):
    text = normalize(sentence).rstrip(".!")
    return any(text == normalize(w).rstrip(".!") for w in rule[lang]["witnesses"])


_SUBJECT = {"en": r"(?:this|that)(?: (?:property|result|conclusion))?",
            "es": r"(?:esto|eso|esta (?:propiedad|conclusión)|este resultado)"}
_PREDICATE = {"en": r"(?:holds|applies|works)(?: also)?",
              "es": r"(?:vale|funciona|se cumple|se aplica)(?: también)?"}
_OPEN_DOMAIN = {
    "en": r"without (?:any )?restrictions? on (?:the ambient class|the domain of application)",
    "es": r"sin (?:(?:ninguna )?restricción|restricciones) sobre (?:la clase ambiente|el dominio de aplicación)",
}


def extension(sentence, rule, lang):
    """Return the matched scope change for a bounded affirmative restatement."""
    spec = rule[lang]
    nouns = "(?-i:" + "|".join(re.escape(normalize(n)) for n in spec["extensions"]) + ")"
    if lang == "en":
        new_class = rf"(?:for|to) (?:all|every|each|any) (?P<objects>{nouns})(?: as well| too)?"
    else:
        new_class = rf"(?:para|a) (?:tod[oa]s? (?:l[oa]s? )?|cada |cualquier )(?P<objects>{nouns})(?: también)?"
    pat = rf"(?P<subject>{_SUBJECT[lang]}) {_PREDICATE[lang]} (?:{new_class}|(?P<unrestricted>{_OPEN_DOMAIN[lang]}))[.!]?"
    m = re.fullmatch(pat, sentence, re.I)
    if not m:
        return None
    added = m.group("objects") or m.group("unrestricted")
    detail = (f"property '{spec['property']}' applies to '{spec['objects']}'; "
              f"restatement '{m.group().rstrip('.!')}' extends it to '{added}'.")
    return detail
