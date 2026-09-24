"""Catalogue des fonctionnalités et assemblage du pipeline."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from chatbot.guards import Guard
from chatbot.guards.prompt_injection import PromptInjectionGuard
from chatbot.guards.system_prompt_leak import SystemPromptLeakGuard
from chatbot.pipeline import LLM, Pipeline


@dataclass(frozen=True)
class Feature:
    """Une fonctionnalité activable."""

    label: str
    stage: Literal["input", "output"]
    build: Callable[[], Guard]


# Seulement les guards légers : ils tiennent dans les 512 Mo de Render Free.
FEATURES: dict[str, Feature] = {
    "prompt_injection": Feature("Anti prompt injection", "input", PromptInjectionGuard),
    "system_prompt_leak": Feature("Anti fuite du prompt système", "output", SystemPromptLeakGuard),
}


def build_pipeline(llm: LLM, enabled: list[str], get_guard: Callable[[str], Guard]) -> Pipeline:
    """Construit le pipeline avec les seules fonctionnalités `enabled`.

    `get_guard` fournit l'instance d'un guard à partir de sa clé.
    """
    pipeline = Pipeline(llm=llm)
    for key in enabled:
        guard = get_guard(key)
        if FEATURES[key].stage == "input":
            pipeline.input_guards.append(guard)
        else:
            pipeline.output_guards.append(guard)
    return pipeline
