# Individual Reflection — Wasim Akram
## Role: Agent Architect
### AI for Engineers — Group Assignment 2

## Personal Role and Contributions

As Agent Architect, I was responsible for the overall pipeline design, the architecture diagram, the shared location module, and ensuring all pipeline stages integrated correctly. My primary contributions included:

- **Pipeline Architecture Design:** I designed the four-stage sequential pipeline (Search → Filter → Rank → Tailor) with clear input/output contracts between modules. Each stage accepts a list of job dictionaries and returns an augmented list, enabling independent development and testing.

- **Shared Location Module (`location.py`):** I built the hierarchical geographic matching system that both `filter.py` and `rank.py` rely on. This module resolves city names to states (50+ US cities mapped), expands state abbreviations, and provides both boolean matching (for filtering) and numeric scoring (for ranking). Without this shared module, we would have had inconsistent location handling across stages.

- **Filter Logic (`filter.py`):** I implemented the four-rule filter pipeline: FAANG blacklist check, startup keyword detection, location matching via the hierarchical system, and custom blacklist support. Each filter decision is logged with a clear reason for auditability.

- **Integration and Testing:** I ensured all modules work together seamlessly in the Streamlit UI. This included verifying that data flows correctly from search results through filtering, ranking, and tailoring, with session state properly managed across user interactions.

- **Architecture Documentation:** I created the pipeline diagram and documented the data flow, module responsibilities, and integration contracts in the Design Document.

The biggest technical challenge was the location module. Resolving "Austin, TX" to Texas, handling abbreviations (TX vs Texas), supporting compound locations like "Kansas City, MO," and distinguishing between cities with the same name in different states required a hierarchical matching system. The three-tier scoring (city=100%, state=70%, none=0%) provides nuanced ranking while the boolean filter uses the same underlying resolution for consistency.

## Reflection on Hiring Equity and Ethical Impact

From an architectural perspective, I have come to appreciate that design decisions have real equity implications. The separation of concerns I maintained — isolating filtering, ranking, and generation into separate modules — means each bias-relevant decision is auditable in isolation. If the filter has a bug that discriminates against certain companies, it can be identified and fixed without touching the ranking logic.

The hierarchical location scoring system I designed has important fairness implications. By giving partial credit (70%) to jobs in the same state but different city, the system avoids a binary cutoff that would completely exclude nearby opportunities. A candidate in Des Moines searching for Iowa jobs will still see opportunities in Cedar Rapids, even though it is a different city. This graduated approach is more equitable than a hard city-match filter.

However, the location module also encodes geographic knowledge that could be biased. The city-to-state mapping covers 50+ US cities but inevitably misses smaller towns. Jobs in unmapped cities fall back to substring matching, which is less reliable. This means candidates in smaller or less well-known cities might experience lower-quality location matching, effectively receiving less precise job recommendations.

One architectural decision I am particularly proud of is making all pipeline decisions logged and exportable. This transparency is not just a technical feature — it is an ethical requirement. When an automated system makes decisions that affect people's careers (even in a simulation), those decisions should be explainable and auditable. Our logging system ensures that every filter rejection, ranking score, and LLM generation is traceable to a specific rule or input, which is essential for accountability.

Going forward, I would recommend adding a feedback loop where users can flag incorrect filter decisions or location matches, allowing the system to improve its geographic intelligence over time while maintaining transparency about how those improvements affect results.
