"""Guardrail d'entrée : bloque les mots-clés d'attaque avec RegexMatch (Guardrails Hub).

Seule source des motifs : GET /features les renvoie, et le site les affiche dans son guide.
"""

from dataclasses import dataclass

from chatbot.guards.base import GuardResult


@dataclass(frozen=True)
class BannedPattern:
    """Un motif interdit, avec de quoi l'afficher et l'expliquer sur le site."""

    label: str
    regex: str  # insensible à la casse
    explanation: str


BANNED_PATTERNS: list[BannedPattern] = [
    BannedPattern(
        "Ignorer les consignes",
        r"(ignor|oubli|forget|disregard)\w*\s+(\S+\s+){0,3}(instructions?|consignes?|r[eè]gles?|rules)",
        "Un mot qui commence par « ignor » ou « oubli » (ou forget, disregard), puis au plus 3 mots, puis "
        "« instructions », « consignes » ou « règles ». Attrape « Oublie toutes tes règles », pas « Ignore la théorie ».",
    ),
    BannedPattern(
        "Demander le prompt système",
        r"(prompt|message)\s+(syst[eè]me|system)|system\s+prompt",
        "« prompt système », « message système » ou « system prompt ».",
    ),
    BannedPattern(
        "Nouvelles consignes",
        r"nouvel(le)?s?\s+(consignes?|instructions?|r[eè]gles?)|restrictions?\s+(sont\s+)?(suspendue|lev[ée]e|d[ée]sactiv[ée]e)s?",
        "« nouvelle(s) consigne(s) / instruction(s) / règle(s) », ou des restrictions « suspendues », « levées » "
        "ou « désactivées ».",
    ),
    BannedPattern(
        "Faux format système",
        r"\[\s*/?\s*(system|syst[eè]me|admin)\s*\]",
        "Une balise comme [SYSTEM], [/SYSTEM] ou [ADMIN]. Les crochets sont précédés d'un \\ car ils ont un sens "
        "spécial en regex.",
    ),
    BannedPattern(
        "Personnage sans règles",
        r"sans\s+(aucune\s+)?(restrictions?|r[eè]gles?|limites?|filtres?)|aucune\s+r[eè]gle|\bDAN\b",
        "« sans (aucune) restriction / règle / limite / filtre », « aucune règle », ou le mot DAN seul "
        "(grâce à \\b, « dans » n'est pas concerné).",
    ),
    BannedPattern(
        "Texte encodé (base64)",
        r"[A-Za-z0-9+/]{24,}={0,2}",
        "Au moins 24 caractères d'affilée parmi lettres, chiffres, + et /, sans espace : la forme d'un texte encodé "
        "en base64. Aucun mot français n'est aussi long.",
    ),
]


def forbid(pattern: str) -> str:
    """Transforme « le texte contient le motif » en « le texte ne contient PAS le motif ».

    RegexMatch bloque ce qui NE correspond PAS à sa regex : on lui donne donc un lookahead négatif (?!…).
    """
    return rf"(?i)^(?![\s\S]*(?:{pattern}))"


class RegexKeywordsGuard:
    """Bloque le message s'il contient un des motifs de BANNED_PATTERNS. Pas de seuil : trouvé ou pas."""

    name = "regex_keywords"

    def __init__(self) -> None:
        # Import local : le validateur n'est requis que si ce guard est activé.
        from guardrails import Guard as GuardrailsGuard
        from guardrails_ai.regex_match import RegexMatch

        # Un validateur par motif, pour savoir lequel a bloqué.
        self.guards = {
            pattern.label: GuardrailsGuard().use(
                RegexMatch(regex=forbid(pattern.regex), match_type="search", on_fail="noop")
            )
            for pattern in BANNED_PATTERNS
        }

    def check(self, text: str) -> GuardResult:
        """Renvoie un échec au premier motif interdit trouvé dans le texte."""
        for label, guard in self.guards.items():
            if not guard.validate(text).validation_passed:
                return GuardResult(passed=False, reason=f"Motif interdit détecté : « {label} ».")
        return GuardResult(passed=True)
