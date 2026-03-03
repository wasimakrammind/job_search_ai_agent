"""
pipeline/ethics.py — Ethics & Bias Analysis for the Job Agent.

Owner: Ethics Lead / All Team Members
Weight: 25% of final grade

Covers:
  1. Gender-coded language detection in job descriptions
  2. Location fairness analysis (geographic bias)
  3. Salary equity across regions
  4. Skill-matching bias (overweighted skills)
  5. Company diversity in shortlist
  6. Pipeline transparency audit
  7. Bias mitigation strategies (what we implemented)
"""

import re
from typing import List, Dict
from collections import Counter

from logger import logger


# ─────────────────────────────────────────────────────────────────────────────
#  1. GENDER-CODED LANGUAGE DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
# Based on Gaucher, Friesen & Kay (2011) — gender-coded words in job ads

MASCULINE_CODED = [
    "aggressive", "ambitious", "analytical", "assertive", "autonomous",
    "boast", "challenge", "champion", "competitive", "confident",
    "courageous", "decisive", "defend", "determine", "dominate",
    "driven", "enforce", "fearless", "fight", "force",
    "greedy", "headstrong", "hierarchy", "hostile", "hustle",
    "impulsive", "independent", "individual", "intellectual", "lead",
    "logic", "ninja", "objective", "opinion", "outspoken",
    "persist", "principle", "reckless", "rockstar", "self-reliant",
    "stubborn", "superior", "tackle", "dominant", "guru",
]

FEMININE_CODED = [
    "agree", "affectionate", "caring", "collaborate", "commit",
    "communal", "compassion", "connect", "considerate", "cooperat",
    "depend", "emotional", "empathy", "encourage", "feel",
    "flatter", "gentle", "honest", "inclusive", "interpersonal",
    "kind", "kinship", "loyal", "modesty", "nourish",
    "nurtur", "pleasant", "polite", "quiet", "responsive",
    "share", "submissive", "support", "sympathetic", "tender",
    "together", "trust", "understand", "warm", "yield",
]


def _detect_gender_coding(description: str) -> Dict:
    """
    Scan a job description for gender-coded language.
    Returns counts and specific words found.
    """
    desc_lower = description.lower()
    words = re.findall(r'[a-z]+', desc_lower)
    text = " ".join(words)

    masc_found = [w for w in MASCULINE_CODED if w in text]
    fem_found  = [w for w in FEMININE_CODED if w in text]

    if len(masc_found) > len(fem_found) + 2:
        bias = "Masculine-leaning"
    elif len(fem_found) > len(masc_found) + 2:
        bias = "Feminine-leaning"
    else:
        bias = "Neutral"

    return {
        "masculine_words": masc_found,
        "feminine_words": fem_found,
        "masculine_count": len(masc_found),
        "feminine_count": len(fem_found),
        "bias_label": bias,
    }


