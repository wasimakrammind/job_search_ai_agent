# Individual Reflection — Damini
## Role: Web Engineer
### AI for Engineers — Group Assignment 2

## Personal Role and Contributions

As Web Engineer, I was responsible for the job search module, SerpAPI integration, and data extraction. My primary contributions included:

- **SerpAPI Integration (`search.py`):** I built the search module that queries Google Jobs via SerpAPI using plain HTTP requests. This approach avoids the overhead of the official SDK while providing full control over pagination through `next_page_token` handling. The module supports configurable query parameters, location targeting, and result limits.

- **Data Extraction and Parsing:** I implemented robust extraction for all required fields from SerpAPI responses: title, company, location, skills_mentioned, salary, URL, and posted date. Each field has fallback parsing to handle inconsistent data from the API — for example, some listings lack salary information, others have locations in non-standard formats.

- **Demo Dataset Curation:** I helped curate the 32-job demo dataset that enables the agent to function without an API key. The dataset includes jobs across 10+ states and covers companies in insurance, agriculture, healthcare, manufacturing, finance, retail, defense, and technology — ensuring diverse representation for evaluation.

- **Pagination Support:** I implemented multi-page result fetching using SerpAPI's `next_page_token`, allowing the agent to retrieve up to 50 results across multiple API calls while respecting rate limits.

- **Streamlit UI Contributions:** I contributed to the search interface in the Streamlit UI, including the query input, location field, max results selector, and the results display with source indicators (SerpAPI vs Demo).

The main challenge was handling inconsistent data from the Google Jobs API. Some listings have skills explicitly listed while others require inference from the description. Salary formats vary widely ("$130K-$155K/yr" vs "$130,000-$155,000 per year" vs "N/A"). Location strings sometimes include country codes, zip codes, or "Remote" designations. I built normalization logic for each field to maximize extraction reliability.

## Reflection on Hiring Equity and Ethical Impact

Working on the data extraction layer gave me unique insight into how data quality directly affects hiring equity. The search module is the first stage of the pipeline — any bias or incompleteness here propagates through filtering, ranking, and tailoring.

One significant equity concern is skill extraction bias. Our system extracts skills by checking job descriptions against a predefined list of 18 common AI/ML skills. This approach works well for standardized job postings from larger companies that use common terminology, but smaller companies often describe the same skills differently. A job posting that says "build neural networks" instead of "deep learning" would not be matched, potentially disadvantaging smaller companies that use less standardized language.

Geographic representation in search results is another equity issue. SerpAPI returns results influenced by Google's job indexing, which may over-represent companies that actively post on major job boards and under-represent those that rely on local channels. Our demo dataset partially addresses this by including a curated set of Middle America companies, but the live search inherits whatever biases exist in Google's job index.

I also learned that even seemingly technical decisions — like how many results to fetch per page, or which fields to extract — have ethical dimensions. Fetching only 10 results per page means the agent may miss relevant opportunities on later pages. Extracting salary only when it is explicitly listed means we have no salary data for roughly 30% of listings, which could affect analysis accuracy.

For a production system, I would recommend implementing multiple search sources (LinkedIn, Indeed, company career pages) to reduce dependence on any single platform's biases, and developing more sophisticated NLP-based skill extraction that goes beyond keyword matching to understand semantic equivalence.
