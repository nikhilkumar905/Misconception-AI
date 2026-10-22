#!/usr/bin/env python3
"""
MisconAI Streamlit Studio

An interactive web app for identifying and diagnosing programming misconceptions in student code
using the MisconAI single-instance and multi-instance mining approach.
"""

import streamlit as st
import os
import sys
import re
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
mining_dir = current_dir
project_root = mining_dir.parent

# Add project root to path so we can import shared module
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from utils.llm_clients import OpenAIClient, AnthropicClient, GeminiClient
    from utils.misconception_rag import MisconceptionRAG
except ImportError as e:
    print(f"Error importing shared.llm_clients: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Mining directory: {mining_dir}")
    print(f"Project root: {project_root}")
    print(f"sys.path: {sys.path[:3]}")
    raise

# Initialize Misconception RAG Indexer
rag_indexer = MisconceptionRAG()


def load_prompt_template(enhanced: bool = True) -> str:
    """Load mining prompt template (enhanced CoT or basic zeroshot)."""
    if enhanced:
        template_path = mining_dir / "prompt_templates" / "mining" / "enhanced-cot-mining.md"
    else:
        template_path = mining_dir / "prompt_templates" / "mining" / "zeroshot-no-reasoning.md"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Remove markdown header if present
    lines = template_content.split('\n')
    if lines and lines[0].startswith('#'):
        lines = lines[1:]
        if lines and lines[0].strip() == '':
            lines = lines[1:]
    
    return '\n'.join(lines)


def create_mining_prompt(template: str, problem_title: str, problem_description: str, student_code: str, candidate_prompt: str = "") -> str:
    """Create a prompt for inferring misconceptions from code."""
    prompt = template
    prompt = prompt.replace("{problem_title}", problem_title)
    prompt = prompt.replace("{problem_description}", problem_description)
    prompt = prompt.replace("{student_code}", student_code)
    prompt = prompt.replace("{candidate_misconceptions}", candidate_prompt)
    return prompt


def parse_mining_response(response: str) -> Dict[str, Any]:
    """Parse LLM response for inferred misconceptions, trace, and verification."""
    result = {
        "reasoning": "",
        "trace": "",
        "verification": "",
        "misconception_found": False,
        "description": "",
        "explanation": "",
        "raw_response": response,
        "parse_success": False
    }
    
    try:
        # Extract full reasoning (if present)
        reasoning_match = re.search(r'<reasoning>\s*(.*?)\s*</reasoning>', response, re.DOTALL)
        if reasoning_match:
            result["reasoning"] = reasoning_match.group(1).strip()
            
            # Extract trace subtag
            trace_match = re.search(r'<trace>\s*(.*?)\s*</trace>', result["reasoning"], re.DOTALL)
            if trace_match:
                result["trace"] = trace_match.group(1).strip()
                
            # Extract verification subtag
            verif_match = re.search(r'<verification>\s*(.*?)\s*</verification>', result["reasoning"], re.DOTALL)
            if verif_match:
                result["verification"] = verif_match.group(1).strip()
        
        # Extract misconception
        misconception_match = re.search(r'<misconception>\s*(.*?)\s*</misconception>', response, re.DOTALL)
        if misconception_match:
            misconception_text = misconception_match.group(1).strip()
            desc_match = re.search(r'<description>\s*(.*?)\s*</description>', misconception_text, re.DOTALL)
            
            if desc_match and desc_match.group(1).strip() and desc_match.group(1).strip().upper() != "NONE":
                result["misconception_found"] = True
                result["description"] = desc_match.group(1).strip()
                explanation_match = re.search(r'<explanation>\s*(.*?)\s*</explanation>', misconception_text, re.DOTALL)
                if explanation_match:
                    result["explanation"] = explanation_match.group(1).strip()
            elif misconception_text.upper() == "NONE" or "<no_misconception" in misconception_text:
                result["misconception_found"] = False
                result["description"] = "No misconception detected"
            elif misconception_text and "<no_misconception" not in misconception_text:
                result["misconception_found"] = True
                result["description"] = misconception_text.split('\n')[0].strip()
                explanation_match = re.search(r'<explanation>\s*(.*?)\s*</explanation>', misconception_text, re.DOTALL)
                if explanation_match:
                    result["explanation"] = explanation_match.group(1).strip()
            else:
                result["misconception_found"] = False
                result["description"] = "No misconception detected"
            
            result["parse_success"] = True
        elif "<no_misconceptions/>" in response or "<no_misconception>" in response:
            result["misconception_found"] = False
            result["description"] = "No misconception detected"
            result["parse_success"] = True
            
    except Exception as e:
        result["parse_error"] = str(e)
    
    return result


def create_llm_client(provider: str, model: str):
    """Create the appropriate LLM client."""
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("❌ GROQ_API_KEY not found in environment variables")
            return None
        return OpenAIClient(api_key=api_key, model=model, base_url="https://api.groq.com/openai/v1", use_responses_api=False)
    
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ OPENAI_API_KEY not found in environment variables")
            return None
        return OpenAIClient(api_key=api_key)
    
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ GEMINI_API_KEY not found in environment variables")
            return None
        return GeminiClient(api_key=api_key, model=model)
    
    return None


def get_llm_config(provider: str, model: str) -> Dict[str, Any]:
    """Get LLM configuration including reasoning settings."""
    # Reasoning-capable models
    groq_reasoning = ["deepseek-r1-distill-llama-70b"]
    openai_reasoning = ["o3-mini", "o1-mini", "o1", "o1-preview", "o3", "o4-mini"]
    gemini_reasoning = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash"]
    
    config = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": 4000,
        "reasoning": False,
    }
    
    # Enable reasoning for compatible models
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


def analyze_code(provider: str, model: str, problem_title: str, problem_description: str, student_code: str, enhanced_mode: bool = True):
    """Analyze student code for misconceptions."""
    # Load template
    template = load_prompt_template(enhanced=enhanced_mode)
    
    # Retrieve candidates if enhanced mode is active
    candidate_prompt = ""
    retrieved_candidates = []
    if enhanced_mode:
        retrieved_candidates = rag_indexer.retrieve_candidates(student_code)
        candidate_prompt = rag_indexer.format_candidates_prompt(retrieved_candidates)
    
    # Create prompt
    prompt = create_mining_prompt(template, problem_title, problem_description, student_code, candidate_prompt)
    
    # Create LLM client
    client = create_llm_client(provider, model)
    if not client:
        return None
    
    # Get configuration
    config = get_llm_config(provider, model)
    
    # Create messages
    messages = [{"role": "user", "content": prompt}]
    
    # Call LLM
    try:
        with st.spinner(f"Analyzing with {model} ({'Enhanced Mode' if enhanced_mode else 'Standard Mode'})..."):
            if provider == "groq":
                response = client.create_message(
                    messages,
                    kwargs={"model": config["model"], "temperature": config["temperature"], "max_tokens": config["max_tokens"]},
                    reasoning=config.get("reasoning", False)
                )
            elif provider == "openai":
                response = client.create_message(
                    messages,
                    kwargs={"model": config["model"], "temperature": config["temperature"], "max_tokens": config["max_tokens"]},
                    reasoning=config.get("reasoning", False),
                    reasoning_effort=config.get("reasoning_effort", "medium")
                )
            elif provider == "gemini":
                response = client.create_message(
                    messages,
                    kwargs={"max_output_tokens": config["max_tokens"], "temperature": config["temperature"]},
                    reasoning=config.get("reasoning", False),
                    thinking_budget=config.get("thinking_budget", 2000)
                )
            else:
                st.error(f"Unsupported provider: {provider}")
                return None
        
        # Parse response
        parsed = parse_mining_response(response)
        parsed["retrieved_candidates"] = retrieved_candidates
        return parsed
        
    except Exception as e:
        st.error(f"Error analyzing code: {str(e)}")
        return None


