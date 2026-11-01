#!/usr/bin/env python3
"""
MisconAI API

JSON API over the Enhanced Methodology engine, consumed by the Next.js frontend in web/.

Run from the project root:  python src/server.py   (serves http://127.0.0.1:8000)
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
for p in (str(PROJECT_ROOT), str(SRC_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

load_dotenv(PROJECT_ROOT / ".env", override=True)

from core.engine import MODEL_OPTIONS, API_KEY_ENV, analyze_code, analyze_free_text_answer, get_llm_config, has_api_key  # noqa: E402
from core.presets import PRESET_EXAMPLES  # noqa: E402
from core.questions import CHATBOT_QUESTIONS  # noqa: E402
from core.results import load_enhanced_results  # noqa: E402

app = FastAPI(title="MisconAI API")

QUESTIONS_BY_ID = {q["id"]: q for q in CHATBOT_QUESTIONS}


class Engine(BaseModel):
    provider: str = Field(description="groq | gemini | openai")
    model: str


class CodeRequest(Engine):
    title: str = ""
    description: str = ""
    code: str


class AnswerRequest(Engine):
    question_id: int
    answer: str


def _validate_engine(req: Engine):
    names = {k.lower(): k for k in MODEL_OPTIONS}
    if req.provider not in names or req.model not in MODEL_OPTIONS[names[req.provider]]:
        raise HTTPException(400, f"Unknown provider/model: {req.provider}/{req.model}")
    if not has_api_key(req.provider):
        raise HTTPException(400, f"{API_KEY_ENV[req.provider]} is not set. Add it to the .env file and restart the API.")


def _slim_candidates(result: dict) -> dict:
    result["retrieved_candidates"] = [
        {
            "id": c["id"],
            "description": c["description"],
            "constructs": c.get("meta_data", {}).get("related_constructs", []),
        }
        for c in result.get("retrieved_candidates", [])
    ]
    return result


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/models")
def models():
    return [
        {
            "provider": provider.lower(),
            "label": provider,
            "has_key": has_api_key(provider.lower()),
            "key_env": API_KEY_ENV[provider.lower()],
            "models": [
                {"id": m, "label": label, "reasoning": get_llm_config(provider.lower(), m)["reasoning"]}
                for m, label in options.items()
            ],
        }
        for provider, options in MODEL_OPTIONS.items()
    ]


@app.get("/api/presets")
def presets():
    return [{"name": name, **p} for name, p in PRESET_EXAMPLES.items()]


@app.get("/api/questions")
def questions():
    return CHATBOT_QUESTIONS


@app.get("/api/results")
def results():
    return load_enhanced_results()


@app.get("/api/taxonomy")
def taxonomy():
    bank = json.loads((PROJECT_ROOT / "dataset" / "misconception_bank.json").read_text(encoding="utf-8"))
    return [
        {
            "id": m["id"],
            "description": m["description"],
            "example": m.get("example", ""),
            "constructs": m.get("meta_data", {}).get("related_constructs", []),
        }
        for m in bank
    ]


@app.post("/api/analyze/code")
def analyze_code_endpoint(req: CodeRequest):
    _validate_engine(req)
    if not req.code.strip():
        raise HTTPException(400, "Student code is empty.")
    try:
        result = analyze_code(req.provider, req.model, req.title, req.description, req.code)
    except Exception as e:
        raise HTTPException(502, f"Model call failed: {e}")
    return _slim_candidates(result)


@app.post("/api/analyze/answer")
def analyze_answer_endpoint(req: AnswerRequest):
    _validate_engine(req)
    question = QUESTIONS_BY_ID.get(req.question_id)
    if not question:
        raise HTTPException(404, f"Unknown question {req.question_id}")
    if not req.answer.strip():
        raise HTTPException(400, "Answer is empty.")
    try:
        result = analyze_free_text_answer(req.provider, req.model, question, req.answer)
    except Exception as e:
        raise HTTPException(502, f"Model call failed: {e}")
    return _slim_candidates(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
