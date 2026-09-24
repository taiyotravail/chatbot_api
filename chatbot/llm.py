"""Brique LLM : appel au modèle Mistral."""

from mistralai.client import Mistral

from chatbot import config
from chatbot.system_prompt import SYSTEM_PROMPT


class MistralLLM:
    """Client de chat Mistral."""

    def __init__(self, api_key: str = config.MISTRAL_API_KEY, model: str = config.MODEL) -> None:
        self.client = Mistral(api_key=api_key)
        self.model = model

    def complete(self, messages: list[dict[str, str]]) -> str:
        """Envoie le prompt système + l'historique au modèle et renvoie la réponse."""
        system_message = {"role": "system", "content": SYSTEM_PROMPT}
        response = self.client.chat.complete(model=self.model, messages=[system_message] + messages)
        return response.choices[0].message.content
