# MisconAI — Diagnosing Programming Misconceptions in Student Code

<div align="center">
  <h3>High-precision misconception mining with execution tracing, verification and taxonomy RAG</h3>
  <p>
    <b>Engines:</b> Groq · Google Gemini · OpenAI &nbsp;|&nbsp;
    <b>Taxonomy:</b> 67 misconceptions &nbsp;|&nbsp;
    <b>Problems:</b> 501
  </p>
</div>

---

## Table of contents
1. [Overview](#overview)
2. [What is a programming misconception?](#what-is-a-programming-misconception)
3. [The Enhanced Methodology](#the-enhanced-methodology)
4. [Architecture](#architecture)
5. [Results](#results)
6. [MisconAI Studio (web app)](#misconai-studio-web-app)
7. [Concept tutor — how it works](#concept-tutor--how-it-works)
8. [Datasets](#datasets)
9. [Project structure](#project-structure)
10. [Installation](#installation)
11. [Running the app](#running-the-app)
12. [Acknowledgments](#acknowledgments)
13. [License](#license)

---

## Overview

When students learn Python, their errors are rarely random typos. They usually come from **conceptual misconceptions** — false mental models of language semantics (believing `range(n)` includes `n`, that tuples can be modified in place, or confusing `=` with `==`).

Unit tests and linters only report *that* code failed. **MisconAI** explains *why*: it analyzes a student submission, simulates its execution, filters out false alarms on correct code, and maps the error onto a taxonomy of **67 standardized Python misconceptions**.

---

## What is a programming misconception?

A **programming misconception** is:
* a systematic, false belief about language semantics, built-in functions or data structures;
* **concrete and reproducible** across different problems;
* **distinct from typos, syntax slips or a misread prompt**.

### Examples
1. **Range boundary** — believing `range(n)` yields `1 … n` instead of `0 … n-1`.
2. **Tuple immutability** — calling `test_tup.append(val)`, or expecting `list(test_tup)` to mutate the tuple.
3. **Assignment vs. equality** — writing `if x = 0:` instead of `if x == 0:`.
4. **Boolean distribution** — writing `if x == a or b:` and expecting it to test `x == a or x == b`.

---

## The Enhanced Methodology

MisconAI uses a single analysis pipeline built around three mechanisms that force the model to reason before it diagnoses:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Student code                                                        │
│       │                                                              │
│       ▼                                                              │
│  [Construct extractor]  loops · indexing · operators · calls · …     │
│       │                                                              │
│       ▼                                                              │
│  [Taxonomy RAG]  top-K candidates from the 67-misconception bank     │
│       │                                                              │
│       ▼                                                              │
│  [Enhanced prompt]                                                   │
│    1. <trace>         mental step-by-step execution on a test input  │
│    2. <verification>  correctness gate — valid code ⇒ NONE           │
│    3. RAG candidates  reference definitions injected in context      │
│       │                                                              │
│       ▼                                                              │
│  Verified misconception  ──or──  NONE (clean code)                   │
└──────────────────────────────────────────────────────────────────────┘
```

1. **Mental execution tracing (`<trace>`)** — the model simulates the program on a concrete input *before* drawing any conclusion, so diagnoses are grounded in actual behaviour.
2. **Correctness verification (`<verification>`)** — an explicit gate asks whether the code is actually valid or an acceptable alternative. If it is, the output is forced to `NONE`. This is what keeps false alarms low on clean code.
3. **In-context taxonomy RAG (`utils/misconception_rag.py`)** — the code's constructs are matched against the misconception bank and the most relevant definitions are injected into the prompt, keeping descriptions aligned with standard terminology.

The output is structured XML:

```xml
<reasoning>
  <trace>…</trace>
  <verification>…</verification>
</reasoning>
<misconception>
  <description>The student believes …</description>
  <explanation>…</explanation>
</misconception>
```

The full prompt is in [src/prompt_templates/mining/enhanced-cot-mining.md](src/prompt_templates/mining/enhanced-cot-mining.md).

---

## Architecture

* **RAG retrieval engine — [utils/misconception_rag.py](utils/misconception_rag.py)**
  - Detects code constructs (range, loops, indexing, boolean operators, identity, return/print, division, …).
  - Indexes `dataset/misconception_bank.json` by related construct and keyword.
  - Scores every entry and formats the top-K as an in-context reference section.

* **Analysis engine — [src/core/engine.py](src/core/engine.py)**
  - Builds the enhanced prompt, calls the selected provider and parses the trace / verification / diagnosis tags.
  - Shared by the mining lab (code) and the concept tutor (free-text answers).

* **LLM clients — [utils/llm_clients.py](utils/llm_clients.py)**
  - **Groq** via the OpenAI-compatible API (LPU inference).
  - **Google Gemini** via the native GenAI SDK, with thinking-budget support.
  - **OpenAI** including `o3-mini` / `o1-mini` reasoning-effort controls.

---

## Results

Evaluated on **50 balanced bags** — 35 bags containing a ground-truth misconception and 15 bags of correct code only.

| Model | Accuracy | Precision | Recall | F1 | Clean-code accuracy | False alarms |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Google Gemini** (`gemini-flash-lite-latest`) | **60.00%** | **88.89%** | 47.06% | **61.54%** | **93.33%** (14/15) | **2** |
| **Groq** (`qwen/qwen3.8-27b`) | 54.00% | 71.43% | 46.88% | 56.60% | 80.00% (12/15) | 6 |

| Model | TP | FP | FN | TN |
| :--- | :---: | :---: | :---: | :---: |
| Gemini Flash Lite | 16 | 2 | 18 | 14 |
| Qwen 3.8 27B | 15 | 6 | 17 | 12 |

**Reading the numbers:** the verification gate is deliberately conservative. When the model cannot establish that the code is wrong, it answers `NONE` instead of inventing a misconception. That buys high precision and clean-code accuracy at the cost of some recall.

Raw results: [dataset/bags_and_results/gemini_evaluations/](dataset/bags_and_results/gemini_evaluations/) and [dataset/bags_and_results/enhanced_evaluations/](dataset/bags_and_results/enhanced_evaluations/).

---

## MisconAI Studio (web app)

A **Next.js** frontend ([web/](web/)) backed by a **FastAPI** service ([src/server.py](src/server.py)) that wraps the analysis engine.

* **Design:** an official navy / royal-blue palette with a restrained gold accent, IBM Plex Sans and Plex Mono, and a responsive layout from phone to desktop.
* **Engine picker:** the provider and model are chosen once from the picker in the header. The choice is remembered and shared by every page. A status dot shows whether that provider's API key is configured.

| Page | What it does |
| :--- | :--- |
| **Overview** | Headline metrics, the four-step pipeline and a worked example. |
| **Mining lab** | Paste a student submission or pick one of five examples (three buggy, two clean). Shows the diagnosis plus expandable **execution trace**, **verification gate** and **taxonomy candidates**. |
| **Concept tutor** | Chat-style tutor: pick one of 75 questions, answer in plain English and get a diagnosis of your mental model. |
| **Results** | Per-model metric cards, a grouped bar chart and confusion counts, loaded directly from the stored evaluation JSON. |
| **Taxonomy** | Search and filter all 67 misconceptions by keyword, ID or construct, with code examples. |

---

## Concept tutor — how it works

The tutor applies the same Enhanced Methodology to **free-text answers** instead of code.

```
┌────────────────────────────────────────────────────────────────┐
│  Question bank — 75 questions across 24 topics                 │
│       │                                                        │
│       ▼                                                        │
│  Student picks a question and answers in natural language      │
│       │                                                        │
│       ▼                                                        │
│  1. RAG retrieval                                              │
│     query = topic + question + answer + misconception hint     │
│     → top-K related entries from misconception_bank.json       │
│       │                                                        │
│       ▼                                                        │
│  2. Enhanced CoT prompt                                        │
│     <trace>         the student's mental model, step by step   │
│     <verification>  what Python actually does                  │
│     <description>   named misconception, or NONE               │
│     <explanation>   friendly correction or reinforcement       │
│       │                                                        │
│       ▼                                                        │
│  3. Parsed into a chat reply                                   │
│     ✔ correct   → reinforcement + example                      │
│     ⚠ wrong     → misconception + explanation + trace + RAG    │
└────────────────────────────────────────────────────────────────┘
```

| Mechanism | Role in the tutor |
| --- | --- |
| **RAG retrieval** | The answer text and topic form the query, so retrieved entries match what the student actually wrote. |
| **`<trace>`** | Reconstructs the student's reasoning: *"The student appears to believe that `b = a` copies the list because…"* |
| **`<verification>`** | States the real Python behaviour, grounded in language semantics. |

Topics include Basics, Strings, Lists, Tuples, Sets, Dicts, Control Flow, Functions, OOP, Exceptions, Comprehensions, File I/O, Modules, Generators, Decorators, Types, Built-ins, Memory, Scope, Recursion, Operators, Iterators, Python 3 and Advanced.

**Design choices**
1. **Free text, not multiple choice** — the student has to articulate a mental model; the model judges reasoning, not keywords.
2. **No scoring** — it is a learning tool, not an assessment.
3. **Conversation per question** — answer, read the feedback, try again; the reference answer is one click away.
4. **Same engine settings** — the provider/model chosen in the header applies here too.

---

## Datasets

All data lives in `dataset/`:

1. **`problems_processed.json`** — 501 programming tasks (MBPP, Socratic Debugging, Auckland logic errors, FalconCode and handcrafted educator tasks), averaging 3.31 unit tests per problem.
2. **`misconception_bank.json`** — 67 standardized misconceptions (drawn from the Python Programming Misconception Bank, SIDELib and education research), each with related constructs and a canonical example.
3. **`corrupted_codes_best/`** — 1,063 code samples with ground-truth misconception annotations.
4. **`bags_and_results/`** — multi-instance problem bags and stored evaluation runs.

---

## Project structure

```text
mcminer/
├── dataset/
│   ├── bags_and_results/              # Problem bags & evaluation outputs
│   ├── corrupted_codes_best/          # Ground-truth code samples
│   ├── misconception_bank.json        # 67 misconceptions
│   └── problems_processed.json        # 501 problems with unit tests
├── src/
│   ├── server.py                      # FastAPI service consumed by the frontend
│   ├── core/
│   │   ├── engine.py                  # Enhanced pipeline: prompt, LLM call, parsing
│   │   ├── questions.py               # 75-question concept bank
│   │   ├── presets.py                 # Mining-lab examples
│   │   └── results.py                 # Loads stored evaluation metrics
│   └── prompt_templates/mining/
│       └── enhanced-cot-mining.md     # Enhanced trace + verification + RAG prompt
├── utils/
│   ├── llm_clients.py                 # Groq, Gemini and OpenAI connectors
│   └── misconception_rag.py           # Construct-based taxonomy RAG
├── web/                               # Next.js frontend (App Router + Tailwind)
│   └── src/
│       ├── app/                       # /, /lab, /tutor, /results, /taxonomy
│       ├── components/                # Header, engine picker, diagnosis view, UI kit
│       └── lib/                       # Typed API client
├── requirements.txt
└── LICENSE
```

---

## Installation

**Prerequisites:** Python 3.10–3.13 and Node.js 20.9+ on Windows, macOS or Linux.

```bash
git clone https://github.com/nikhilkumarsah/miscon-ai.git
cd miscon-ai

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

cd web && npm install && cd ..
```

Create a `.env` file in the project root (see `.env.example`):

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here   # optional
```

Only the key for the provider you pick is required. The engine picker shows whether it was found.

---

## Running the app

Run the API and the frontend in two terminals:

```bash
# Terminal 1 — project root, with the venv active
python src/server.py          # API on http://127.0.0.1:8000

# Terminal 2
cd web
npm run dev                   # UI on http://localhost:3000
```

Then open **http://localhost:3000**. The frontend proxies `/api/*` to the Python service. Set `MISCONAI_API_URL` to point it elsewhere.

For a production build: `cd web && npm run build && npm start`.

---

## Acknowledgments

MisconAI builds on the open-source **MCMiner** research framework for automated misconception mining, released under the MIT License. It also builds on the public datasets and misconception collections listed under [Datasets](#datasets).

---

## License

Released under the **MIT License**. See [LICENSE](LICENSE).
