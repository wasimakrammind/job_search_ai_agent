"""
pipeline/rank.py — Step 3: Rank filtered jobs by weighted scoring.

Owner: LLM Engineer
Formula: composite = skill_match% × w1 + location_match% × w2 + recency% × w3
"""

import re, copy
from typing import List, Dict, Tuple

import pandas as pd

from config import DEFAULT_SKILLS
from logger import logger


# ─────────────────────────────────────────────────────────────────────────────
#  Recency Parser
# ─────────────────────────────────────────────────────────────────────────────
_RECENCY_MAP = {
    "just posted": 0, "today": 0, "1 day ago": 1, "2 days ago": 2,
    "3 days ago": 3, "4 days ago": 4, "5 days ago": 5, "6 days ago": 6,
    "1 week ago": 7, "7 days ago": 7, "8 days ago": 8, "9 days ago": 9,
    "10 days ago": 10, "12 days ago": 12, "15 days ago": 15,
    "2 weeks ago": 14, "3 weeks ago": 21, "1 month ago": 30, "30+ days ago": 45,
}

def _posted_to_days(posted: str) -> int:
    """Convert 'X days ago' string to integer days."""
    p = posted.lower().strip()
    if p in _RECENCY_MAP:
        return _RECENCY_MAP[p]
    m = re.search(r"(\d+)\s*day", p)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*week", p)
    if m:
        return int(m.group(1)) * 7
    m = re.search(r"(\d+)\s*month", p)
    if m:
        return int(m.group(1)) * 30
    return 30   # conservative default


# ─────────────────────────────────────────────────────────────────────────────
#  Scoring
# ─────────────────────────────────────────────────────────────────────────────
def _score_job(
    job: Dict,
    user_skills: List[str],
    pref_locations: List[str],
    w_skill: float, w_loc: float, w_recency: float,
) -> Dict:
    """Score a single job. Returns an augmented copy with score fields."""
    j = copy.deepcopy(job)

    # ── Skill match (0–100) ──────────────────────────────────────────────
    if user_skills:
        desc_lower = j["description"].lower()
        matched = [s for s in user_skills if s.lower() in desc_lower]
        skill_pct = len(matched) / len(user_skills) * 100
    else:
        matched = j["skills_mentioned"]
        skill_pct = min(len(matched) / max(len(DEFAULT_SKILLS), 1) * 100, 100)

    j["matched_skills"] = matched
    j["skill_score"] = round(skill_pct, 1)

    # ── Location match (hierarchical: city=100, same state=70, none=0) ───
    from pipeline.location import score_location
    if pref_locations:
        j["location_score"] = score_location(j["location"], pref_locations)
    else:
        j["location_score"] = 50.0   # neutral when no preference

    # ── Recency (0–100, newer = higher) ──────────────────────────────────
    days_old = _posted_to_days(j.get("posted", "30 days ago"))
    j["days_old"] = days_old
    j["recency_score"] = round(max(0, 100 - (days_old / 30) * 100), 1)

    # ── Composite ────────────────────────────────────────────────────────
    j["composite_score"] = round(
        j["skill_score"]    * w_skill +
        j["location_score"] * w_loc +
        j["recency_score"]  * w_recency,
        2,
    )
    return j


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────
def run_rank(
    jobs: List[Dict],
    user_skills_str: str = "",
    pref_location_str: str = "",
    w_skill: float = 0.50,
    w_loc: float = 0.30,
    w_recency: float = 0.20,
    top_n: int = 10,
) -> Tuple[List[Dict], pd.DataFrame]:
    """
    Rank jobs by weighted composite score. Returns (ranked_list, summary_df).
    """
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 3  ▸  RANK")
    logger.info("=" * 60)

    if not jobs:
        logger.warning("No jobs to rank.")
        return [], pd.DataFrame(columns=["Rank","Score","Skill%","Loc%","Recency%","Title","Company","Location","Posted","Salary","Top Skills"])

    # Parse user inputs
    user_skills = (
        [s.strip().lower() for s in user_skills_str.split(",") if s.strip()]
        if user_skills_str.strip() else []
    )
    pref_locs = (
        [s.strip().lower() for s in pref_location_str.split(",") if s.strip()]
        if pref_location_str.strip() else []
    )

    # Normalise weights
    wt = w_skill + w_loc + w_recency or 1.0
    ws, wl, wr = w_skill / wt, w_loc / wt, w_recency / wt

    logger.info(f"Skills: {user_skills or 'default set'}")
    logger.info(f"Preferred locations: {pref_locs or 'any'}")
    logger.info(f"Weights (norm): skill={ws:.2f}  loc={wl:.2f}  recency={wr:.2f}")

    # Score and sort
    scored = [_score_job(j, user_skills, pref_locs, ws, wl, wr) for j in jobs]
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    top = scored[:int(top_n)]

    # Build summary DataFrame
    rows = []
    for rank, j in enumerate(top, 1):
        rows.append({
            "Rank": rank,
            "Score": j["composite_score"],
            "Skill%": j["skill_score"],
            "Loc%": j["location_score"],
            "Recency%": j["recency_score"],
            "Title": j["title"],
            "Company": j["company"],
            "Location": j["location"],
            "Posted": j["posted"],
            "Salary": j["salary"],
            "Top Skills": ", ".join(j["matched_skills"][:6]),
        })
        logger.info(
            f"  #{rank}  {j['title']} @ {j['company']}  "
            f"score={j['composite_score']}  skill={j['skill_score']}  "
            f"loc={j['location_score']}  recency={j['recency_score']}"
        )

    logger.info(f"Ranking complete — top {len(top)} returned.")
    return top, pd.DataFrame(rows)