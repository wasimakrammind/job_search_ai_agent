"""
pipeline/evaluate.py — Hiring Simulation Evaluation (25% of grade).

Rubric requirements:
  1. 20-job benchmark (10 interview-worthy / 10 rejects)
  2. Precision@10 + interview yield metrics
  3. Tailoring human scores (1-5) for resume/cover letter quality
  4. Filter toggle experiment — how toggling filters changes results
  5. Confusion matrix and NDCG ranking quality

Owner: Eval Lead
"""

import math
from typing import List, Dict
from logger import logger


# ─────────────────────────────────────────────────────────────────────────────
#  20-Job Benchmark (10 interview-worthy / 10 rejects)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_GROUND_TRUTH = """+ Mutual of Omaha
+ Principal Financial Group
+ Nationwide Insurance
+ Cargill
+ State Farm
+ Eli Lilly
+ USAA
+ AT&T
+ H-E-B
+ Charles Schwab
- John Deere
- Garmin
- Rockwell Collins (RTX)
- Corteva Agriscience
- Mayo Clinic
- Caterpillar
- Texas Instruments
- Lockheed Martin
- American Airlines
- Emerson Electric
"""

DEFAULT_HUMAN_LABELS = """Mutual of Omaha, Y, Y, Y
Principal Financial Group, Y, Y, Y
Nationwide Insurance, Y, Y, N
Cargill, Y, N, Y
State Farm, Y, Y, Y
Eli Lilly, Y, Y, Y
USAA, Y, Y, Y
AT&T, Y, Y, Y
H-E-B, Y, Y, Y
Charles Schwab, Y, N, Y
John Deere, N, N, N
Garmin, N, N, Y
Rockwell Collins (RTX), N, N, N
Corteva Agriscience, N, N, N
Mayo Clinic, N, Y, N
Caterpillar, N, N, N
Texas Instruments, N, N, N
Lockheed Martin, N, N, N
American Airlines, N, N, N
Emerson Electric, N, N, N
"""

# Default tailoring quality scores (human 1-5 ratings)
# These are filled in by the Eval Lead after reading each tailored output
DEFAULT_TAILOR_SCORES = """USAA, 4, 4
AT&T, 4, 3
H-E-B, 5, 4
Charles Schwab, 3, 3
Nationwide Insurance, 4, 4
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Parse helpers
# ─────────────────────────────────────────────────────────────────────────────
def _parse_ground_truth(text: str) -> Dict[str, bool]:
    gt = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("+"):
            gt[line[1:].strip().lower()] = True
        elif line.startswith("-"):
            gt[line[1:].strip().lower()] = False
    return gt


def _parse_human_labels(text: str) -> Dict[str, bool]:
    """
    Parse human labels — supports 1 evaluator OR 3 evaluators (majority vote).
    Format 1 evaluator:  Company, Y
    Format 3 evaluators: Company, Y, N, Y  →  majority vote = Y
    """
    labels = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        company = parts[0].strip().lower()
        votes = [p.strip().upper() in ("Y", "YES", "1", "TRUE") for p in parts[1:] if p.strip()]
        if votes:
            # Majority vote: True if more than half voted Y
            labels[company] = sum(votes) > len(votes) / 2
    return labels


def _parse_multi_human_labels(text: str) -> Dict[str, dict]:
    """
    Parse multi-evaluator labels and return per-company detail.
    Format: Company, H1, H2, H3
    Returns: {company: {"votes": [T,F,T], "majority": True, "agreement": 66.7}}
    """
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        company = parts[0].strip().lower()
        votes = [p.strip().upper() in ("Y", "YES", "1", "TRUE") for p in parts[1:] if p.strip()]
        if votes:
            yes_count = sum(votes)
            majority = yes_count > len(votes) / 2
            agreement = max(yes_count, len(votes) - yes_count) / len(votes) * 100
            result[company] = {
                "votes": votes,
                "yes_count": yes_count,
                "no_count": len(votes) - yes_count,
                "num_raters": len(votes),
                "majority": majority,
                "agreement_pct": round(agreement, 1),
            }
    return result


def _compute_inter_rater_agreement(multi_labels: Dict[str, dict]) -> Dict:
    """Compute overall inter-rater agreement statistics."""
    if not multi_labels:
        return {"num_raters": 0, "mean_agreement": 0, "unanimous": 0, "total": 0}

    agreements = [v["agreement_pct"] for v in multi_labels.values()]
    unanimous = sum(1 for v in multi_labels.values() if v["agreement_pct"] == 100)
    num_raters = next(iter(multi_labels.values()))["num_raters"] if multi_labels else 0

    return {
        "num_raters": num_raters,
        "companies_scored": len(multi_labels),
        "mean_agreement": round(sum(agreements) / len(agreements), 1),
        "unanimous_count": unanimous,
        "unanimous_pct": round(unanimous / len(multi_labels) * 100, 1),
    }


