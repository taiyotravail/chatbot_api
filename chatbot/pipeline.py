"""Orchestration : guards d'entrée -> LLM -> guards de sortie."""

from dataclasses import dataclass, field
from typing import Protocol

from chatbot.guards import Guard


class LLM(Protocol):
    """Tout objet capable de compléter un historique de messages."""

    def complete(self, messages: list[dict[str, str]]) -> str:
        """Renvoie la réponse du modèle à l'historique `messages`."""
        ...


@dataclass(frozen=True)
class PipelineResult:
    """Réponse du pipeline, ou raison du blocage."""

    answer: str | None = None
    blocked_by: str | None = None
    reason: str = ""

    @property
    def blocked(self) -> bool:
        """Vrai si un guard a bloqué le message ou la réponse."""
        return self.blocked_by is not None


def run_guards(guards: list[Guard], text: str) -> PipelineResult | None:
    """Passe `text` dans chaque guard ; renvoie le premier blocage, sinon None."""
    for guard in guards:
        result = guard.check(text)
        if not result.passed:
            return PipelineResult(blocked_by=guard.name, reason=result.reason)
    return None


@dataclass
class Pipeline:
    """Enchaîne les briques. Ajouter un guard = l'ajouter à une des listes."""

    llm: LLM
    input_guards: list[Guard] = field(default_factory=list)
    output_guards: list[Guard] = field(default_factory=list)

    def run(self, messages: list[dict[str, str]]) -> PipelineResult:
        """Valide le dernier message utilisateur, appelle le LLM, valide la réponse."""
        blocked = run_guards(self.input_guards, messages[-1]["content"])
        if blocked:
            return blocked

        answer = self.llm.complete(messages)

        blocked = run_guards(self.output_guards, answer)
        if blocked:
            return blocked

        return PipelineResult(answer=answer)
