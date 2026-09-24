"""Contrat commun à tous les guardrails."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GuardResult:
    """Résultat d'un guardrail : passé ou bloqué, avec la raison."""

    passed: bool
    reason: str = ""


class Guard(Protocol):
    """Un guardrail valide un texte et renvoie un GuardResult."""

    name: str

    def check(self, text: str) -> GuardResult:
        """Valide `text`."""
        ...
