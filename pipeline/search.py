"""
pipeline/search.py — Step 1: Search job boards.

Owner: Web Engineer
Source: SerpAPI Google Jobs  OR  built-in demo dataset.
"""

import math
import requests
from typing import List, Dict, Tuple

import pandas as pd

from config import SERPAPI_KEY, DEFAULT_SKILLS
from logger import logger


# ─────────────────────────────────────────────────────────────────────────────
#  SerpAPI Search (live, using plain requests — no serpapi package needed)
# ─────────────────────────────────────────────────────────────────────────────
SERPAPI_URL = "https://serpapi.com/search.json"


def _serpapi_search(query: str, location: str, num: int, api_key: str) -> List[Dict]:
    """
    Call SerpAPI Google Jobs endpoint using plain HTTP requests.
    No serpapi package needed — just requests.
    """
    all_jobs: List[Dict] = []
    next_token = None
    pages = max(1, math.ceil(num / 10))

    for page in range(pages):
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "hl": "en",
            "api_key": api_key,
        }
        # First page: no token. Subsequent pages: use next_page_token
        if next_token:
            params["next_page_token"] = next_token

        logger.info(f"SerpAPI request: page={page+1} q='{query}' loc='{location}'"
                     + (f" token={next_token[:20]}..." if next_token else ""))

        try:
            resp = requests.get(SERPAPI_URL, params=params, timeout=30)
            logger.info(f"SerpAPI HTTP status: {resp.status_code}")

            if resp.status_code != 200:
                logger.error(f"SerpAPI HTTP error: {resp.status_code} — {resp.text[:500]}")
                break

            data = resp.json()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"SerpAPI connection error: {e}")
            break
        except requests.exceptions.Timeout:
            logger.error("SerpAPI timeout after 30s")
            break
        except Exception as e:
            logger.error(f"SerpAPI request error: {type(e).__name__}: {e}")
            break

        # Check for API-level errors
        if "error" in data:
            logger.error(f"SerpAPI API error: {data['error']}")
            break

        # Parse jobs
        jobs = data.get("jobs_results", [])
        logger.info(f"SerpAPI page {page+1}: {len(jobs)} jobs returned")

        if not jobs:
            logger.warning("No more SerpAPI results.")
            break

        for j in jobs:
            desc = j.get("description", "")[:2000]
            desc_lower = desc.lower()

            # Extract apply URL
            apply_url = "N/A"
            try:
                opts = j.get("apply_options", [])
                if opts and isinstance(opts, list) and len(opts) > 0:
                    apply_url = opts[0].get("link", "N/A")
                elif j.get("related_links"):
                    apply_url = j["related_links"][0].get("link", "N/A")
                elif j.get("share_link"):
                    apply_url = j["share_link"]
            except (IndexError, KeyError, TypeError):
                pass

            parsed = {
                "title":    j.get("title", "N/A"),
                "company":  j.get("company_name", "N/A"),
                "location": j.get("location", "N/A"),
                "description": desc,
                "posted":   j.get("detected_extensions", {}).get("posted_at", "N/A"),
                "schedule": j.get("detected_extensions", {}).get("schedule_type", "N/A"),
                "salary":   j.get("detected_extensions", {}).get("salary", "N/A"),
                "url": apply_url,
                "skills_mentioned": [s for s in DEFAULT_SKILLS if s in desc_lower],
                "source": "SerpAPI",
            }
            all_jobs.append(parsed)
            logger.info(f"  SCRAPED: {parsed['title']} @ {parsed['company']} | {parsed['location']}")

        # Get next page token for pagination
        next_token = None
        pagination = data.get("serpapi_pagination", {})
        if pagination:
            next_token = pagination.get("next_page_token")
        if not next_token:
            # Also check alternate location
            next_token = data.get("next_page_token")

        if len(all_jobs) >= num:
            break
        if not next_token:
            logger.info("No next_page_token — last page reached.")
            break

    logger.info(f"SerpAPI total: {len(all_jobs)} jobs scraped.")
    return all_jobs[:num]


