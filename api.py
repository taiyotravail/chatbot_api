"""API HTTP du chatbot : le même pipeline que app.py, sans interface."""

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chatbot.factory import FEATURES, build_pipeline
from chatbot.llm import MistralLLM
from chatbot.pipeline import PipelineResult


class Message(BaseModel):
    """Un message de la conversation."""

    role: Literal["user", "assistant"]  # pas "system" : le visiteur ne doit pas pouvoir remplacer le prompt système
    content: str = Field(max_length=2000)  # limite la taille (et donc le coût) d'un message


class ChatRequest(BaseModel):
    """La conversation envoyée par le site, et les guards choisis. Rien n'est stocké côté serveur."""

    messages: list[Message] = Field(min_length=1, max_length=20)
    features: list[str] = []  # clés de FEATURES ; vide = chat normal


class FeatureInfo(BaseModel):
    """Description d'un guard, pour afficher son interrupteur sur le site."""

    key: str
    label: str
    stage: Literal["input", "output"]


app = FastAPI(title="Chatbot échecs")
llm = MistralLLM()
# Tous les guards sont créés une seule fois, au démarrage ; chaque requête choisit ceux qu'elle utilise.
guards = {key: feature.build() for key, feature in FEATURES.items()}


@app.get("/features")
def list_features() -> list[FeatureInfo]:
    """Liste les guards disponibles (le site en fait des interrupteurs)."""
    return [FeatureInfo(key=key, label=feature.label, stage=feature.stage) for key, feature in FEATURES.items()]


@app.post("/chat")
def chat(request: ChatRequest) -> PipelineResult:
    """Envoie la conversation au pipeline avec les guards choisis ; renvoie la réponse ou le blocage."""
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="Le dernier message doit venir de l'utilisateur.")
    unknown = set(request.features) - FEATURES.keys()
    if unknown:
        raise HTTPException(status_code=422, detail=f"Guards inconnus : {sorted(unknown)}")

    pipeline = build_pipeline(llm, request.features, guards.__getitem__)
    return pipeline.run([message.model_dump() for message in request.messages])
