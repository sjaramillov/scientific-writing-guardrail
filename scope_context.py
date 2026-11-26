"""Recognize bounded reporting denials and open questions in normalized EN/ES text."""

import re


# Recognize the reporting clause from its beginning. A suffix search for
# "does not claim" would also match "It is false that the theorem does not claim".
_EN_VERB = r"(?:claim|assert|state|say|show|prove|establish|imply|entail|guarantee|conclude|demonstrate)"
_EN_SUBJECT = r"(?:(?:the|this|our) (?:theorem|result|paper|article|study|proof|construction|argument)|it)"
_EN_PLURAL = r"(?:we|the authors|the researchers|(?:the|these|our) results)"
_EN_ISOLATION = r"(?:on (?:its|their) own|by (?:itself|themselves)|(?:taken )?in isolation)"
_ES_ISOLATION = r"(?:por sí (?:sol[oa]s?|mism[oa]s?)|(?:considerad[oa]s?|tomad[oa]s?) aisladamente)"


def with_isolation(subject, qualifier):
    # Only admit a known qualifier in the subject slot. Stripping all text
    # before a comma would also erase inversions such as "It is false that,".
    return rf"{subject}(?:, {qualifier},| {qualifier})?"


_EN_REPORT = (
    rf"(?:(?:{with_isolation(_EN_SUBJECT, _EN_ISOLATION)} (?:does not|doesn['’]t)|"
    rf"{with_isolation(_EN_PLURAL, _EN_ISOLATION)} (?:do not|don['’]t)) "
    rf"{_EN_VERB}|{_EN_SUBJECT} makes no claim)"
)
_EN_INFERENCE = (
    r"(?:it (?:does not|doesn['’]t) follow(?: from (?:this|this result|the theorem))?|"
    r"(?:we|one|the authors) (?:cannot|can['’]t) (?:conclude|infer|deduce))"
)
_EN_ERROR = (
    r"it (?:is|would be) (?:a mistake|an error|incorrect|unjustified|misleading) to "
    r"(?:say|claim|assert|conclude|infer|assume)"
)
_EN_DENIAL = re.compile(
    rf"(?:(?:although|though) )?(?:{_EN_ISOLATION},? )?(?:{_EN_REPORT}|{_EN_INFERENCE}|{_EN_ERROR})"
    r"(?: that)?"
    r"(?: (?:it|this|the result|the conclusion) (?:holds for|applies to))?"
    r"(?: (?:a|an))?"
)

_ES_VERB = r"(?:afirma|asegura|acredita|demuestra|establece|implica|sostiene|garantiza|prueba|indica|dice|concluye)"
_ES_PLURAL_VERB = r"(?:afirman|aseguran|acreditan|demuestran|establecen|sostienen|garantizan|prueban|dicen|concluyen)"
_ES_SUBJECT = (
    r"(?:(?:el|este|nuestro) (?:teorema|resultado|artículo|estudio|argumento)|"
    r"(?:la|esta|nuestra) (?:prueba|demostración|construcción))"
)
_ES_REPORT = (
    rf"(?:(?:{with_isolation(_ES_SUBJECT, _ES_ISOLATION)} )?(?:no|tampoco) {_ES_VERB}|"
    rf"{with_isolation('(?:los autores|las autoras)', _ES_ISOLATION)} (?:no|tampoco) {_ES_PLURAL_VERB}|no se {_ES_VERB}|"
    r"(?:no|tampoco) (?:afirmamos|sostenemos|aseguramos|mostramos|concluimos|demostramos))"
)
_ES_INFERENCE = (
    r"(?:(?:(?:de (?:ello|esto|ahí|aquí|este resultado)|del teorema) )?"
    r"(?:no|tampoco) se (?:sigue|deduce|desprende|infiere)|"
    r"(?:no|tampoco) (?:se puede|podemos|cabe) (?:afirmar|concluir|inferir|deducir))"
)
_ES_ERROR = (
    r"(?:es|sería) (?:un error|incorrecto|injustificado|engañoso) "
    r"(?:decir|afirmar|sostener|concluir|inferir|suponer)"
)
_ES_DENIAL = re.compile(
    rf"(?:aunque )?(?:{_ES_ISOLATION},? )?(?:{_ES_REPORT}|{_ES_INFERENCE}|{_ES_ERROR}) que"
    r"(?: (?:esto|el resultado|la conclusión) "
    r"(?:se cumpla|se aplique|valga|vale|se cumple|se aplica) (?:a|para|con))?"
    r"(?: (?:un|una))?"
)

