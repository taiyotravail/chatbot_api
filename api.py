"""API HTTP du chatbot : le même pipeline que app.py, sans interface."""

from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chatbot.factory import FEATURES, Threshold, build_pipeline
from chatbot.guards import Guard
from chatbot.guards.regex_keywords import BannedPattern
from chatbot.llm import MistralLLM
from chatbot.pipeline import PipelineResult


class Message(BaseModel):
    """Un message de la conversation."""

    role: Literal["user", "assistant"]  # pas "system" : le visiteur ne doit pas pouvoir remplacer le prompt système
    content: str = Field(max_length=2000)  # limite la taille (et donc le coût) d'un message


class ChatRequest(BaseModel):
    """La conversation envoyée par le site, les guards choisis et leurs seuils. Rien n'est stocké côté serveur."""

    messages: list[Message] = Field(min_length=1, max_length=20)
    features: list[str] = []  # clés de FEATURES ; vide = chat normal
    thresholds: dict[str, float] = {}  # seuil par guard ; absent = seuil par défaut


class FeatureInfo(BaseModel):
    """Description d'un guard, pour afficher son interrupteur et son curseur de seuil sur le site."""

    key: str
    label: str
    stage: Literal["input", "output"]
    threshold: Threshold | None  # None = pas de seuil réglable
    patterns: list[BannedPattern] | None  # motifs interdits, pour le guide du site (guard regex seulement)


app = FastAPI(title="Chatbot échecs")
llm = MistralLLM()


def default_threshold(key: str) -> float | None:
    """Seuil par défaut du guard, ou None s'il n'a pas de seuil."""
    threshold = FEATURES[key].threshold
    return threshold.default if threshold else None


@lru_cache(maxsize=64)
def get_guard(key: str, threshold: float | None) -> Guard:
    """Crée le guard pour ce seuil, une seule fois par couple (guard, seuil)."""
    return FEATURES[key].build(threshold) if threshold is not None else FEATURES[key].build()


# Au démarrage, on crée chaque guard avec son seuil par défaut : s'il manque un validateur, l'API refuse de démarrer.
for key in FEATURES:
    get_guard(key, default_threshold(key))


@app.get("/features")
def list_features() -> list[FeatureInfo]:
    """Liste les guards disponibles, leur plage de seuil et leurs motifs (le site en fait interrupteurs, curseurs et guide)."""
    return [
        FeatureInfo(
            key=key, label=feature.label, stage=feature.stage, threshold=feature.threshold, patterns=feature.patterns
        )
        for key, feature in FEATURES.items()
    ]


@app.post("/chat")
def chat(request: ChatRequest) -> PipelineResult:
    """Envoie la conversation au pipeline avec les guards et seuils choisis ; renvoie la réponse ou le blocage."""
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="Le dernier message doit venir de l'utilisateur.")
    unknown = (set(request.features) | request.thresholds.keys()) - FEATURES.keys()
    if unknown:
        raise HTTPException(status_code=422, detail=f"Guards inconnus : {sorted(unknown)}")
    for key, value in request.thresholds.items():
        limits = FEATURES[key].threshold
        if limits is None:
            raise HTTPException(status_code=422, detail=f"{key} n'a pas de seuil réglable.")
        if not limits.min <= value <= limits.max:
            raise HTTPException(status_code=422, detail=f"Seuil de {key} hors limites : {limits.min} à {limits.max}.")

    def guard_for(key: str) -> Guard:
        return get_guard(key, request.thresholds.get(key, default_threshold(key)))

    pipeline = build_pipeline(llm, request.features, guard_for)
    return pipeline.run([message.model_dump() for message in request.messages])
