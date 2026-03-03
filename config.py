"""
config.py — Central configuration for the Middle America Job Agent.

Owns: constants, blacklists, sample resume, model pricing, budget tracker.
Role: Product Lead defines these; everyone imports from here.
"""

import os
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

SERPAPI_KEY       = os.getenv("SERPAPI_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL         = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001")
BUDGET_LIMIT       = float(os.getenv("BUDGET_LIMIT", "5.00"))


# ── FAANG / Big-Tech Blacklist ───────────────────────────────────────────────
# Assignment requires mid-sized "Middle America" companies only.
FAANG_BLACKLIST = {
    "google", "alphabet", "meta", "facebook", "amazon", "apple", "netflix",
    "microsoft", "nvidia", "tesla", "openai", "anthropic", "deepmind",
    "x corp", "twitter", "uber", "airbnb", "snap", "snapchat", "spotify",
    "palantir", "databricks", "snowflake", "stripe", "coinbase", "tiktok",
    "bytedance", "salesforce", "oracle", "ibm", "intel", "amd", "qualcomm",
}


# ── Startup Signals (heuristic for <50 employees) ───────────────────────────
STARTUP_SIGNALS = [
    "stealth", "seed stage", "pre-seed", "series a", "series b",
    "ycombinator", "y combinator", "techstars", "incubator", "accelerator",
    "founded 2023", "founded 2024", "founded 2025", "founded 2026",
]


# ── Default Skills (AI Engineer profile) ────────────────────────────────────
DEFAULT_SKILLS = [
    "python", "tensorflow", "pytorch", "mlflow", "docker",
    "aws", "gcp", "machine learning", "deep learning",
    "nlp", "computer vision", "sql", "kubernetes", "ci/cd",
    "data pipelines", "model deployment", "llm", "transformers",
]


# ── OpenRouter Model Menu ───────────────────────────────────────────────────
# Sorted by cost: free first, then budget, then premium.
OPENROUTER_MODELS = [
    # --- FREE TIER (best for staying under $5) ---
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-4-maverick:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen3-235b-a22b:free",
    # --- BUDGET (pennies per call) ---
    "google/gemini-2.0-flash-001",          # $0.10/$0.40 per 1M tok
    "openai/gpt-4o-mini",                   # $0.15/$0.60 per 1M tok
    "meta-llama/llama-3.3-70b-instruct",    # $0.30/$0.30 per 1M tok
    # --- PREMIUM (use sparingly) ---
    "google/gemini-2.5-pro-preview",        # $1.25/$10.00
    "anthropic/claude-sonnet-4",            # $3.00/$15.00
    "openai/gpt-4o",                        # $2.50/$10.00
]


# ── Model Pricing (USD per 1M tokens) ───────────────────────────────────────
# Used by BudgetTracker to estimate costs.
MODEL_PRICING = {
    # model_name: (input_per_1M, output_per_1M)
    "deepseek/deepseek-chat-v3-0324:free":            (0.0, 0.0),
    "meta-llama/llama-4-maverick:free":                (0.0, 0.0),
    "mistralai/mistral-small-3.1-24b-instruct:free":   (0.0, 0.0),
    "qwen/qwen3-235b-a22b:free":                       (0.0, 0.0),
    "google/gemini-2.0-flash-001":                     (0.10, 0.40),
    "openai/gpt-4o-mini":                              (0.15, 0.60),
    "meta-llama/llama-3.3-70b-instruct":               (0.30, 0.30),
    "google/gemini-2.5-pro-preview":                   (1.25, 10.00),
    "anthropic/claude-sonnet-4":                       (3.00, 15.00),
    "openai/gpt-4o":                                   (2.50, 10.00),
}


# ── Budget Tracker ───────────────────────────────────────────────────────────
class BudgetTracker:
    """
    Tracks estimated LLM spend across the session.
    Raises BudgetExceededError if the limit is hit.
    """

    def __init__(self, limit: float = BUDGET_LIMIT):
        self.limit = limit
        self.total_spent = 0.0
        self.call_log = []          # list of dicts

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.total_spent)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        prices = MODEL_PRICING.get(model, (0.50, 1.50))   # conservative default
        cost = (input_tokens / 1_000_000) * prices[0] + \
               (output_tokens / 1_000_000) * prices[1]
        return round(cost, 6)

    def record(self, model: str, input_tokens: int, output_tokens: int, purpose: str = ""):
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.total_spent += cost
        self.call_log.append({
            "model": model,
            "input_tok": input_tokens,
            "output_tok": output_tokens,
            "cost_usd": cost,
            "cumulative_usd": round(self.total_spent, 6),
            "purpose": purpose,
        })
        return cost

    def check(self):
        """Raise if budget exceeded."""
        if self.total_spent >= self.limit:
            raise BudgetExceededError(
                f"Budget exhausted: ${self.total_spent:.4f} / ${self.limit:.2f}. "
                f"Switch to a free model or increase BUDGET_LIMIT."
            )

    def summary(self) -> str:
        lines = [
            f"💰 Budget: ${self.total_spent:.4f} / ${self.limit:.2f}  "
            f"(${self.remaining:.4f} remaining)",
            f"   Calls: {len(self.call_log)}",
        ]
        for c in self.call_log:
            lines.append(
                f"   • {c['purpose'][:40]:<40s}  "
                f"{c['model']:<45s}  "
                f"in={c['input_tok']:>5d}  out={c['output_tok']:>5d}  "
                f"${c['cost_usd']:.4f}"
            )
        return "\n".join(lines)


class BudgetExceededError(Exception):
    pass


# Singleton — import this everywhere
budget = BudgetTracker()


# ── Sample Resume ────────────────────────────────────────────────────────────
SAMPLE_RESUME = """\
ALEX JOHNSON
AI / Machine Learning Engineer  •  Des Moines, IA
alex.johnson@email.com | (515) 555-0199 | linkedin.com/in/alexjohnson-ai

SUMMARY
AI Engineer with 4 years of experience designing and deploying production ML
systems. Skilled in Python, TensorFlow, PyTorch, MLflow, Docker, and cloud
platforms (AWS, GCP). Passionate about bringing AI solutions to real-world
business problems outside of Big Tech.

EXPERIENCE
Machine Learning Engineer — Heartland Analytics, Des Moines, IA
Jun 2021 – Present (3+ yrs)
• Built demand-forecasting pipeline serving 200+ retail clients (TensorFlow,
  Airflow, BigQuery). Reduced MAPE by 18%.
• Deployed real-time fraud-detection model on AWS SageMaker processing 50K
  events/sec with <50 ms p99 latency.
• Created MLflow experiment-tracking framework adopted by 4 teams.

Junior Data Scientist — AgriTech Solutions, Ames, IA
Jul 2019 – May 2021 (2 yrs)
• Developed crop-yield prediction models using satellite imagery (PyTorch,
  OpenCV). Achieved 92% accuracy on hold-out set.
• Automated ETL pipeline reducing manual data prep from 6 hrs to 20 min.

EDUCATION
M.S. Computer Science — Iowa State University, 2019
B.S. Mathematics — University of Iowa, 2017

SKILLS
Languages: Python, SQL, Bash, Java
ML/AI: TensorFlow, PyTorch, Scikit-learn, Hugging Face, LangChain
MLOps: MLflow, Docker, Kubernetes, Airflow, GitHub Actions
Cloud: AWS (SageMaker, Lambda, S3), GCP (Vertex AI, BigQuery)
Other: Git, REST APIs, Agile/Scrum

CERTIFICATIONS
AWS Certified Machine Learning – Specialty (2023)
TensorFlow Developer Certificate (2022)
"""
