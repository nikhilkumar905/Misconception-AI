# MisconAI API (FastAPI) — serves http://0.0.0.0:8000
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY utils/ utils/
COPY src/ src/

# Only the data the API reads: the taxonomy bank and the two evaluation summaries.
COPY dataset/misconception_bank.json dataset/
COPY dataset/bags_and_results/gemini_evaluations/gemini_baseline_vs_enhanced.json dataset/bags_and_results/gemini_evaluations/
COPY dataset/bags_and_results/enhanced_evaluations/baseline_vs_enhanced_comparison.json dataset/bags_and_results/enhanced_evaluations/

EXPOSE 8000

# API keys come from the environment (docker compose passes .env); nothing secret is baked in.
# Hosts such as Render inject PORT; locally it falls back to 8000.
CMD ["sh", "-c", "uvicorn server:app --app-dir src --host 0.0.0.0 --port ${PORT:-8000}"]
