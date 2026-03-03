"""
pipeline/filter.py — Step 2: Filter out unwanted jobs.

Owner: Agent Architect
Filters: FAANG/Big-Tech blacklist, startup heuristic, location, custom list.
"""

from typing import List, Dict, Tuple

import pandas as pd

from config import FAANG_BLACKLIST, STARTUP_SIGNALS
from logger import logger


# ─────────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────────
def _is_faang(company: str) -> bool:
    return any(b in company.lower() for b in FAANG_BLACKLIST)


def _is_startup(job: Dict) -> bool:
    text = (job["company"] + " " + job.get("description", "")).lower()
    return any(kw in text for kw in STARTUP_SIGNALS)


def _in_custom_blacklist(company: str, blacklist_str: str) -> bool:
    if not blacklist_str.strip():
        return False
    bl = [b.strip().lower() for b in blacklist_str.split(",") if b.strip()]
    co = company.lower()
    return any(b in co for b in bl)


def _fails_location(job: Dict, state_filter: str) -> bool:
    """Check if job location doesn't match using hierarchical geo matching."""
    if not state_filter.strip():
        return False

    from pipeline.location import location_matches_filter
    terms = [s.strip() for s in state_filter.split(",") if s.strip()]

    for term in terms:
        if location_matches_filter(job["location"], term):
            return False  # job matches -> keep it

    return True  # nothing matched -> fail


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────
def run_filter(
    jobs: List[Dict],
    exclude_faang: bool = True,
    exclude_startups: bool = True,
    state_filter: str = "",
    custom_blacklist: str = "",
) -> Tuple[List[Dict], pd.DataFrame]:
    """
    Filter jobs and return (kept_list, summary_dataframe).
    """
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 2  >  FILTER")
    logger.info("=" * 60)

    if not jobs:
        logger.warning("No jobs to filter.")
        return [], pd.DataFrame(
            columns=["#", "Title", "Company", "Location", "Posted", "Salary", "Skills"]
        )

    # Parse custom blacklist
    logger.info(f"Filters: FAANG={exclude_faang}  Startups={exclude_startups}  "
                f"Location='{state_filter}'  Blacklist='{custom_blacklist}'")

    kept = []
    for j in jobs:
        co = j["company"]

        if exclude_faang and _is_faang(co):
            logger.info(f"  REJECTED (FAANG/BigTech): {j['title']} @ {co}")
            continue

        if exclude_startups and _is_startup(j):
            logger.info(f"  REJECTED (Startup): {j['title']} @ {co}")
            continue

        if _in_custom_blacklist(co, custom_blacklist):
            logger.info(f"  REJECTED (Custom BL): {j['title']} @ {co}")
            continue

        if _fails_location(j, state_filter):
            logger.info(f"  REJECTED (Location): {j['title']} @ {co} | {j['location']}")
            continue

        logger.info(f"  KEPT: {j['title']} @ {co}")
        kept.append(j)

    # Build summary DataFrame
    rows = [{
        "#": i, "Title": j["title"], "Company": j["company"],
        "Location": j["location"], "Posted": j["posted"],
        "Salary": j["salary"], "Skills": len(j["skills_mentioned"]),
    } for i, j in enumerate(kept, 1)]

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["#", "Title", "Company", "Location", "Posted", "Salary", "Skills"]
    )

    logger.info(f"Filter complete: {len(kept)}/{len(jobs)} kept.")
    return kept, df