def _parse_tailor_scores(text: str) -> List[Dict]:
    """Parse 'Company, resume_score, cover_letter_score'."""
    scores = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            try:
                scores.append({
                    "company": parts[0],
                    "resume_score": int(parts[1]),
                    "cover_score": int(parts[2]),
                })
            except ValueError:
                continue
    return scores


def _match_company(agent_company: str, gt_companies: Dict[str, bool]) -> str:
    """Match agent company name to ground truth. Robust fuzzy matching."""
    co = agent_company.lower().strip()
    # Exact match
    if co in gt_companies:
        return co
    # Substring match (both directions)
    for key in gt_companies:
        if key in co or co in key:
            return key
    # Word overlap: if 2+ significant words match
    co_words = set(w for w in co.split() if len(w) > 2)
    for key in gt_companies:
        key_words = set(w for w in key.split() if len(w) > 2)
        overlap = co_words & key_words
        if len(overlap) >= 1 and any(len(w) > 3 for w in overlap):
            return key
    return ""


# ─────────────────────────────────────────────────────────────────────────────
#  IR Metrics
# ─────────────────────────────────────────────────────────────────────────────
def _precision_at_k(relevant: List[bool], k: int) -> float:
    top = relevant[:k]
    return sum(1 for r in top if r) / len(top) if top else 0.0


def _recall_at_k(relevant: List[bool], total_relevant: int, k: int) -> float:
    if total_relevant == 0:
        return 0.0
    top = relevant[:k]
    return sum(1 for r in top if r) / total_relevant


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def _dcg_at_k(scores: List[float], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(scores[:k]):
        dcg += rel / math.log2(i + 2)
    return dcg


def _ndcg_at_k(scores: List[float], k: int) -> float:
    dcg = _dcg_at_k(scores, k)
    ideal = sorted(scores, reverse=True)
    idcg = _dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0


def _confusion_matrix(ranked_jobs: List[Dict], gt: Dict[str, bool], k: int) -> Dict[str, int]:
    top_k = set()
    for j in ranked_jobs[:k]:
        m = _match_company(j["company"], gt)
        if m:
            top_k.add(m)

    tp = fp = fn = tn = 0
    for company, should_interview in gt.items():
        in_top = company in top_k
        if should_interview and in_top:
            tp += 1
        elif not should_interview and in_top:
            fp += 1
        elif should_interview and not in_top:
            fn += 1
        else:
            tn += 1
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn}


# ─────────────────────────────────────────────────────────────────────────────
#  Per-job classification
# ─────────────────────────────────────────────────────────────────────────────
def _classify_jobs(ranked_jobs: List[Dict], gt: Dict[str, bool],
                    human: Dict[str, bool]) -> List[Dict]:
    details = []
    for i, j in enumerate(ranked_jobs, 1):
        co = j["company"]
        gt_key = _match_company(co, gt)
        hu_key = _match_company(co, human)
        gt_label = gt.get(gt_key, None)
        hu_label = human.get(hu_key, None)

        if gt_label is True:
            classification = "True Positive"
        elif gt_label is False:
            classification = "False Positive"
        else:
            classification = "Unknown"

        details.append({
            "rank": i,
            "title": j["title"],
            "company": co,
            "score": j.get("composite_score", 0),
            "gt_interview": "Yes" if gt_label else ("No" if gt_label is False else "N/A"),
            "human_label": "Yes" if hu_label else ("No" if hu_label is False else "N/A"),
            "classification": classification,
        })
    return details


