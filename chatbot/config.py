"""Configuration centralisée (variables d'environnement)."""

import os

from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
MODEL: str = os.getenv("MISTRAL_MODEL", "ministral-14b-latest")
