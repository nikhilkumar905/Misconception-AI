"""
MisconAI analysis engine.

Implements the Enhanced Methodology: mental execution tracing, a correctness
verification gate, and in-context taxonomy RAG over the 67-entry misconception bank.
"""

import os
import re
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any

from utils.llm_clients import OpenAIClient, GeminiClient
from utils.misconception_rag import MisconceptionRAG

SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_DIR.parent
TEMPLATE_PATH = SRC_DIR / "prompt_templates" / "mining" / "enhanced-cot-mining.md"

MODEL_OPTIONS = {
    "Groq": {
        "qwen/qwen3.8-27b": "Qwen 3.8 27B",
        "openai/gpt-oss-120b": "GPT OSS 120B",
        "openai/gpt-oss-20b": "GPT OSS 20B",
        "allam-2-7b": "Allam 2 7B",
    },
    "Gemini": {
        "gemini-flash-lite-latest": "Gemini Flash Lite",
        "gemini-3.8-flash": "Gemini 3.8 Flash",
        "gemini-flash-latest": "Gemini Flash Latest",
    },
    "OpenAI": {
        "o3-mini": "o3-mini",
        "o1-mini": "o1-mini",
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
    },
}

API_KEY_ENV = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


@lru_cache(maxsize=1)
def get_rag_indexer() -> MisconceptionRAG:
    """Load and index the misconception bank once per server process."""
    return MisconceptionRAG()


@lru_cache(maxsize=1)
def load_prompt_template() -> str:
    """Load the enhanced CoT mining template, dropping its markdown header."""
    lines = TEMPLATE_PATH.read_text(encoding="utf-8").split("\n")
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
    return "\n".join(lines)


def has_api_key(provider: str) -> bool:
    key = os.getenv(API_KEY_ENV.get(provider, ""), "")
    return bool(key) and key != "YOUR_API_KEY"


def create_mining_prompt(problem_title: str, problem_description: str, student_code: str, candidate_prompt: str) -> str:
    """Fill the enhanced template with the problem, code and RAG candidates."""
    prompt = load_prompt_template()
    prompt = prompt.replace("{problem_title}", problem_title)
    prompt = prompt.replace("{problem_description}", problem_description)
    prompt = prompt.replace("{student_code}", student_code)
    prompt = prompt.replace("{candidate_misconceptions}", candidate_prompt)
    return prompt


def parse_mining_response(response: str) -> Dict[str, Any]:
    """Parse the LLM response for trace, verification and the diagnosed misconception."""
    result = {
        "reasoning": "",
        "trace": "",
        "verification": "",
        "misconception_found": False,
        "description": "",
        "explanation": "",
        "raw_response": response,
        "parse_success": False,
    }

    try:
        reasoning_match = re.search(r"<reasoning>\s*(.*?)\s*</reasoning>", response, re.DOTALL)
        if reasoning_match:
            result["reasoning"] = reasoning_match.group(1).strip()

            trace_match = re.search(r"<trace>\s*(.*?)\s*</trace>", result["reasoning"], re.DOTALL)
            if trace_match:
                result["trace"] = trace_match.group(1).strip()

            verif_match = re.search(r"<verification>\s*(.*?)\s*</verification>", result["reasoning"], re.DOTALL)
            if verif_match:
                result["verification"] = verif_match.group(1).strip()

        misconception_match = re.search(r"<misconception>\s*(.*?)\s*</misconception>", response, re.DOTALL)
        if misconception_match:
            misconception_text = misconception_match.group(1).strip()
            desc_match = re.search(r"<description>\s*(.*?)\s*</description>", misconception_text, re.DOTALL)
            explanation_match = re.search(r"<explanation>\s*(.*?)\s*</explanation>", misconception_text, re.DOTALL)
            if explanation_match:
                result["explanation"] = explanation_match.group(1).strip()

            if desc_match and desc_match.group(1).strip() and desc_match.group(1).strip().upper() != "NONE":
                result["misconception_found"] = True
                result["description"] = desc_match.group(1).strip()
            elif desc_match or misconception_text.upper() == "NONE" or "<no_misconception" in misconception_text:
                result["description"] = "No misconception detected"
            elif misconception_text:
                result["misconception_found"] = True
                result["description"] = misconception_text.split("\n")[0].strip()

            result["parse_success"] = True
        elif "<no_misconceptions/>" in response or "<no_misconception>" in response:
            result["description"] = "No misconception detected"
            result["parse_success"] = True

    except Exception as e:
        result["parse_error"] = str(e)

    return result


def create_llm_client(provider: str, model: str):
    """Create the LLM client for the selected provider."""
    if not has_api_key(provider):
        raise ValueError(f"{API_KEY_ENV.get(provider, provider)} is not set. Add it to your .env file.")
    api_key = os.getenv(API_KEY_ENV[provider])

    if provider == "groq":
        return OpenAIClient(api_key=api_key, model=model, base_url="https://api.groq.com/openai/v1", use_responses_api=False)
    if provider == "openai":
        return OpenAIClient(api_key=api_key)
    if provider == "gemini":
        return GeminiClient(api_key=api_key, model=model)
    raise ValueError(f"Unsupported provider: {provider}")


