"""Guardrail de sortie : bloque les réponses qui ressemblent au prompt système (Guardrails Hub)."""

from chatbot.guards.base import GuardResult
from chatbot.system_prompt import SYSTEM_PROMPT


class SystemPromptLeakGuard:
    """Bloque la réponse si elle ressemble trop au prompt système."""

    name = "system_prompt_leak"

    def __init__(self, threshold: float) -> None:
        # threshold : ressemblance de 0 à 100 ; bloqué si ressemblance > threshold (défaut dans factory.py).
        # Import local : le validateur n'est requis que si ce guard est activé.
        from guardrails import Guard as GuardrailsGuard
        from guardrails_ai.detect_system_prompt_leakage import DetectSystemPromptLeakage

        detector = DetectSystemPromptLeakage(
            system_prompt=SYSTEM_PROMPT,
            threshold=threshold,  # score de ressemblance de 0 à 100
            on_fail="noop",  # renvoie un échec au lieu de lever une exception
        )
        self.guard = GuardrailsGuard().use(detector)

    def check(self, text: str) -> GuardResult:
        """Renvoie un échec si la réponse ressemble au prompt système."""
        outcome = self.guard.validate(text)
        if outcome.validation_passed:
            return GuardResult(passed=True)
        return GuardResult(passed=False, reason="La réponse ressemble trop au prompt système.")
