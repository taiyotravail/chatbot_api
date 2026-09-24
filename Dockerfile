# Image de base : Python 3.12, version allégée
FROM python:3.12-slim

WORKDIR /app

# 1. Installer les dépendances (étape mise en cache tant que requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Couper la télémétrie de Guardrails (sinon il envoie des traces à un serveur externe)
RUN guardrails configure --disable-metrics --disable-remote-inferencing --token ""

# 3. Copier le code
COPY chatbot/ chatbot/
COPY api.py .

# 4. Démarrer l'API. Render fournit le port dans la variable PORT (8000 en local).
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
