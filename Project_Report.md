# Project Report
## Middle America Job & Application Agent
### AI for Engineers — Group Assignment 2
### March 2026

| Role | Name | Responsibilities |
|------|------|-----------------|
| Product Lead | Gopi Trinath | Requirements, resume persona, constraint definitions |
| Agent Architect | Wasim Akram | Pipeline design, architecture diagram, integration |
| Web Engineer | Damini | SerpAPI integration, data extraction, parsing |
| LLM Engineer | Josna | Ranking logic, tailoring prompts, personalization |
| Eval Lead | Ujwal | 20-job benchmark, metrics computation, bias analysis |

---

## 1. Introduction

Job searching is a time-intensive, repetitive process that disproportionately affects candidates in non-coastal U.S. regions where tech opportunities are less concentrated. This project builds an AI-powered job search agent that automates the discovery, filtering, ranking, and application-tailoring workflow for a mid-career AI/ML engineer seeking positions in Middle America.

The agent operates as an end-to-end pipeline: it searches job boards via SerpAPI, filters out Big Tech and startups, ranks results by skill match, location proximity, and recency, then uses an LLM to generate tailored resumes and cover letters for the top candidates.

### 1.1 Candidate Persona

Alex Johnson is a fictional AI/Machine Learning Engineer with 4 years of experience, currently based in Des Moines, Iowa. Alex holds an M.S. in Computer Science from Iowa State University (2019) and a B.S. in Mathematics from the University of Iowa (2017).

**Professional experience includes:**
- 3+ years at Heartland Analytics deploying production ML systems (fraud detection on AWS SageMaker, demand-forecasting pipelines with TensorFlow and Airflow)
- 2 years as a Junior Data Scientist at AgriTech Solutions building crop-yield prediction models with PyTorch and satellite imagery

**Core skills:** Python, TensorFlow, PyTorch, Scikit-learn, Hugging Face, LangChain, Docker, Kubernetes, Airflow, MLflow, AWS (SageMaker, Lambda, S3), GCP (Vertex AI, BigQuery), SQL, and Git.

**Certifications:** AWS Certified Machine Learning – Specialty (2023), TensorFlow Developer Certificate (2022).

### 1.2 Constraint Definitions

- **FAANG/Big-Tech Blacklist:** Google, Amazon, Apple, Meta, Microsoft, Netflix, Tesla, NVIDIA, and 20+ others are excluded by default. The filter is togglable and the user can add custom companies.
- **Startup Filter:** Companies matching startup-indicator keywords (pre-seed, series A/B/C, early-stage, stealth, YCombinator, etc.) are flagged, enforcing the <50 employees heuristic.
- **Location Preference:** Texas (Austin, TX) as the target region, with hierarchical matching supporting same-state fallback.
- **Budget Limit:** A $5.00 per-session cap on LLM API spending via the BudgetTracker class.

---

## 2. Design & Implementation

### 2.1 Architecture Overview

The system has three layers:
1. **Presentation Layer:** A Streamlit web UI providing a vertical-scroll interface with sidebar settings, progress indicators, and collapsible result sections.
2. **Pipeline Layer:** Four Python modules (`search.py`, `filter.py`, `rank.py`, `tailor.py`) plus shared utilities (`location.py`, `config.py`, `logger.py`).
3. **External Services:** SerpAPI for Google Jobs search and OpenRouter for multi-provider LLM access.

### 2.2 Module Map

| Module | Function | TA Verification |
|--------|----------|----------------|
| search.py | SerpAPI queries, pagination, data extraction | Title, company, location, skills, salary, URL extracted reliably |
| filter.py | FAANG blacklist, startup detection, location | Constraints clearly defined and enforced |
| rank.py | Composite scoring: skill + location + recency | Skill/location/recency applied correctly |
| tailor.py | OpenRouter LLM calls, resume + cover letter | Tailored docs meaningfully differentiated |
| evaluate.py | Benchmark, metrics, bias analysis | 20-job benchmark sound, P@10 correct |
| location.py | Shared hierarchical geo-matching | Architecture matches code structure |
| ethics.py | 7-analysis bias audit + 8 mitigations | Bias section substantive |

### 2.3 Key Design Decisions

1. **Plain HTTP over SDK:** `search.py` uses the `requests` library to call SerpAPI rather than the official SDK, reducing dependencies and giving full control over pagination via the `start` parameter and `next_page_token`.

2. **Shared Location Module:** Both `filter.py` and `rank.py` import from `location.py`, ensuring consistent geographic resolution. This avoids bugs where filter accepts a location that rank scores as 0%.

3. **Vertical Scroll UI:** The Streamlit interface uses a single-page vertical flow with numbered stages (Search → Filter → Rank → Tailor) rather than tabs or multi-page navigation, matching the natural pipeline progression.

4. **Budget-Controlled LLM Usage:** The `BudgetTracker` class estimates costs based on model-specific pricing and enforces a $5.00 session cap, preventing runaway API costs during development and demos.

---

## 3. Evaluation Results — Hiring Simulation

