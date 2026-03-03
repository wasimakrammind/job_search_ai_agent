# Design Document
## Middle America Job & Application Agent
### AI for Engineers — Group Assignment 2

**Team Members:**

| Role | Name |
|------|------|
| Product Lead | Gopi Trinath |
| Agent Architect | Wasim Akram |
| Web Engineer | Damini |
| LLM Engineer | Josna |
| Eval Lead | Ujwal |

---

## 1. Pipeline Architecture

The agent follows a four-stage sequential pipeline. Each stage is a separate Python module with clear input/output contracts, enabling independent testing and ownership.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. SEARCH   │───>│  2. FILTER   │───>│  3. RANK     │───>│  4. TAILOR   │
│  search.py   │    │  filter.py   │    │  rank.py     │    │  tailor.py   │
│              │    │              │    │              │    │              │
│ SerpAPI      │    │ FAANG list   │    │ Skill match  │    │ OpenRouter   │
│ Google Jobs  │    │ Startup det. │    │ Location     │    │ LLM API      │
│ 30 results   │    │ Location     │    │ scoring      │    │ Resume +     │
│ Pagination   │    │ hierarchy    │    │ Recency      │    │ Cover Letter │
│              │    │              │    │ weighting    │    │ Budget track │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Data Flow

1. User inputs query and location in sidebar.
2. `search.py` queries SerpAPI and returns a list of job dictionaries with title, company, location, salary, skills, URL, and posted date.
3. `filter.py` applies configurable exclusion rules and returns kept/removed lists with reasons.
4. `rank.py` computes a composite score from skill match, location proximity, and recency, then sorts descending.
5. `tailor.py` sends each top-N job plus the base resume to an LLM via OpenRouter and returns personalized resume and cover letter text.

### Shared Module — location.py

A hierarchical location-matching module used by both `filter.py` and `rank.py`. It resolves city names to states, expands state abbreviations (e.g., TX to Texas), and supports "Middle America" as a region encompassing 20+ central U.S. states. This avoids duplicating geography logic across modules.

### Supporting Modules

- `config.py` — Central configuration (blacklists, skills, model pricing, budget tracker, sample resume)
- `logger.py` — Centralized decision logging with in-memory buffer for UI integration
- `app.py` — Streamlit web UI with vertical-scroll pipeline flow

---

## 2. Filter Heuristics

The filter stage applies four configurable exclusion rules. Each decision is logged with a reason string for full auditability.

### 2.1 FAANG/Big-Tech Blacklist

Companies excluded by default: Google, Amazon, Apple, Meta, Microsoft, Netflix, Tesla, NVIDIA, OpenAI, Anthropic, and 20+ others. The user can toggle this filter on/off and add custom companies to the blacklist via the sidebar.

**Justification:** The assignment requires mid-sized "Middle America" companies. FAANG and Big Tech dominate coastal markets and skew results away from the target demographic.

### 2.2 Startup Detection

Heuristic keyword scan of company names and descriptions for startup indicators: stealth, pre-seed, seed-stage, series A/B/C, early-stage, YCombinator, TechStars, incubator, accelerator, and recently founded companies (2023-2026).

**Justification:** Enforces the <50 employees constraint per assignment requirements. Startups typically have fewer than 50 employees and different hiring dynamics.

### 2.3 Location Hierarchy

Three-tier matching:
- **Tier 1:** Exact city match → 100% location score
- **Tier 2:** Same state, different city → 70% location score
- **Tier 3:** No match → 0% location score

The module expands abbreviations (TX → Texas), resolves ambiguous city names via a 50+ city mapping, and handles remote/hybrid designations. User-entered preferred location carries through from the Search sidebar input.

### 2.4 Decision Logging

Every filter decision is recorded in the agent log with format:
```
[FILTER] Company | action=KEEP/REMOVE | reason=<rule>
```
Example: `[FILTER] Google | action=REMOVE | reason=FAANG blacklist`

This log is exportable for the report appendix.

---

## 3. Tailoring Workflow

The tailoring stage generates personalized application materials for each of the top-N ranked jobs using an LLM via the OpenRouter API.

### 3.1 Prompt Design

Each LLM call sends a structured prompt containing:
1. The base resume text (editable by the user in the UI)
2. The job title, company, location, and extracted skills
3. Instructions to produce a tailored resume and cover letter separated by a delimiter (`---COVER LETTER---`)

The prompt instructs the model to be professional, concise, and to avoid gendered or culturally-specific language.

### 3.2 Model Selection and Budget

The system uses OpenRouter, which provides access to multiple LLM providers through a single API. The default model is `google/gemini-2.0-flash-001` (free tier). Users can select alternative models from a dropdown including:
- **Free tier:** DeepSeek, Llama 4, Mistral, Qwen3
- **Budget:** Gemini Flash, GPT-4o-mini, Llama 3.3 70B
- **Premium:** Gemini 2.5 Pro, Claude Sonnet 4, GPT-4o

A `BudgetTracker` class enforces a $5.00 spending cap across all API calls in a session.

### 3.3 Output Parsing and Error Handling

The LLM response is split on the `---COVER LETTER---` delimiter to extract the resume and cover letter as separate strings. If the delimiter is missing, the entire response is treated as the resume and a fallback is generated. Network errors, rate limits, and malformed responses are caught and logged.

### 3.4 Human Evaluation

After generation, a human evaluator rates each tailored resume and cover letter on a 1-5 scale for relevance, specificity, and professional quality. These scores feed into the evaluation module's Tailoring Quality metric. In the current evaluation, average scores were 4.0/5 for resumes and 3.6/5 for cover letters across 5 evaluated jobs.