def get_llm_config(provider: str, model: str) -> Dict[str, Any]:
    """Get LLM configuration including reasoning settings."""
    groq_reasoning = ["deepseek-r1-distill-llama-70b"]
    openai_reasoning = ["o3-mini", "o1-mini", "o1", "o1-preview", "o3", "o4-mini"]
    gemini_reasoning = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash"]

    config = {"model": model, "temperature": 0.1, "max_tokens": 4000, "reasoning": False}

    if provider == "groq" and model in groq_reasoning:
        config["reasoning"] = True
        config["budget_tokens"] = 2000
    elif provider == "openai" and model in openai_reasoning:
        config["reasoning"] = True
        config["reasoning_effort"] = "medium"
    elif provider == "gemini" and model in gemini_reasoning:
        config["reasoning"] = True
        config["thinking_budget"] = 2000

    return config


def call_llm(provider: str, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
    """Send a single-turn prompt to the selected provider and return the text response."""
    client = create_llm_client(provider, model)

    config = get_llm_config(provider, model)
    messages = [{"role": "user", "content": prompt}]

    if provider in ("groq", "openai"):
        extra = {"reasoning_effort": config.get("reasoning_effort", "medium")} if provider == "openai" else {}
        return client.create_message(
            messages,
            kwargs={"model": config["model"], "temperature": temperature, "max_tokens": max_tokens},
            reasoning=config.get("reasoning", False),
            **extra,
        )
    if provider == "gemini":
        return client.create_message(
            messages,
            kwargs={"max_output_tokens": max_tokens, "temperature": temperature},
            reasoning=config.get("reasoning", False),
            thinking_budget=config.get("thinking_budget", 2000),
        )
    raise ValueError(f"Unsupported provider: {provider}")


def analyze_code(provider: str, model: str, problem_title: str, problem_description: str, student_code: str) -> Dict[str, Any]:
    """Diagnose a student code submission with the Enhanced Methodology."""
    rag = get_rag_indexer()
    retrieved_candidates = rag.retrieve_candidates(student_code)
    candidate_prompt = rag.format_candidates_prompt(retrieved_candidates)
    prompt = create_mining_prompt(problem_title, problem_description, student_code, candidate_prompt)

    response = call_llm(provider, model, prompt, temperature=0.1, max_tokens=4000)

    parsed = parse_mining_response(response)
    parsed["retrieved_candidates"] = retrieved_candidates
    return parsed


def build_concept_prompt(question_data: dict, student_answer: str, candidate_prompt: str) -> str:
    """Enhanced CoT prompt for diagnosing a free-text conceptual answer."""
    return f"""You are MisconAI — an expert Python educator and misconception analyst using the Enhanced Chain-of-Thought methodology.

A student has answered a Python conceptual question. Evaluate their answer and diagnose any misconceptions.

## Question
Topic: {question_data.get("topic", "Python")}
{question_data["question"]}

## Additional Context
{question_data.get("context", "")}

## Student's Answer
"{student_answer}"

## Correct Answer Reference
{question_data["correct_answer"]}

{candidate_prompt}

## Your Task
First determine: is the student's answer CORRECT, PARTIALLY CORRECT, or INCORRECT/shows a MISCONCEPTION?

Respond using EXACTLY this XML format:

<reasoning>
<trace>
Walk through the student's answer step by step. What mental model are they using? Is their reasoning sound?
</trace>
<verification>
Compare student's answer to the correct Python behavior. Identify exactly what is right or wrong.
</verification>
</reasoning>

<misconception>
<description>
If the answer is correct, write: NONE
If incorrect/partial, name the specific misconception concisely (e.g., "Off-by-one error in range()", "Confusing is with ==").
</description>
<explanation>
If correct: Write a brief confirmation of why their understanding is correct, with a reinforcing example.
If incorrect/partial: Write a friendly, clear explanation that:
  1. Acknowledges what part of their thinking is reasonable
  2. Explains exactly what Python actually does, with a concrete code example
  3. Gives a memorable tip or mental model to remember the correct behavior
</explanation>
</misconception>"""


def analyze_free_text_answer(provider: str, model: str, question_data: dict, student_answer: str) -> Dict[str, Any]:
    """Diagnose a free-text conceptual answer with RAG + chain-of-thought."""
    rag = get_rag_indexer()
    rag_query = f"{question_data.get('topic', '')} {question_data['question']} {student_answer} {question_data.get('misconception_hint', '')}"
    retrieved_candidates = rag.retrieve_candidates(rag_query)
    prompt = build_concept_prompt(question_data, student_answer, rag.format_candidates_prompt(retrieved_candidates))

    response = call_llm(provider, model, prompt, temperature=0.2, max_tokens=1800)

    parsed = parse_mining_response(response)
    parsed["retrieved_candidates"] = retrieved_candidates
    return parsed