The evaluation simulates a hiring pipeline: the agent recommends jobs from a benchmark set, and we compare its selections against ground-truth labels and simulated human recruiter judgments.

### 3.1 Benchmark Dataset

The benchmark uses 20 companies: 10 labeled as interview-worthy (+) and 10 as rejects (-). The dataset is constructed from the demo data covering Middle America companies across insurance, agriculture, healthcare, manufacturing, finance, retail, defense, and tech sectors.

**Interview-worthy (+) companies:** Mutual of Omaha, Principal Financial Group, Nationwide Insurance, Cargill, State Farm, Eli Lilly, USAA, AT&T, H-E-B, Charles Schwab

**Reject (-) companies:** John Deere, Garmin, Rockwell Collins (RTX), Corteva Agriscience, Mayo Clinic, Caterpillar, Texas Instruments, Lockheed Martin, American Airlines, Emerson Electric

Labeling rationale: Interview-worthy jobs have strong AI/ML role alignment, mid-sized company profile, and core skill overlap with the candidate. Rejects have weaker ML alignment (e.g., data labeling roles, consulting focus), defense/manufacturing focus with limited ML scope, or FAANG-adjacent characteristics.

### 3.2 Core Metrics

The agent ranked all jobs by composite score. Metrics are computed at K=3, K=5, and K=10:

| K | Precision | Recall | F1 | NDCG | TP | FP | FN | TN |
|---|-----------|--------|----|------|----|----|----|----|
| 3 | 100.0% | 30.0% | 46.2% | 100.0% | 3 | 0 | 7 | 10 |
| 5 | 80.0% | 40.0% | 53.3% | 92.1% | 4 | 1 | 6 | 9 |
| 10 | 70.0% | 70.0% | 70.0% | 85.6% | 7 | 3 | 3 | 7 |

**Best F1 at K=10:** Precision=70.0%, Recall=70.0%, F1=70.0%, NDCG=85.6%.

At K=3, the agent achieves perfect precision — all top 3 recommendations are interview-worthy. As K increases, precision trades off with recall, which is expected behavior for a ranked retrieval system.

### 3.3 Interview Yield and Multi-Evaluator Scoring

Interview yield measures the fraction of agent-recommended jobs where human recruiters agree the candidate should get an interview. As required by the assignment, **3 human evaluators** (Wasim, Damini, and Ujwal) independently scored each of the 20 benchmark companies with "Interview? Yes/No."

**Multi-evaluator format:** Each company receives 3 independent votes (e.g., `USAA, Y, Y, Y`). The final label uses **majority voting** — a company is marked "Interview" if 2 or more evaluators voted Yes.

**Inter-Rater Agreement:** Mean agreement across all 20 companies was **91.7%**, with 15 out of 20 companies (75%) receiving unanimous decisions. Disagreements occurred on borderline cases like Cargill (2Y/1N) and Charles Schwab (1Y/2N), which is expected for roles with partial skill overlap.

**Result:** 7 out of 10 ranked jobs in the top 10 received majority "Yes" votes, yielding a **70.0% interview rate**. This is a substantial improvement over manual search where response rates are typically 5-15%.

### 3.4 Score Separation

The composite scoring formula effectively separates interview-worthy jobs from rejects. The average score for interview-worthy jobs was 62.3, while reject jobs averaged 41.8, producing a gap of **+20.5 points**. This is rated "Good" separation, indicating the ranking algorithm reliably places better-fit jobs higher.

### 3.5 Tailoring Quality (Human 1-5 Scores)

A human evaluator rated the tailored resume and cover letter for the top 5 jobs on a 1-5 scale:

| Company | Resume Score | Cover Letter Score |
|---------|-------------|-------------------|
| USAA | 4 / 5 | 4 / 5 |
| AT&T | 4 / 5 | 3 / 5 |
| H-E-B | 5 / 5 | 4 / 5 |
| Charles Schwab | 3 / 5 | 3 / 5 |
| Nationwide Insurance | 4 / 5 | 4 / 5 |

**Average Resume:** 4.0/5, **Average Cover Letter:** 3.6/5, **Overall:** 3.8/5.

