"""Check an asserted change of mathematical scope using editor-declared roles."""
import re
from functools import lru_cache

from scope_relations import _literal, _normalize


# Each construction describes a grammatical relation. Its scientific nouns,
# predicates, stronger values and comparison classes come from the claim map.
_ROLES = {
    "relaxed_condition": ("subject", "retained", "excluded"),
    "partial_sufficiency": ("condition", "conclusion"),
    "excluded_instance": ("instance", "actor", "outcome"),
    "strengthened_value": ("subject", "value"),
    "discarded_condition": ("subject", "condition"),
    "unconditional_bound": ("condition", "quantity", "limit"),
    "eventual_bound": ("quantity", "index"),
    "wider_domain": ("subject", "domain"),
    "distributed_uniqueness": ("member", "object"),
}

# Spaces belonging to optional articles and modifiers are consumed here.
_WORDS = {
    "en": {
        "det": r"(?:(?:a|an|the) )?",
        "connector": r"(?:(?:therefore|thus|hence|consequently|accordingly|in particular|as a result),? )?",
        "adv": r"(?:(?:therefore|thus|still|always|necessarily|also) )?",
        "selected": r"(?:(?:chosen|selected|given|specified) )?",
        "all": r"(?:every |each |any |all (?:the )?)",
        "this": r"(?:this|that|the (?:same )?(?:result|conclusion|guarantee)|this (?:result|conclusion))",
        "holds": r"(?:(?:still|also) )?(?:holds|applies|remains (?:true|valid)|is (?:true|valid|guaranteed))",
        "strong": r"(?:needs?|requires?|equals?|must (?:be(?: exactly)?|equal|attain|have)|(?:has|have) exactly|(?:is|are) (?:exactly|necessarily(?: equal to)?))",
        "implies": r"(?:ensures?|implies?|guarantees?|establishes?|suffices? for|is sufficient for)",
        "discard": r"(?:discarding|dropping|removing|omitting|without(?: (?:assuming|requiring))?)",
        "source": r"(?:the (?:paper|theorem|result|argument|proof|authors)|we)",
        "quantity_bound": r"(?:infinitely many|arbitrarily many) <quantity> (?:of (?:size|length|order) )?(?:at most|no more than) <limit>",
    },
    "es": {
        "det": r"(?:(?:el|la|los|las|un|una|unos|unas) )?",
        "connector": r"(?:(?:por (?:tanto|lo tanto|consiguiente)|así(?: pues)?|en consecuencia|en particular|de ahí que),? )?",
        "adv": r"(?:(?:por tanto|entonces|así|siempre|necesariamente|también) )?",
        "selected": r"(?: (?:elegid[oa]s?|seleccionad[oa]s?|escogid[oa]s?|dad[oa]s?))?",
        "all": r"(?:tod[oa] |tod[oa]s (?:l[oa]s )?|cada |cualquier )",
        "this": r"(?:esto|eso|lo anterior|(?:esta|esa|la|la misma) (?:conclusión|garantía)|(?:este|ese|el|el mismo) resultado)",
        "holds": r"(?:(?:también|aún) )?(?:vale|rige|se (?:cumple|aplica|mantiene)|sigue siendo (?:ciert[oa]|válid[oa])|es (?:ciert[oa]|válid[oa]))",
        "strong": r"(?:necesita[n]?|requiere[n]?|deben? (?:ser(?: exactamente)?|alcanzar|tener)|tiene[n]? que (?:ser(?: exactamente)?|alcanzar|tener)|(?:tiene[n]?|vale[n]?) exactamente|(?:es|son) (?:exactamente|necesariamente)|equivale[n]? a)",
        "implies": r"(?:asegura[n]?|garantiza[n]?|implica[n]?|establece[n]?|basta[n]? para|es suficiente para)",
        "discard": r"(?:descartando|eliminando|omitiendo|retirando|sin(?: (?:suponer|exigir|imponer))?)",
        "source": r"(?:el (?:artículo|teorema|resultado|argumento)|la (?:demostración|prueba)|los autores)",
        "quantity_bound": r"(?:infinit[oa]s|arbitrariamente much[oa]s) <quantity> (?:de (?:tamaño|longitud|orden) )?(?:a lo sumo|como máximo) <limit>",
    },
}