# ─────────────────────────────────────────────────────────────────────────────
#  Full Demo Dataset
# ─────────────────────────────────────────────────────────────────────────────
_DEMO_DATA = [
    # --- Midwest / Mid-America ---
    ("AI Engineer","Mutual of Omaha","Omaha, NE","Build ML models insurance risk. Python, TensorFlow, Docker, AWS, SQL, data pipelines, model deployment, machine learning, deep learning.","3 days ago","$130,000-$155,000/yr",["python","tensorflow","docker","aws","sql","data pipelines","model deployment","machine learning","deep learning"]),
    ("ML Engineer","John Deere","Moline, IL","Computer vision autonomous tractors. PyTorch, Python, computer vision, docker, kubernetes, gcp, ci/cd, deep learning, model deployment.","5 days ago","$125,000-$150,000/yr",["python","pytorch","docker","kubernetes","gcp","ci/cd","computer vision","deep learning","model deployment"]),
    ("Senior ML Engineer","Principal Financial Group","Des Moines, IA","NLP financial docs. Python, pytorch, transformers, llm, nlp, aws, mlflow, docker, sql, machine learning.","1 day ago","$140,000-$170,000/yr",["python","pytorch","transformers","llm","nlp","aws","mlflow","docker","sql","machine learning"]),
    ("AI/ML Engineer","Cerner (Oracle Health)","Kansas City, MO","Healthcare AI. Python, tensorflow, aws, docker, kubernetes, sql, data pipelines, machine learning, deep learning.","7 days ago","$120,000-$145,000/yr",["python","tensorflow","aws","docker","kubernetes","sql","data pipelines","machine learning","deep learning"]),
    ("Data Scientist ML","Garmin","Olathe, KS","ML wearables. Python, pytorch, tensorflow, computer vision, docker, aws, machine learning, deep learning, data pipelines.","10 days ago","$115,000-$140,000/yr",["python","pytorch","tensorflow","computer vision","docker","aws","machine learning","deep learning","data pipelines"]),
    ("ML Platform Engineer","Nationwide Insurance","Columbus, OH","MLOps platform. Python, mlflow, docker, kubernetes, aws, ci/cd, sql, data pipelines, machine learning, model deployment.","2 days ago","$135,000-$160,000/yr",["python","mlflow","docker","kubernetes","aws","ci/cd","sql","data pipelines","machine learning","model deployment"]),
    ("NLP Engineer","Cargill","Minneapolis, MN","NLP supply-chain. Python, transformers, llm, nlp, pytorch, aws, docker, sql, machine learning.","4 days ago","$130,000-$155,000/yr",["python","transformers","llm","nlp","pytorch","aws","docker","sql","machine learning"]),
    ("AI Engineer II","State Farm","Bloomington, IL","Claims automation. Python, tensorflow, aws, docker, sql, data pipelines, machine learning, deep learning, model deployment.","6 days ago","$125,000-$150,000/yr",["python","tensorflow","aws","docker","sql","data pipelines","machine learning","deep learning","model deployment"]),
    ("CV Engineer","Rockwell Collins (RTX)","Cedar Rapids, IA","Vision avionics. Python, pytorch, computer vision, docker, gcp, deep learning, tensorflow, ci/cd.","12 days ago","$130,000-$160,000/yr",["python","pytorch","computer vision","docker","gcp","deep learning","tensorflow","ci/cd"]),
    ("ML Scientist","Corteva Agriscience","Indianapolis, IN","Crop genomics ML. Python, pytorch, tensorflow, aws, docker, sql, machine learning, deep learning, data pipelines, kubernetes.","8 days ago","$120,000-$150,000/yr",["python","pytorch","tensorflow","aws","docker","sql","machine learning","deep learning","data pipelines","kubernetes"]),
    ("AI Research Engineer","Mayo Clinic","Rochester, MN","Medical imaging. Python, pytorch, deep learning, computer vision, docker, aws, tensorflow.","15 days ago","$125,000-$155,000/yr",["python","pytorch","deep learning","computer vision","docker","aws","tensorflow"]),
    ("ML Engineer","Target","Minneapolis, MN","Recommendations. Python, tensorflow, pytorch, aws, docker, kubernetes, sql, machine learning, data pipelines, llm.","2 days ago","$140,000-$170,000/yr",["python","tensorflow","pytorch","aws","docker","kubernetes","sql","machine learning","data pipelines","llm"]),
    ("Data & ML Engineer","Caterpillar","Peoria, IL","IoT+ML heavy equip. Python, tensorflow, aws, docker, sql, data pipelines, machine learning, deep learning.","9 days ago","$115,000-$140,000/yr",["python","tensorflow","aws","docker","sql","data pipelines","machine learning","deep learning"]),
    ("AI/ML Engineer","Eli Lilly","Indianapolis, IN","Drug discovery ML. Python, pytorch, tensorflow, aws, docker, machine learning, deep learning, nlp, data pipelines.","4 days ago","$135,000-$165,000/yr",["python","pytorch","tensorflow","aws","docker","machine learning","deep learning","nlp","data pipelines"]),
    ("MLOps Engineer","Allstate","Chicago, IL","MLOps. Python, mlflow, docker, kubernetes, aws, ci/cd, machine learning, model deployment, data pipelines, sql.","6 days ago","$125,000-$150,000/yr",["python","mlflow","docker","kubernetes","aws","ci/cd","machine learning","model deployment","data pipelines","sql"]),
    ("AI Engineer","Emerson Electric","St. Louis, MO","Industrial AI. Python, tensorflow, docker, aws, sql, machine learning, data pipelines, model deployment.","5 days ago","$120,000-$145,000/yr",["python","tensorflow","docker","aws","sql","machine learning","data pipelines","model deployment"]),
    ("ML Engineer","Deere & Company","Urbandale, IA","Autonomous systems. Python, pytorch, computer vision, docker, kubernetes, gcp, deep learning, ci/cd, machine learning.","3 days ago","$130,000-$155,000/yr",["python","pytorch","computer vision","docker","kubernetes","gcp","deep learning","ci/cd","machine learning"]),
    ("ML Engineer","Progressive Insurance","Cleveland, OH","Telematics ML. Python, tensorflow, aws, docker, sql, machine learning, data pipelines, model deployment, deep learning.","7 days ago","$120,000-$145,000/yr",["python","tensorflow","aws","docker","sql","machine learning","data pipelines","model deployment","deep learning"]),
    ("NLP/LLM Engineer","Kroger","Cincinnati, OH","LLM retail. Python, transformers, llm, nlp, pytorch, aws, docker, sql, machine learning, model deployment.","3 days ago","$130,000-$155,000/yr",["python","transformers","llm","nlp","pytorch","aws","docker","sql","machine learning","model deployment"]),
    # --- Texas ---
    ("AI Engineer","USAA","San Antonio, TX","ML for insurance and banking. Python, tensorflow, pytorch, aws, docker, sql, machine learning, deep learning, data pipelines, model deployment.","2 days ago","$130,000-$160,000/yr",["python","tensorflow","pytorch","aws","docker","sql","machine learning","deep learning","data pipelines","model deployment"]),
    ("ML Engineer","Texas Instruments","Dallas, TX","ML for chip design optimization. Python, pytorch, tensorflow, docker, kubernetes, machine learning, deep learning, computer vision, ci/cd.","4 days ago","$125,000-$155,000/yr",["python","pytorch","tensorflow","docker","kubernetes","machine learning","deep learning","computer vision","ci/cd"]),
    ("AI/ML Engineer","H-E-B","San Antonio, TX","Supply chain ML and demand forecasting. Python, tensorflow, aws, docker, sql, data pipelines, machine learning, deep learning, mlflow.","3 days ago","$120,000-$150,000/yr",["python","tensorflow","aws","docker","sql","data pipelines","machine learning","deep learning","mlflow"]),
    ("Senior AI Engineer","American Airlines","Fort Worth, TX","Revenue optimization ML. Python, pytorch, aws, docker, sql, kubernetes, machine learning, deep learning, data pipelines, model deployment.","5 days ago","$140,000-$170,000/yr",["python","pytorch","aws","docker","sql","kubernetes","machine learning","deep learning","data pipelines","model deployment"]),
    ("ML Platform Engineer","AT&T","Dallas, TX","MLOps platform. Python, mlflow, docker, kubernetes, aws, gcp, ci/cd, sql, machine learning, model deployment.","1 day ago","$135,000-$165,000/yr",["python","mlflow","docker","kubernetes","aws","gcp","ci/cd","sql","machine learning","model deployment"]),
    ("Computer Vision Engineer","Lockheed Martin","Fort Worth, TX","Defense CV systems. Python, pytorch, computer vision, docker, deep learning, tensorflow, aws, ci/cd.","6 days ago","$135,000-$165,000/yr",["python","pytorch","computer vision","docker","deep learning","tensorflow","aws","ci/cd"]),
    ("NLP Engineer","Charles Schwab","Austin, TX","NLP for financial services. Python, transformers, llm, nlp, pytorch, aws, docker, sql, machine learning.","3 days ago","$130,000-$160,000/yr",["python","transformers","llm","nlp","pytorch","aws","docker","sql","machine learning"]),
    # --- FAANG / Big Tech (should be filtered out) ---
    ("AI Engineer","Google","Chicago, IL","Large-scale AI. Python, tensorflow, kubernetes, gcp, machine learning, deep learning, llm, transformers.","1 day ago","$180,000-$250,000/yr",["python","tensorflow","kubernetes","gcp","machine learning","deep learning","llm","transformers"]),
    ("AI Developer","Meta","Austin, TX","AI infra. Python, pytorch, llm, transformers, docker, kubernetes, machine learning, deep learning.","3 days ago","$190,000-$260,000/yr",["python","pytorch","llm","transformers","docker","kubernetes","machine learning","deep learning"]),
    ("Senior AI Engineer","Amazon","Nashville, TN","Alexa AI. Python, pytorch, llm, transformers, aws, deep learning.","2 days ago","$175,000-$240,000/yr",["python","pytorch","llm","transformers","aws","deep learning"]),
    ("AI Platform Eng","Microsoft","Redmond, WA","Azure AI. Python, pytorch, kubernetes, docker, machine learning, deep learning, llm, transformers.","1 day ago","$170,000-$230,000/yr",["python","pytorch","kubernetes","docker","machine learning","deep learning","llm","transformers"]),
    # --- Startups (should be filtered out) ---
    ("ML Intern","Stealth AI Startup","Remote","Seed stage stealth startup. Python, pytorch, machine learning.","1 day ago","N/A",["python","pytorch","machine learning"]),
    ("AI Engineer","Tiny AI Labs (YCombinator W24)","Remote","Series A. Python, pytorch, llm, transformers, machine learning.","1 day ago","N/A",["python","pytorch","llm","transformers","machine learning"]),
]


