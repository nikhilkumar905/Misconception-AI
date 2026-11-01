"""Load stored Enhanced Methodology evaluation results (50 balanced bags per model)."""

import json
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "dataset" / "bags_and_results"

RESULT_FILES = [
    ("Gemini Flash Lite", "Gemini", RESULTS_DIR / "gemini_evaluations" / "gemini_baseline_vs_enhanced.json"),
    ("Qwen 3.8 27B", "Groq", RESULTS_DIR / "enhanced_evaluations" / "baseline_vs_enhanced_comparison.json"),
]

METRIC_KEYS = ["overall_accuracy", "precision", "recall", "f1_score", "correct_only_accuracy", "misconception_accuracy", "tp", "fp", "fn", "tn"]


@lru_cache(maxsize=1)
def load_enhanced_results() -> List[Dict[str, Any]]:
    """Return the enhanced-run metrics for each evaluated model."""
    rows = []
    for label, provider, path in RESULT_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        enhanced = data["enhanced"]
        row = {"label": label, "provider": provider, "model": data.get("model", "")}
        row.update({k: enhanced[k] for k in METRIC_KEYS})
        rows.append(row)
    return rows