_PATTERNS = {
    "relaxed_condition": {
        "en": (
            r"<this> <holds> for <all>(?:other )?<subject> (?:that|which) (?:is|are) <retained>,? (?:even if|even when|although) (?:it|they) <excluded>",
            r"<all>(?:other )?<subject> (?:that|which) (?:is|are) <retained> (?:has|have) (?:the same|this|that) property,? (?:even if|even when|although) (?:it|they) <excluded>",
        ),
        "es": (
            r"<this> <holds> para <all>(?:otr[oa]s? )?<subject> que (?:sea[n]?|es|son) <retained>,? (?:aunque|incluso si|aun cuando) <excluded>",
            r"<all><subject> que (?:sea[n]?|es|son) <retained> tiene[n]? (?:esta|esa|la misma) propiedad,? (?:aunque|incluso si|aun cuando) <excluded>",
        ),
    },
    "partial_sufficiency": {
        "en": (
            r"to (?:obtain|derive|establish|ensure) <det><conclusion>,? it (?:is (?:enough|sufficient)|suffices) to (?:check|verify|assume|require) <det><condition>",
            r"<det><condition> (?:alone |by itself )?<adv><implies> <adv><det><conclusion>",
            r"<this> (?:yields|gives) <det><conclusion> (?:from|under) <det><condition> alone",
            r"<det><conclusion> (?:follows|can be derived) from <det><condition> alone",
            r"for <det><conclusion>,? <det><condition> (?:alone )?(?:suffices|is enough|is sufficient)",
        ),
        "es": (
            r"para (?:obtener|deducir|establecer|garantizar) <det><conclusion>,? (?:basta(?: con)?|es suficiente) (?:comprobar|verificar|suponer|exigir) <det><condition>",
            r"(?:por sí sol[oa],? )?<det><condition> (?:por sí sol[oa] |por sí mism[oa] )?<adv><implies> <adv><det><conclusion>",
            r"<det><conclusion> se (?:deduce|sigue|deriva) (?:de |del )(?:la )?(?:sola )?<condition> (?:por sí sol[oa]|solamente)",
            r"para <det><conclusion>,? (?:basta(?: con)?|es suficiente) <det><condition>",
        ),
    },
    "excluded_instance": {
        "en": (
            r"(?:even )?(?:for|on|with) <det><instance>,? <det><actor> (?:will |can |must )?<adv>(?:return|produce|find|provide|guarantee|returns|produces|finds|provides|guarantees) <det><outcome>",
            r"<det><actor> (?:will |can |must )?<adv>(?:return|produce|find|provide|guarantee|returns|produces|finds|provides|guarantees) <det><outcome> (?:even )?(?:for|on) <det><instance>",
        ),
        "es": (
            r"(?:(?:incluso|aun|también) )?(?:para|con|en) <det><instance>,? <det><actor> <adv>(?:devolverá|devuelve|produce|producirá|encuentra|encontrará|proporciona|garantiza) <det><outcome>",
            r"<det><actor> <adv>(?:devolverá|devuelve|produce|producirá|encuentra|encontrará|proporciona|garantiza) <det><outcome> (?:(?:incluso|aun) )?(?:para|en) <det><instance>",
        ),
    },
    "strengthened_value": {
        "en": (
            r"<det><selected><subject> <adv><strong> <det><value>",
            r"<det><value> (?:is|are) (?:therefore )?(?:needed|required|necessary) (?:for|by) <det><selected><subject>",
        ),
        "es": (
            r"<det><subject><selected> <adv><strong> <det><value>",
            r"(?:se necesita[n]?|se requiere[n]?) <det><value> para <det><subject><selected>",
        ),
    },
    "discarded_condition": {
        "en": (
            r"<this> <holds> (?:even )?without (?:requiring|assuming) (?:that )?<det><subject> (?:to (?:satisfy|be|have)|satisfy|satisfies|have|has|be|is|are) <det><condition>",
            r"<this> <holds> (?:even )?(?:if|when) <det><subject> (?:fail(?:s)? to satisfy|(?:do|does) not satisfy|lack(?:s)?|(?:is|are) not) <det><condition>",
        ),
        "es": (
            r"<this> <holds> (?:(?:aun|incluso) )?sin (?:exigir|suponer|requerir|imponer) que <det><subject> (?:satisfaga[n]?|cumpla[n]?|tenga[n]?|sea[n]?) <det><condition>",
            r"<this> <holds> (?:aunque|incluso si) <det><subject> (?:no (?:satisfaga[n]?|cumpla[n]?|tenga[n]?|sea[n]?)) <det><condition>",
        ),
    },
    "unconditional_bound": {
        "en": (
            r"<discard> <det><condition> (?:still )?leaves (?:the (?:paper|theorem|argument)['’]s|our) guarantee of <quantity_bound>",
            r"(?:even )?<discard> <det><condition>,? <source> (?:still )?(?:guarantees?|establish(?:es)?|ensures?|proves?) <quantity_bound>",
            r"<source> (?:still )?(?:guarantees?|establish(?:es)?|ensures?|proves?) <quantity_bound> (?:even )?without <det><condition>",
        ),
        "es": (
            r"(?:(?:aun|incluso) )?<discard> <det><condition>,? <source> (?:todavía )?(?:garantiza[n]?|establece[n]?|asegura[n]?|demuestra[n]?) <quantity_bound>",
            r"<source> <adv>(?:garantiza[n]?|establece[n]?|asegura[n]?|demuestra[n]?) <quantity_bound> (?:(?:aun|incluso) )?sin <det><condition>",
        ),
    },
    "eventual_bound": {
        "en": (
            r"(?:the same|this|that) (?:bound|estimate|guarantee) <adv>(?:applies to|holds for|covers) <det><quantity> (?:at|for) (?:every|each|all) sufficiently large <index>",
            r"(?:from|beyond) (?:some|a certain) <index>(?: onwards?)?,? (?:the same|this|that) (?:bound|estimate) (?:covers|applies to|holds for) (?:all|every|each) <quantity>",
        ),
        "es": (
            r"(?:(?:la misma|esta|esa) (?:cota|estimación|garantía)) <adv>(?:se aplica a|vale para|cubre) (?:tod[oa]s? (?:l[oa]s )?|cada )<quantity> (?:a partir de (?:cierto|algún|un determinado)|para (?:todo|cada)) <index>(?: suficientemente grande)?",
            r"a partir de (?:cierto|algún) <index>,? (?:la misma|esta|esa) (?:cota|estimación) (?:cubre|se aplica a|vale para) (?:tod[oa]s (?:l[oa]s )?|cada )<quantity>",
        ),
    },
    "wider_domain": {
        "en": (
            r"<all><subject> (?:on|in|over|of) <det><domain> (?:has|have|satisfies|satisfy) (?:(?:the same|that|this) (?:property|conclusion|guarantee))",
            r"<this> <holds> (?:for|on|over|to) <all><subject> (?:on|in|over|of) <det><domain>",
        ),
        "es": (
            r"<all><subject> (?:en |sobre |de )<det><domain> (?:tiene[n]?|satisface[n]?|cumple[n]?) (?:la misma|esta|esa) (?:propiedad|conclusión|garantía)",
            r"<this> <holds> (?:para|en) <all><subject> (?:en |sobre |de )<det><domain>",
        ),
    },
    "distributed_uniqueness": {
        "en": (
            r"(?:<all>|each of the )<member> (?:on (?:its|their) own |separately |individually )?(?:has|have|admits|admit) (?:exactly one|a unique|one and only one) <object>",
            r"<all><member> (?:has|have|admits|admit) (?:exactly one|a unique|one and only one) <object> (?:on (?:its|their) own|separately|individually)",
        ),
        "es": (
            r"(?:<all>|cada un[oa] de l[oa]s )<member> (?:por separado |individualmente |por sí sol[oa] )?(?:tiene[n]?|admite[n]?) (?:exactamente un[oa]?|un[oa]? únic[oa]|un[oa]? sol[oa]) <object>",
            r"<all><member> (?:tiene[n]?|admite[n]?) (?:exactamente un[oa]?|un[oa]? únic[oa]|un[oa]? sol[oa]) <object> (?:por separado|individualmente)",
        ),
    },
}

