"""Guardrail d'entrée : bloque les mots-clés d'attaque avec RegexMatch (Guardrails Hub).

Les motifs sont expliqués sur le site (portfolio/components/chatbot/guide-content.ts) :
garder les deux fichiers synchronisés.
"""

from chatbot.guards.base import GuardResult

# Nom affiché -> motif interdit (insensible à la casse).
BANNED_PATTERNS: dict[str, str] = {
    "Ignorer les consignes": r"(ignor|oubli|forget|disregard)\w*\s+(\S+\s+){0,3}(instructions?|consignes?|r[eè]gles?|rules)",
    "Demander le prompt système": r"(prompt|message)\s+(syst[eè]me|system)|system\s+prompt",
    "Nouvelles consignes": r"nouvel(le)?s?\s+(consignes?|instructions?|r[eè]gles?)|restrictions?\s+(sont\s+)?(suspendue|lev[ée]e|d[ée]sactiv[ée]e)s?",
    "Faux format système": r"\[\s*/?\s*(system|syst[eè]me|admin)\s*\]",
    "Personnage sans règles": r"sans\s+(aucune\s+)?(restrictions?|r[eè]gles?|limites?|filtres?)|aucune\s+r[eè]gle|\bDAN\b",
    "Texte encodé (base64)": r"[A-Za-z0-9+/]{24,}={0,2}",
}


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
            label: GuardrailsGuard().use(RegexMatch(regex=forbid(pattern), match_type="search", on_fail="noop"))
            for label, pattern in BANNED_PATTERNS.items()
        }

    def check(self, text: str) -> GuardResult:
        """Renvoie un échec au premier motif interdit trouvé dans le texte."""
        for label, guard in self.guards.items():
            if not guard.validate(text).validation_passed:
                return GuardResult(passed=False, reason=f"Motif interdit détecté : « {label} ».")
        return GuardResult(passed=True)