_DENIAL = {"en": _EN_DENIAL, "es": _ES_DENIAL}
# An indirect question can contain universal wording without asserting it.
# Require its introductory clause at the sentence boundary. "It is known
# whether" and "we now know that" do not introduce an open question.
_OPEN_QUESTION = {
    "en": re.compile(
        r"(?:it is (?:not (?:yet )?known|(?:still )?(?:unknown|unresolved|unclear|an open question))|"
        r"it remains (?:unknown|unresolved|unclear|open|an open question)|"
        r"we (?:do not|don['’]t) (?:yet )?know) whether\b"
    ),
    "es": re.compile(
        r"(?:(?:(?:aún|todavía) )?(?:se desconoce|no se sabe|no sabemos)(?: (?:aún|todavía))?|"
        r"sigue sin saberse|sigue abierta la cuestión de|es una (?:cuestión|pregunta) abierta) si\b"
    ),
}
_ARTICLES = {"en": {"", "a", "an"}, "es": {"", "un", "una"}}
# In the same or immediately following clause, an explicit answer may settle
# the previously open question without repeating the quantifier.
_ANSWER = {
    "en": re.compile(
        r"(?:^|[,;:.!?—–]\s*|\b(?:but|yet|however|in fact|actually)\b[, ]+)"
        r"(?:(?:but|yet|however|in fact|actually|now)\b[, ]+)*"
        r"(?:(?:the|our) answer is (?:yes|affirmative)|we (?:now know|have (?:since |now )?proved) "
        r"(?:this|that it (?:is|does))|(?:this|it) has (?:since |now )?been (?:shown|proved)|"
        r"(?:yes|it (?:is|does))(?=[.!?;]|$))\b"
    ),
    "es": re.compile(
        r"(?:^|[,;:.!?—–]\s*|\b(?:pero|sin embargo|de hecho|en realidad)\b[, ]+)"
        r"(?:(?:pero|sin embargo|de hecho|en realidad|ahora)\b[, ]+)*"
        r"(?:(?:la|nuestra) respuesta es (?:sí|afirmativa)|(?:ya |ahora )?sabemos que sí|"
        r"(?:(?:ya|ahora) )?(?:lo demostramos|lo hemos demostrado)|sí que (?:lo es|se cumple)|"
        r"sí(?=[.!?;]|$))\b"
    ),
}
# A later explicit construction can supply its own witness. In the absence
# of that signal, a noun inside an unresolved question cannot establish it.
_INDEPENDENT_CONSTRUCTION = {
    "en": re.compile(r", (?:but|yet|and) (?:we|the authors) (?:construct|exhibit|give|find|provide)$"),
    "es": re.compile(r", (?:pero|y) (?:construimos|exhibimos|damos|encontramos|presentamos)$"),
}
_STOP = re.compile(r"[.!?;]")
_NEGATED_CONTENT = {
    "en": re.compile(r"\b(?:not|never|no|neither|nor)\b|n['’]t\b"),
    "es": re.compile(r"\b(?:no|nunca|jamás|tampoco|ni)\b"),
}
# Elliptical corrections can endorse the proposition without repeating its
# noun ("but we do"). Leave such a sentence for review even after a denial.
_CORRECTION = {
    "en": re.compile(
        r"\b(?:but|yet|however|in fact|nevertheless)\b[, ]+"
        r"(?:(?:in fact|actually|indeed) )?(?:it|we|they|this|that|the authors) "
        r"(?:do|does|did|is true|is so|holds)\b"
    ),
    "es": re.compile(
        r"\b(?:pero|sino que|sin embargo|de hecho|no obstante)\b[, ]+"
        r"(?:(?:nosotros|ellos|el teorema|los autores|en realidad) )?"
        r"(?:sí|así es|es cierto|es verdad|lo (?:hace|demuestra|afirma))\b"
    ),
}


def clause_prefix(text, start):
    sentence_start = max(text.rfind(c, 0, start) for c in ".!?;") + 1
    return text[sentence_start:start].strip()


def is_disclaimed(text, start, end, lang):
    """Whether this occurrence is inside a known denial or open-question frame.

    Offsets refer to the NFC, whitespace-normalized, casefolded text used for
    matching. Call once per occurrence, including later matches in a sentence.
    Negating a universal or its predicate can itself assert a new scientific
    claim, so a separate negative within the complement stays reviewable.
    """
    frame = clause_prefix(text, start)
    question = _OPEN_QUESTION[lang].match(frame)
    if question:
        if frame[question.end():].strip() not in _ARTICLES[lang]:
            return False
    elif not _DENIAL[lang].fullmatch(frame):
        return False
    stop = _STOP.search(text, end)
    if stop and stop.group() == "?":
        return False
    remainder = text[end:stop.start() if stop else len(text)]
    if question:
        if _ANSWER[lang].search(remainder):
            return False
        if stop and _ANSWER[lang].match(text[stop.end():].lstrip()):
            return False
    if _CORRECTION[lang].search(remainder):
        return False
    # Limit the double-negation check to the same clause. Enumerations or
    # unrecognized constructions can still require a human decision.
    complement = re.split(r"[,—–]|\b(?:but|yet|whereas|pero|sino|aunque)\b", remainder, maxsplit=1)[0]
    return _NEGATED_CONTENT[lang].search(text[start:end] + complement) is None


def is_unasserted_witness(text, start, end, lang):
    """A noun under a question, even a negated question, is not a witness."""
    frame = clause_prefix(text, start)
    question = _OPEN_QUESTION[lang].match(frame)
    if question and not _INDEPENDENT_CONSTRUCTION[lang].search(frame[question.end():]):
        return True
    return is_disclaimed(text, start, end, lang)