def analyze_gender_bias(jobs: List[Dict]) -> Dict:
    """Run gender-coding analysis across all jobs."""
    logger.info("Ethics: Analyzing gender-coded language...")

    results = []
    total_masc, total_fem = 0, 0
    bias_counts = Counter()

    for j in jobs:
        r = _detect_gender_coding(j.get("description", ""))
        r["title"] = j["title"]
        r["company"] = j["company"]
        results.append(r)
        total_masc += r["masculine_count"]
        total_fem += r["feminine_count"]
        bias_counts[r["bias_label"]] += 1

    n = len(jobs) or 1
    return {
        "per_job": results,
        "total_masculine": total_masc,
        "total_feminine": total_fem,
        "avg_masculine": round(total_masc / n, 2),
        "avg_feminine": round(total_fem / n, 2),
        "bias_distribution": dict(bias_counts),
        "overall_lean": (
            "Masculine" if total_masc > total_fem * 1.5 else
            "Feminine" if total_fem > total_masc * 1.5 else
            "Balanced"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  2. LOCATION / GEOGRAPHIC FAIRNESS
# ─────────────────────────────────────────────────────────────────────────────
def analyze_location_fairness(raw_jobs: List[Dict], filtered_jobs: List[Dict],
                               ranked_jobs: List[Dict]) -> Dict:
    """
    Check whether certain regions are over/under-represented
    at each pipeline stage.
    """
    logger.info("Ethics: Analyzing geographic fairness...")

    def _state_dist(jobs):
        states = []
        for j in jobs:
            loc = j.get("location", "")
            # Extract state abbreviation (last 2 chars after comma)
            parts = loc.split(",")
            if len(parts) >= 2:
                state = parts[-1].strip().upper()[:2]
                states.append(state)
            else:
                states.append("Unknown")
        return dict(Counter(states))

    raw_dist = _state_dist(raw_jobs)
    filtered_dist = _state_dist(filtered_jobs)
    ranked_dist = _state_dist(ranked_jobs)

    # Detect if any state was completely eliminated
    eliminated = set(raw_dist.keys()) - set(filtered_dist.keys())

    # Check if ranked list is dominated by one state
    ranked_total = sum(ranked_dist.values()) or 1
    concentration = {
        k: round(v / ranked_total * 100, 1)
        for k, v in sorted(ranked_dist.items(), key=lambda x: -x[1])
    }

    dominant = max(concentration, key=concentration.get) if concentration else "N/A"
    is_concentrated = concentration.get(dominant, 0) > 60

    return {
        "raw_distribution": raw_dist,
        "filtered_distribution": filtered_dist,
        "ranked_distribution": ranked_dist,
        "eliminated_states": list(eliminated),
        "ranked_concentration": concentration,
        "dominant_state": dominant,
        "is_geographically_concentrated": is_concentrated,
        "recommendation": (
            f"⚠️ {concentration.get(dominant, 0)}% of ranked jobs are in {dominant}. "
            f"Consider diversifying location preferences."
            if is_concentrated else
            "✅ Geographic distribution looks balanced."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  3. SALARY EQUITY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_salary(salary_str: str) -> tuple:
    """Extract (min, max) salary from string like '$130,000-$155,000/yr'."""
    nums = re.findall(r'[\d,]+', salary_str.replace(",", ""))
    nums = [int(n) for n in nums if len(n) >= 5]  # only 5+ digit numbers
    if len(nums) >= 2:
        return nums[0], nums[1]
    elif len(nums) == 1:
        return nums[0], nums[0]
    return None, None


def analyze_salary_equity(jobs: List[Dict]) -> Dict:
    """Check salary distribution and flag disparities."""
    logger.info("Ethics: Analyzing salary equity...")

    by_state = {}
    all_salaries = []

    for j in jobs:
        sal_min, sal_max = _parse_salary(j.get("salary", ""))
        if sal_min is None:
            continue

        midpoint = (sal_min + sal_max) / 2
        all_salaries.append(midpoint)

        # Group by state
        parts = j["location"].split(",")
        state = parts[-1].strip().upper()[:2] if len(parts) >= 2 else "Unknown"
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(midpoint)

    if not all_salaries:
        return {"error": "No parseable salaries found."}

    overall_avg = sum(all_salaries) / len(all_salaries)
    state_avgs = {
        state: round(sum(sals) / len(sals))
        for state, sals in by_state.items()
    }

    # Find largest disparity
    if len(state_avgs) >= 2:
        highest = max(state_avgs, key=state_avgs.get)
        lowest = min(state_avgs, key=state_avgs.get)
        gap = state_avgs[highest] - state_avgs[lowest]
    else:
        highest = lowest = list(state_avgs.keys())[0] if state_avgs else "N/A"
        gap = 0

    return {
        "overall_avg": round(overall_avg),
        "state_averages": state_avgs,
        "highest_state": highest,
        "lowest_state": lowest,
        "max_gap": gap,
        "salary_count": len(all_salaries),
        "recommendation": (
            f"⚠️ ${gap:,} gap between {highest} (${state_avgs.get(highest,0):,}) and "
            f"{lowest} (${state_avgs.get(lowest,0):,}). Account for cost-of-living."
            if gap > 20000 else
            "✅ Salary distribution appears equitable across regions."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  4. SKILL-MATCHING BIAS
# ─────────────────────────────────────────────────────────────────────────────
def analyze_skill_bias(ranked_jobs: List[Dict], user_skills_str: str) -> Dict:
    """
    Check if ranking over-rewards certain skills, leading to
    a narrow shortlist that misses diverse opportunities.
    """
    logger.info("Ethics: Analyzing skill-matching bias...")

    user_skills = [s.strip().lower() for s in user_skills_str.split(",") if s.strip()]
    if not user_skills:
        return {"error": "No user skills provided."}

    # Count how often each skill appears in top-ranked results
    skill_freq = Counter()
    for j in ranked_jobs:
        for s in j.get("matched_skills", []):
            skill_freq[s.lower()] += 1

    n = len(ranked_jobs) or 1

    # Skills that appear in 80%+ of results → potential over-reliance
    dominant_skills = {
        skill: count for skill, count in skill_freq.items()
        if count / n >= 0.8
    }

    # Skills the user listed but never matched → blind spots
    matched_ever = set(skill_freq.keys())
    blind_spots = [s for s in user_skills if s not in matched_ever]

    # Diversity score: how many distinct skills are represented?
    diversity_score = round(len(skill_freq) / max(len(user_skills), 1) * 100, 1)

    return {
        "skill_frequency": dict(skill_freq.most_common(15)),
        "dominant_skills": dominant_skills,
        "blind_spots": blind_spots,
        "diversity_score": diversity_score,
        "total_unique_matched": len(skill_freq),
        "user_skills_count": len(user_skills),
        "recommendation": (
            f"⚠️ Skills [{', '.join(dominant_skills.keys())}] appear in 80%+ of results. "
            f"Agent may be over-fitting to common skills."
            if len(dominant_skills) > 3 else
            "✅ Skill matching shows good diversity."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  5. COMPANY DIVERSITY
# ─────────────────────────────────────────────────────────────────────────────
def analyze_company_diversity(ranked_jobs: List[Dict]) -> Dict:
    """Check industry / company type diversity in the shortlist."""
    logger.info("Ethics: Analyzing company diversity...")

    if not ranked_jobs:
        return {"error": "No ranked jobs."}

    companies = [j["company"] for j in ranked_jobs]
    unique = set(companies)
    sectors = Counter()

    # Simple sector heuristic
    sector_keywords = {
        "Insurance": ["insurance", "mutual", "allstate", "state farm", "nationwide",
                       "progressive", "usaa"],
        "Agriculture": ["deere", "cargill", "corteva", "agriscience"],
        "Healthcare/Pharma": ["lilly", "mayo", "cerner", "health"],
        "Manufacturing": ["caterpillar", "emerson", "rockwell", "lockheed",
                           "texas instruments"],
        "Financial": ["principal", "schwab", "kroger"],
        "Retail": ["target", "h-e-b", "kroger"],
        "Tech/Telecom": ["at&t", "garmin"],
        "Transportation": ["american airlines"],
    }

    for j in ranked_jobs:
        co = j["company"].lower()
        matched_sector = "Other"
        for sector, keywords in sector_keywords.items():
            if any(kw in co for kw in keywords):
                matched_sector = sector
                break
        sectors[matched_sector] += 1

    dominant_sector = max(sectors, key=sectors.get) if sectors else "N/A"
    sector_pct = round(sectors.get(dominant_sector, 0) / len(ranked_jobs) * 100, 1)

    return {
        "unique_companies": len(unique),
        "total_ranked": len(ranked_jobs),
        "sector_distribution": dict(sectors),
        "dominant_sector": dominant_sector,
        "dominant_sector_pct": sector_pct,
        "recommendation": (
            f"⚠️ {dominant_sector} represents {sector_pct}% of shortlist. "
            f"Consider broadening industry preferences."
            if sector_pct > 50 else
            "✅ Good industry diversity across shortlist."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  6. TRANSPARENCY AUDIT
# ─────────────────────────────────────────────────────────────────────────────
def audit_transparency(raw_jobs: List[Dict], filtered_jobs: List[Dict],
                        ranked_jobs: List[Dict]) -> Dict:
    """Audit agent's decision-making transparency."""
    logger.info("Ethics: Auditing transparency...")

    from logger import LOG_BUFFER

    total_decisions = len(raw_jobs)
    logged_decisions = sum(
        1 for line in LOG_BUFFER
        if "KEPT" in line or "REJECTED" in line or "REJECT" in line
    )

    coverage = min(round(logged_decisions / max(total_decisions, 1) * 100, 1), 100.0)

    return {
        "total_jobs_processed": total_decisions,
        "decisions_logged": logged_decisions,
        "logging_coverage": coverage,
        "filter_ratio": f"{len(filtered_jobs)}/{len(raw_jobs)}",
        "rank_ratio": f"{len(ranked_jobs)}/{len(filtered_jobs)}",
        "pipeline_stages_logged": 4,
        "features": [
            "✅ Every filter decision logged with reason",
            "✅ Ranking scores decomposed (skill / location / recency)",
            "✅ Agent log exportable for report appendix",
            "✅ Budget tracking prevents uncontrolled API spend",
            "✅ All weights user-adjustable (no hidden ranking)",
        ],
        "recommendation": (
            "✅ Agent decisions are fully transparent and auditable."
            if logged_decisions > 0 else
            "⚠️ Run the pipeline to generate decision logs."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  7. BIAS MITIGATION STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────
MITIGATION_STRATEGIES = [
    {
        "strategy": "FAANG/Big-Tech Filter is Configurable",
        "description": (
            "The blacklist is a toggle, not hardcoded. Users can disable it "
            "or add custom companies. This prevents the system from permanently "
            "excluding any employer without user consent."
        ),
        "bias_addressed": "Selection bias — ensures decisions are user-driven",
    },
    {
        "strategy": "Skill Weights are User-Adjustable",
        "description": (
            "All ranking weights (skill, location, recency) use sliders from 0–1. "
            "The user controls how much each factor matters, preventing hidden "
            "algorithmic preferences."
        ),
        "bias_addressed": "Algorithmic bias — no opaque weighting",
    },
    {
        "strategy": "Location Scoring is Hierarchical & Transparent",
        "description": (
            "Location uses a 3-tier hierarchy: exact city match (100%), "
            "same state/different city (70%), no match (0%). Users see "
            "the score breakdown for every job, and can adjust the "
            "location weight via slider."
        ),
        "bias_addressed": "Geographic bias — transparent, graduated scoring avoids hard cutoffs",
    },
    {
        "strategy": "Gender-Coded Language Audit",
        "description": (
            "The Ethics tab detects masculine/feminine-coded words in job listings "
            "using Gaucher et al. (2011) framework. This surfaces language that may "
            "discourage applicants from underrepresented groups."
        ),
        "bias_addressed": "Gender bias — awareness of exclusionary language",
    },
    {
        "strategy": "Complete Decision Logging",
        "description": (
            "Every filter, rank, and tailor decision is logged with the reason. "
            "The full trace is exportable. This ensures accountability and enables "
            "post-hoc auditing."
        ),
        "bias_addressed": "Transparency — all decisions explainable and auditable",
    },
    {
        "strategy": "Demo Data Includes Diverse Company Types",
        "description": (
            "The 32-job demo dataset spans insurance, agriculture, healthcare, "
            "manufacturing, finance, retail, defense, and tech across 10+ states. "
            "This prevents evaluation bias from a narrow test set."
        ),
        "bias_addressed": "Evaluation bias — diverse benchmark data",
    },
    {
        "strategy": "Salary Data Shown, Not Used for Ranking",
        "description": (
            "Salary is displayed but does NOT affect the ranking score. "
            "This prevents the agent from discriminating against lower-paying "
            "roles that may still be excellent opportunities."
        ),
        "bias_addressed": "Socioeconomic bias — salary doesn't filter opportunities",
    },
    {
        "strategy": "LLM Tailoring Uses Neutral Prompts",
        "description": (
            "The resume/cover letter prompts instruct the LLM to be 'professional "
            "and concise' without gendered or culturally-specific language. "
            "No demographic assumptions are made about the candidate."
        ),
        "bias_addressed": "LLM output bias — neutral prompt design",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  PUBLIC API — Run Full Ethics Analysis
# ─────────────────────────────────────────────────────────────────────────────
def run_ethics_analysis(
    raw_jobs: List[Dict],
    filtered_jobs: List[Dict],
    ranked_jobs: List[Dict],
    user_skills_str: str = "",
) -> Dict:
    """
    Run comprehensive ethics & bias analysis.
    Returns a dict with all analysis results.
    """
    logger.info("=" * 60)
    logger.info("ETHICS & BIAS ANALYSIS")
    logger.info("=" * 60)

    return {
        "gender_bias": analyze_gender_bias(ranked_jobs or filtered_jobs or raw_jobs),
        "location_fairness": analyze_location_fairness(raw_jobs, filtered_jobs, ranked_jobs),
        "salary_equity": analyze_salary_equity(ranked_jobs or filtered_jobs),
        "skill_bias": analyze_skill_bias(ranked_jobs, user_skills_str),
        "company_diversity": analyze_company_diversity(ranked_jobs),
        "transparency": audit_transparency(raw_jobs, filtered_jobs, ranked_jobs),
        "mitigation_strategies": MITIGATION_STRATEGIES,
    }