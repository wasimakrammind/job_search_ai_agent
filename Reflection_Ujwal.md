# Individual Reflection — Ujwal
## Role: Eval Lead
### AI for Engineers — Group Assignment 2

## Personal Role and Contributions

As Eval Lead, I was responsible for the evaluation framework, benchmark dataset, metrics computation, and the ethics/bias analysis module. My primary contributions included:

- **20-Job Benchmark Dataset:** I constructed the ground-truth benchmark with 10 interview-worthy and 10 reject companies. Labeling was based on manual review of each job's skill alignment with the candidate persona, company profile (mid-sized vs. large/defense), role seniority, and ML focus. I documented the labeling rationale to ensure the benchmark is reproducible and defensible.

- **Metrics Implementation (`evaluate.py`):** I implemented the full suite of information retrieval metrics: Precision@K, Recall@K, F1@K, NDCG@K, and confusion matrix computation. Metrics are computed at multiple K values (3, 5, 10, N) to show how performance varies with shortlist size. I also implemented fuzzy company name matching to handle discrepancies between agent output and benchmark labels.

- **Interview Yield Calculation:** I implemented the interview yield metric, which measures what fraction of agent-recommended jobs receive a "Yes, interview" vote from human evaluators. This directly addresses the assignment's requirement for human scoring of the agent shortlist.

- **Ethics Module (`ethics.py`):** I built the comprehensive bias analysis system with seven analyses: gender-coded language detection (using Gaucher et al. 2011 framework), location fairness, salary equity, skill-matching bias, company diversity, transparency audit, and bias mitigation strategies.

- **Filter Toggle Experiment:** I implemented the automated filter toggle experiment that runs the same job set through four filter configurations (no filters, FAANG only, startup only, both) and compares the results to quantify filter impact.

The hardest part was creating a fair and meaningful benchmark. With the demo dataset of 32 companies, the 20-job benchmark (10+/10-) required careful manual review of each company's actual job posting to determine interview-worthiness. Borderline cases — like Lockheed Martin (large defense contractor with legitimate ML roles) or John Deere (agriculture company with strong autonomy work) — required judgment calls. I documented each decision's rationale and used majority voting from team members to validate controversial labels.

## Reflection on Hiring Equity and Ethical Impact

As Eval Lead, I was responsible for both measuring the agent's performance and auditing its fairness, which gave me a dual perspective on how evaluation itself can be biased.

The most important lesson I learned is that evaluation is inherently subjective. My decision about which jobs "deserve" interviews reflects my assessment of skill alignment and role quality — a different evaluator might label differently. The 1-5 tailoring scores are similarly subjective. Our metric of 70.0% interview yield and 4.0/5 tailoring quality measures agreement with our evaluators' judgment, not objective job quality.

To mitigate evaluator bias, we used three independent human evaluators and majority voting for the interview labels. This reduces individual bias but does not eliminate it — all three evaluators are graduate students with similar backgrounds, so we share certain blind spots. A more rigorous evaluation would include evaluators from diverse professional backgrounds and geographic regions.

The gender-coded language analysis was particularly eye-opening. Even seemingly neutral job descriptions contain words that research shows discourage certain applicants. Finding that our job pool was "Balanced" (roughly equal masculine and feminine-coded words) was reassuring, but the analysis also revealed that individual listings can lean strongly in one direction. Making this data visible to users empowers them to be aware of subtle biases in the jobs they are considering.

The ethics module's transparency audit confirmed that our pipeline logs 100% of filter decisions with reasons, ranking scores are decomposed into component factors, and all weights are user-adjustable. This level of transparency is not just a technical feature — it is an ethical requirement for any system that influences career decisions. Opaque algorithms that make unexplainable recommendations about someone's career path are fundamentally inequitable.

One area where I see room for improvement is in the benchmark's demographic diversity. Our benchmark companies are concentrated in certain industries (insurance, agriculture, manufacturing) that may not represent the full range of Middle America employers. A more comprehensive benchmark would include healthcare systems, universities, government agencies, and non-profit organizations to better capture the diversity of the regional job market.

For future work, I would recommend longitudinal evaluation — tracking whether agent recommendations lead to actual interviews and offers over time — and incorporating candidate feedback to continuously improve the benchmark and scoring criteria.
