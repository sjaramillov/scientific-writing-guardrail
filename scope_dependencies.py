"""Bilingual assertion frames for a quantity that may depend on a parameter."""

import re
import unicodedata
from functools import lru_cache


def _normal(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def validate(rule):
    if not isinstance(rule, dict) or set(rule) != {"kind", "source", "en", "es"}:
        raise ValueError("dependency rule requires kind, source, en and es")
    if rule["kind"] != "dependency" or not isinstance(rule["source"], str) or not rule["source"].strip():
        raise ValueError("expected dependency rule with a nonempty source excerpt")
    for lang in ("en", "es"):
        edition = rule[lang]
        roles = ("quantity", "parameter")
        allowed = {"quantity", "parameter", "quantity_symbols", "parameter_symbols", "limit_values"}
        if not isinstance(edition, dict) or not set(roles) <= set(edition) <= allowed:
            raise ValueError(f"{lang} dependency needs quantity and parameter aliases")
        for key, values in edition.items():
            if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
                raise ValueError(f"{lang} dependency {key} must be a list of nonempty strings")
        for role in roles:
            if not edition[role] and not edition.get(role + "_symbols"):
                raise ValueError(f"{lang} dependency {role} has no words or symbols")
        # R and r can name distinct quantities. Word aliases match both cases.
        words = [{_normal(a).casefold() for a in edition[k]} for k in roles]
        symbols = [{_normal(a) for a in edition.get(k + "_symbols", [])} for k in roles]
        overlap = (words[0] & words[1] or symbols[0] & symbols[1]
                   or words[0] & {s.casefold() for s in symbols[1]}
                   or words[1] & {s.casefold() for s in symbols[0]})
        if overlap:
            raise ValueError(f"{lang} dependency designates one expression for both roles")


def _role(words, symbols):
    aliases = [re.escape(w) for w in words]
    # Keep mathematical identifiers exact, including primes and subscripts.
    for symbol in symbols:
        aliases.append(r"(?-i:" + re.escape(symbol) + r")(?![′″'\^_])")
    return r"(?<!\w)(?:" + "|".join(aliases) + r")(?!\w)"


def _frames(lang, q, p, limit_values):
    # Editors can name a limiting value at which a uniform guarantee would
    # strengthen the source. A fixed quantity on a restricted subinterval
    # need not yield the same guarantee at the limiting value.
    limit = "(?-i:" + "|".join(re.escape(v) for v in limit_values) + ")"

    if lang == "en":
        entity = rf"(?:the |this |our )?{q}"
        parameter = rf"(?:the |this )?{p}"
        universal = rf"(?:every|each|any|all) (?:values? of (?:the )?)?{p}"
        single = rf"(?:a single|one(?: common| fixed)?|a common|the same) {q}"
        motion = r"(?:varies|changes|decreases|increases)"
        if limit_values:
            motion = rf"(?:{motion}|(?:decreases|increases|tends) (?:to|towards?) {limit}|approaches {limit})"
        return (
            rf"{single} (?:is (?:therefore |thus )?(?:enough|sufficient|valid)|(?:therefore |thus )?(?:suffices|works|applies)) for {universal}",
            rf"{entity} (?:is (?:independent of|uniform in)|does not depend on) {parameter}",
            rf"{entity} can be (?:chosen|selected) (?:independently of|uniformly in) {parameter}",
            rf"we (?:can )?(?:choose|select) (?:a |the )?{q} (?:independently of|uniformly in) {parameter}",
            rf"{entity} (?:can be (?:kept|held)|is (?:kept|held)|remains|stays) fixed (?:as|while|when) {parameter} {motion}",
        )
    entity = rf"(?:(?:el|la|esta|este|nuestra|nuestro) )?{q}"
    parameter = rf"(?:(?:el|la|esta|este) )?{p}"
    universal = rf"(?:cualquier|cada|tod[oa]|tod[oa]s l[oa]s) (?:valor(?:es)? (?:de (?:la )?|del ))?{p}"
    single = rf"(?:(?:un|una) (?:sol[oa]|mism[oa]|únic[oa])|(?:el|la) mism[oa]) {q}"
    motion = r"(?:varía|cambia|disminuye|aumenta|decrece|crece)"
    if limit_values:
        motion = rf"(?:{motion}|(?:disminuye|aumenta|decrece|crece|tiende|se aproxima) (?:a|hacia) {limit})"
    return (
        rf"{single} (?:basta|sirve|es suficiente|es válid[oa]) para {universal}",
        rf"basta {single} para {universal}",
        rf"{entity} (?:(?:es independiente|no depende) (?:de |del )|es uniforme (?:en |respecto (?:a |al |de |del ))){parameter}",
        rf"{entity} puede (?:elegirse|escogerse) (?:independientemente (?:de |del )|uniformemente en ){parameter}",
        rf"(?:elegimos|escogemos|podemos (?:elegir|escoger)) (?:el |la |un |una )?{q} (?:independientemente (?:de |del )|uniformemente en ){parameter}",
        rf"{entity} (?:puede (?:mantenerse|quedar)|se mantiene|permanece) fij[oa] (?:cuando|mientras|conforme|a medida que) {parameter} {motion}",
    )


@lru_cache(maxsize=256)
def _compiled(lang, q_words, q_symbols, p_words, p_symbols, limit_values):
    quantity = "(?P<quantity>" + _role(q_words, q_symbols) + ")"
    parameter = "(?P<parameter>" + _role(p_words, p_symbols) + ")"
    return tuple(re.compile(frame, re.IGNORECASE) for frame in _frames(lang, quantity, parameter, limit_values))


# Only accept an assertion starting at a clause boundary, optionally after an
# explicit discourse marker. A quoted claim, question, hypothesis or uncertain
# reporting clause cannot silently become an author's unconditional assertion.
_PREFIX = {
    "en": re.compile(r"(?:(?:therefore|thus|hence|in particular|once (?:chosen|selected|fixed)),? )*", re.I),
    "es": re.compile(r"(?:(?:por (?:tanto|consiguiente)|así|en particular|una vez (?:elegid[oa]|seleccionad[oa]|fijad[oa])),? )*", re.I),
}
_CLAUSE = {
    "en": re.compile(r"(?:;|,\s*(?:but|yet|whereas|however)\b)"
                     r"(?!\s*(?:but\s+)?(?:only|if|when|assuming|under|except|provided|unless)\b)\s*", re.I),
    "es": re.compile(r"(?:;|,\s*(?:pero|mientras que|sin embargo)\b)"
                     r"(?!\s*(?:pero\s+)?(?:s[oó]lo|solamente|únicamente|si|cuando|salvo|suponiendo|bajo)\b)\s*", re.I),
}


def findings(sentence, rule, lang):
    """Identify assertions that make the declared quantity independent of its parameter."""
    edition = rule[lang]
    aliases = [tuple(sorted({_normal(v) for v in edition.get(key, [])}, key=lambda v: (-len(v), v)))
               for key in ("quantity", "quantity_symbols", "parameter", "parameter_symbols", "limit_values")]
    patterns = _compiled(lang, *aliases)
    found = []
    for clause in _CLAUSE[lang].split(_normal(sentence)):
        clause = clause.strip().rstrip(".!…").rstrip()
        if not clause or clause.endswith("?") or clause.startswith("¿"):
            continue
        start = _PREFIX[lang].match(clause).end()
        for pattern in patterns:
            match = pattern.fullmatch(clause, start)
            if match:
                found.append(f"quantity '{match['quantity']}' may depend on parameter "
                             f"'{match['parameter']}'; possible uniformity asserted in '{match.group()}'.")
                break
    return found