def _build_demo_jobs() -> List[Dict]:
    """Convert raw tuple data into job dicts."""
    jobs = []
    for i, (title, co, loc, desc, posted, sal, skills) in enumerate(_DEMO_DATA, 1):
        jobs.append({
            "title": title, "company": co, "location": loc,
            "description": desc, "posted": posted, "schedule": "Full-time",
            "salary": sal, "url": f"https://example.com/job{i}",
            "skills_mentioned": skills, "source": "Demo",
        })
    return jobs


def _filter_demo_by_location(jobs: List[Dict], location: str) -> List[Dict]:
    """
    If the user typed a specific location in the search box,
    filter demo data to only include matching jobs.
    Generic locations like 'United States' or blank return all jobs.
    Uses hierarchical matching: city → same state.
    """
    from pipeline.location import GENERIC_LOCATIONS, demo_location_matches

    loc = location.strip().lower()
    if loc in GENERIC_LOCATIONS:
        return jobs

    logger.info(f"Demo location filter: '{location}'")

    filtered = [j for j in jobs if demo_location_matches(j["location"], location)]

    logger.info(f"Demo location filter: {len(filtered)}/{len(jobs)} match '{location}'")

    if not filtered:
        logger.warning(f"No demo jobs match '{location}'. Returning all.")
        return jobs

    return filtered


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────
def run_search(query: str, location: str, num_results: int = 25,
               api_key: str = "") -> Tuple[List[Dict], pd.DataFrame]:
    """
    Execute job search. Returns (jobs_list, summary_dataframe).
    Falls back to demo data if no SerpAPI key or 0 results.
    """
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 1  >  SEARCH")
    logger.info("=" * 60)

    key = api_key.strip() or SERPAPI_KEY
    jobs = []
    source = "Demo"

    if key:
        logger.info(f"SerpAPI key found ({key[:8]}...). Attempting live search...")
        try:
            jobs = _serpapi_search(query, location, int(num_results), key)
            if jobs:
                source = "SerpAPI"
                logger.info(f"SerpAPI SUCCESS: {len(jobs)} live jobs!")
            else:
                logger.warning("SerpAPI returned 0 jobs. Check query/location/key.")
        except Exception as e:
            logger.error(f"SerpAPI FAILED: {type(e).__name__}: {e}")
    else:
        logger.info("No SerpAPI key. Using demo dataset.")

    # Fallback to demo data
    if not jobs:
        if key:
            logger.warning("SerpAPI produced no results. Falling back to demo data.")
        all_demo = _build_demo_jobs()
        jobs = _filter_demo_by_location(all_demo, location)
        source = "Demo"

    # Build summary DataFrame
    rows = [{
        "#": i, "Title": j["title"], "Company": j["company"],
        "Location": j["location"], "Posted": j["posted"],
        "Salary": j["salary"], "Skills": len(j["skills_mentioned"]),
    } for i, j in enumerate(jobs, 1)]

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["#", "Title", "Company", "Location", "Posted", "Salary", "Skills"]
    )

    logger.info(f"Search complete — {len(jobs)} jobs from {source}.")
    return jobs, df, source