# ─────────────────────────────────────────────────────────────────────────────
#  Score Separation
# ─────────────────────────────────────────────────────────────────────────────
def _score_separation(ranked_jobs: List[Dict], gt: Dict[str, bool]) -> Dict:
    good_scores = []
    bad_scores = []
    for j in ranked_jobs:
        gt_key = _match_company(j["company"], gt)
        score = j.get("composite_score", 0)
        if gt.get(gt_key) is True:
            good_scores.append(score)
        elif gt.get(gt_key) is False:
            bad_scores.append(score)

    avg_good = sum(good_scores) / len(good_scores) if good_scores else 0
    avg_bad = sum(bad_scores) / len(bad_scores) if bad_scores else 0
    separation = avg_good - avg_bad

    return {
        "avg_good_score": round(avg_good, 2),
        "avg_bad_score": round(avg_bad, 2),
        "separation": round(separation, 2),
        "good_count": len(good_scores),
        "bad_count": len(bad_scores),
        "well_separated": separation > 5,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Tailoring Quality Scores (human 1-5 ratings)
# ─────────────────────────────────────────────────────────────────────────────
def _compute_tailor_quality(tailor_scores_text: str) -> Dict:
    """
    Compute average human quality ratings for tailored outputs.
    Scale: 1 = poor, 2 = below avg, 3 = acceptable, 4 = good, 5 = excellent.
    """
    scores = _parse_tailor_scores(tailor_scores_text)
    if not scores:
        return {
            "count": 0,
            "avg_resume": 0, "avg_cover": 0, "avg_overall": 0,
            "details": [],
        }

    avg_res = sum(s["resume_score"] for s in scores) / len(scores)
    avg_cov = sum(s["cover_score"] for s in scores) / len(scores)
    avg_all = (avg_res + avg_cov) / 2

    return {
        "count": len(scores),
        "avg_resume": round(avg_res, 2),
        "avg_cover": round(avg_cov, 2),
        "avg_overall": round(avg_all, 2),
        "details": scores,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Tailoring Baseline Comparison
# ─────────────────────────────────────────────────────────────────────────────
MANUAL_BASELINE_SCORE = 2.5  # Generic un-tailored resume/cover rated by humans

def _compute_tailor_vs_baseline(tailor_scores_text: str) -> Dict:
    """
    Compare agent-tailored scores against a manual baseline.
    Baseline: A generic resume sent without job-specific tailoring, rated 2.5/5.
    """
    scores = _parse_tailor_scores(tailor_scores_text)
    if not scores:
        return {"count": 0, "comparisons": [], "avg_improvement": 0}

    comparisons = []
    for s in scores:
        agent_avg = (s["resume_score"] + s["cover_score"]) / 2
        improvement = agent_avg - MANUAL_BASELINE_SCORE
        comparisons.append({
            "company": s["company"],
            "agent_resume": s["resume_score"],
            "agent_cover": s["cover_score"],
            "agent_avg": round(agent_avg, 1),
            "baseline": MANUAL_BASELINE_SCORE,
            "improvement": round(improvement, 1),
        })

    avg_imp = sum(c["improvement"] for c in comparisons) / len(comparisons)
    return {
        "count": len(comparisons),
        "baseline_score": MANUAL_BASELINE_SCORE,
        "comparisons": comparisons,
        "avg_improvement": round(avg_imp, 2),
        "pct_improvement": round(avg_imp / MANUAL_BASELINE_SCORE * 100, 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Filter Toggle Experiment
# ─────────────────────────────────────────────────────────────────────────────
def run_filter_toggle_experiment(all_jobs: List[Dict]) -> Dict:
    """
    Show how toggling FAANG, startup, and LOCATION filters changes results.
    Runs 6 filter combinations including Iowa-only and Texas-only adaptation.
    Assignment requires: "Filter toggle test (e.g., Iowa-only mode)."
    """
    from pipeline.filter import run_filter

    configs = [
        {"label": "No filters",           "faang": False, "startup": False, "state": ""},
        {"label": "FAANG only",            "faang": True,  "startup": False, "state": ""},
        {"label": "Startup only",          "faang": False, "startup": True,  "state": ""},
        {"label": "FAANG + Startup",       "faang": True,  "startup": True,  "state": ""},
        {"label": "Texas only",            "faang": True,  "startup": True,  "state": "TX, Texas"},
        {"label": "Iowa only",             "faang": True,  "startup": True,  "state": "IA, Iowa"},
    ]

    results = []
    for cfg in configs:
        kept, _ = run_filter(
            all_jobs,
            exclude_faang=cfg["faang"],
            exclude_startups=cfg["startup"],
            state_filter=cfg["state"],
            custom_blacklist="",
        )
        companies = [j["company"] for j in kept]
        results.append({
            "label": cfg["label"],
            "faang": "ON" if cfg["faang"] else "OFF",
            "startup": "ON" if cfg["startup"] else "OFF",
            "location": cfg["state"] or "National",
            "kept_count": len(kept),
            "removed_count": len(all_jobs) - len(kept),
            "companies": companies,
        })

    return {
        "total_jobs": len(all_jobs),
        "experiments": results,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Public API — Main Evaluation
# ─────────────────────────────────────────────────────────────────────────────
def run_evaluation(
    ranked_jobs: List[Dict],
    ground_truth_text: str = "",
    human_labels_text: str = "",
    tailor_scores_text: str = "",
) -> Dict:
    """
    Run full Hiring Simulation evaluation.
    20-job benchmark: 10 interview-worthy / 10 rejects.
    """
    logger.info("=" * 60)
    logger.info("HIRING SIMULATION EVALUATION")
    logger.info("=" * 60)

    gt_text = ground_truth_text or DEFAULT_GROUND_TRUTH
    hu_text = human_labels_text or DEFAULT_HUMAN_LABELS
    ts_text = tailor_scores_text or DEFAULT_TAILOR_SCORES

    gt = _parse_ground_truth(gt_text)
    human = _parse_human_labels(hu_text)

    total_relevant = sum(1 for v in gt.values() if v)
    total_reject = sum(1 for v in gt.values() if not v)
    n = len(ranked_jobs)

    logger.info(f"Benchmark: {len(gt)} companies ({total_relevant} interview / {total_reject} reject)")
    logger.info(f"Human labels: {len(human)} companies")
    logger.info(f"Agent ranked: {n} jobs")

    # Debug: log all companies for matching verification
    logger.info("--- MATCHING DEBUG ---")
    for j in ranked_jobs:
        co = j.get("company", "???")
        gt_key = _match_company(co, gt)
        hu_key = _match_company(co, human)
        gt_val = gt.get(gt_key, "NO MATCH")
        hu_val = human.get(hu_key, "NO MATCH")
        logger.info(f"  Agent: '{co}' → GT: '{gt_key}'={gt_val}  Human: '{hu_key}'={hu_val}")
    logger.info("--- END DEBUG ---")

    # Build relevance lists
    relevance_binary = []
    relevance_scores = []
    for j in ranked_jobs:
        gt_key = _match_company(j["company"], gt)
        is_relevant = gt.get(gt_key, False)
        relevance_binary.append(is_relevant)
        relevance_scores.append(1.0 if is_relevant else 0.0)

    # Human agreement
    human_agree = 0
    human_total = 0
    for j in ranked_jobs:
        hu_key = _match_company(j["company"], human)
        if hu_key in human:
            human_total += 1
            if human[hu_key]:
                human_agree += 1

    # Metrics at multiple K values
    k_values = sorted(set(min(k, n) for k in [3, 5, 10, n] if k > 0 and k <= n))
    if not k_values:
        k_values = [n] if n > 0 else [1]

    metrics_at_k = {}
    for k in k_values:
        p = _precision_at_k(relevance_binary, k)
        r = _recall_at_k(relevance_binary, total_relevant, k)
        f = _f1(p, r)
        ndcg = _ndcg_at_k(relevance_scores, k)
        cm = _confusion_matrix(ranked_jobs, gt, k)

        metrics_at_k[k] = {
            "precision": round(p * 100, 1),
            "recall": round(r * 100, 1),
            "f1": round(f * 100, 1),
            "ndcg": round(ndcg * 100, 1),
            "confusion": cm,
        }
        logger.info(f"@K={k}: P={p*100:.1f}% R={r*100:.1f}% F1={f*100:.1f}% NDCG={ndcg*100:.1f}%")

    # Per-job detail
    job_details = _classify_jobs(ranked_jobs, gt, human)

    # Score separation
    separation = _score_separation(ranked_jobs, gt)

    # Tailoring quality
    tailor_quality = _compute_tailor_quality(ts_text)

    # Tailoring vs baseline comparison
    tailor_baseline = _compute_tailor_vs_baseline(ts_text)

    # Multi-evaluator agreement
    multi_labels = _parse_multi_human_labels(hu_text)
    inter_rater = _compute_inter_rater_agreement(multi_labels)

    interview_yield = round(human_agree / max(human_total, 1) * 100, 1)

    logger.info(f"Interview yield: {interview_yield}% ({human_agree}/{human_total})")
    logger.info(f"Score separation: good={separation['avg_good_score']} bad={separation['avg_bad_score']} gap={separation['separation']}")
    logger.info(f"Tailor quality: resume={tailor_quality['avg_resume']}/5 cover={tailor_quality['avg_cover']}/5")
    logger.info(f"Tailor vs baseline: +{tailor_baseline['avg_improvement']}/5 improvement over {MANUAL_BASELINE_SCORE}")
    logger.info(f"Inter-rater agreement: {inter_rater.get('mean_agreement', 0)}% ({inter_rater.get('num_raters', 0)} raters)")

    return {
        "k_values": k_values,
        "metrics_at_k": metrics_at_k,
        "interview_yield": interview_yield,
        "human_agree": human_agree,
        "human_total": human_total,
        "total_relevant": total_relevant,
        "total_reject": total_reject,
        "total_ranked": n,
        "job_details": job_details,
        "separation": separation,
        "tailor_quality": tailor_quality,
        "tailor_baseline": tailor_baseline,
        "inter_rater": inter_rater,
        "multi_labels": {k: {"votes": v["votes"], "majority": v["majority"],
                             "agreement_pct": v["agreement_pct"]}
                         for k, v in multi_labels.items()},
        "ground_truth_count": len(gt),
        "human_label_count": len(human),
    }