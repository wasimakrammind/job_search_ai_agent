# Individual Reflection — Josna
## Role: LLM Engineer
### AI for Engineers — Group Assignment 2

## Personal Role and Contributions

As LLM Engineer, I was responsible for the ranking logic and the LLM-based tailoring module. My primary contributions included:

- **Ranking Algorithm (`rank.py`):** I implemented the weighted composite scoring system that combines three factors: skill match (0-100%), location proximity (0-100% via hierarchical scoring), and posting recency (0-100%, newer is higher). The formula `composite = skill% * w_skill + location% * w_loc + recency% * w_recency` with user-adjustable weights via sliders provides transparent, controllable ranking.

- **Tailoring Module (`tailor.py`):** I built the OpenRouter API integration for generating tailored resumes and cover letters. This included prompt engineering, response parsing with delimiter-based section extraction, error handling for API failures, and integration with the BudgetTracker.

- **Prompt Engineering:** I iteratively refined the tailoring prompt to produce high-quality, differentiated outputs. The final prompt structure includes the target job details (title, company, location, skills), the full candidate resume, and specific formatting instructions with a `---COVER LETTER---` delimiter for reliable parsing.

- **Model Selection Architecture:** I configured the OpenRouter model menu with 10 models across three tiers (free, budget, premium), allowing users to balance quality against cost. The default free-tier model (Gemini Flash) produces good results at zero cost.

- **Budget Tracking:** I integrated cost estimation and enforcement throughout the tailoring pipeline. Each API call logs estimated input/output token counts and cost, and the system refuses additional calls once the $5.00 session budget is exhausted.

The most challenging aspect was prompt engineering. Early prompts produced generic outputs that did not meaningfully differentiate between jobs — a tailored resume for a healthcare company looked nearly identical to one for a manufacturing company. The breakthrough was including specific job skills and company context directly in the prompt, along with explicit instructions to reference job requirements. This brought the human evaluation score from approximately 2.5/5 to 4.0/5.

## Reflection on Hiring Equity and Ethical Impact

The ranking and tailoring modules are where the agent's decisions most directly affect candidate outcomes, making ethical considerations paramount.

Ranking weights are value judgments disguised as technical parameters. Setting the default skill weight to 0.50 (the highest) implies that skill match matters most. This choice benefits candidates with conventional AI/ML backgrounds and standard skill sets, but may disadvantage career-changers, bootcamp graduates, or candidates with non-traditional paths who possess equivalent capabilities under different terminology. Making weights adjustable is our primary mitigation, but defaults still influence outcomes for the majority of users who accept them without modification.

The recency bias in our scoring (newer postings score higher) is another equity concern. While recent postings are more likely to still be accepting applications, this systematically disadvantages companies that post early or keep listings open longer — which may correlate with company size, industry, or HR practices rather than job quality.

On the tailoring side, LLM-generated application materials raise important fairness questions. Our system gives all candidates access to the same quality of tailoring, which could be seen as an equalizer — candidates without professional resume-writing resources get the same quality output as those who can afford career coaches. However, if employers begin to expect AI-polished applications, this could disadvantage candidates who choose not to use such tools.

I was deliberate about including neutral language instructions in the tailoring prompt. The system does not assume the candidate's gender, ethnicity, or cultural background, and explicitly avoids gendered language. This is a small but meaningful step toward ensuring the LLM does not introduce demographic biases into application materials.

For future work, I would recommend A/B testing different prompt structures to measure their impact on interview callback rates, and implementing candidate-specific customization that goes beyond skill matching to consider career trajectory and growth potential.