_TOKEN = re.compile(r"<([a-z_]+)>")


def validate(rule):
    if not isinstance(rule, dict) or set(rule) != {"kind", "source", "en", "es"}:
        raise ValueError("contrast requires kind, source, en and es")
    if rule["kind"] != "contrast" or not isinstance(rule["source"], str) or not rule["source"].strip():
        raise ValueError("contrast requires a nonempty source quotation")
    for lang in ("en", "es"):
        spec = rule[lang]
        if not isinstance(spec, dict) or set(spec) != {"frame", "roles", "licensed"}:
            raise ValueError(f"{lang}: expected frame, roles and licensed")
        frame = spec["frame"]
        if not isinstance(frame, str) or frame not in _ROLES:
            raise ValueError(f"{lang}: unknown contrast frame")
        if not isinstance(spec["licensed"], str) or not spec["licensed"].strip():
            raise ValueError(f"{lang}: describe the source-supported assertion")
        roles = spec["roles"]
        if not isinstance(roles, dict) or set(roles) != set(_ROLES[frame]):
            raise ValueError(f"{lang}: {frame} expects roles {', '.join(_ROLES[frame])}")
        for name, aliases in roles.items():
            if not isinstance(aliases, list) or not aliases or not all(isinstance(v, str) and v.strip() for v in aliases):
                raise ValueError(f"{lang}: expected literal phrases for {name}")
    if rule["en"]["frame"] != rule["es"]["frame"]:
        raise ValueError("Both editions must use the same contrast frame")


@lru_cache(maxsize=256)
def _compiled(lang, frame, items):
    slots = {name: f"(?P<{name}>" + "|".join(_literal(v) for v in values) + ")"
             for name, values in items}
    def expand(template):
        def replace(match):
            name = match[1]
            return slots[name] if name in slots else expand(_WORDS[lang][name])
        return _TOKEN.sub(replace, template)

    return tuple(re.compile(expand("<connector>" + pattern), re.I)
                 for pattern in _PATTERNS[frame][lang])


def findings(sentence, rule, lang):
    """Match complete assertions; a qualification, denial or question can change their scope."""
    spec = rule[lang]
    roles = tuple((k, tuple(v)) for k, v in sorted(spec["roles"].items()))
    assertion = _normalize(sentence).rstrip(".!").rstrip()
    for pattern in _compiled(lang, spec["frame"], roles):
        match = pattern.fullmatch(assertion)
        if match:
            labels = ", ".join(f"{key} '{val}'" for key, val in match.groupdict().items())
            return [f"{spec['frame']}: {labels}. Compare the editor-declared scope "
                    f"'{spec['licensed']}'. Matched '{assertion}'."]
    return []