def main():
    st.set_page_config(
        page_title="MisconAI: Misconception Intelligence Studio",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 MisconAI: Programming Misconception Intelligence Studio")
    st.markdown("Identify, verify, and remediate programming misconceptions in student Python code using multi-model AI reasoning.")
    
    # Sidebar for model selection
    st.sidebar.header("⚙️ Model Settings")
    
    # Model selection
    model_options = {
        "Groq": {
            "qwen/qwen3.8-27b": "Qwen 3.8 27B (Recommended)",
            "openai/gpt-oss-120b": "GPT OSS 120B",
            "openai/gpt-oss-20b": "GPT OSS 20B",
            "allam-2-7b": "Allam 2 7B",
        },
        "Gemini": {
            "gemini-flash-lite-latest": "Gemini Flash Lite (Fastest & 88.9% Precision)",
            "gemini-3.8-flash": "Gemini 3.8 Flash",
            "gemini-flash-latest": "Gemini Flash Latest",
        },
        "OpenAI": {
            "o3-mini": "o3-mini",
            "o1-mini": "o1-mini",
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
        }
    }
    
    provider = st.sidebar.selectbox(
        "Provider",
        options=list(model_options.keys()),
        index=0
    )
    
    model = st.sidebar.selectbox(
        "Model",
        options=list(model_options[provider].keys()),
        format_func=lambda x: model_options[provider][x],
        index=0
    )
    
    # Show reasoning status
    config = get_llm_config(provider.lower(), model)
    if config.get("reasoning"):
        st.sidebar.success("✅ Reasoning / CoT enabled")
    else:
        st.sidebar.info("ℹ️ Standard reasoning mode")
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Methodology")
    analysis_mode = st.sidebar.radio(
        "Mining Strategy",
        options=["Enhanced (Trace + Verification + RAG)", "Standard (Basic Zero-Shot)"],
        index=0,
        help="Enhanced mode executes mental tracing, verification, and injects known candidates from the Misconception Bank for higher accuracy."
    )
    enhanced_mode = (analysis_mode.startswith("Enhanced"))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👨‍💻 Project Info")
    st.sidebar.caption("**Author:** NIKHIL KUMAR SAH")
    st.sidebar.caption("**System:** MisconAI Programming Misconception Suite")
    st.sidebar.caption("**Engines:** Groq LPU & Google Gemini API")


# Preset Examples Library
PRESET_EXAMPLES = {
    "Factorial range(n) Misconception": {
        "title": "Factorial Function",
        "desc": "Write the factorial(n) function that computes the factorial n! of a natural number n. If input n is negative, return 0.",
        "code": """def factorial(n):
    if n < 0:
        return 0
    fact = 1
    for i in range(n):
        fact = fact * i
    return fact""",
        "notes": "Student believes range(n) produces values from 1 to n inclusive."
    },
    "Tuple In-Place Mutability Misconception": {
        "title": "Append to Tuple",
        "desc": "Write a function that appends a dictionary to a tuple of elements.",
        "code": """def add_dict_to_tuple(test_tup, test_dict):
    list(test_tup)
    test_tup.append(test_dict)
    tuple(test_tup)
    return test_tup""",
        "notes": "Student believes tuples can be mutated in-place and list(tup) modifies tup."
    },
    "Conditional Assignment '=' vs '==' Misconception": {
        "title": "Filter Long Words",
        "desc": "Write a function to return words longer than length n from a string.",
        "code": """def long_words(n, str):
    word_len = []
    txt = str.split(" ")
    for x in txt:
        if len(x) = n:
            word_len.append(x)
    return word_len""",
        "notes": "Student confuses assignment operator (=) with comparison operator (==)."
    },
    "Clean & Correct Recursive Factorial (No Misconception)": {
        "title": "Factorial Recursive",
        "desc": "Write a factorial function that recursively computes factorial.",
        "code": """def factorial(n):
    if n <= 0:
        return 1
    return n * factorial(n - 1)""",
        "notes": "Correct implementation. Verifies that the model outputs NO MISCONCEPTIONS."
    },
    "Clean & Correct Matrix Transpose (No Misconception)": {
        "title": "Matrix Transpose",
        "desc": "Transpose an n x n square matrix in place.",
        "code": """def transpose(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    return matrix""",
        "notes": "Correct implementation with upper-triangle iteration."
    }
}


def inject_custom_css():
    """Inject modern, rich CSS styles."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Header Gradient Hero */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60A5FA 0%, #A78BFA 50%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 14px;
    }
    
    .pill-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(96, 165, 250, 0.15);
        color: #93C5FD;
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    
    .pill-green {
        background: rgba(52, 211, 153, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    
    .pill-purple {
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(96, 165, 250, 0.4);
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 2px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .metric-gain {
        font-size: 0.82rem;
        font-weight: 700;
        color: #34D399;
        margin-top: 4px;
    }
    
    /* Result Banners */
    .result-flaw {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(185, 28, 28, 0.05) 100%);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    .result-clean {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_analyzer_tab(provider: str, model: str, enhanced_mode: bool):
    """Render the primary misconception mining lab."""
    col_input, col_output = st.columns([1, 1], gap="large")
    
    with col_input:
        st.markdown("### 📝 Code Submission & Context")
        
        # Preset selector
        selected_preset = st.selectbox(
            "⚡ Quick Preset Example",
            options=["Custom Code"] + list(PRESET_EXAMPLES.keys()),
            help="Choose an authentic student code case to test"
        )
        
        if selected_preset != "Custom Code":
            preset_data = PRESET_EXAMPLES[selected_preset]
            init_title = preset_data["title"]
            init_desc = preset_data["desc"]
            init_code = preset_data["code"]
            st.caption(f"💡 **Case Note:** {preset_data['notes']}")
        else:
            init_title = "Factorial Function"
            init_desc = "Write the factorial(n) function that computes the factorial n! of a natural number n. If input n is negative, return 0."
            init_code = """def factorial(n):
    if n < 0:
        return 0
    fact = 1
    for i in range(n):
        fact = fact * i
    return fact"""

        problem_title = st.text_input("Problem Title", value=init_title)
        problem_description = st.text_area("Problem Description", value=init_desc, height=110)
        student_code = st.text_area("Python Student Code", value=init_code, height=240)
        
        analyze_btn = st.button("🚀 Analyze Student Code", type="primary", use_container_width=True)
    
    with col_output:
        st.markdown("### 📊 Mining Diagnostics & Output")
        
        if analyze_btn:
            if not student_code.strip():
                st.warning("⚠️ Please provide student code to analyze.")
            else:
                result = analyze_code(
                    provider.lower(),
                    model,
                    problem_title,
                    problem_description,
                    student_code,
                    enhanced_mode=enhanced_mode
                )
                
                if result and result.get("parse_success"):
                    if result["misconception_found"]:
                        st.markdown(f"""
                        <div class="result-flaw">
                            <h3 style="color:#F87171; margin:0 0 8px 0;">🐛 Misconception Identified</h3>
                            <div style="font-size:1.05rem; font-weight:600; color:#FEE2E2;">
                                {result['description']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("#### 📖 Pedagogical Explanation")
                        st.markdown(result["explanation"])
                        
                        if result.get("trace"):
                            with st.expander("🔍 Mental Execution Trace (Step-by-Step Simulation)", expanded=True):
                                st.markdown(result["trace"])
                                
                        if result.get("verification"):
                            with st.expander("🛡️ Correctness & False-Positive Verification Check", expanded=True):
                                st.markdown(result["verification"])
                                
                        if result.get("retrieved_candidates"):
                            with st.expander("📚 In-Context Taxonomy RAG Candidates Evaluated"):
                                for cand in result["retrieved_candidates"]:
                                    st.markdown(f"- **ID {cand['id']}:** {cand['description']}")
                                    
                    else:
                        st.markdown("""
                        <div class="result-clean">
                            <h3 style="color:#34D399; margin:0 0 8px 0;">✅ Valid Code (No Misconceptions Detected)</h3>
                            <div style="font-size:0.95rem; color:#D1FAE5;">
                                The code executes correctly or employs an acceptable alternative approach without systemic language misunderstandings.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if result.get("verification"):
                            with st.expander("🛡️ Verification Check Details", expanded=True):
                                st.markdown(result["verification"])
                                
                        if result.get("trace"):
                            with st.expander("🔍 Execution Trace"):
                                st.markdown(result["trace"])
                elif result:
                    st.error("❌ Failed to parse response cleanly")
                    with st.expander("View Raw LLM Output"):
                        st.code(result.get("raw_response", ""))
        else:
            st.info("👈 Select a preset or input custom Python code, then click **Analyze Student Code**.")
            st.markdown("""
            **Enhanced Mode Benefits:**
            - **Mental Execution Tracing:** Simulates concrete runtime state to confirm whether code actually fails.
            - **Verification Filter:** Prevents hallucinating bugs on clean code (80%–93% clean code specificity).
            - **Taxonomy RAG:** Maps student errors directly to standard computer science pedagogy definitions.
            """)


def render_benchmark_tab():
    """Render the Empirical Performance Matrix dashboard."""
    st.markdown("### 📈 Empirical Benchmark & Performance Matrix")
    st.markdown("Head-to-head empirical results on dataset bags comparing **Baseline (Old Method)** vs. **Enhanced Methodology (New Method)**.")
    
    # KPI Grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Gemini Accuracy</div>
            <div class="metric-value">60.00%</div>
            <div class="metric-gain">▲ +14.00% vs Baseline</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Groq Qwen Accuracy</div>
            <div class="metric-value">54.00%</div>
            <div class="metric-gain">▲ +8.00% vs Baseline</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Gemini Precision</div>
            <div class="metric-value">88.89%</div>
            <div class="metric-gain">▲ +27.35% Reliability</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">False Alarm Drop</div>
            <div class="metric-value">-71% to -80%</div>
            <div class="metric-gain">▼ Drastic FP Reduction</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("#### 📊 Column-Wise Model Accuracy & Difference Table")
    
    comp_data = [
        {"Model Engine": "Google Gemini (gemini-flash-lite)", "Baseline Acc (Old)": "46.00%", "Enhanced Acc (New)": "60.00%", "Acc Diff (Δ)": "+14.00%", "Baseline Precision": "61.54%", "Enhanced Precision": "88.89%", "Precision Diff (Δ)": "+27.35%", "Clean Code Acc (Old)": "46.67%", "Clean Code Acc (New)": "93.33%", "FP Reduction": "-80.0%"},
        {"Model Engine": "Groq LPU (qwen/qwen3.8-27b)", "Baseline Acc (Old)": "46.00%", "Enhanced Acc (New)": "54.00%", "Acc Diff (Δ)": "+8.00%", "Baseline Precision": "51.16%", "Enhanced Precision": "71.43%", "Precision Diff (Δ)": "+20.27%", "Clean Code Acc (Old)": "6.67%", "Clean Code Acc (New)": "80.00%", "FP Reduction": "-71.4%"},
        {"Model Engine": "Groq LPU (openai/gpt-oss-120b)", "Baseline Acc (Old)": "18.29%", "Enhanced Acc (New)": "24.50%", "Acc Diff (Δ)": "+6.21%", "Baseline Precision": "40.00%", "Enhanced Precision": "55.00%", "Precision Diff (Δ)": "+15.00%", "Clean Code Acc (Old)": "100.00%", "Clean Code Acc (New)": "100.00%", "FP Reduction": "0.0%"},
        {"Model Engine": "Groq LPU (openai/gpt-oss-20b)", "Baseline Acc (Old)": "17.70%", "Enhanced Acc (New)": "22.10%", "Acc Diff (Δ)": "+4.40%", "Baseline Precision": "0.00%", "Enhanced Precision": "33.33%", "Precision Diff (Δ)": "+33.33%", "Clean Code Acc (Old)": "100.00%", "Clean Code Acc (New)": "100.00%", "FP Reduction": "0.0%"}
    ]
    st.dataframe(comp_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("#### 🏆 Overall Benchmark Comparison (MisconAI Multi-Bag Benchmark)")
    bench_data = [
        {"Model": "OpenAI o3-mini (Medium Effort)", "Provider": "OpenAI", "Accuracy": "78.49%", "Precision": "83.27%", "Recall": "70.83%", "F1 Score": "76.55%"},
        {"Model": "OpenAI o3-mini (Low Effort)", "Provider": "OpenAI", "Accuracy": "76.98%", "Precision": "85.65%", "Recall": "67.49%", "F1 Score": "75.49%"},
        {"Model": "Claude Sonnet 4.5 (Reasoning)", "Provider": "Anthropic", "Accuracy": "68.68%", "Precision": "83.76%", "Recall": "77.21%", "F1 Score": "80.35%"},
        {"Model": "Gemini 2.5 Flash (Paper Baseline)", "Provider": "Google", "Accuracy": "62.83%", "Precision": "79.79%", "Recall": "56.20%", "F1 Score": "65.95%"},
        {"Model": "Google Gemini (Enhanced Mode)", "Provider": "Google", "Accuracy": "60.00%", "Precision": "88.89%", "Recall": "47.06%", "F1 Score": "61.54%"},
        {"Model": "Groq Qwen 3.8 27B (Enhanced Mode)", "Provider": "Groq", "Accuracy": "54.00%", "Precision": "71.43%", "Recall": "46.88%", "F1 Score": "56.60%"},
        {"Model": "Groq Qwen 3.8 27B (Baseline Mode)", "Provider": "Groq", "Accuracy": "46.00%", "Precision": "51.16%", "Recall": "78.57%", "F1 Score": "61.97%"}
    ]
    st.dataframe(bench_data, use_container_width=True, hide_index=True)




# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT QUESTION BANK  (75 free-text Python questions, 18 topics)
# Each has: id, topic, question, correct_answer, context, misconception_hint
# ─────────────────────────────────────────────────────────────────────────────
CHATBOT_QUESTIONS = [
    {"id": 1,  "topic": "Basics",
     "question": "What is the output of `print(type(3/2))` in Python 3? Explain why.",
     "correct_answer": "<class 'float'> — because `/` in Python 3 always performs true division and returns a float, even if both operands are integers.",
     "context": "In Python 3, the `/` operator always returns a float. `3/2 = 1.5` so `type(3/2)` is `float`.",
     "misconception_hint": "Confusing Python 3 true division with Python 2 integer division where 3/2 would give 1."},
    {"id": 2,  "topic": "Basics",
     "question": "What is the result of `10 % 3`? What does the `%` operator do?",
     "correct_answer": "1. The `%` (modulo) operator returns the remainder after integer division. 10 ÷ 3 = 3 remainder 1.",
     "context": "Modulo returns the remainder: 10 = 3×3 + 1, so 10 % 3 = 1.",
     "misconception_hint": "Confusing modulo with division or thinking % gives a percentage."},
    {"id": 3,  "topic": "Basics",
     "question": "Is `bool(0)` True or False in Python? Explain what 'falsy' means.",
     "correct_answer": "False. In Python, `0`, empty strings `''`, empty lists `[]`, `None`, and `0.0` are all 'falsy' — they evaluate to False in a boolean context.",
     "context": "Python has truthy/falsy values. 0 is falsy so bool(0) is False.",
     "misconception_hint": "Thinking only the literal False is falsy, not understanding Python's truthiness rules."},
    {"id": 4,  "topic": "Basics",
     "question": "What does `2 ** 3 ** 2` evaluate to? Why?",
     "correct_answer": "512. The `**` operator is right-associative, so `2 ** 3 ** 2` = `2 ** (3**2)` = `2 ** 9` = 512.",
     "context": "Right-associativity: evaluated right-to-left for **.",
     "misconception_hint": "Assuming left-to-right evaluation: 2**3=8, 8**2=64 (wrong)."},
    {"id": 5,  "topic": "Basics",
     "question": "What is the difference between `//` and `/` in Python 3?",
     "correct_answer": "`/` is true division (always returns float). `//` is floor division (truncated toward -∞). E.g., `7/2=3.5`, `7//2=3`, `-7//2=-4`.",
     "context": "// is floor division (rounds down), / is true division.",
     "misconception_hint": "Thinking // just truncates decimal (it floors, which differs for negatives: -7//2=-4, not -3)."},
    {"id": 6,  "topic": "Strings",
     "question": "What does `'hello'[1]` return? Why doesn't it return 'h'?",
     "correct_answer": "'e'. Python uses 0-based indexing — index 0 is 'h', index 1 is 'e'.",
     "context": "0-based indexing: index 0='h', 1='e', 2='l', 3='l', 4='o'.",
     "misconception_hint": "Assuming 1-based indexing where index 1 means the first element."},
    {"id": 7,  "topic": "Strings",
     "question": "What does `'abc' * 3` produce in Python?",
     "correct_answer": "'abcabcabc'. The `*` operator on strings means repetition — it concatenates the string that many times.",
     "context": "String repetition: 'abc' * 3 = 'abcabcabc'.",
     "misconception_hint": "Thinking * is multiplication and will raise an error, or produce '3abc'."},
    {"id": 8,  "topic": "Strings",
     "question": "Are strings mutable in Python? What happens if you try `s = 'hello'; s[0] = 'H'`?",
     "correct_answer": "No, strings are immutable. `s[0] = 'H'` raises a TypeError. To get 'Hello', you must create a new string: `s = 'H' + s[1:]`.",
     "context": "Strings are immutable in Python — you cannot change characters in-place.",
     "misconception_hint": "Treating strings like lists and assuming in-place character assignment works."},
    {"id": 9,  "topic": "Strings",
     "question": "What does `'hello'.upper()` return? Does it modify the original string?",
     "correct_answer": "Returns 'HELLO'. It does NOT modify the original string — strings are immutable. It returns a new string.",
     "context": "String methods return new strings, they don't modify in-place.",
     "misconception_hint": "Thinking string methods like .upper() modify the string in-place."},
    {"id": 10, "topic": "Strings",
     "question": "Explain what `s[-1]` does for `s = 'python'`.",
     "correct_answer": "Returns 'n' — the last character. Negative indices count from the end: -1 is last, -2 is second-to-last, etc.",
     "context": "Negative indexing: s[-1] is the last element.",
     "misconception_hint": "Not knowing negative indices exist or thinking s[-1] raises an error."},
    {"id": 11, "topic": "Lists",
     "question": "What does `[1,2,3].append(4)` return? What is the list after this call?",
     "correct_answer": "Returns `None`. The list is modified in-place to `[1,2,3,4]`. `.append()` returns None, not the modified list.",
     "context": "List mutating methods return None. The list itself is changed in-place.",
     "misconception_hint": "Expecting .append() to return the new list like in some other languages."},
    {"id": 12, "topic": "Lists",
     "question": "What happens when you do `a = [1,2,3]; b = a; b.append(4); print(a)`?",
     "correct_answer": "Prints `[1,2,3,4]`. `b = a` does NOT copy the list — both `a` and `b` point to the same list object. Mutating `b` also changes `a`.",
     "context": "Assignment copies the reference, not the object. Both names point to the same list.",
     "misconception_hint": "Thinking b = a creates an independent copy of the list."},
    {"id": 13, "topic": "Lists",
     "question": "What does `[1,2,3,4][1:3]` return? Is the stop index included?",
     "correct_answer": "`[2,3]`. Slicing `[start:stop]` includes index `start` but EXCLUDES index `stop`. So `[1:3]` gives indices 1 and 2.",
     "context": "Slicing is [start:stop) — stop is exclusive.",
     "misconception_hint": "Thinking the stop index is inclusive and expecting [2,3,4]."},
    {"id": 14, "topic": "Lists",
     "question": "How do you create a proper copy of a list `a` so that modifying the copy doesn't affect `a`?",
     "correct_answer": "Use `a[:]`, `list(a)`, or `a.copy()`. All create a shallow copy. Using `b = a` just creates another reference to the same list.",
     "context": "Shallow copy methods: a[:], list(a), a.copy(). Not b=a.",
     "misconception_hint": "Using b = a thinking it copies the list, or not knowing about copy methods."},
    {"id": 15, "topic": "Lists",
     "question": "What is the difference between `.sort()` and `sorted()`?",
     "correct_answer": "`.sort()` sorts the list in-place and returns `None`. `sorted()` returns a new sorted list without modifying the original.",
     "context": ".sort() in-place returns None. sorted() returns new list.",
     "misconception_hint": "Thinking .sort() returns the sorted list or that sorted() modifies the original."},
    {"id": 16, "topic": "Tuples",
     "question": "How do you create a tuple with only ONE element?",
     "correct_answer": "`(1,)` — with a trailing comma. `(1)` is just the integer 1. The trailing comma is what makes it a tuple.",
     "context": "Single-element tuple requires trailing comma: (1,). Without comma, (1) is just parenthesized int.",
     "misconception_hint": "Thinking (1) creates a single-element tuple."},
    {"id": 17, "topic": "Tuples",
     "question": "Are tuples mutable? What happens if you try to change an element?",
     "correct_answer": "No, tuples are immutable. `t[0] = 10` on a tuple raises a `TypeError`. To 'change' a tuple, you must create a new one.",
     "context": "Tuples are immutable — element assignment raises TypeError.",
     "misconception_hint": "Treating tuples like lists and assuming in-place modification works."},
    {"id": 18, "topic": "Tuples",
     "question": "If a tuple contains a list, e.g. `t = (1, [2,3])`, can you modify the list inside?",
     "correct_answer": "Yes! `t[1].append(4)` works — the tuple itself is immutable (you can't replace `t[1]`), but the list object inside can be mutated.",
     "context": "Tuples are immutable in terms of what objects they hold, but mutable objects inside can still be changed.",
     "misconception_hint": "Thinking immutability extends to all nested objects inside the tuple."},
    {"id": 19, "topic": "Sets",
     "question": "What does `{1, 2, 2, 3}` evaluate to? What property of sets explains this?",
     "correct_answer": "`{1, 2, 3}`. Sets only store unique elements — duplicates are automatically removed.",
     "context": "Sets are unordered collections of unique elements.",
     "misconception_hint": "Not knowing sets eliminate duplicates, expecting {1,2,2,3}."},
    {"id": 20, "topic": "Sets",
     "question": "What is the difference between `|` and `&` for sets?",
     "correct_answer": "`|` is union (all elements from both). `&` is intersection (only elements in both). E.g., `{1,2} | {2,3} = {1,2,3}` and `{1,2} & {2,3} = {2}`.",
     "context": "| = union, & = intersection for sets.",
     "misconception_hint": "Confusing union (|) with intersection (&)."},
    {"id": 21, "topic": "Dicts",
     "question": "What happens if you access a missing key with `d['missing_key']`? How can you avoid the error?",
     "correct_answer": "Raises a `KeyError`. Use `d.get('missing_key')` which returns `None`, or `d.get('key', default)` to specify a fallback.",
     "context": "Missing key with [] raises KeyError. .get() returns None or a default safely.",
     "misconception_hint": "Expecting None or a default value instead of KeyError from direct key access."},
    {"id": 22, "topic": "Dicts",
     "question": "What does `{'a': 1, 'a': 2}['a']` return? Are duplicate keys allowed?",
     "correct_answer": "Returns `2`. Python allows duplicate keys — the last value overwrites previous ones silently.",
     "context": "Last key-value wins when there are duplicates in dict literal.",
     "misconception_hint": "Thinking duplicate keys raise an error or that both values are stored."},
    {"id": 23, "topic": "Dicts",
     "question": "What is the difference between `.keys()`, `.values()`, and `.items()`?",
     "correct_answer": "`.keys()` = view of all keys. `.values()` = view of all values. `.items()` = view of `(key, value)` pairs as tuples.",
     "context": ".keys()=keys, .values()=values, .items()=(key,value) pairs.",
     "misconception_hint": "Confusing which method returns what, or thinking they return lists."},
    {"id": 24, "topic": "Dicts",
     "question": "How does dictionary ordering work in Python 3.7+?",
     "correct_answer": "Since Python 3.7, dicts maintain insertion order — keys are iterated in the order they were added. This is a language guarantee.",
     "context": "Python 3.7+ dicts preserve insertion order.",
     "misconception_hint": "Thinking dicts are unordered (was true in Python 2 and before 3.7)."},
    {"id": 25, "topic": "Control Flow",
     "question": "What does `range(5)` produce? Does it include 5?",
     "correct_answer": "Produces integers 0, 1, 2, 3, 4. It does NOT include 5 — `range(stop)` is exclusive of stop.",
     "context": "range(n) produces 0 to n-1. Stop is exclusive.",
     "misconception_hint": "Thinking range(n) starts from 1 or is inclusive of n."},
    {"id": 26, "topic": "Control Flow",
     "question": "What is the difference between `break` and `continue` in a loop?",
     "correct_answer": "`break` exits the entire loop. `continue` skips the rest of the current iteration and jumps to the next.",
     "context": "break exits loop, continue skips current iteration.",
     "misconception_hint": "Confusing break (exit loop) with continue (skip iteration)."},
    {"id": 27, "topic": "Control Flow",
     "question": "Explain what `else` on a `for` loop does in Python.",
     "correct_answer": "The `else` runs if the loop completed normally without hitting `break`. It does NOT run if `break` was triggered.",
     "context": "for/else: else runs when loop completes without break.",
     "misconception_hint": "Thinking for/else is like if/else (runs when loop body is empty or condition was False)."},
    {"id": 28, "topic": "Control Flow",
     "question": "What does the ternary expression `x if condition else y` do?",
     "correct_answer": "Returns `x` if `condition` is True, otherwise returns `y`. E.g., `'even' if n%2==0 else 'odd'`.",
     "context": "Python ternary: value_if_true if condition else value_if_false.",
     "misconception_hint": "Not knowing Python's ternary syntax or confusing the order."},
    {"id": 29, "topic": "Functions",
     "question": "What does a Python function return if it has no explicit `return` statement?",
     "correct_answer": "`None`. All Python functions implicitly return `None` when execution reaches the end without a `return`.",
     "context": "No return statement → returns None.",
     "misconception_hint": "Thinking no return statement causes an error, or that the function returns 0 or False."},
    {"id": 30, "topic": "Functions",
     "question": "Why is using a mutable default argument like `def f(lst=[]):` dangerous?",
     "correct_answer": "The default list `[]` is created ONCE when the function is defined. Mutations persist across calls. Fix: use `def f(lst=None): if lst is None: lst = []`.",
     "context": "Mutable defaults are created once at definition time, shared across calls.",
     "misconception_hint": "Thinking default arguments are re-created fresh on every function call."},
    {"id": 31, "topic": "Functions",
     "question": "What is the difference between `*args` and `**kwargs`?",
     "correct_answer": "`*args` collects extra positional arguments into a tuple. `**kwargs` collects extra keyword arguments into a dict.",
     "context": "*args = extra positional as tuple, **kwargs = extra keyword as dict.",
     "misconception_hint": "Confusing *args with **kwargs or thinking they're interchangeable."},
    {"id": 32, "topic": "Functions",
     "question": "What is a lambda function? What are its limitations?",
     "correct_answer": "A lambda is an anonymous, single-expression function: `lambda x: x*2`. It can only contain one expression — no statements, no multiple lines.",
     "context": "lambda = anonymous single-expression function. No statements allowed.",
     "misconception_hint": "Thinking lambdas can contain multiple statements or be multi-line."},
    {"id": 33, "topic": "Functions",
     "question": "Explain the concept of variable scope in Python (LEGB rule).",
     "correct_answer": "Python resolves names: Local → Enclosing → Global → Built-in (LEGB). Use `global` for module-level vars, `nonlocal` for enclosing function vars.",
     "context": "LEGB: Local, Enclosing, Global, Built-in scope lookup order.",
     "misconception_hint": "Not understanding scope lookup or thinking inner functions can freely modify outer variables."},
    {"id": 34, "topic": "OOP",
     "question": "What is `self` in a Python class method? Is it a keyword?",
     "correct_answer": "`self` refers to the instance. It is NOT a keyword — it's a convention. Python passes the instance automatically as the first argument.",
     "context": "self is the instance, passed automatically as first arg. It's a convention, not keyword.",
     "misconception_hint": "Thinking self is a reserved Python keyword like Java's `this`."},
    {"id": 35, "topic": "OOP",
     "question": "What is the difference between `__init__` and `__new__` in Python?",
     "correct_answer": "`__new__` creates the instance. `__init__` initializes it. In practice you almost always only override `__init__`.",
     "context": "__new__ creates, __init__ initializes. Normally only override __init__.",
     "misconception_hint": "Thinking __init__ creates the object (it doesn't — __new__ does)."},
    {"id": 36, "topic": "OOP",
     "question": "What is the difference between `@staticmethod` and `@classmethod`?",
     "correct_answer": "`@staticmethod`: no `self` or `cls`. `@classmethod`: receives `cls` as first arg, used for factory methods or class-level state.",
     "context": "@staticmethod: no self/cls. @classmethod: receives cls as first arg.",
     "misconception_hint": "Confusing staticmethod (no class/instance access) with classmethod (receives cls)."},
    {"id": 37, "topic": "OOP",
     "question": "What is `__repr__` vs `__str__` in a class?",
     "correct_answer": "`__repr__` is the developer-facing representation (REPL, debuggers). `__str__` is the user-facing representation (used by `print()`). If only `__repr__` is defined, it's used for both.",
     "context": "__repr__ for developers/debugging, __str__ for users/print. repr used as fallback.",
     "misconception_hint": "Thinking __repr__ and __str__ are the same or interchangeable."},
    {"id": 38, "topic": "Exceptions",
     "question": "What is the difference between `try/except/else/finally`? When does `else` run?",
     "correct_answer": "`else`: runs ONLY if no exception in `try`. `finally`: ALWAYS runs regardless. Use `finally` for cleanup (closing files etc.).",
     "context": "else: runs if no exception. finally: always runs.",
     "misconception_hint": "Confusing else (no exception) with finally (always runs)."},
    {"id": 39, "topic": "Exceptions",
     "question": "What is the difference between `raise` in Python vs `throw` in Java/JavaScript?",
     "correct_answer": "Python uses `raise` (not `throw`). `raise ValueError('msg')` raises an exception. `raise` alone inside `except` re-raises the current exception.",
     "context": "Python uses raise, not throw. raise alone inside except re-raises.",
     "misconception_hint": "Using throw (Java/JS syntax) instead of raise in Python."},
    {"id": 40, "topic": "Exceptions",
     "question": "What exception does Python raise for division by zero?",
     "correct_answer": "`ZeroDivisionError`. Both `0/0` and `0//0` raise it. Python doesn't produce NaN like JavaScript.",
     "context": "ZeroDivisionError for any division by zero.",
     "misconception_hint": "Expecting ArithmeticError (Java) or NaN (JavaScript) instead of ZeroDivisionError."},
    {"id": 41, "topic": "Comprehensions",
     "question": "What does `[x**2 for x in range(4)]` produce? Trace through it.",
     "correct_answer": "[0, 1, 4, 9]. `range(4)` = 0,1,2,3. Squaring each: 0,1,4,9.",
     "context": "range(4) gives 0,1,2,3. List comprehension squares each.",
     "misconception_hint": "Off-by-one: thinking range(4) gives 1,2,3,4 and expecting [1,4,9,16]."},
    {"id": 42, "topic": "Comprehensions",
     "question": "What is a generator expression vs a list comprehension? When should you use each?",
     "correct_answer": "List comprehension `[x for x in ...]` creates a full list in memory. Generator expression `(x for x in ...)` is lazy — yields one value at a time. Use generators for large data.",
     "context": "[] = eager list in memory. () = lazy generator on demand.",
     "misconception_hint": "Not knowing generator expressions exist or thinking (x for x) creates a tuple."},
    {"id": 43, "topic": "Comprehensions",
     "question": "Write a dict comprehension that maps numbers 1–5 to their squares.",
     "correct_answer": "`{n: n**2 for n in range(1, 6)}` → `{1: 1, 2: 4, 3: 9, 4: 16, 5: 25}`. Dict comprehensions use `{key: value for ... in ...}`.",
     "context": "{k:v for ...} syntax for dict comprehensions.",
     "misconception_hint": "Using [] for dict comprehension or wrong key:value syntax."},
    {"id": 44, "topic": "File I/O",
     "question": "What is the difference between file modes `'r'`, `'w'`, `'a'`, and `'x'`?",
     "correct_answer": "`'r'`: read (error if missing). `'w'`: write, creates or TRUNCATES. `'a'`: append. `'x'`: exclusive create (error if exists).",
     "context": "r=read, w=write/truncate, a=append, x=exclusive create.",
     "misconception_hint": "Confusing modes — especially 'w' truncating vs 'a' appending."},
    {"id": 45, "topic": "File I/O",
     "question": "Why use `with open(...) as f:` instead of manually calling `f.close()`?",
     "correct_answer": "The `with` statement (context manager) automatically calls `f.close()` even if an exception occurs. Manual close can be skipped on exception.",
     "context": "with = context manager, guarantees close even on exception.",
     "misconception_hint": "Not knowing context managers or thinking manual close is equivalent."},
    {"id": 46, "topic": "Modules",
     "question": "What is the difference between `import math` and `from math import sqrt`?",
     "correct_answer": "`import math`: must use `math.sqrt()`. `from math import sqrt`: imports `sqrt` directly into namespace, use as `sqrt()`. Can cause name collisions.",
     "context": "import module: need module.func. from module import func: direct access.",
     "misconception_hint": "Not understanding namespace differences between import styles."},
    {"id": 47, "topic": "Modules",
     "question": "What does `if __name__ == '__main__':` do? Why is it useful?",
     "correct_answer": "When run directly, `__name__` is `'__main__'`. When imported, `__name__` is the filename. The guard ensures code only runs when the file is the entry point.",
     "context": "__name__ == '__main__' only when script run directly, not when imported.",
     "misconception_hint": "Not understanding the import/run-directly distinction."},
    {"id": 48, "topic": "Generators",
     "question": "What does the `yield` keyword do? How does it differ from `return`?",
     "correct_answer": "`yield` pauses execution and saves state — the function becomes a generator. `return` exits completely. Generator state is preserved between `next()` calls.",
     "context": "yield pauses execution and saves state. return exits completely.",
     "misconception_hint": "Thinking yield is just like return but can be used multiple times."},
    {"id": 49, "topic": "Generators",
     "question": "What is the memory advantage of generators over lists? Give an example.",
     "correct_answer": "Generators produce values on demand (lazy). `range(1_000_000_000)` takes ~48 bytes; `list(range(1_000_000_000))` would use ~8GB RAM.",
     "context": "Generators: lazy, O(1) memory. Lists: eager, O(n) memory.",
     "misconception_hint": "Not understanding lazy evaluation — thinking generator still stores all values."},
    {"id": 50, "topic": "Decorators",
     "question": "What does a Python decorator do? Explain with a simple example.",
     "correct_answer": "A decorator wraps a function to add/modify behavior. `@my_decorator` is sugar for `f = my_decorator(f)`. E.g., a timer decorator measures function execution time.",
     "context": "@decorator is sugar for f = decorator(f). Wraps function behavior.",
     "misconception_hint": "Not knowing decorators are just higher-order functions using @syntax."},
    {"id": 51, "topic": "Types",
     "question": "What does `isinstance(True, int)` return? Explain why.",
     "correct_answer": "`True`. In Python, `bool` is a subclass of `int`. `True == 1` and `False == 0`. So `True + True == 2`.",
     "context": "bool is subclass of int. True=1, False=0.",
     "misconception_hint": "Not knowing bool inherits from int, expecting False."},
    {"id": 52, "topic": "Types",
     "question": "What is dynamic typing in Python? How does it differ from Java?",
     "correct_answer": "Python is dynamically typed — variable types determined at runtime and can change. Java is statically typed. Python type hints are optional, not enforced at runtime.",
     "context": "Dynamic typing: type assigned at runtime. Type hints are not enforced.",
     "misconception_hint": "Thinking Python type hints enforce type checking like Java's static types."},
    {"id": 53, "topic": "Built-ins",
     "question": "What is the difference between `map()` and a list comprehension?",
     "correct_answer": "`map(func, iterable)` returns a lazy iterator. A list comprehension `[func(x) for x in iterable]` returns an eager list. `map` is slightly faster; comprehensions are more readable.",
     "context": "map() is lazy iterator. list comprehension is eager list.",
     "misconception_hint": "Thinking map() returns a list directly (it returns a map object in Python 3)."},
    {"id": 54, "topic": "Built-ins",
     "question": "What does `enumerate()` do? Give an example of why it's useful.",
     "correct_answer": "`enumerate(iterable)` returns `(index, value)` pairs. Avoids the `for i in range(len(lst)):` anti-pattern. E.g., `for i, val in enumerate(lst):`.",
     "context": "enumerate gives (index, value) pairs. Avoids range(len()) pattern.",
     "misconception_hint": "Using range(len(x)) pattern instead of enumerate."},
    {"id": 55, "topic": "Built-ins",
     "question": "Explain what `zip()` does with an example.",
     "correct_answer": "`zip([1,2,3], ['a','b','c'])` → `(1,'a'), (2,'b'), (3,'c')`. Stops at shortest iterable. Used for parallel iteration.",
     "context": "zip pairs elements from multiple iterables into tuples.",
     "misconception_hint": "Thinking zip concatenates lists or fills unequal lengths with None (that's zip_longest)."},
    {"id": 56, "topic": "Built-ins",
     "question": "What does `filter(lambda x: x > 2, [1,2,3,4])` return?",
     "correct_answer": "A filter object (lazy iterator) yielding `3, 4`. Use `list(filter(...))` to get `[3, 4]`.",
     "context": "filter returns lazy iterator of elements where func is True.",
     "misconception_hint": "Thinking filter returns a list or keeps elements where func is False."},
    {"id": 57, "topic": "Memory",
     "question": "What is the difference between `is` and `==` in Python?",
     "correct_answer": "`==` checks value equality. `is` checks identity (same object in memory). Never use `is` to compare values — use `==`.",
     "context": "== checks value. is checks identity (same object in memory).",
     "misconception_hint": "Using 'is' to compare values like strings or numbers."},
    {"id": 58, "topic": "Memory",
     "question": "What is the difference between shallow copy and deep copy?",
     "correct_answer": "Shallow copy creates new container but nested objects are shared. Deep copy (`copy.deepcopy()`) recursively copies all nested objects too.",
     "context": "Shallow: new container, shared nested. Deep: fully independent recursive copy.",
     "misconception_hint": "Thinking shallow copy fully isolates the copy — it doesn't for nested mutable objects."},
    {"id": 59, "topic": "Scope",
     "question": "What is a closure in Python? Give a practical example.",
     "correct_answer": "A closure is a function that 'remembers' variables from its enclosing scope after that scope has finished. Used in factory functions and decorators.",
     "context": "Closure: inner function captures variables from outer function's scope.",
     "misconception_hint": "Not understanding closures or thinking inner function can't access outer variables after outer returns."},
    {"id": 60, "topic": "Scope",
     "question": "When do you need `global` vs `nonlocal` in Python?",
     "correct_answer": "`global x`: write to module-level `x`. `nonlocal x`: write to enclosing function's `x`. Without these, assignment creates a new local variable.",
     "context": "global: module-level write. nonlocal: enclosing function write.",
     "misconception_hint": "Not knowing nonlocal exists or thinking you can write to outer scope variables without keyword."},
    {"id": 61, "topic": "Recursion",
     "question": "What is the base case in recursion and why is it essential?",
     "correct_answer": "The base case returns a result without a recursive call. Without it, recursion never terminates and raises `RecursionError`.",
     "context": "Base case prevents infinite recursion and RecursionError.",
     "misconception_hint": "Writing recursive functions without a base case."},
    {"id": 62, "topic": "Recursion",
     "question": "What error does Python raise for infinite recursion and why?",
     "correct_answer": "`RecursionError: maximum recursion depth exceeded`. Python has a default ~1000 frame limit. Use `sys.setrecursionlimit()` to change it.",
     "context": "RecursionError with ~1000 default limit. sys.setrecursionlimit can change it.",
     "misconception_hint": "Expecting StackOverflowError (Java/C++) instead of RecursionError."},
    {"id": 63, "topic": "Operators",
     "question": "Explain Python's `not`, `and`, and `or` operators with short-circuit evaluation.",
     "correct_answer": "`and` returns first falsy or last value. `or` returns first truthy or last. E.g., `None or 'default'` = `'default'`, `5 and 'yes'` = `'yes'`.",
     "context": "Short-circuit: and returns first falsy or last. or returns first truthy or last.",
     "misconception_hint": "Thinking and/or always return True/False instead of one of the operands."},
    {"id": 64, "topic": "Operators",
     "question": "What does `x = x or []` do and why is it a common Python idiom?",
     "correct_answer": "If `x` is falsy, assigns `[]` to `x`. If truthy, keeps `x`. Used as a safe default: `def f(lst=None): lst = lst or []`.",
     "context": "x or y returns x if truthy, else y. Used for safe defaults.",
     "misconception_hint": "Not understanding short-circuit evaluation making this pattern work."},
    {"id": 65, "topic": "Advanced",
     "question": "What is the GIL (Global Interpreter Lock) in CPython? How does it affect threading?",
     "correct_answer": "The GIL allows only ONE thread to execute Python bytecode at a time. Threads can't achieve CPU parallelism for CPU-bound tasks. Use `multiprocessing` for that.",
     "context": "GIL limits one thread at a time in CPython. Affects CPU-bound, not I/O-bound.",
     "misconception_hint": "Thinking Python threads give CPU parallelism like Java/C++ threads."},
    {"id": 66, "topic": "Advanced",
     "question": "What is `*` (star) unpacking in Python? Give examples.",
     "correct_answer": "`a, *b, c = [1,2,3,4,5]` → `a=1, b=[2,3,4], c=5`. Also used in function calls `func(*list)` and merging `[*list1, *list2]`.",
     "context": "* unpacks iterables in assignment, function calls, and literals.",
     "misconception_hint": "Not knowing Python's extended unpacking (*) syntax."},
    {"id": 67, "topic": "Advanced",
     "question": "Explain Python's `__dunder__` (double underscore) methods. Why are they called magic methods?",
     "correct_answer": "Dunder methods like `__len__`, `__add__`, `__iter__` define how objects respond to Python operators and built-ins. Python calls them implicitly (e.g., `len(obj)` calls `obj.__len__()`).",
     "context": "Dunder methods define Python operator/built-in behavior. Called implicitly by Python.",
     "misconception_hint": "Thinking dunder methods must be called directly rather than through built-ins."},
    {"id": 68, "topic": "Python 3",
     "question": "What does `input()` return in Python 3? How is it different from Python 2?",
     "correct_answer": "In Python 3, `input()` ALWAYS returns a string. Must cast for numbers: `int(input())`. Python 2's `input()` evaluated input as code.",
     "context": "Python 3 input() always returns str. Must cast for numeric types.",
     "misconception_hint": "Assuming input() can auto-detect type or return int (Python 2 behavior)."},
    {"id": 69, "topic": "Python 3",
     "question": "What are f-strings and what makes them better than `.format()` or `%` formatting?",
     "correct_answer": "f-strings (Python 3.6+): `f'Hello {name}!'`. Faster, more readable, support expressions `f'{2+2}'`, attributes `f'{obj.name}'`, format specs `f'{val:.2f}'`.",
     "context": "f-strings: fast, readable, support expressions. f'...' prefix.",
     "misconception_hint": "Not knowing f-string syntax or thinking you need quotes inside the braces."},
    {"id": 70, "topic": "Python 3",
     "question": "What are type hints in Python? Are they enforced at runtime?",
     "correct_answer": "Type hints (PEP 484) are annotations like `def f(x: int) -> str:`. NOT enforced at runtime — Python still allows wrong types. They're for documentation and static analysis tools.",
     "context": "Type hints are documentation only, not enforced at runtime.",
     "misconception_hint": "Thinking Python type hints enforce types at runtime like Java/TypeScript."},
    {"id": 71, "topic": "Iterators",
     "question": "What is the difference between an iterable and an iterator in Python?",
     "correct_answer": "An **iterable** has `__iter__()` (lists, strings). An **iterator** has both `__iter__()` and `__next__()`. Iterators are one-pass — once exhausted, they're done.",
     "context": "Iterable: has __iter__. Iterator: has __iter__ + __next__. One-pass.",
     "misconception_hint": "Thinking iterables and iterators are the same thing."},
    {"id": 72, "topic": "Iterators",
     "question": "What happens when you call `next()` on an exhausted iterator?",
     "correct_answer": "Raises `StopIteration`. This is how for loops know to stop. Use `next(iterator, default)` to avoid the exception.",
     "context": "StopIteration raised when iterator is exhausted. next(it, default) avoids exception.",
     "misconception_hint": "Expecting None or looping back to start when iterator is exhausted."},
    {"id": 73, "topic": "Strings",
     "question": "What is the difference between `split()` and `split(' ')`?",
     "correct_answer": "`split()` splits on any whitespace and collapses multiple spaces. `split(' ')` splits only on single spaces and produces empty strings for consecutive spaces.",
     "context": "split() handles all whitespace + collapses. split(' ') only single space.",
     "misconception_hint": "Thinking split() and split(' ') are identical."},
    {"id": 74, "topic": "Strings",
     "question": "How does string `join()` work? Why is `''.join(list)` faster than concatenation with `+`?",
     "correct_answer": "`'sep'.join(iterable)` concatenates with sep between elements. Faster than `+` because strings are immutable — each `+` creates a new object. `join()` does it in one pass.",
     "context": "join() is O(n). Repeated + concatenation is O(n²) due to immutability.",
     "misconception_hint": "Not knowing join() or thinking + concatenation is equally efficient."},
    {"id": 75, "topic": "Strings",
     "question": "What is string interning in Python? Why does `'hello' is 'hello'` return True?",
     "correct_answer": "Python reuses ('interns') identical string literals that look like identifiers. But dynamically created strings may not be interned. Always use `==` to compare string values — never `is`.",
     "context": "String interning: Python reuses some string objects. Always use == for value comparison.",
     "misconception_hint": "Using 'is' to compare strings and being confused by inconsistent results due to interning."},
]


def analyze_free_text_with_llm(provider: str, model: str, question_data: dict, student_answer: str, enhanced_mode: bool = True):
    """Wrapper that calls analyze_free_text_answer and returns structured result."""
    return analyze_free_text_answer(provider, model, question_data, student_answer, enhanced_mode)


def analyze_free_text_answer(provider: str, model: str, question_data: dict, student_answer: str, enhanced_mode: bool = True):

    """Use LLM + RAG to evaluate a free-text student answer and diagnose any misconception."""
    question_text = question_data["question"]
    correct_answer = question_data["correct_answer"]
    topic = question_data.get("topic", "Python")
    misconception_hint = question_data.get("misconception_hint", "")
    context = question_data.get("context", "")

    # RAG: retrieve related misconceptions from the bank
    retrieved_candidates = []
    candidate_prompt = ""
    if enhanced_mode:
        rag_query = f"{topic} {question_text} {student_answer} {misconception_hint}"
        retrieved_candidates = rag_indexer.retrieve_candidates(rag_query)
        candidate_prompt = rag_indexer.format_candidates_prompt(retrieved_candidates)

    prompt = f"""You are MisconAI — an expert Python educator and misconception analyst using the Enhanced Chain-of-Thought methodology.

A student has answered a Python conceptual question. Evaluate their answer and diagnose any misconceptions.

## Question
Topic: {topic}
{question_text}

## Additional Context
{context}

## Student's Answer
"{student_answer}"

## Correct Answer Reference
{correct_answer}

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

    client = create_llm_client(provider, model)
    if not client:
        return None

    config = get_llm_config(provider, model)
    messages = [{"role": "user", "content": prompt}]

    try:
        with st.spinner(f"🔍 Analyzing your answer with {model} (Enhanced RAG Mode)..."):
            if provider == "groq":
                response = client.create_message(
                    messages,
                    kwargs={"model": config["model"], "temperature": 0.2, "max_tokens": 1800},
                    reasoning=config.get("reasoning", False)
                )
            elif provider == "openai":
                response = client.create_message(
                    messages,
                    kwargs={"model": config["model"], "temperature": 0.2, "max_tokens": 1800},
                    reasoning=config.get("reasoning", False),
                    reasoning_effort=config.get("reasoning_effort", "medium")
                )
            elif provider == "gemini":
                response = client.create_message(
                    messages,
                    kwargs={"max_output_tokens": 1800, "temperature": 0.2},
                    reasoning=config.get("reasoning", False),
                    thinking_budget=config.get("thinking_budget", 1500)
                )
            else:
                return None

        parsed = parse_mining_response(response)
        parsed["retrieved_candidates"] = retrieved_candidates
        parsed["raw_response"] = response
        return parsed

    except Exception as e:
        st.error(f"Error in misconception analysis: {str(e)}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION BANK  — free-text misconception chatbot (75 questions, 18 topics)
# Each question has: id, topic, question, correct_answer, context, misconception_hint
# ─────────────────────────────────────────────────────────────────────────────
CHATBOT_QUESTIONS = [
    # ── Basics ──
    {"id": 1,  "topic": "Basics",
     "question": "What is the output of `print(type(3/2))` in Python 3? Explain why.",
     "correct_answer": "<class 'float'> — because `/` in Python 3 always performs true division and returns a float, even if both operands are integers.",
     "context": "In Python 3, the `/` operator always returns a float. `3/2 = 1.5` so `type(3/2)` is `float`.",
     "misconception_hint": "Confusing Python 3 true division with Python 2 integer division where 3/2 would give 1."},

    {"id": 2,  "topic": "Basics",
     "question": "What is the result of `10 % 3`? What does the `%` operator do?",
     "correct_answer": "1. The `%` (modulo) operator returns the remainder after integer division. 10 ÷ 3 = 3 remainder 1.",
     "context": "Modulo returns the remainder: 10 = 3×3 + 1, so 10 % 3 = 1.",
     "misconception_hint": "Confusing modulo with division or thinking % gives a percentage."},

    {"id": 3,  "topic": "Basics",
     "question": "Is `bool(0)` True or False in Python? Explain what 'falsy' means.",
     "correct_answer": "False. In Python, `0`, empty strings `''`, empty lists `[]`, `None`, and `0.0` are all 'falsy' — they evaluate to False in a boolean context.",
     "context": "Python has truthy/falsy values. 0 is falsy so bool(0) is False.",
     "misconception_hint": "Thinking only the literal False is falsy, not understanding Python's truthiness rules."},

    {"id": 4,  "topic": "Basics",
     "question": "What does `2 ** 3 ** 2` evaluate to? Why?",
     "correct_answer": "512. The `**` operator is right-associative, so `2 ** 3 ** 2` = `2 ** (3**2)` = `2 ** 9` = 512.",
     "context": "Right-associativity: evaluated right-to-left for **.",
     "misconception_hint": "Assuming left-to-right evaluation: 2**3=8, 8**2=64 (wrong)."},

    {"id": 5,  "topic": "Basics",
     "question": "What is the difference between `//` and `/` in Python 3?",
     "correct_answer": "`/` is true division (always returns float). `//` is floor division (returns int or float, but truncated toward negative infinity). E.g., `7/2=3.5`, `7//2=3`.",
     "context": "// is floor division (rounds down), / is true division.",
     "misconception_hint": "Thinking // just truncates decimal (it floors, which differs for negatives: -7//2=-4, not -3)."},

    # ── Strings ──
    {"id": 6,  "topic": "Strings",
     "question": "What does `'hello'[1]` return? Why doesn't it return 'h'?",
     "correct_answer": "'e'. Python uses 0-based indexing — index 0 is 'h', index 1 is 'e'.",
     "context": "0-based indexing: index 0='h', 1='e', 2='l', 3='l', 4='o'.",
     "misconception_hint": "Assuming 1-based indexing where index 1 means the first element."},

    {"id": 7,  "topic": "Strings",
     "question": "What does `'abc' * 3` produce in Python?",
     "correct_answer": "'abcabcabc'. The `*` operator on strings means repetition — it concatenates the string that many times.",
     "context": "String repetition: 'abc' * 3 = 'abcabcabc'.",
     "misconception_hint": "Thinking * is multiplication and will raise an error, or produce '3abc'."},

    {"id": 8,  "topic": "Strings",
     "question": "Are strings mutable in Python? What happens if you try `s = 'hello'; s[0] = 'H'`?",
     "correct_answer": "No, strings are immutable. `s[0] = 'H'` raises a TypeError. To get 'Hello', you must create a new string: `s = 'H' + s[1:]`.",
     "context": "Strings are immutable in Python — you cannot change characters in-place.",
     "misconception_hint": "Treating strings like lists and assuming in-place character assignment works."},

    {"id": 9,  "topic": "Strings",
     "question": "What does `'hello'.upper()` return? Does it modify the original string?",
     "correct_answer": "Returns 'HELLO'. It does NOT modify the original string — it returns a new string. The variable `'hello'` is unchanged because strings are immutable.",
     "context": "String methods return new strings, they don't modify in-place.",
     "misconception_hint": "Thinking string methods like .upper() modify the string in-place and the original is changed."},

    {"id": 10, "topic": "Strings",
     "question": "Explain what `s[-1]` does for `s = 'python'`.",
     "correct_answer": "Returns 'n' — the last character. Negative indices count from the end: -1 is last, -2 is second-to-last, etc.",
     "context": "Negative indexing: s[-1] is the last element.",
     "misconception_hint": "Not knowing negative indices exist or thinking s[-1] raises an error."},

    # ── Lists ──
    {"id": 11, "topic": "Lists",
     "question": "What does `[1,2,3].append(4)` return? What is the list after this call?",
     "correct_answer": "Returns `None`. The list is modified in-place to `[1,2,3,4]`. `.append()` is a mutating method that returns None, not the modified list.",
     "context": "List mutating methods return None. The list itself is changed in-place.",
     "misconception_hint": "Expecting .append() to return the new list like in some other languages."},

    {"id": 12, "topic": "Lists",
     "question": "What happens when you do `a = [1,2,3]; b = a; b.append(4); print(a)`?",
     "correct_answer": "Prints `[1,2,3,4]`. `b = a` does NOT copy the list — both `a` and `b` point to the same list object. Mutating `b` also changes `a`.",
     "context": "Assignment copies the reference, not the object. Both names point to the same list.",
     "misconception_hint": "Thinking b = a creates an independent copy of the list."},

    {"id": 13, "topic": "Lists",
     "question": "What does `[1,2,3,4][1:3]` return? Is the stop index included?",
     "correct_answer": "`[2,3]`. Slicing `[start:stop]` includes index `start` but EXCLUDES index `stop`. So `[1:3]` gives indices 1 and 2.",
     "context": "Slicing is [start:stop) — stop is exclusive.",
     "misconception_hint": "Thinking the stop index is inclusive and expecting [2,3,4]."},

    {"id": 14, "topic": "Lists",
     "question": "How do you create a proper copy of a list `a` so that modifying the copy doesn't affect `a`?",
     "correct_answer": "Use `a[:]`, `list(a)`, or `a.copy()`. All create a shallow copy. Using `b = a` just creates another reference to the same list.",
     "context": "Shallow copy methods: a[:], list(a), a.copy(). Not b=a.",
     "misconception_hint": "Using b = a thinking it copies the list, or not knowing about copy methods."},

    {"id": 15, "topic": "Lists",
     "question": "What is the difference between `.sort()` and `sorted()`?",
     "correct_answer": "`.sort()` sorts the list in-place and returns `None`. `sorted()` returns a new sorted list without modifying the original. Use `sorted()` when you need the original preserved.",
     "context": ".sort() in-place returns None. sorted() returns new list.",
     "misconception_hint": "Thinking .sort() returns the sorted list or that sorted() modifies the original."},

    # ── Tuples ──
    {"id": 16, "topic": "Tuples",
     "question": "How do you create a tuple with only ONE element?",
     "correct_answer": "`(1,)` — with a trailing comma. `(1)` is just the integer 1 in parentheses, not a tuple. The trailing comma is what makes it a tuple.",
     "context": "Single-element tuple requires trailing comma: (1,). Without comma, (1) is just parenthesized int.",
     "misconception_hint": "Thinking (1) creates a single-element tuple."},

    {"id": 17, "topic": "Tuples",
     "question": "Are tuples mutable? What happens if you try to change an element?",
     "correct_answer": "No, tuples are immutable. `t[0] = 10` on a tuple raises a `TypeError`. To 'change' a tuple, you must create a new one.",
     "context": "Tuples are immutable — element assignment raises TypeError.",
     "misconception_hint": "Treating tuples like lists and assuming in-place modification works."},

    {"id": 18, "topic": "Tuples",
     "question": "If a tuple contains a list, e.g. `t = (1, [2,3])`, can you modify the list inside?",
     "correct_answer": "Yes! `t[1].append(4)` works — the tuple itself is immutable (you can't replace `t[1]`), but the list object inside can be mutated. So `t` becomes `(1, [2,3,4])`.",
     "context": "Tuples are immutable in terms of what objects they hold, but mutable objects inside can still be changed.",
     "misconception_hint": "Thinking immutability extends to all nested objects inside the tuple."},

    # ── Sets ──
    {"id": 19, "topic": "Sets",
     "question": "What does `{1, 2, 2, 3}` evaluate to? What property of sets explains this?",
     "correct_answer": "`{1, 2, 3}`. Sets only store unique elements — duplicates are automatically removed.",
     "context": "Sets are unordered collections of unique elements.",
     "misconception_hint": "Not knowing sets eliminate duplicates, expecting {1,2,2,3}."},

    {"id": 20, "topic": "Sets",
     "question": "What is the difference between `|` and `&` for sets?",
     "correct_answer": "`|` is the union operator (all elements from both sets). `&` is the intersection operator (only elements in both sets). E.g., `{1,2} | {2,3} = {1,2,3}` and `{1,2} & {2,3} = {2}`.",
     "context": "| = union, & = intersection for sets.",
     "misconception_hint": "Confusing union (|) with intersection (&)."},

    # ── Dictionaries ──
    {"id": 21, "topic": "Dicts",
     "question": "What happens if you access a missing key with `d['missing_key']`? How can you avoid the error?",
     "correct_answer": "Raises a `KeyError`. To safely access a key, use `d.get('missing_key')` which returns `None` by default, or `d.get('missing_key', default_value)` to specify a default.",
     "context": "Missing key with [] raises KeyError. .get() returns None or a default safely.",
     "misconception_hint": "Expecting None or a default value instead of KeyError from direct key access."},

    {"id": 22, "topic": "Dicts",
     "question": "What does `{'a': 1, 'a': 2}['a']` return? Are duplicate keys allowed?",
     "correct_answer": "Returns `2`. Python allows duplicate keys in a dict literal — the last value silently overwrites previous ones. So `'a': 2` overwrites `'a': 1`.",
     "context": "Last key-value wins when there are duplicates in dict literal.",
     "misconception_hint": "Thinking duplicate keys raise an error or that both values are stored."},

    {"id": 23, "topic": "Dicts",
     "question": "What is the difference between `.keys()`, `.values()`, and `.items()`?",
     "correct_answer": "`.keys()` returns a view of all keys. `.values()` returns a view of all values. `.items()` returns a view of all `(key, value)` pairs as tuples. All return dict_view objects (not lists) that reflect changes to the dict.",
     "context": ".keys()=keys, .values()=values, .items()=(key,value) pairs.",
     "misconception_hint": "Confusing which method returns what, or thinking they return lists."},

    {"id": 24, "topic": "Dicts",
     "question": "How does dictionary ordering work in Python 3.7+?",
     "correct_answer": "Since Python 3.7, dictionaries maintain insertion order — keys are iterated in the order they were added. This is a language guarantee (not just CPython implementation detail).",
     "context": "Python 3.7+ dicts preserve insertion order.",
     "misconception_hint": "Thinking dicts are unordered (was true in Python 2 and Python 3 before 3.7)."},

    # ── Control Flow ──
    {"id": 25, "topic": "Control Flow",
     "question": "What does `range(5)` produce? Does it include 5?",
     "correct_answer": "Produces integers 0, 1, 2, 3, 4. It does NOT include 5 — `range(stop)` is exclusive of stop. To include 5, use `range(6)` or `range(1,6)` to get 1–5.",
     "context": "range(n) produces 0 to n-1. Stop is exclusive.",
     "misconception_hint": "Thinking range(n) starts from 1 or is inclusive of n."},

    {"id": 26, "topic": "Control Flow",
     "question": "What is the difference between `break` and `continue` in a loop?",
     "correct_answer": "`break` immediately exits the entire loop. `continue` skips the rest of the current iteration and jumps to the next iteration. Neither exits the function.",
     "context": "break exits loop, continue skips current iteration.",
     "misconception_hint": "Confusing break (exit loop) with continue (skip iteration)."},

    {"id": 27, "topic": "Control Flow",
     "question": "Explain what `else` on a `for` loop does in Python. Is it like `try/except` else?",
     "correct_answer": "A `for/else` block: the `else` runs if the loop completed normally without hitting `break`. It does NOT run if `break` was triggered. It's useful to detect if a search in a loop succeeded.",
     "context": "for/else: else runs when loop completes without break.",
     "misconception_hint": "Thinking for/else is like if/else (runs when loop body is empty or condition was False)."},

    {"id": 28, "topic": "Control Flow",
     "question": "What does the ternary expression `x if condition else y` do?",
     "correct_answer": "It returns `x` if `condition` is True, otherwise returns `y`. E.g., `'even' if n%2==0 else 'odd'` returns 'even' for even numbers. It's Python's one-line if-else.",
     "context": "Python ternary: value_if_true if condition else value_if_false.",
     "misconception_hint": "Not knowing Python's ternary syntax or confusing the order."},

    # ── Functions ──
    {"id": 29, "topic": "Functions",
     "question": "What does a Python function return if it has no explicit `return` statement?",
     "correct_answer": "`None`. All Python functions implicitly return `None` when execution reaches the end without a `return` statement.",
     "context": "No return statement → returns None.",
     "misconception_hint": "Thinking no return statement causes an error, or that the function returns 0 or False."},

    {"id": 30, "topic": "Functions",
     "question": "Why is using a mutable default argument like `def f(lst=[]):` dangerous?",
     "correct_answer": "The default list `[]` is created ONCE when the function is defined, not on each call. So if you mutate `lst` inside `f`, the changes persist across subsequent calls. This is a classic Python gotcha. Fix: use `def f(lst=None): if lst is None: lst = []`.",
     "context": "Mutable defaults are created once at definition time, shared across calls.",
     "misconception_hint": "Thinking default arguments are re-created fresh on every function call."},

    {"id": 31, "topic": "Functions",
     "question": "What is the difference between `*args` and `**kwargs`?",
     "correct_answer": "`*args` collects extra positional arguments into a tuple. `**kwargs` collects extra keyword arguments into a dict. E.g., `def f(*args, **kwargs)` can accept any combination of positional and keyword args.",
     "context": "*args = extra positional as tuple, **kwargs = extra keyword as dict.",
     "misconception_hint": "Confusing *args with **kwargs or thinking they're interchangeable."},

    {"id": 32, "topic": "Functions",
     "question": "What is a lambda function? What are its limitations compared to a regular function?",
     "correct_answer": "A lambda is an anonymous, single-expression function: `lambda x: x*2`. Limitations: can only contain a single expression (no statements, no assignments, no multiple lines). For complex logic, use `def`.",
     "context": "lambda = anonymous single-expression function. No statements allowed.",
     "misconception_hint": "Thinking lambdas can contain multiple statements or be multi-line."},

    {"id": 33, "topic": "Functions",
     "question": "Explain the concept of variable scope in Python (LEGB rule).",
     "correct_answer": "Python resolves variable names in this order: Local → Enclosing → Global → Built-in (LEGB). A variable in an inner function shadows outer ones. Use `global` to write to module-level vars, `nonlocal` to write to enclosing function vars.",
     "context": "LEGB: Local, Enclosing, Global, Built-in scope lookup order.",
     "misconception_hint": "Not understanding scope lookup or thinking inner functions can freely modify outer variables."},

    # ── OOP ──
    {"id": 34, "topic": "OOP",
     "question": "What is `self` in a Python class method? Is it a keyword?",
     "correct_answer": "`self` refers to the instance the method is called on. It's NOT a keyword — it's a convention. Python automatically passes the instance as the first argument. You could name it anything (like `this`), but `self` is the universal convention.",
     "context": "self is the instance, passed automatically as first arg. It's a convention, not keyword.",
     "misconception_hint": "Thinking self is a reserved Python keyword like in Java's `this`."},

    {"id": 35, "topic": "OOP",
     "question": "What is the difference between `__init__` and `__new__` in Python?",
     "correct_answer": "`__new__` creates the instance (allocates memory). `__init__` initializes the already-created instance with attributes. In practice, you almost always override `__init__` — `__new__` is only overridden for metaclasses or immutable types like int.",
     "context": "__new__ creates, __init__ initializes. Normally only override __init__.",
     "misconception_hint": "Thinking __init__ creates the object (it doesn't — __new__ does)."},

    {"id": 36, "topic": "OOP",
     "question": "What is the difference between `@staticmethod` and `@classmethod`?",
     "correct_answer": "`@staticmethod`: doesn't receive `self` or `cls` — just a regular function namespaced in the class. `@classmethod`: receives `cls` (the class itself) as first arg, useful for factory methods or accessing class-level state.",
     "context": "@staticmethod: no self/cls. @classmethod: receives cls as first arg.",
     "misconception_hint": "Confusing staticmethod (no class/instance access) with classmethod (receives cls)."},

    {"id": 37, "topic": "OOP",
     "question": "What is `__repr__` vs `__str__` in a class?",
     "correct_answer": "`__repr__` is the 'official' developer representation (shown in REPL, debuggers). `__str__` is the 'friendly' user-facing representation (used by `print()`). If only `__repr__` is defined, it's used for both. Guideline: `repr` should ideally be unambiguous/parseable.",
     "context": "__repr__ for developers/debugging, __str__ for users/print. repr used as fallback.",
     "misconception_hint": "Thinking __repr__ and __str__ are the same or interchangeable."},

    # ── Exceptions ──
    {"id": 38, "topic": "Exceptions",
     "question": "What is the difference between `try/except/else/finally`? When does `else` run?",
     "correct_answer": "`try`: code to attempt. `except`: runs if an exception occurs. `else`: runs ONLY if no exception occurred in `try`. `finally`: ALWAYS runs, exception or not. Use `finally` for cleanup (closing files etc.).",
     "context": "else: runs if no exception. finally: always runs.",
     "misconception_hint": "Confusing else (no exception) with finally (always runs)."},

    {"id": 39, "topic": "Exceptions",
     "question": "What is the difference between `raise` in Python vs `throw` in Java/JavaScript?",
     "correct_answer": "Python uses `raise` (not `throw`). `raise ValueError('msg')` raises an exception. You can also `raise` with no argument inside `except` to re-raise the current exception.",
     "context": "Python uses raise, not throw. raise alone inside except re-raises.",
     "misconception_hint": "Using throw (Java/JS syntax) instead of raise in Python."},

    {"id": 40, "topic": "Exceptions",
     "question": "What exception does Python raise for division by zero? What about `0/0` vs `0//0`?",
     "correct_answer": "Both `0/0` and `0//0` raise `ZeroDivisionError`. For floats, `0.0/0` also raises `ZeroDivisionError` (Python doesn't produce NaN like some languages).",
     "context": "ZeroDivisionError for any division by zero including integer and floor division.",
     "misconception_hint": "Expecting ArithmeticError (Java) or NaN (JavaScript) instead of ZeroDivisionError."},

    # ── Comprehensions ──
    {"id": 41, "topic": "Comprehensions",
     "question": "What does `[x**2 for x in range(4)]` produce? Trace through it.",
     "correct_answer": "[0, 1, 4, 9]. `range(4)` = 0,1,2,3. Squaring: 0²=0, 1²=1, 2²=4, 3²=9. Result: [0,1,4,9].",
     "context": "range(4) gives 0,1,2,3. List comprehension squares each.",
     "misconception_hint": "Off-by-one: thinking range(4) gives 1,2,3,4 and expecting [1,4,9,16]."},

    {"id": 42, "topic": "Comprehensions",
     "question": "What is a generator expression vs a list comprehension? When should you use each?",
     "correct_answer": "List comprehension `[x for x in ...]` creates a full list in memory. Generator expression `(x for x in ...)` is lazy — yields one value at a time, uses much less memory. Use generators for large data or when you only need to iterate once.",
     "context": "[] = eager list in memory. () = lazy generator on demand.",
     "misconception_hint": "Not knowing generator expressions exist or thinking (x for x) creates a tuple."},

    {"id": 43, "topic": "Comprehensions",
     "question": "Write a dict comprehension that maps numbers 1–5 to their squares.",
     "correct_answer": "`{n: n**2 for n in range(1, 6)}` → `{1: 1, 2: 4, 3: 9, 4: 16, 5: 25}`. Dict comprehensions use `{}` with `key: value` syntax.",
     "context": "{k:v for ...} syntax for dict comprehensions.",
     "misconception_hint": "Using [] for dict comprehension or wrong syntax for key:value."},

    # ── File I/O ──
    {"id": 44, "topic": "File I/O",
     "question": "What is the difference between file modes `'r'`, `'w'`, `'a'`, and `'x'`?",
     "correct_answer": "`'r'`: read (error if missing). `'w'`: write, creates or TRUNCATES. `'a'`: append (creates if missing). `'x'`: exclusive create (error if file exists). Add 'b' for binary: `'rb'`, `'wb'`.",
     "context": "r=read, w=write/truncate, a=append, x=exclusive create.",
     "misconception_hint": "Confusing modes — especially 'w' truncating vs 'a' appending."},

    {"id": 45, "topic": "File I/O",
     "question": "Why use `with open(...) as f:` instead of manually calling `f.close()`?",
     "correct_answer": "The `with` statement (context manager) automatically calls `f.close()` when the block exits — even if an exception occurs. Manual `f.close()` can be skipped if an exception happens before it. `with` is safer and more Pythonic.",
     "context": "with = context manager, guarantees close even on exception.",
     "misconception_hint": "Not knowing context managers or thinking manual close is equivalent."},

    # ── Modules ──
    {"id": 46, "topic": "Modules",
     "question": "What is the difference between `import math` and `from math import sqrt`?",
     "correct_answer": "`import math`: imports the module. Must use `math.sqrt(x)`. `from math import sqrt`: imports only `sqrt` into current namespace. Can use `sqrt(x)` directly. The latter can cause name collisions if you have a local `sqrt`.",
     "context": "import module: need module.func. from module import func: direct access.",
     "misconception_hint": "Not understanding namespace differences between import styles."},

    {"id": 47, "topic": "Modules",
     "question": "What does `if __name__ == '__main__':` do? Why is it useful?",
     "correct_answer": "When a Python file is run directly, `__name__` is `'__main__'`. When it's imported as a module, `__name__` is the module's filename. This guard ensures certain code (like running a demo) only executes when the file is run directly, not when imported.",
     "context": "__name__ == '__main__' only when script run directly, not when imported.",
     "misconception_hint": "Not understanding the import/run-directly distinction."},

    # ── Generators ──
    {"id": 48, "topic": "Generators",
     "question": "What does the `yield` keyword do? How does it differ from `return`?",
     "correct_answer": "`yield` makes a function a generator. When called, the function returns a generator object — it doesn't execute. Each `next()` call resumes until the next `yield`. Unlike `return`, the function's state (local variables) is preserved between calls.",
     "context": "yield pauses execution and saves state. return exits completely.",
     "misconception_hint": "Thinking yield is just like return but can be used multiple times."},

    {"id": 49, "topic": "Generators",
     "question": "What is the memory advantage of generators over lists? Give an example.",
     "correct_answer": "Generators produce values one at a time (lazy evaluation) so they don't store all values in memory. For example, `range(1_000_000_000)` takes ~48 bytes (a range object), while `list(range(1_000_000_000))` would take ~8GB of RAM.",
     "context": "Generators: lazy, O(1) memory. Lists: eager, O(n) memory.",
     "misconception_hint": "Not understanding lazy evaluation — thinking generator still stores all values."},

    # ── Decorators ──
    {"id": 50, "topic": "Decorators",
     "question": "What does a Python decorator do? Explain with a simple example.",
     "correct_answer": "A decorator wraps a function to extend or modify its behavior. `@my_decorator` before `def f():` is syntactic sugar for `f = my_decorator(f)`. Example: a timing decorator can measure how long any function takes without modifying its source.",
     "context": "@decorator is sugar for f = decorator(f). Wraps function behavior.",
     "misconception_hint": "Not knowing decorators are just higher-order functions using @syntax."},

    # ── Types ──
    {"id": 51, "topic": "Types",
     "question": "What does `isinstance(True, int)` return? Explain why.",
     "correct_answer": "`True`. In Python, `bool` is a subclass of `int`. `True == 1` and `False == 0`. So `True` is an instance of both `bool` and `int`. This means `True + True == 2` works.",
     "context": "bool is subclass of int. True=1, False=0.",
     "misconception_hint": "Not knowing bool inherits from int, expecting False."},

    {"id": 52, "topic": "Types",
     "question": "What is dynamic typing in Python? How does it differ from static typing in Java?",
     "correct_answer": "Python is dynamically typed — a variable's type is determined at runtime and can change. `x = 5` (int), then `x = 'hello'` (str) is valid. Java is statically typed — type is declared at compile time and can't change. Python type hints are optional annotations, not enforced at runtime.",
     "context": "Dynamic typing: type assigned at runtime. Type hints are not enforced.",
     "misconception_hint": "Thinking Python type hints enforce type checking like Java's static types."},

    # ── Built-ins ──
    {"id": 53, "topic": "Built-ins",
     "question": "What is the difference between `map()` and a list comprehension?",
     "correct_answer": "Both apply a function to each element. `map(func, iterable)` returns a lazy iterator (like a generator). A list comprehension `[func(x) for x in iterable]` returns an eager list. `map` is slightly faster for simple function calls; comprehensions are more readable and support filtering.",
     "context": "map() is lazy iterator. list comprehension is eager list.",
     "misconception_hint": "Thinking map() returns a list directly (it returns a map object in Python 3)."},

    {"id": 54, "topic": "Built-ins",
     "question": "What does `enumerate()` do? Give an example of why it's useful.",
     "correct_answer": "`enumerate(iterable)` returns `(index, value)` pairs. Instead of `for i in range(len(lst)): print(i, lst[i])`, you write `for i, val in enumerate(lst): print(i, val)`. Cleaner and more Pythonic.",
     "context": "enumerate gives (index, value) pairs. Avoids range(len()) pattern.",
     "misconception_hint": "Using range(len(x)) pattern instead of enumerate, or not knowing enumerate exists."},

    {"id": 55, "topic": "Built-ins",
     "question": "Explain what `zip()` does with an example.",
     "correct_answer": "`zip([1,2,3], ['a','b','c'])` produces `(1,'a'), (2,'b'), (3,'c')`. It pairs elements from multiple iterables. If lengths differ, it stops at the shortest. Used for parallel iteration.",
     "context": "zip pairs elements from multiple iterables into tuples.",
     "misconception_hint": "Thinking zip concatenates lists or that it handles unequal lengths by filling with None (that's zip_longest)."},

    {"id": 56, "topic": "Built-ins",
     "question": "What does `filter(lambda x: x > 2, [1,2,3,4])` return?",
     "correct_answer": "Returns a filter object (lazy iterator) yielding `3, 4`. `filter(func, iterable)` keeps elements where `func(element)` is True. Convert to list with `list(filter(...))` to get `[3, 4]`.",
     "context": "filter returns lazy iterator of elements where func is True.",
     "misconception_hint": "Thinking filter returns a list or keeps elements where func is False."},

    # ── Memory & References ──
    {"id": 57, "topic": "Memory",
     "question": "What is the difference between `is` and `==` in Python?",
     "correct_answer": "`==` checks value equality (do they have the same value?). `is` checks identity (do they point to the same object in memory?). `[1,2] == [1,2]` is True, but `[1,2] is [1,2]` is False — two different list objects. Never use `is` to compare values.",
     "context": "== checks value. is checks identity (same object in memory).",
     "misconception_hint": "Using 'is' to compare values like strings or numbers (works by accident for small ints due to caching)."},

    {"id": 58, "topic": "Memory",
     "question": "What is the difference between shallow copy and deep copy?",
     "correct_answer": "Shallow copy (`list.copy()`, `list[:]`) creates a new container but nested objects are still shared. Deep copy (`copy.deepcopy()`) recursively copies all nested objects too. For `[[1,2],[3,4]]`, shallow copy shares the inner lists; deep copy creates independent inner lists.",
     "context": "Shallow: new container, shared nested. Deep: fully independent recursive copy.",
     "misconception_hint": "Thinking shallow copy fully isolates the copy — it doesn't for nested mutable objects."},

    # ── Scope ──
    {"id": 59, "topic": "Scope",
     "question": "What is a closure in Python? Give a practical example.",
     "correct_answer": "A closure is a function that 'remembers' variables from its enclosing scope even after that scope has finished. Example: `def make_counter(): count=0; def counter(): nonlocal count; count+=1; return count; return counter` — the inner `counter` closes over `count`.",
     "context": "Closure: inner function captures variables from outer function's scope.",
     "misconception_hint": "Not understanding closures or thinking inner function can't access outer variables after outer returns."},

    {"id": 60, "topic": "Scope",
     "question": "When do you need `global` vs `nonlocal` in Python?",
     "correct_answer": "`global x`: inside a function, lets you write to the module-level variable `x`. `nonlocal x`: inside a nested function, lets you write to the enclosing function's variable `x`. Without these keywords, assigning to `x` creates a new local variable.",
     "context": "global: module-level write. nonlocal: enclosing function write.",
     "misconception_hint": "Not knowing nonlocal exists or thinking you can write to outer scope variables without keyword."},

    # ── Recursion ──
    {"id": 61, "topic": "Recursion",
     "question": "What is the base case in recursion and why is it essential?",
     "correct_answer": "The base case is a condition where the function returns a result directly without making a recursive call. Without it, recursion never terminates, eventually hitting Python's recursion limit and raising `RecursionError`.",
     "context": "Base case prevents infinite recursion and RecursionError.",
     "misconception_hint": "Writing recursive functions without a base case or misplacing the base case condition."},

    {"id": 62, "topic": "Recursion",
     "question": "What error does Python raise for infinite recursion and why?",
     "correct_answer": "`RecursionError: maximum recursion depth exceeded`. Python has a default stack depth limit (~1000 frames). Use `sys.setrecursionlimit()` to change it, but deep recursion can cause memory issues. Consider iteration or memoization for deeply recursive problems.",
     "context": "RecursionError with ~1000 default limit. sys.setrecursionlimit can change it.",
     "misconception_hint": "Expecting StackOverflowError (Java/C++) or that Python has unlimited stack depth."},

    # ── Operators ──
    {"id": 63, "topic": "Operators",
     "question": "Explain Python's `not`, `and`, and `or` operators with short-circuit evaluation.",
     "correct_answer": "`not x` inverts boolean. `x and y`: returns `x` if falsy, else `y` (short-circuits — if x is False, y is never evaluated). `x or y`: returns `x` if truthy, else `y`. E.g., `None or 'default'` = `'default'`, `5 and 'yes'` = `'yes'`.",
     "context": "Short-circuit: and returns first falsy or last. or returns first truthy or last.",
     "misconception_hint": "Thinking and/or always return True/False instead of one of the operands."},

    {"id": 64, "topic": "Operators",
     "question": "What does `x = x or []` do and why is it a common Python idiom?",
     "correct_answer": "If `x` is falsy (None, 0, empty), assigns `[]` to `x`. If `x` is truthy, keeps `x`. It's equivalent to `x if x else []`. Used as a safe default: `def f(lst=None): lst = lst or []`.",
     "context": "x or y returns x if truthy, else y. Used for safe defaults.",
     "misconception_hint": "Not understanding short-circuit evaluation making this pattern work."},

    # ── Advanced ──
    {"id": 65, "topic": "Advanced",
     "question": "What is the GIL (Global Interpreter Lock) in CPython? How does it affect threading?",
     "correct_answer": "The GIL is a mutex in CPython that allows only ONE thread to execute Python bytecode at a time. This means Python threads can't achieve true CPU parallelism for CPU-bound tasks. For I/O-bound tasks, threads still work well (GIL is released during I/O). Use `multiprocessing` for CPU parallelism.",
     "context": "GIL limits one thread at a time in CPython. Affects CPU-bound, not I/O-bound.",
     "misconception_hint": "Thinking Python threads give CPU parallelism like Java/C++ threads."},

    {"id": 66, "topic": "Advanced",
     "question": "What is `*` (star) unpacking in Python? Give examples.",
     "correct_answer": "`a, *b, c = [1,2,3,4,5]` → `a=1, b=[2,3,4], c=5`. In function calls: `func(*my_list)` unpacks list as positional args. In list literals: `[*list1, *list2]` merges lists. Very versatile Python 3 feature.",
     "context": "* unpacks iterables in assignment, function calls, and literals.",
     "misconception_hint": "Not knowing Python's extended unpacking (*) syntax."},

    {"id": 67, "topic": "Advanced",
     "question": "Explain Python's `__dunder__` (double underscore) methods. Why are they called magic methods?",
     "correct_answer": "Dunder (double-under) methods like `__len__`, `__add__`, `__iter__` define how objects respond to Python operators and built-in functions. E.g., `__len__` makes `len(obj)` work, `__add__` enables `+`. They're called magic because Python calls them implicitly.",
     "context": "Dunder methods define Python operator/built-in behavior. Called implicitly by Python.",
     "misconception_hint": "Thinking dunder methods must be called directly (e.g., obj.__len__()) rather than through built-ins."},

    # ── Python 3 ──
    {"id": 68, "topic": "Python 3",
     "question": "What does `input()` return in Python 3? How is it different from Python 2?",
     "correct_answer": "In Python 3, `input()` ALWAYS returns a string. To get an integer: `int(input())`. In Python 2, `input()` evaluated the input as Python code (dangerous!) and `raw_input()` returned a string.",
     "context": "Python 3 input() always returns str. Must cast for numeric types.",
     "misconception_hint": "Assuming input() can auto-detect type or return int (Python 2 behavior)."},

    {"id": 69, "topic": "Python 3",
     "question": "What are f-strings and what makes them better than `.format()` or `%` formatting?",
     "correct_answer": "f-strings (PEP 498, Python 3.6+): `f'Hello {name}!'`. Advantages: faster, more readable, support expressions directly `f'{2+2}'`, can access attributes `f'{obj.name}'`, and support format specs `f'{val:.2f}'`.",
     "context": "f-strings: fast, readable, support expressions. f'...' prefix.",
     "misconception_hint": "Not knowing f-string syntax or thinking you need quotes inside the braces."},

    {"id": 70, "topic": "Python 3",
     "question": "What are type hints in Python? Are they enforced at runtime?",
     "correct_answer": "Type hints (PEP 484): `def f(x: int) -> str: ...`. They are NOT enforced at runtime — Python still allows wrong types without error. They're for documentation and static analysis tools (mypy, pyright, IDEs). Runtime enforcement requires libraries like `pydantic`.",
     "context": "Type hints are documentation only, not enforced at runtime.",
     "misconception_hint": "Thinking Python type hints enforce types at runtime like Java/TypeScript."},

    # ── Iterators ──
    {"id": 71, "topic": "Iterators",
     "question": "What is the difference between an iterable and an iterator in Python?",
     "correct_answer": "An **iterable** has `__iter__()` (lists, strings, dicts). An **iterator** has both `__iter__()` and `__next__()`. `iter(x)` converts an iterable to an iterator. Iterators are one-pass — once exhausted, they're done. Lists can be iterated multiple times.",
     "context": "Iterable: has __iter__. Iterator: has __iter__ + __next__. One-pass.",
     "misconception_hint": "Thinking iterables and iterators are the same thing."},

    {"id": 72, "topic": "Iterators",
     "question": "What happens when you call `next()` on an exhausted iterator?",
     "correct_answer": "Raises `StopIteration`. This is how Python's for loops know to stop — internally they catch `StopIteration`. You can provide a default: `next(iterator, default_value)` to avoid the exception.",
     "context": "StopIteration raised when iterator is exhausted. next(it, default) avoids exception.",
     "misconception_hint": "Expecting None or looping back to start when iterator is exhausted."},

    # ── String Methods ──
    {"id": 73, "topic": "Strings",
     "question": "What is the difference between `split()` and `split(' ')`?",
     "correct_answer": "`split()` (no arg) splits on any whitespace (spaces, tabs, newlines) and removes empty strings. `split(' ')` splits ONLY on single spaces and can produce empty strings for consecutive spaces. E.g., `'a  b'.split()` = `['a','b']` but `'a  b'.split(' ')` = `['a','','b']`.",
     "context": "split() handles all whitespace + collapses. split(' ') only single space.",
     "misconception_hint": "Thinking split() and split(' ') are identical."},

    {"id": 74, "topic": "Strings",
     "question": "How does string `join()` work? Why is `''.join(list)` faster than concatenation with `+`?",
     "correct_answer": "`'sep'.join(iterable)` concatenates strings with `sep` between them. `'+'.join(['a','b','c'])` = `'a+b+c'`. It's faster than `a + b + c` because Python strings are immutable — each `+` creates a new string object. `join()` does it in one pass.",
     "context": "join() is O(n). Repeated + concatenation is O(n²) due to immutability.",
     "misconception_hint": "Not knowing join() or thinking + concatenation is equally efficient."},

    {"id": 75, "topic": "Strings",
     "question": "What is string interning in Python? Why does `'hello' is 'hello'` return True but `a is b` (for two separately created strings) might not?",
     "correct_answer": "Python automatically 'interns' (reuses the same object for) string literals that look like identifiers. So two `'hello'` literals may share the same object. But `a = ''.join(['hel','lo'])` creates a new object. This is an implementation detail — always use `==` to compare string values, never `is`.",
     "context": "String interning: Python reuses some string objects. Always use == for value comparison.",
     "misconception_hint": "Using 'is' to compare strings and being confused by inconsistent results due to interning."},
]


def analyze_free_text_with_llm(provider: str, model: str, question_data: dict, student_answer: str, enhanced_mode: bool = True):
    """Wrapper that calls analyze_free_text_answer and returns structured result."""
    return analyze_free_text_answer(provider, model, question_data, student_answer, enhanced_mode)


def render_chatbot_tab(provider: str, model: str, enhanced_mode: bool):
    """Render the Python Misconception Chatbot tab — free-text answer + RAG diagnosis."""

    st.markdown("""
    <style>
    .cb-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid rgba(99,102,241,0.5);
        border-radius: 18px;
        padding: 24px 30px;
        margin-bottom: 22px;
    }
    .cb-title {
        font-size: 1.7rem;
        font-weight: 800;
        background: linear-gradient(90deg, #818CF8 0%, #C084FC 55%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .cb-sub { color: #94A3B8; font-size: 0.95rem; line-height: 1.5; }
    .topic-chip {
        display: inline-block;
        background: rgba(99,102,241,0.18);
        color: #A5B4FC;
        border: 1px solid rgba(99,102,241,0.4);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.75rem;
        font-weight: 700;
        margin: 2px 3px 2px 0;
        cursor: pointer;
    }
    .q-card {
        background: rgba(15,23,42,0.7);
        border: 1px solid rgba(99,102,241,0.3);
        border-left: 5px solid #818CF8;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 18px;
        line-height: 1.6;
    }
    .q-topic-badge {
        background: rgba(99,102,241,0.2);
        color: #A5B4FC;
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.73rem;
        font-weight: 700;
        margin-bottom: 10px;
        display: inline-block;
    }
    .q-text {
        font-size: 1.05rem;
        font-weight: 600;
        color: #E2E8F0;
        margin-top: 6px;
    }
    .q-context {
        font-size: 0.82rem;
        color: #64748B;
        margin-top: 8px;
        font-style: italic;
    }
    .result-correct {
        background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(5,150,105,0.04));
        border: 1px solid rgba(16,185,129,0.45);
        border-radius: 14px;
        padding: 18px 22px;
        margin: 14px 0;
    }
    .result-misconception {
        background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(185,28,28,0.04));
        border: 1px solid rgba(239,68,68,0.45);
        border-radius: 14px;
        padding: 18px 22px;
        margin: 14px 0;
    }
    .result-partial {
        background: linear-gradient(135deg, rgba(251,191,36,0.1), rgba(180,130,0,0.04));
        border: 1px solid rgba(251,191,36,0.4);
        border-radius: 14px;
        padding: 18px 22px;
        margin: 14px 0;
    }
    .misconception-label {
        background: rgba(251,191,36,0.1);
        border: 1px solid rgba(251,191,36,0.35);
        border-radius: 10px;
        padding: 10px 16px;
        margin: 12px 0;
        font-weight: 700;
        color: #FCD34D;
        font-size: 0.92rem;
    }
    .rag-pill {
        display: inline-block;
        background: rgba(168,85,247,0.15);
        border: 1px solid rgba(168,85,247,0.35);
        color: #C084FC;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .q-list-item {
        padding: 7px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        cursor: pointer;
        font-size: 0.88rem;
        color: #CBD5E1;
    }
    .hint-box {
        background: rgba(30,41,59,0.5);
        border: 1px dashed rgba(99,102,241,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 0.83rem;
        color: #64748B;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero header ──
    st.markdown("""
    <div class="cb-header">
        <div class="cb-title">🤖 Python Misconception Chatbot</div>
        <div class="cb-sub">
            Browse <strong>75 Python questions</strong> across 18 topics. Select any question,
            write your own answer in natural language, and the AI will tell you if your understanding
            is correct — or precisely diagnose which misconception you hold and explain it.
            <br><span class="rag-pill" style="margin-top:6px; display:inline-block;">🧠 Enhanced RAG + Chain-of-Thought Analysis</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Session state
    for key, default in [
        ("cb_selected_q_id", None),
        ("cb_last_answer", ""),
        ("cb_diagnosis", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Layout
    col_left, col_right = st.columns([1, 2], gap="large")

    with col_left:
        st.markdown("### 📚 Browse Questions")

        # Topic filter
        all_topics = sorted(set(q["topic"] for q in CHATBOT_QUESTIONS))
        selected_topic = st.selectbox(
            "Filter by Topic",
            options=["All Topics"] + all_topics,
            key="cb_topic_filter"
        )

        filtered_qs = CHATBOT_QUESTIONS if selected_topic == "All Topics" else [
            q for q in CHATBOT_QUESTIONS if q["topic"] == selected_topic
        ]

        st.caption(f"Showing **{len(filtered_qs)}** questions")

        # Question list as radio
        q_labels = [f"Q{q['id']}  {q['question'][:60]}..." for q in filtered_qs]

        # Find current index
        current_idx = 0
        if st.session_state.cb_selected_q_id:
            ids = [q["id"] for q in filtered_qs]
            if st.session_state.cb_selected_q_id in ids:
                current_idx = ids.index(st.session_state.cb_selected_q_id)

        selected_label = st.radio(
            "Select a question:",
            options=q_labels,
            index=current_idx,
            key="cb_q_radio"
        )
        selected_idx_in_filtered = q_labels.index(selected_label)
        selected_q = filtered_qs[selected_idx_in_filtered]

        # Reset diagnosis when question changes
        if st.session_state.cb_selected_q_id != selected_q["id"]:
            st.session_state.cb_selected_q_id = selected_q["id"]
            st.session_state.cb_last_answer = ""
            st.session_state.cb_diagnosis = None

    with col_right:
        q = selected_q

        # ── Question card ──
        st.markdown(f"""
        <div class="q-card">
            <span class="q-topic-badge">🏷️ {q['topic']}</span>
            <div class="q-text">Q{q['id']}. {q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Answer input ──
        st.markdown("#### ✍️ Your Answer")
        st.caption("Write your answer in plain English. Explain your reasoning — the AI analyses your conceptual understanding, not just keywords.")

        student_answer = st.text_area(
            "Type your answer here:",
            value=st.session_state.cb_last_answer,
            height=130,
            placeholder="e.g., 'range(5) gives 0,1,2,3,4 because...' or 'I think it returns None because...'",
            key=f"cb_answer_{q['id']}",
            label_visibility="collapsed"
        )

        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            submit_btn = st.button(
                "🔍 Analyse My Answer",
                type="primary",
                use_container_width=True,
                disabled=not student_answer.strip()
            )
        with col_btn2:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)

        if clear_btn:
            st.session_state.cb_last_answer = ""
            st.session_state.cb_diagnosis = None
            st.rerun()

        if submit_btn and student_answer.strip():
            st.session_state.cb_last_answer = student_answer
            diagnosis = analyze_free_text_with_llm(
                provider.lower(), model, q, student_answer, enhanced_mode
            )
            st.session_state.cb_diagnosis = diagnosis
            st.rerun()

        # ── Diagnosis result ──
        diagnosis = st.session_state.cb_diagnosis
        if diagnosis and st.session_state.cb_selected_q_id == q["id"]:

            desc = diagnosis.get("description", "").strip()
            explanation = diagnosis.get("explanation", "").strip()
            trace = diagnosis.get("trace", "").strip()
            verification = diagnosis.get("verification", "").strip()
            candidates = diagnosis.get("retrieved_candidates", [])

            is_correct = (
                not diagnosis.get("misconception_found", True)
                or desc.upper() == "NONE"
                or desc == ""
            )

            st.markdown("---")
            st.markdown("### 🧠 AI Diagnosis")

            if is_correct:
                # ── Correct ──
                st.markdown(f"""
                <div class="result-correct">
                    <h3 style="color:#34D399;margin:0 0 8px 0;">✅ Correct Understanding</h3>
                    <div style="color:#D1FAE5;font-size:0.95rem;">Your answer demonstrates the correct conceptual model for this Python topic.</div>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

                if explanation:
                    st.markdown("#### 📖 Reinforcement")
                    st.markdown(explanation)

            else:
                # ── Misconception detected ──
                st.markdown(f"""
                <div class="result-misconception">
                    <h3 style="color:#F87171;margin:0 0 6px 0;">⚠️ Misconception Detected</h3>
                    <div style="color:#FEE2E2;font-size:0.9rem;">Your answer reveals a common misunderstanding about this Python concept.</div>
                </div>
                """, unsafe_allow_html=True)

                if desc and desc.upper() != "NONE":
                    st.markdown(f"""
                    <div class="misconception-label">🧩 Misconception: {desc}</div>
                    """, unsafe_allow_html=True)

                if explanation:
                    st.markdown("#### 📖 Explanation & Correction")
                    st.markdown(explanation)

                if trace:
                    with st.expander("🔍 How Your Reasoning Led Here (Trace)", expanded=True):
                        st.markdown(trace)

                if verification:
                    with st.expander("🛡️ What Python Actually Does", expanded=True):
                        st.markdown(verification)

                if candidates:
                    with st.expander("📚 Related Misconceptions from Taxonomy Bank (RAG)"):
                        for cand in candidates:
                            meta = cand.get("meta_data", {})
                            constructs = meta.get("related_constructs", [])
                            tag = " · ".join([f"`{c}`" for c in constructs[:3]]) if constructs else ""
                            st.markdown(f"- **[ID {cand['id']}]** {cand['description']}  {tag}")

            # Show correct reference answer in expander
            with st.expander("📋 Reference Answer"):
                st.markdown(f"**{q['correct_answer']}**")

            if not diagnosis.get("parse_success"):
                with st.expander("⚙️ Raw LLM Response (Debug)"):
                    st.code(diagnosis.get("raw_response", ""), language=None)

        elif not diagnosis:
            st.markdown("""
            <div class="hint-box">
                💡 <strong>How to use:</strong> Write your understanding of the concept in your own words.
                Don't worry about being perfect — the AI will identify exactly what you got right or wrong
                and explain any misconceptions using the Python Misconception Taxonomy database.
            </div>
            """, unsafe_allow_html=True)



def render_taxonomy_tab():
    """Render the Misconception Bank Explorer."""
    st.markdown("### 📚 Standardized Python Misconception Taxonomy")
    st.markdown("Explore the 67 standardized programming misconceptions indexed by the MisconAI RAG engine.")
    
    bank_path = project_root / "dataset" / "misconception_bank.json"
    if not bank_path.exists():
        st.warning("Misconception bank file not found.")
        return
        
    import json
    with open(bank_path, "r", encoding="utf-8") as f:
        misconceptions = json.load(f)
        
    search = st.text_input("🔍 Search Misconceptions (by keyword, construct, or ID)", placeholder="e.g. range, slicing, tuple, recursion, assignment")
    
    filtered = []
    for m in misconceptions:
        desc = m.get("description", "").lower()
        constructs = " ".join(m.get("meta_data", {}).get("related_constructs", [])).lower()
        s_lower = search.lower().strip()
        if not s_lower or s_lower in desc or s_lower in constructs or s_lower == str(m.get("id")):
            filtered.append(m)
            
    st.caption(f"Showing **{len(filtered)}** of **{len(misconceptions)}** misconceptions in database.")
    
    for item in filtered:
        with st.expander(f"📌 [ID {item['id']}] {item['description']}"):
            constructs = item.get("meta_data", {}).get("related_constructs", [])
            if constructs:
                st.markdown("**Related Constructs:** " + " ".join([f"`{c}`" for c in constructs]))
            st.markdown(item.get("example", "No code example available."))


def main():
    st.set_page_config(
        page_title="MisconAI: Programming Misconception Studio",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_custom_css()
    
    # Hero Banner
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">⚡ MisconAI Studio</div>
        <div class="hero-subtitle">High-Precision Automated Discovery & Diagnosis of Programming Misconceptions in Student Code</div>
        <div>
            <span class="pill-badge pill-green">🚀 Enhanced Methodology (+14% Gain)</span>
            <span class="pill-badge pill-purple">🧠 AST & In-Context RAG Taxonomy</span>
            <span class="pill-badge">⚡ Groq LPU & Gemini Ultra-Fast Inference</span>
            <span class="pill-badge">👤 Created by NIKHIL KUMAR SAH</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Model configuration from sidebar
    st.sidebar.header("⚙️ Engine & Architecture")
    model_options = {
        "Groq": {
            "qwen/qwen3.8-27b": "Qwen 3.8 27B (Recommended)",
            "openai/gpt-oss-120b": "GPT OSS 120B",
            "openai/gpt-oss-20b": "GPT OSS 20B",
            "allam-2-7b": "Allam 2 7B",
        },
        "Gemini": {
            "gemini-flash-lite-latest": "Gemini Flash Lite (Fastest & 88.9% Precision)",
            "gemini-3.8-flash": "Gemini 3.8 Flash",
            "gemini-flash-latest": "Gemini Flash Latest",
        },
        "OpenAI": {
            "o3-mini": "o3-mini",
            "o1-mini": "o1-mini",
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
        }
    }
    
    provider = st.sidebar.selectbox("Provider", options=list(model_options.keys()), index=0)
    model = st.sidebar.selectbox("Model", options=list(model_options[provider].keys()), format_func=lambda x: model_options[provider][x], index=0)
    
    config = get_llm_config(provider.lower(), model)
    if config.get("reasoning"):
        st.sidebar.success("✅ Chain-of-Thought Reasoning Active")
    else:
        st.sidebar.info("ℹ️ Standard Inference Mode")
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Methodology Settings")
    analysis_mode = st.sidebar.radio(
        "Mining Methodology",
        options=["Enhanced (Trace + Verification + RAG)", "Standard (Basic Zero-Shot)"],
        index=0,
        help="Enhanced mode executes mental tracing, verification, and injects known candidates from the Misconception Bank for higher accuracy."
    )
    enhanced_mode = (analysis_mode.startswith("Enhanced"))
    
    st.sidebar.markdown("---")
    st.sidebar.caption("**Author:** NIKHIL KUMAR SAH")
    st.sidebar.caption("**Corpus:** MisconAI Benchmark Suite")
    
    # Top Tab Navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔬 Misconception Mining Lab",
        "🤖 Python Quiz Chatbot",
        "📈 Empirical Benchmark & Performance Matrix",
        "📚 Taxonomy Bank Explorer (67 Misconceptions)"
    ])
    
    with tab1:
        render_analyzer_tab(provider, model, enhanced_mode)
        
    with tab2:
        render_chatbot_tab(provider, model, enhanced_mode)
        
    with tab3:
        render_benchmark_tab()
        
    with tab4:
        render_taxonomy_tab()


if __name__ == "__main__":
    main()


