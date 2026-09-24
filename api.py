"""API HTTP du chatbot : le même pipeline que app.py, sans interface."""

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chatbot.factory import FEATURES, build_pipeline
from chatbot.llm import MistralLLM
from chatbot.pipeline import PipelineResult

# Guards actifs : choisis ici par toi, pas par le visiteur du site.
ENABLED_FEATURES = ["prompt_injection", "system_prompt_leak"]


class Message(BaseModel):
    """Un message de la conversation."""

    role: Literal["user", "assistant"]  # pas "system" : le visiteur ne doit pas pouvoir remplacer le prompt système
    content: str = Field(max_length=2000)  # limite la taille (et donc le coût) d'un message


class ChatRequest(BaseModel):
    """La conversation envoyée par le site. Rien n'est stocké côté serveur."""

    messages: list[Message] = Field(min_length=1, max_length=20)


app = FastAPI(title="Chatbot échecs")
pipeline = build_pipeline(MistralLLM(), ENABLED_FEATURES, lambda key: FEATURES[key].build())


@app.post("/chat")
def chat(request: ChatRequest) -> PipelineResult:
    """Envoie la conversation au pipeline ; renvoie la réponse ou la raison du blocage."""
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="Le dernier message doit venir de l'utilisateur.")
    return pipeline.run([message.model_dump() for message in request.messages])
