# Individual Reflection — Gopi Trinath
## Role: Product Lead
### AI for Engineers — Group Assignment 2

## Personal Role and Contributions

As Product Lead, I took the initiative to set up the project foundation and defined the core requirements that guided the team's implementation. My primary contributions included:

- **Candidate Persona Definition:** I created the Alex Johnson persona — a 4-year AI/ML engineer based in Des Moines, Iowa, with Python, TensorFlow, PyTorch, MLflow, and cloud platform expertise. This realistic profile (3-5 years experience) anchored the entire tailoring and evaluation pipeline.

- **Constraint System Design:** I established the FAANG/Big-Tech blacklist (28+ companies), the startup detection heuristic (<50 employees via keyword signals), and the location preference hierarchy. These constraints directly address the assignment's "Middle America" focus and are clearly defined in `config.py`.

- **Sample Resume:** I authored the base resume used by the tailoring module, ensuring it reflected a realistic mid-career AI engineer with quantifiable achievements (e.g., "Reduced MAPE by 18%", "50K events/sec with <50ms p99 latency").

- **Initial Project Setup:** I built the first working version of the codebase, established the project structure, and created the demo dataset of 32 jobs spanning multiple states and industries.

- **Configuration Management:** I centralized all configurable parameters in `config.py`, including the FAANG blacklist, startup signals, default skills, model pricing, and budget limits, making it easy for teammates to reference and modify constraints.

The most challenging aspect of my role was calibrating the FAANG blacklist. While excluding companies like Google is straightforward, edge cases — consulting firms with Big Tech contracts, FAANG subsidiaries, defense contractors that are technically large but not "Big Tech" — required careful judgment. I ultimately made the filter togglable so users retain control, which directly addresses the TA verification point about constraints being "clearly defined and enforced."

## Reflection on Hiring Equity and Ethical Impact

Working on this project has made me think deeply about how hiring tools encode values. Every constraint I defined — which companies to exclude, which skills to prioritize, which locations to prefer — reflects assumptions about what constitutes a "good" job. These assumptions may systematically disadvantage candidates who do not share them.

For example, the FAANG blacklist assumes that mid-career engineers in Middle America prefer non-Big-Tech employers. While this aligns with the assignment scenario, a real-world deployment would need to validate this assumption against actual user preferences. Similarly, the startup filter uses keyword heuristics that could incorrectly exclude legitimate small companies that happen to mention "accelerator" in their description.

The configurable nature of our filters is a partial mitigation — users can disable any filter or add custom rules. But defaults carry weight: most users accept defaults without modification. This means the Product Lead's choices about default settings have outsized influence on outcomes.

One positive ethical outcome is that our agent surfaces opportunities in regions that are typically underserved by tech job platforms. By focusing on Middle America and providing equal-quality tailored applications regardless of company size or prestige, the agent could help reduce the geographic concentration of AI talent and promote more equitable access to opportunities across the country.

If deployed at scale, I would recommend regular audits of the default blacklist against actual hiring outcomes, user studies to validate constraint definitions, and an opt-in feedback mechanism for candidates to report when the agent's filtering was too aggressive or too permissive.
