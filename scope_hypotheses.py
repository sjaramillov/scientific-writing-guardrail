"""Recognize an editorial claim that a source condition can be dispensed with."""
import re

from scope_relations import _normalize, _slot


_ROLES = {"subjects", "hypotheses", "domains", "conclusions"}


def validate(rule):
    if not isinstance(rule, dict) or set(rule) != {"kind", "source", "en", "es"}:
        raise ValueError("A hypothesis rule requires kind, source, en and es")
    if rule["kind"] != "hypothesis" or not isinstance(rule["source"], str) or not rule["source"].strip():
        raise ValueError("Expected a hypothesis rule with a nonempty source quotation")
    for lang in ("en", "es"):
        terms = rule[lang]
        if not isinstance(terms, dict) or set(terms) != _ROLES:
            raise ValueError(f"{lang}: expected subjects, hypotheses, domains and conclusions")
        for role in sorted(_ROLES):
            values = terms[role]
            if (not isinstance(values, list) or not values
                    or not all(isinstance(v, str) and v.strip() for v in values)):
                raise ValueError(f"{lang}: {role} requires nonempty literal phrases")


_EN_DET = r"(?:(?:the|an?|its|their) )?"
_ES_DET = r"(?:(?:el|la|los|las|un|una|su|sus) )?"
_EN_LOSS = r"(?:need not (?:admit|have|satisfy|possess|be)|may (?:lack|fail to satisfy)|does not (?:need|have) to (?:be|have|admit|satisfy))"
_ES_LOSS = r"(?:puede carecer de|puede incumplir|no necesita(?: (?:tener|admitir|cumplir|ser))?|no tiene por qué (?:tener|admitir|cumplir|ser))"

# Dismissing a particular sufficient condition leaves room for another. In
# this frame the author also explicitly removes all alternatives in the
# declared domain. "Without additional assumptions" alone does not do this.
_EN_WAIVER = (
    r"(?:(?:(?:even )?in the absence of|(?:even )?without) any (?:other |further )?"
    r"(?:hypothes(?:is|es)|conditions?|assumptions?|restrictions?) (?:on|about)|"
    r"(?:even (?:if|when) )?nothing (?:else|further) is assumed (?:about|of)) "
)
_ES_WAIVER = (
    r"(?:(?:(?:incluso|aun|aún) )?si no se (?:supone|asume|exige) nada más (?:sobre|de)|"
    r"(?:(?:incluso|aun|aún) )?sin (?:ninguna otra|ningún otro|otra) "
    r"(?:hipótesis|condición|supuesto|restricción) (?:sobre|de)|"
    r"en ausencia de (?:cualquier otra|cualquier otro) "
    r"(?:hipótesis|condición|supuesto|restricción) (?:sobre|de)) "
)


def _frames(terms, lang):
    subject = _slot("subjects", terms)
    hypothesis = _slot("hypotheses", terms)
    domain = _slot("domains", terms)
    conclusion = _slot("conclusions", terms)
    # Match a whole assertion. A reporting denial, a question, a hypothetical
    # premise or a retained condition changes what is being asserted.
    if lang == "en":
        intro = r"(?:(?:hence|therefore|thus|consequently|in particular),? )?"
        loss = rf"{_EN_DET}{subject} {_EN_LOSS} {_EN_DET}{hypothesis}"
        waiver = rf"{_EN_WAIVER}{_EN_DET}{domain}"
        claim = rf"{_EN_DET}{conclusion} (?:still )?(?:holds?|appl(?:ies|y)|follows?|remains? valid)"
        waiver_of_hypothesis = rf"(?:even )?without (?:assuming |imposing |requiring )?{_EN_DET}{hypothesis}"
        absent = r"(?:lacks?|fails? to satisfy|(?:does|do) not (?:have|admit|satisfy)|(?:is|are) not)"
        claim_without = rf"{claim} (?:even )?(?:when|if) {_EN_DET}{subject} {absent} {_EN_DET}{hypothesis}"
        dispenses = rf"{_EN_DET}{conclusion} (?:does not|do not|doesn['’]t|don['’]t) require {_EN_DET}{hypothesis}"
        unnecessary = rf"{_EN_DET}{hypothesis} (?:is|are) (?:unnecessary|not (?:required|necessary)) for {_EN_DET}{conclusion}"
    else:
        intro = r"(?:(?:así|por tanto|por lo tanto|por consiguiente|en particular),? )?"
        loss = rf"{_ES_DET}{subject} {_ES_LOSS} {_ES_DET}{hypothesis}"
        waiver = rf"{_ES_WAIVER}{_ES_DET}{domain}"
        claim = rf"{_ES_DET}{conclusion} (?:también )?(?:se (?:cumple|aplica|mantiene)|sigue siendo válid[oa]|vale)"
        waiver_of_hypothesis = rf"(?:(?:incluso|aun|aún) )?sin (?:suponer |imponer |exigir )?{_ES_DET}{hypothesis}"
        absent = r"(?:carece de|no (?:tiene|admite|satisface|cumple|es))"
        claim_without = rf"{claim} (?:(?:incluso|aun|aún) )?(?:cuando|si) {_ES_DET}{subject} {absent} {_ES_DET}{hypothesis}"
        dispenses = rf"{_ES_DET}{conclusion} no (?:requiere[n]?|necesita[n]?) {_ES_DET}{hypothesis}"
        unnecessary = rf"{_ES_DET}{hypothesis} (?:es|son) innecesari[oa]s? para {_ES_DET}{conclusion}"
    return [
        intro + loss + r",? " + waiver,
        intro + claim + " " + waiver_of_hypothesis,
        intro + claim_without,
        intro + dispenses,
        intro + unnecessary,
    ]


def findings(sentence, rule, lang):
    """Return source-attributed review cues, not a verdict on necessity."""
    assertion = _normalize(sentence).rstrip(".!").rstrip()
    terms = rule[lang]
    for frame in _frames(terms, lang):
        match = re.fullmatch(frame, assertion, re.IGNORECASE)
        if not match:
            continue
        fields = match.groupdict()
        conclusion = fields.get("conclusions") or terms["conclusions"][0]
        if fields.get("domains"):
            return [f"hypothesis '{fields['hypotheses']}' waived for '{fields['subjects']}' "
                    f"with other conditions on '{fields['domains']}' also waived; "
                    f"compare the declared conclusion '{conclusion}'. Matched '{assertion}'."]
        subject = fields.get("subjects") or terms["subjects"][0]
        return [f"conclusion '{conclusion}' asserted without the declared hypothesis "
                f"'{fields['hypotheses']}' on '{subject}'. Matched '{assertion}'."]
    return []
