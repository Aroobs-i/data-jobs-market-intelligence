# step5_scale_scraper.py
# Goal: scrape MANY search terms x MANY pages, reusing the resilient functions
# we already built in step4, instead of rewriting them (this is called "importing
# your own code" -- a core Python skill once projects grow beyond one file)

from urllib.parse import quote
import time
import random
import pandas as pd

# This line imports the two functions we already wrote and tested in step4,
# without re-running step4's own __main__ block (that's exactly what the
# `if __name__ == "__main__":` guard in step4 protects against)
from step4_resilient_scraper import fetch_rendered_html, parse_job_listings

# --- CONFIGURE YOUR SCRAPE HERE ---
SEARCH_TERMS = [
    "Data Analyst",
    "Data Scientist",
    "Business Analyst",
    "SQL Developer",
    "Data Engineer",
    "Power BI",
    "Tableau",
    "Machine Learning",
    "Python Developer",
    "MIS Officer",
]
PAGES_PER_TERM = 3  # each page = ~20 jobs, so 3 pages = up to ~60 per term

all_jobs = []

for term in SEARCH_TERMS:
    for page_num in range(PAGES_PER_TERM):
        offset = page_num * 20
        encoded_term = quote(term)
        url = f"https://www.rozee.pk/job/jsearch/q/{encoded_term}/?fpn={offset}"

        print(f"\n=== Searching '{term}', page {page_num + 1} (offset={offset}) ===")
        html = fetch_rendered_html(url, max_attempts=2)

        if html is None:
            print(f"Skipping this page after failed attempts.")
            continue

        jobs = parse_job_listings(html)
        print(f"Got {len(jobs)} jobs")

        # Tag each job with which search term found it -- useful later for analysis
        for job in jobs:
            job["search_term"] = term
        all_jobs.extend(jobs)

        # Be a polite scraper: random delay between requests so we're not
        # hammering the site as fast as possible. This also reduces the
        # chance of triggering rate-limiting/CAPTCHAs.
        delay = random.uniform(2, 5)
        print(f"Waiting {delay:.1f}s before next request...")
        time.sleep(delay)

print(f"\n\n=== DONE: collected {len(all_jobs)} total job entries (before deduping) ===")

df = pd.DataFrame(all_jobs)

# The same job can appear under multiple search terms (e.g. a "Data Analyst /
# Power BI" job matches both "Data Analyst" and "Power BI" searches).
# We dedupe by link, since that's the one truly unique identifier per job.
before = len(df)
df = df.drop_duplicates(subset="link", keep="first")
after = len(df)
print(f"Removed {before - after} duplicate listings, {after} unique jobs remain.")

df.to_csv("../data/rozee_jobs_multi.csv", index=False, encoding="utf-8-sig")
print("Saved to ../data/rozee_jobs_multi.csv")