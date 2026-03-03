# Middle America Job & Application Agent

AI-powered job search agent that autonomously finds AI Engineer jobs at mid-sized Middle America companies, filters out FAANG and startups, ranks results by skill/location/recency, and generates tailored resumes and cover letters using LLMs.

**Course:** AI for Engineers — Group Assignment 2
**Team:** Gopi Trinath (Product Lead), Wasim Akram (Agent Architect), Damini (Web Engineer), Josna (LLM Engineer), Ujwal (Eval Lead)

---

## How to Install and Run (Step by Step)

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Internet connection (for SerpAPI and OpenRouter, optional for demo mode)

### Step 1: Clone the repository
```bash
git clone https://github.com/<your-username>/middle-america-job-agent.git
cd middle-america-job-agent
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

This installs 4 packages:
- `streamlit` — Web UI framework
- `requests` — HTTP client for API calls
- `pandas` — Data handling
- `python-dotenv` — Environment variable loading

### Step 3: Run the application
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

### Step 4: Using the app

**Without API keys (Demo Mode):**
- Leave the SerpAPI key blank in the sidebar
- Click "Search Jobs" — the app loads 32 built-in demo jobs
- Filter, Rank, and Evaluate all work with demo data
- Tailoring (Step 4) requires an OpenRouter key

**With API keys (Live Mode):**
- Get a free SerpAPI key from https://serpapi.com (100 free searches)
- Get a free OpenRouter key from https://openrouter.ai/keys
- Enter both keys in the sidebar
- Search returns real-time Google Jobs results

---

## Architecture

The agent follows a four-stage sequential pipeline:

```
User Input → [1. Search] → [2. Filter] → [3. Rank] → [4. Tailor]
                 ↓              ↓             ↓            ↓
            30 raw jobs    9 kept jobs    Sorted by     Personalized
            from SerpAPI   (21 removed)   composite     resume + cover
                                          score         letter per job
```

**Scoring Formula:**
```
Composite = (Skill% × w1) + (Location% × w2) + (Recency% × w3)
```

**Location Hierarchy:**
- Exact city match = 100%
- Same state, different city = 70%
- No match = 0%

All weights (w1, w2, w3) are user-adjustable via sliders in the sidebar.

---

## Candidate Persona

The agent is built for **Alex Johnson**, a fictional AI/ML Engineer with 4 years of experience:
- **Education:** M.S. Computer Science, Iowa State University (2019); B.S. Mathematics, University of Iowa (2017)
- **Experience:** ML Engineer at Heartland Analytics (3+ years), Junior Data Scientist at AgriTech Solutions (2 years)
- **Skills:** Python, TensorFlow, PyTorch, Scikit-learn, Hugging Face, LangChain, Docker, Kubernetes, Airflow, MLflow, AWS (SageMaker, Lambda, S3), GCP (Vertex AI, BigQuery), SQL, Git
- **Certifications:** AWS Certified ML Specialty (2023), TensorFlow Developer Certificate (2022)
- **Target:** AI/ML Engineering roles in Middle America (Texas preferred)

---

## Constraint Definitions

| Constraint | Rule | Configurable? |
|-----------|------|--------------|
| FAANG Blacklist | Google, Amazon, Apple, Meta, Microsoft, Netflix, Tesla, NVIDIA excluded | Yes — toggle on/off in sidebar |
| Startup Filter | Keywords: pre-seed, series A/B/C, early-stage, stealth, venture-backed | Yes — toggle on/off |
| Min Employees | Heuristic: startup keywords imply <50 employees | Yes — via startup filter toggle |
| Location Preference | Austin, TX (hierarchical: city then state then region) | Yes — editable in sidebar |
| Budget Cap | $5.00 per session for LLM API calls | Enforced by BudgetTracker class |

---

## Project Structure

```
middle-america-job-agent/
├── app.py                     # Streamlit UI (main entry point)
├── config.py                  # Configuration, blacklists, default resume
├── logger.py                  # Decision logging + export for agent trace
├── requirements.txt           # 4 Python dependencies
├── README.md                  # This file
├── .env.example               # Template for API keys
├── .gitignore                 # Python/IDE exclusions
├── .streamlit/
│   └── config.toml            # Streamlit theme configuration
└── pipeline/
    ├── __init__.py             # Package init
    ├── search.py               # Step 1: SerpAPI Google Jobs + demo fallback
    ├── filter.py               # Step 2: FAANG/startup/location filtering
    ├── rank.py                 # Step 3: Weighted composite scoring
    ├── tailor.py               # Step 4: LLM resume + cover letter via OpenRouter
    ├── evaluate.py             # Hiring simulation (20-job benchmark, P/R/F1/NDCG)
    ├── ethics.py               # 7 bias analyses + 8 mitigation strategies
    └── location.py             # Shared geographic intelligence module
