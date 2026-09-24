# Chatbot échecs – API

API FastAPI du chatbot, prête pour Render. Version allégée du POC `test_mistral` :
pas de Streamlit, seulement les 2 guards légers (≈ 270 Mo de RAM).

## Architecture

```
api.py                         POST /chat  (guards choisis dans ENABLED_FEATURES)
chatbot/
  config.py                    variables d'environnement
  system_prompt.py             prompt système
  llm.py                       appel à Mistral
  pipeline.py                  guards d'entrée -> LLM -> guards de sortie
  factory.py                   catalogue des guards + assemblage
  guards/
    base.py                    contrat commun
    prompt_injection.py        entrée : PromptInjectionDetector (Guardrails Hub)
    system_prompt_leak.py      sortie : DetectSystemPromptLeakage (Guardrails Hub)
Dockerfile                     comment construire et lancer le conteneur
requirements.txt               paquets Python (versions figées)
```

## Lancer en local (sans Docker)

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # puis mettre ta clé Mistral dedans
.venv/bin/uvicorn api:app --reload
```

Swagger : http://localhost:8000/docs

## Lancer avec Docker

```bash
docker build -t chatbot-echecs-api .
docker run --rm -p 8000:8000 -e MISTRAL_API_KEY=ta_cle chatbot-echecs-api
```

## Déployer sur Render

1. Mettre ce dossier sur un dépôt GitHub (le `.gitignore` exclut `.env`).
2. Sur render.com : **New → Web Service** → choisir le dépôt.
3. Render détecte le `Dockerfile` tout seul. Choisir :
   - **Region** : Frankfurt (Europe, pour le RGPD)
   - **Instance Type** : Free
4. **Environment** → ajouter `MISTRAL_API_KEY` = ta clé, **sans guillemets**.
5. **Deploy**. L'API sera sur `https://<nom>.onrender.com/docs`.

Offre Free : l'API se met en veille après 15 min sans visite, et le réveil prend ~1 min.
