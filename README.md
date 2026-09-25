# 📊 Data Analytics Job Market Intelligence

**Live dashboard:** https://data-jobs-market-intelligence-anbucscac4bdoy3sp47kwr.streamlit.app

A self-updating analytics platform comparing Pakistan's data/analytics job market against the global market (US, UK, Canada, Australia). Built end-to-end: live web scraping → cloud database → SQL analysis → interactive dashboard → automated daily updates → ML modeling.

Born out of my own frustration job-hunting as a fresher — I wanted real evidence of what the market actually looks like, not guesses.

---

## 🔑 Key Findings

**Pakistan's market still leans on Excel/Power BI, while the global market has shifted to SQL/Python/ML:**

| Skill | Pakistan | Global | Gap |
|---|---|---|---|
| Excel | **42.4%** | 10.6% | Pakistan 4x higher |
| Power BI | **36.4%** | 11.5% | Pakistan 3x higher |
| SQL | 15.2% | **42.7%** | Global 3x higher |
| Python | 15.2% | **37.0%** | Global 2.4x higher |
| Machine Learning | 9.1% | **21.2%** | Global 2.3x higher |
| Tableau | 6.1% | **19.7%** | Global 3x higher |

*(% of each market's own postings that mention the skill — normalized for fair comparison, not raw counts)*

**What predicts job seniority isn't specific skills — it's how many skills are listed.** A Random Forest classifier found `total_skill_count` was ~8x more important than any individual skill (feature importance 0.24 vs ~0.03 for the next-best feature). Mid-senior postings list modestly more skills on average (25.8) than Associate postings (23.0) — the gap holds in both mean and median, so it's a real pattern, not outlier noise.

**Number-of-skills matters more than which skills** for predicting seniority — surprising, and verified with two independent models before trusting it.

---

## 🏗️ Architecture

```
Rozee.pk (Pakistan)          Kaggle Dataset (Global)
   ↓ Selenium scraping           ↓ 1.3M rows, filtered to
   ↓ (JS-rendered site)            ~12.9K data/analytics roles
   ↓
   └──────────┬──────────────────┘
              ↓
   Normalized PostgreSQL schema (Neon, cloud-hosted)
   companies · locations · skills · jobs · job_skills
              ↓
   ┌──────────┼──────────────┐
   ↓          ↓              ↓
SQL Analysis  Streamlit    ML Models
(CTEs, window  Dashboard    (Logistic Regression,
functions,    (deployed,    Random Forest)
self-joins)   auto-refreshing)

   Daily automated scraper (Windows Task Scheduler)
   → writes new postings directly to the cloud DB
   → dashboard reflects new data within the hour, no manual steps
```

---

## 🛠️ Tech Stack

- **Scraping**: Python, Selenium (headless Chrome, JS-rendered site), BeautifulSoup
- **Data processing**: pandas
- **Database**: PostgreSQL (hosted on Neon), SQLAlchemy
- **Analysis**: SQL (CTEs, window functions, self-joins, `CASE`/`HAVING`)
- **Dashboard**: Streamlit, Plotly
- **ML**: scikit-learn (Logistic Regression, Random Forest)
- **Automation**: Windows Task Scheduler, direct-to-cloud daily pipeline
- **Deployment**: Streamlit Community Cloud, GitHub

---

## 📁 Project Structure

```
Analysis/                          -- SQL queries (run in order to see the analytical progression)
  01_top_skills.sql
  02_job_level.sql
  03_top_companies.sql
  04_top_skill_per_city.sql        -- window functions (RANK)
  05_skill_cooccurrence.sql        -- self-join
  06_pakistan_vs_global_percentage.sql
  07_skill_categories.sql          -- CASE WHEN, HAVING
  08_company_hiring_depth.sql      -- chained CTEs, ROW_NUMBER

scraper/
  step1-step10   -- Python fundamentals through pandas analysis, built incrementally
  step11         -- normalized PostgreSQL schema + load pipeline
  step12         -- keyword-based skill extraction for Pakistan postings
  step13-14      -- full job description fetching for richer Pakistan data
  step15-17      -- ML models (job level prediction, model comparison)
  daily_scrape.py -- scheduled scraper, writes directly to the cloud DB
  app.py         -- the dashboard
```

---

## 🧗 Real Challenges Solved Along the Way

This wasn't a smooth, linear build — and the debugging is part of the story:

- **Rozee.pk renders job listings via JavaScript**, so plain `requests` + BeautifulSoup returned empty pages. Solved with Selenium + a resilient retry system (headless Chrome, exponential backoff, intelligent `WebDriverWait` instead of blind `sleep()`).
- **Rate limiting mid-session** after repeated testing — solved with longer randomized delays, incremental saving (so partial progress survives interruptions), and accepting realistic scrape volumes rather than fighting the site indefinitely.
- **Messy real-world data**: inconsistent skill capitalization (fixed via most-common-casing normalization), truncated search-result descriptions (fixed by fetching each job's full detail page), a case where the "wait for element" logic broke when reused on a different page type (fixed by making the wait condition a parameter).
- **Cloud migration**: moved from local PostgreSQL to Neon (serverless Postgres) for public deployment, including handling `sslmode=require`, connection pooling drops (`pool_pre_ping=True`), and Streamlit Cloud's separate secrets system vs local `.env` files.
- **True automation**: the daily scraper writes directly to the cloud database (not just a local file), with deduplication against existing records, so the live dashboard updates itself with zero manual steps.
- **Data provenance nuance**: caught that Rozee.pk lists remote/international postings alongside local Pakistani jobs — some "city" values are actually the hiring company's home country (e.g., "Mexico," "Costa Rica"), not a Pakistan location. Correctly interpreted and labeled in the dashboard rather than treated as a bug or hidden.

---

## 📈 Data Sources

- **Pakistan**: live-scraped from [Rozee.pk](https://rozee.pk),( 134 postings and counting as I write this — small on purpose, since it's fresh data updating in real time) refreshed daily via an automated scheduled scraper
- **Global**: [1.3M LinkedIn Jobs & Skills (2024)](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024) (Kaggle), filtered to ~12,900 data/analytics-relevant roles. Predominantly US-based (85%), with UK/Canada/Australia making up the rest — used here as a global benchmark, not a Pakistan-specific source.

---

## 🚀 Running This Locally

1. Clone the repo, `pip install -r requirements.txt`
2. Download the [Kaggle dataset](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024) into `data/`
3. Set up a PostgreSQL database (local or [Neon](https://neon.tech)), create a `.env` file with your connection details (see `.env` format in `step11_load_to_postgres.py`)
4. Run the pipeline scripts in `scraper/` in numeric order
5. `streamlit run scraper/app.py`

---

## 🔮 What's Next

- Widen skill-category coverage for Pakistan (currently keyword-matched; could use NLP for better recall)
- Add more Pakistan job sources beyond Rozee.pk for a larger sample
- Let the daily scraper accumulate more history — the time-series charts get more meaningful every week
