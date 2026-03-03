"""
pipeline/tailor.py — Step 4: Tailor resume & cover letter via LLM.

Owner: LLM Engineer
API: OpenRouter (supports Claude, GPT, Gemini, Llama, free models)
Budget: Every call is tracked via config.budget
"""

import textwrap
from typing import List, Dict

import requests

from config import (
    OPENROUTER_API_KEY, LLM_MODEL, SAMPLE_RESUME,
    budget, BudgetExceededError,
)
from logger import logger


# ─────────────────────────────────────────────────────────────────────────────
#  OpenRouter API Call (synchronous)
# ─────────────────────────────────────────────────────────────────────────────
def _call_openrouter(
    system_prompt: str,
    user_prompt: str,
    model: str = "",
    api_key: str = "",
) -> str:
    """
    Synchronous chat completion via OpenRouter.
    Tracks token usage and cost in budget.
    """
    model = model or LLM_MODEL
    key   = api_key or OPENROUTER_API_KEY

    # Pre-flight budget check
    budget.check()

    logger.info(f"OpenRouter call  model={model}")

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/middle-america-job-agent",
            "X-Title": "MiddleAmericaJobAgent",
        },
        json={
            "model": model,
            "max_tokens": 2048,
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"OpenRouter error: {data['error']}")

    text = data["choices"][0]["message"]["content"].strip()

    # Track cost
    usage = data.get("usage", {})
    in_tok  = usage.get("prompt_tokens", len(user_prompt) // 4)      # estimate
    out_tok = usage.get("completion_tokens", len(text) // 4)
    cost = budget.record(model, in_tok, out_tok, purpose=f"tailor")

    logger.info(f"Response: {len(text)} chars  tokens(in={in_tok} out={out_tok})  cost=${cost:.4f}")
    logger.info(f"Budget: ${budget.total_spent:.4f} / ${budget.limit:.2f}")

    return text


# ─────────────────────────────────────────────────────────────────────────────
#  Tailor One Job
# ─────────────────────────────────────────────────────────────────────────────
def _tailor_for_job(job: Dict, resume: str, model: str = "", api_key: str = "") -> Dict:
    """Generate tailored resume + cover letter for a single job."""

    sys_prompt = (
        "You are an expert career coach and resume writer. "
        "Tailor resumes and write cover letters for specific job postings. "
        "Be professional, concise, and reference job requirements directly."
    )

    user_prompt = textwrap.dedent(f"""\
=== TARGET JOB ===
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description'][:1500]}

=== CANDIDATE RESUME ===
{resume}

=== INSTRUCTIONS ===
1. TAILORED RESUME: Rewrite the resume emphasising skills matching THIS job.
   Keep same facts but reorder, adjust summary, highlight relevant skills. Plain text.
2. COVER LETTER: 250-350 words to {job['company']} hiring team.
   Reference specific job requirements. Plain text.

Return in EXACTLY this format:

---TAILORED RESUME---
<resume>

---COVER LETTER---
<letter>
""")

    raw = _call_openrouter(sys_prompt, user_prompt, model=model, api_key=api_key)

    # Parse sections
    resume_text, cover_text = raw, ""
    if "---COVER LETTER---" in raw:
        parts = raw.split("---COVER LETTER---")
        resume_text = parts[0].replace("---TAILORED RESUME---", "").strip()
        cover_text = parts[1].strip()
    elif "---TAILORED RESUME---" in raw:
        resume_text = raw.split("---TAILORED RESUME---")[-1].strip()

    return {
        "job_title": job["title"],
        "company": job["company"],
        "tailored_resume": resume_text,
        "cover_letter": cover_text,
        "composite_score": job.get("composite_score", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────
def run_tailor(
    ranked_jobs: List[Dict],
    resume: str = "",
    num_jobs: int = 3,
    model: str = "",
    api_key: str = "",
) -> List[Dict]:
    """
    Tailor resume + cover letter for top N ranked jobs.
    Returns list of tailored output dicts.
    """
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 4  ▸  TAILOR")
    logger.info("=" * 60)

    if not ranked_jobs:
        logger.warning("No ranked jobs to tailor for.")
        return []

    resume = resume.strip() or SAMPLE_RESUME
    n = min(int(num_jobs), len(ranked_jobs))

    logger.info(f"Tailoring for top {n} jobs  model={model or LLM_MODEL}")
    logger.info(f"Budget remaining: ${budget.remaining:.4f}")

    outputs: List[Dict] = []

    for i, job in enumerate(ranked_jobs[:n]):
        logger.info(f"Tailoring {i+1}/{n}: {job['title']} @ {job['company']}")
        try:
            budget.check()
            result = _tailor_for_job(job, resume, model=model, api_key=api_key)
            outputs.append(result)
        except BudgetExceededError as e:
            logger.error(f"Budget exceeded: {e}")
            outputs.append({
                "job_title": job["title"], "company": job["company"],
                "tailored_resume": f"[BUDGET EXCEEDED — switch to a free model]",
                "cover_letter": f"[BUDGET EXCEEDED — ${budget.total_spent:.2f} / ${budget.limit:.2f}]",
                "composite_score": job.get("composite_score", 0),
            })
            break
        except Exception as e:
            logger.error(f"Tailoring failed: {e}")
            outputs.append({
                "job_title": job["title"], "company": job["company"],
                "tailored_resume": f"[ERROR: {e}]",
                "cover_letter": f"[ERROR: {e}]",
                "composite_score": job.get("composite_score", 0),
            })

    logger.info(f"Tailoring complete. {len(outputs)} jobs processed.")
    logger.info(budget.summary())
    return outputs
