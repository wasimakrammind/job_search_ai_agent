"""
pipeline/location.py — Geographic intelligence for location matching.

Hierarchy:  USA → State → City
Scoring:    Exact city/state match → 100%
            Same state (different city) → 70%
            No match → 0%

Used by: search.py, filter.py, rank.py
"""

from typing import List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
#  State abbreviation ↔ full name
# ─────────────────────────────────────────────────────────────────────────────
STATE_ABBR_TO_NAME = {
    "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas",
    "ca": "california", "co": "colorado", "ct": "connecticut", "de": "delaware",
    "fl": "florida", "ga": "georgia", "hi": "hawaii", "id": "idaho",
    "il": "illinois", "in": "indiana", "ia": "iowa", "ks": "kansas",
    "ky": "kentucky", "la": "louisiana", "me": "maine", "md": "maryland",
    "ma": "massachusetts", "mi": "michigan", "mn": "minnesota", "ms": "mississippi",
    "mo": "missouri", "mt": "montana", "ne": "nebraska", "nv": "nevada",
    "nh": "new hampshire", "nj": "new jersey", "nm": "new mexico", "ny": "new york",
    "nc": "north carolina", "nd": "north dakota", "oh": "ohio", "ok": "oklahoma",
    "or": "oregon", "pa": "pennsylvania", "ri": "rhode island", "sc": "south carolina",
    "sd": "south dakota", "tn": "tennessee", "tx": "texas", "ut": "utah",
    "vt": "vermont", "va": "virginia", "wa": "washington", "wv": "west virginia",
    "wi": "wisconsin", "wy": "wyoming", "dc": "district of columbia",
}
STATE_NAME_TO_ABBR = {v: k for k, v in STATE_ABBR_TO_NAME.items()}