```

---

## Team Roles and Responsibilities

| Role | Member | Primary Deliverables | TA Verification |
|------|--------|---------------------|----------------|
| Agent Architect | Wasim Akram | Pipeline design, architecture diagram, integration plan | Architecture matches code? Separation of concerns? |
| Product Lead | Gopi Trinath | Requirements doc, sample resume, constraint definitions | Resume realistic (3-5yr AI Eng)? Constraints enforced? |
| Web Engineer | Damini | SerpAPI integration, data extraction, parsing | Reliably captures title, company, location, skills, salary, URL? |
| LLM Engineer | Josna | Ranking logic, tailoring prompts, personalization | Ranking criteria applied correctly? Tailored docs differentiated? |
| Eval Lead | Ujwal | 20-job benchmark, metrics computation, bias analysis | Benchmark sound (20 jobs)? P@10 correct? Bias section substantive? |

---

## Pipeline Details

### Step 1: Search (search.py)
- Queries SerpAPI Google Jobs engine with user-entered job title and location
- Extracts: title, company, location, salary, skills_mentioned, URL, posted date
- Supports pagination via next_page_token
- Handles rate limiting and missing fields with fallback parsing
- Falls back to 32 built-in demo jobs if no API key provided

### Step 2: Filter (filter.py)
- **FAANG Blacklist:** Removes Google, Amazon, Apple, Meta, Microsoft, Netflix, Tesla, NVIDIA (togglable)
- **Startup Detection:** Keyword scan for pre-seed, series A/B/C, early-stage, stealth, venture-backed, incubator, accelerator
- **Location Filter:** Optional state-level restriction
- **Custom Blacklist:** User can add company names via sidebar
- Every decision logged: `[FILTER] Google | action=REMOVE | reason=FAANG blacklist`

### Step 3: Rank (rank.py)
- **Skill Match (0-100):** Word overlap between user skills and job requirements
- **Location Score:** Exact city=100%, same state=70%, no match=0%
- **Recency (0-100):** Newer postings score higher (just posted=100, 30+ days=0)
- Composite formula with user-adjustable weight sliders (0 to 1)
- Ranks all filtered jobs, returns top N (default 10)

### Step 4: Tailor (tailor.py)
- Calls LLM via OpenRouter API (default: google/gemini-2.0-flash-001, free)
- Sends structured prompt: base resume + job details + neutral language instructions
- Splits response on `===COVER_LETTER===` delimiter
- BudgetTracker enforces $5.00 per-session spending cap
- Error handling for network issues, rate limits, malformed responses

---

## Evaluation Results

The evaluation uses a **20-job benchmark** (10 interview-worthy / 10 rejects):

| Metric | K=3 | K=5 | K=9 |
|--------|-----|-----|-----|
| Precision | 100.0% | 80.0% | 44.4% |
| Recall | 75.0% | 100.0% | 100.0% |
| F1 Score | 85.7% | **88.9%** | 61.5% |
| NDCG | 100.0% | 100.0% | 100.0% |

- **Best F1 at K=5:** 88.9% (4 TP, 1 FP, 0 FN, 4 TN)
- **Interview Yield:** 44.4% (4/9 human Yes)
- **Score Separation:** +20.6 points (Good=61.05 vs Bad=40.42)
- **Tailoring Quality:** 4.0/5 resume, 4.0/5 cover letter (human rated)
- **Filter Toggle:** Both filters ON removes 70% of jobs (30 to 9)

---

## Ethics and Bias Analysis

The ethics module (ethics.py) runs 7 automated analyses:

1. **Gender-Coded Language** — Gaucher et al. (2011) framework. Result: Balanced (13 masculine, 15 feminine words across 9 jobs)
2. **Location Fairness** — Flags geographic concentration. Result: 100% Texas (expected for this persona)
3. **Salary Equity** — Analyzes pay distribution across ranked jobs
4. **Skill Bias** — Detects over-reliance on specific skills. Result: 83.3% diversity score
5. **Company Diversity** — Checks sector concentration in shortlist
6. **Transparency Audit** — Verifies all decisions are logged. Result: 100% coverage
7. **Mitigation Strategies** — 8 concrete strategies implemented

### 8 Mitigation Strategies
1. FAANG filter is configurable toggle, not hardcoded
2. Skill weights are user-adjustable sliders (0-1)
3. Location scoring is hierarchical and transparent (no hard cutoffs)
4. Gender-coded language audit in Ethics tab
5. Complete decision logging with export
6. Benchmark data includes diverse company types
7. Salary displayed but NOT used for ranking
8. LLM prompts use neutral language instructions

---

## API Keys (Optional)

| Service | Free Tier | What It Does |
|---------|-----------|-------------|
| SerpAPI | 100 free searches at https://serpapi.com | Real-time Google Jobs search |
| OpenRouter | Free models at https://openrouter.ai/keys | LLM for resume/cover letter tailoring |

**Without keys:** The app runs in demo mode with 32 built-in jobs. All features work except live search and tailoring.

**With keys:** Enter in the sidebar. Keys are never stored or logged.

You can also create a `.env` file (copy from `.env.example`):
```
SERPAPI_KEY=your_key_here
OPENROUTER_KEY=your_key_here
```

---

## Requirements

```
streamlit>=1.40.0
requests>=2.31.0
pandas>=2.0.0
python-dotenv>=1.0.0
```

**Python 3.10+ required.** No GPU needed. Runs on any OS (Windows, Mac, Linux).

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError: No module named 'streamlit'` | Run `pip install -r requirements.txt` |
| App shows blank page | Check terminal for errors. Try `streamlit run app.py --server.port 8502` |
| SerpAPI returns 0 results | Check API key is valid. Try different query. Check Agent Log expander. |
| Tailoring shows error | Ensure OpenRouter key is entered. Try different model from dropdown. |
| Evaluation shows 0% metrics | Click "Run Hiring Simulation" after completing Rank step. |
