"""Guardrail anti prompt injection : un LLM juge le message (Guardrails Hub)."""

from chatbot import config
from chatbot.guards.base import GuardResult


class PromptInjectionGuard:
    """Bloque les tentatives de prompt injection / jailbreak."""

    name = "prompt_injection"

    def __init__(self, threshold: float) -> None:
        # threshold : note du juge de 0 à 1 ; bloqué si note > threshold (défaut dans factory.py).
        # Import local : le validateur n'est requis que si ce guard est activé.
        from guardrails import Guard as GuardrailsGuard
        from guardrails_ai.prompt_injection_detector import PromptInjectionDetector

        detector = PromptInjectionDetector(
            llm_callable=f"mistral/{config.MODEL}",  # Mistral sert aussi de juge
            threshold=threshold,
            on_fail="noop",  # renvoie un échec au lieu de lever une exception
        )
        self.guard = GuardrailsGuard().use(detector)

    def check(self, text: str) -> GuardResult:
        """Renvoie un échec si le texte est détecté comme une injection."""
        outcome = self.guard.validate(text)
        if outcome.validation_passed:
            return GuardResult(passed=True)
        return GuardResult(passed=False, reason="Tentative de prompt injection détectée.")
