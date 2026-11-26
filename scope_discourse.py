"""Bounded EN/ES wording for a universal restatement of an earlier claim."""

import re


# A period inside a decimal, DOI, or equation number has no following space.
# Include closing punctuation in the span so callers can inspect a whole sentence.
_STOP = re.compile(r"""[.!?…]+["'”’»)\]]*(?=\s|$)""")
_ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|p\. ej|p|pp|figs?|eqs?|thm|sec|dr|prof|et al)$", re.I)


def scope_segments(text):
    """Return sentence spans in the supplied text, without normalizing its offsets."""
    spans = []
    start = 0
    for stop in _STOP.finditer(text):
        if stop.group() == "." and _ABBREVIATION.search(text[max(0, stop.start() - 10):stop.start()]):
            continue
        while start < stop.end() and text[start].isspace():
            start += 1
        if start < stop.end():
            spans.append((start, stop.end()))
        start = stop.end()
    tail = text[start:]
    if tail.strip():
        spans.append((start + len(tail) - len(tail.lstrip()), start + len(tail.rstrip())))
    return spans


# Restrict subject, predicate AND domain. A bare "all", "universal", or "any"
# cannot establish what is being strengthened. In particular, "all its points"
# and "every viscosity" have their own explicit referents.
_ES_SUBJECT = (
    r"(?:esto|eso|lo anterior|esta (?:afirmación|propiedad|conclusión|observación)|"
    r"este (?:resultado|enunciado|argumento)|la (?:primera|última) (?:frase|oración|afirmación)|"
    r"la (?:frase|oración|afirmación|conclusión)(?: (?:anterior|previa))?|el (?:resultado|enunciado)(?: anterior)?)"
)
_EN_SUBJECT = (
    r"(?:this|that|it|(?:this|that) (?:result|claim|conclusion|statement|property|observation)|"
    r"the (?:(?:first|previous|preceding|last) )?(?:sentence|claim|statement|conclusion|result))"
)
_ES_CASES = r"(?:todos los casos(?: posibles)?|cada caso|cualquier caso|todos ellos|todas ellas)"
_EN_CASES = r"(?:all (?:possible )?cases|every case|each case|any case|all of them|any of them|each of them)"
# Removing restrictions on the domain of a result can widen its scope. The
# absence of additional restrictions, or restrictions on labels, does not.
_ES_UNRESTRICTED_DOMAIN = (
    r"sin (?:(?:ninguna )?restricción|restricciones) sobre "
    r"(?:la clase ambiente|el dominio de aplicación)"
)
_EN_UNRESTRICTED_DOMAIN = (
    r"without (?:any )?restrictions? on "
    r"(?:the ambient class|the domain of application)"
)
_ES_PREDICATE = (
    r"(?:(?:vale|valga|rige|se (?:cumpl[ea]|apli(?:ca|que))|funcion[ae]|es (?:válid[oa]|ciert[oa])) "
    rf"(?:(?:a|en|para) {_ES_CASES}|universalmente|sin excepci(?:ón|ones)|{_ES_UNRESTRICTED_DOMAIN})|"
    r"(?:es universal|tiene alcance universal)|"
    r"(?:puede (?:reforzarse|generalizarse|extenderse)|se puede (?:reforzar|generalizar|extender)) "
    rf"(?:a (?:una (?:afirmación|conclusión) universal|un enunciado universal|{_ES_CASES})))"
)
_EN_PREDICATE = (
    rf"(?:(?:holds?|appl(?:y|ies)|works?|is (?:valid|true)) (?:(?:in|for|to|across) {_EN_CASES}|"
    rf"universally|without exception|{_EN_UNRESTRICTED_DOMAIN})|(?:is universal|has universal scope)|"
    r"can be (?:strengthened|generali[sz]ed|extended) (?:to|into) "
    rf"(?:a universal (?:claim|statement|assertion|conclusion)|{_EN_CASES}))"
)

# The arbitrary-choice cue has to concern the choice itself. Its vocabulary
# omits qualifications such as "choice of notation" and bare "all of them".
_ES_CHOICE = (
    r"(?:(?:la|esta) elección (?:concreta|particular|específica|exacta) "
    r"(?:(?:es|sea|result[ae]) (?:irrelevante|indiferente)|no importa)|"
    r"(?:da igual|no importa) cuál (?:se elija|se escoja)|"
    r"cualquiera de (?:ellos|ellas) (?:sirve|funciona|daría el mismo resultado|"
    r"produce el mismo efecto|satisface (?:esa|esta) propiedad))"
)
_EN_CHOICE = (
    r"(?:(?:the|this) (?:specific|particular|exact) choice "
    r"(?:is (?:irrelevant|immaterial)|does not matter|makes no difference)|"
    r"it does not matter which (?:one|of them) is (?:selected|chosen)|"
    r"any (?:one )?of them (?:works|would work|will work|gives the same result|"
    r"produces the same effect|satisfies (?:that|this) property))"
)

# A restriction after "all cases" matters. Requiring a clause end or an explicit
# coordinator leaves continuations such as "we sampled" or "de la muestra" alone.
_CLAUSE_END = (
    r"(?!, (?:if|when|provided|unless|except|si|cuando|siempre que|salvo|excepto)\b)"
    r"""(?=$|[.!?…;:,)"'”’»\]]| (?:and|but|y|pero)\b)"""
)
_RESTATEMENTS = {
    "es": re.compile(rf"(?<!\w)(?:{_ES_SUBJECT} {_ES_PREDICATE}|{_ES_CHOICE}){_CLAUSE_END}"),
    "en": re.compile(rf"(?<!\w)(?:{_EN_SUBJECT} {_EN_PREDICATE}|{_EN_CHOICE}){_CLAUSE_END}"),
}


def universal_restatements(text, lang):
    """Spans start at the anaphoric subject so an outer denial can be evaluated."""
    return [match.span() for match in _RESTATEMENTS[lang].finditer(text)]