# ─────────────────────────────────────────────────────────────────────────────
#  City → State mapping (cities in our demo data + common US cities)
# ─────────────────────────────────────────────────────────────────────────────
CITY_TO_STATE = {
    # Texas
    "dallas": "tx", "fort worth": "tx", "austin": "tx", "houston": "tx",
    "san antonio": "tx", "el paso": "tx", "plano": "tx", "arlington": "tx",
    "irving": "tx", "frisco": "tx", "round rock": "tx",
    # Iowa
    "des moines": "ia", "cedar rapids": "ia", "urbandale": "ia", "ames": "ia",
    # Illinois
    "chicago": "il", "moline": "il", "bloomington": "il", "peoria": "il",
    "naperville": "il", "springfield": "il",
    # Ohio
    "columbus": "oh", "cleveland": "oh", "cincinnati": "oh", "dayton": "oh",
    "akron": "oh",
    # Minnesota
    "minneapolis": "mn", "rochester": "mn", "st paul": "mn",
    # Missouri
    "kansas city": "mo", "st. louis": "mo", "st louis": "mo",
    # Indiana
    "indianapolis": "in",
    # Kansas
    "olathe": "ks", "wichita": "ks", "overland park": "ks",
    # Nebraska
    "omaha": "ne", "lincoln": "ne",
    # Tennessee
    "nashville": "tn", "memphis": "tn", "knoxville": "tn",
    # California
    "san francisco": "ca", "los angeles": "ca", "san jose": "ca",
    "san diego": "ca", "palo alto": "ca", "mountain view": "ca",
    "sunnyvale": "ca", "cupertino": "ca", "menlo park": "ca",
    # Washington
    "seattle": "wa", "redmond": "wa", "bellevue": "wa",
    # New York
    "new york": "ny", "new york city": "ny", "brooklyn": "ny",
    # Others
    "atlanta": "ga", "denver": "co", "boston": "ma", "miami": "fl",
    "detroit": "mi", "milwaukee": "wi", "pittsburgh": "pa",
    "portland": "or", "phoenix": "az", "charlotte": "nc",
    "raleigh": "nc", "salt lake city": "ut",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Parse a job location string → (city, state_abbr)
# ─────────────────────────────────────────────────────────────────────────────
def parse_job_location(location: str) -> Tuple[str, str]:
    """
    Parse "San Antonio, TX" → ("san antonio", "tx")
    Parse "Remote" → ("remote", "")
    """
    loc = location.strip().lower()
    parts = [p.strip() for p in loc.split(",")]

    if len(parts) >= 2:
        city = parts[0]
        state = parts[-1].strip()[:2]  # "TX" → "tx"
        return city, state

    # Single word — could be a city or state
    return loc, ""


# ─────────────────────────────────────────────────────────────────────────────
#  Resolve user input → (state_abbr, is_city, city_name)
# ─────────────────────────────────────────────────────────────────────────────
def resolve_term(term: str) -> dict:
    """
    Figure out what a user-typed location term means.

    "TX"      → state abbreviation for Texas
    "Texas"   → state name for TX
    "Dallas"  → city in TX
    "Austin"  → city in TX
    """
    t = term.strip().lower()

    result = {
        "original": t,
        "is_state_abbr": False,
        "is_state_name": False,
        "is_city": False,
        "state_abbr": "",
        "state_name": "",
        "city": "",
    }

    # Check if it's a 2-letter state abbreviation
    if len(t) == 2 and t.isalpha() and t in STATE_ABBR_TO_NAME:
        result["is_state_abbr"] = True
        result["state_abbr"] = t
        result["state_name"] = STATE_ABBR_TO_NAME[t]
        return result

    # Check if it's a full state name
    if t in STATE_NAME_TO_ABBR:
        result["is_state_name"] = True
        result["state_abbr"] = STATE_NAME_TO_ABBR[t]
        result["state_name"] = t
        return result

    # Check if it's a known city
    if t in CITY_TO_STATE:
        result["is_city"] = True
        result["city"] = t
        result["state_abbr"] = CITY_TO_STATE[t]
        result["state_name"] = STATE_ABBR_TO_NAME.get(CITY_TO_STATE[t], "")
        return result

    # Unknown — treat as substring
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Does a job location MATCH a filter term? (boolean — for filter.py)
# ─────────────────────────────────────────────────────────────────────────────
def location_matches_filter(job_location: str, filter_term: str) -> bool:
    """
    Returns True if a job should be KEPT for this filter term.

    "Dallas"  keeps  "Dallas, TX"       (exact city)
    "Dallas"  keeps  "Fort Worth, TX"   (same state!)
    "Texas"   keeps  "Austin, TX"       (state match)
    "TX"      keeps  "San Antonio, TX"  (abbreviation match)
    "Dallas"  rejects "Moline, IL"      (different state)
    """
    job_city, job_state = parse_job_location(job_location)
    info = resolve_term(filter_term)

    if info["is_state_abbr"] or info["is_state_name"]:
        # User typed a state → match any job in that state
        return job_state == info["state_abbr"]

    if info["is_city"]:
        # User typed a city → match any job in the SAME STATE
        return job_state == info["state_abbr"]

    # Unknown term → substring fallback
    t = info["original"]
    loc = job_location.lower()
    if t in loc:
        return True
    # Also try state expansion
    if len(t) == 2 and t.isalpha() and loc.endswith(f", {t}"):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
#  Score a job location (0–100 — for rank.py)
# ─────────────────────────────────────────────────────────────────────────────
def score_location(job_location: str, pref_terms: List[str]) -> float:
    """
    Hierarchical location scoring:
      - Exact city match         → 100
      - Same state (diff city)   → 70
      - No match                 → 0

    Example with pref = "Dallas":
      "Dallas, TX"      → 100  (exact city)
      "Fort Worth, TX"  → 70   (same state Texas)
      "Austin, TX"      → 70   (same state Texas)
      "Moline, IL"      → 0    (different state)
    """
    if not pref_terms:
        return 50.0  # neutral when no preference

    job_city, job_state = parse_job_location(job_location)
    best_score = 0.0

    for term in pref_terms:
        info = resolve_term(term)

        if info["is_state_abbr"] or info["is_state_name"]:
            # User typed a state → all jobs in that state = 100
            if job_state == info["state_abbr"]:
                best_score = max(best_score, 100.0)

        elif info["is_city"]:
            # User typed a city
            if info["city"] == job_city:
                # Exact city match
                best_score = max(best_score, 100.0)
            elif info["state_abbr"] == job_state:
                # Same state, different city
                best_score = max(best_score, 70.0)

        else:
            # Unknown → substring fallback
            t = info["original"]
            loc = job_location.lower()
            if t in loc:
                best_score = max(best_score, 100.0)
            elif len(t) == 2 and t.isalpha() and loc.endswith(f", {t}"):
                best_score = max(best_score, 100.0)

    return best_score


# ─────────────────────────────────────────────────────────────────────────────
#  Filter demo jobs by search location (for search.py)
# ─────────────────────────────────────────────────────────────────────────────
GENERIC_LOCATIONS = {
    "", "united states", "usa", "us", "north america", "nationwide", "remote",
}

def demo_location_matches(job_location: str, search_location: str) -> bool:
    """
    Should this demo job be included when user searched this location?
    Uses the same hierarchy: city→state expansion.
    """
    terms = [t.strip() for t in search_location.lower().replace(",", " ").split() if t.strip()]

    for term in terms:
        if location_matches_filter(job_location, term):
            return True

    return False