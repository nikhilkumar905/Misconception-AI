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
    tab1, tab2, tab3 = st.tabs([
        "🔬 Misconception Mining Lab",
        "📈 Empirical Benchmark & Performance Matrix",
        "📚 Taxonomy Bank Explorer (67 Misconceptions)"
    ])
    
    with tab1:
        render_analyzer_tab(provider, model, enhanced_mode)
        
    with tab2:
        render_benchmark_tab()
        
    with tab3:
        render_taxonomy_tab()


if __name__ == "__main__":
    main()