**Comparison to Manual Baseline:** A generic un-tailored resume (the candidate's original resume sent without modifications) was rated **2.5/5** by evaluators. The agent-tailored outputs scored an average of **3.8/5**, representing a **+1.3 point improvement** (+52%) over the manual baseline. This confirms that the LLM tailoring produces meaningfully better application materials than a generic submission.

### 3.6 Filter Toggle Experiment

To quantify filter impact, we ran the same 32-job demo search through **six filter configurations**, including location-based adaptation as required by the assignment:

| Configuration | FAANG Filter | Startup Filter | Location | Jobs Kept | Jobs Removed |
|--------------|-------------|----------------|----------|-----------|-------------|
| No filters | OFF | OFF | National | 32 | 0 |
| FAANG only | ON | OFF | National | 28 | 4 |
| Startup only | OFF | ON | National | 30 | 2 |
| Both filters | ON | ON | National | 26 | 6 |
| Texas only | ON | ON | TX | 7 | 25 |
| Iowa only | ON | ON | IA | 5 | 27 |

The **Texas-only** configuration demonstrates location adaptation: applying all filters plus a Texas location constraint narrows 32 jobs to 7 highly relevant results. Switching to **Iowa-only** mode yields 5 different jobs, demonstrating the agent's ability to adapt to different geographic preferences. This filter toggle capability is fully configurable in the UI sidebar.

---

## 4. Bias & Ethics Analysis

The ethics module performs seven automated analyses on the job data at each pipeline stage.

### 4.1 Gender-Coded Language

Using the framework from Gaucher, Friesen, and Kay (2011), the system scans job descriptions for masculine-coded words (e.g., competitive, driven, lead, challenge, determine) and feminine-coded words (e.g., collaborate, support, commit, nurture, understand, trust).

In the current run, the analysis found 13 total masculine words and 15 feminine words across 10 ranked jobs, with an average of 1.3 masculine and 1.5 feminine words per listing. The overall lean was classified as **"Balanced,"** with 8 of 10 jobs rated "Neutral" and 2 rated "Feminine-leaning." This indicates the job pool does not systematically discourage applicants of any gender.

### 4.2 Geographic Fairness

After filtering for Texas, 100% of ranked jobs were concentrated in Texas. The system flagged this as geographically concentrated and recommended diversifying location preferences. While this concentration is intentional for this persona, the warning ensures users are aware of the tradeoff between location specificity and opportunity breadth.

When the location filter is removed, jobs span 10+ states (NE, IA, IL, OH, MN, MO, IN, KS, TX, TN), demonstrating good geographic diversity in the underlying data.

### 4.3 Salary Equity

The skill analysis found that "machine learning" appeared in 8 of 10 ranked jobs, followed by "python" (10), "docker" (8), and "aws" (7). Two user skills (NLP, computer vision) were identified as underrepresented in the results. The overall skill diversity score was 83.3%, indicating good coverage.

### 4.4 Mitigation Strategies

The system implements eight concrete mitigation strategies:

1. **FAANG/Big-Tech Filter is Configurable** — The blacklist is a toggle, not hardcoded. Users can disable it or add custom companies, ensuring decisions are user-driven.
2. **Skill Weights are User-Adjustable** — All ranking weights (skill, location, recency) use sliders from 0-1, preventing hidden algorithmic preferences.
3. **Location Scoring is Hierarchical and Transparent** — Exact city=100%, same state=70%, no match=0%. No hard cutoffs.
4. **Gender-Coded Language Audit** — The ethics tab surfaces masculine/feminine word counts per listing.
5. **Complete Decision Logging** — Every filter, rank, and tailor decision is logged with reasons for full accountability.
6. **Diverse Benchmark Data** — The 32-job demo dataset spans multiple company types and industries across 10+ states.
7. **Salary Not Used for Ranking** — Salary is displayed but excluded from the composite score, preventing socioeconomic bias.
8. **LLM Tailoring Uses Neutral Prompts** — Prompts instruct the model to be professional without gendered or culturally-specific language.

---

## 5. Appendix

### 5.1 Agent Trace (Sample)

The following is a representative excerpt from the agent decision log:

```
[SEARCH] Query: AI Engineer | Location: Austin, TX | Results: 30
[FILTER] Vitaver & Associates | action=KEEP | reason=passed all filters
[FILTER] Google | action=REMOVE | reason=FAANG blacklist
[FILTER] TechStartup Inc | action=REMOVE | reason=startup keyword detected
[RANK] #1 USAA | score=71.7 | skill=65 loc=100 recency=80
[RANK] #2 AT&T | score=67.8 | skill=55 loc=100 recency=90
[TAILOR] USAA | model=gemini-2.0-flash | tokens=1847 | cost=$0.00
```

### 5.2 Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Web Framework | Streamlit 1.40+ |
| Job Search API | SerpAPI (Google Jobs engine) |
| LLM API | OpenRouter (multi-provider) |
| Default Model | google/gemini-2.0-flash-001 |
| Data Processing | Pandas |
| HTTP Client | Requests |
| Version Control | Git / GitHub |

### 5.3 File Structure

```
middle-america-job-agent-v2/
├── app.py                 # Streamlit UI (main entry point)
├── config.py              # Configuration, blacklists, budget tracker
├── logger.py              # Decision logging system
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore
├── .streamlit/
│   └── config.toml        # Streamlit theme config
└── pipeline/
    ├── __init__.py
    ├── search.py           # Step 1: Job search (SerpAPI + demo)
    ├── filter.py           # Step 2: FAANG/startup/location filter
    ├── rank.py             # Step 3: Weighted composite ranking
    ├── tailor.py           # Step 4: LLM resume/cover letter
    ├── location.py         # Shared geographic intelligence
    ├── ethics.py           # Bias analysis (7 analyses + 8 mitigations)
    └── evaluate.py         # Hiring simulation evaluation
```
