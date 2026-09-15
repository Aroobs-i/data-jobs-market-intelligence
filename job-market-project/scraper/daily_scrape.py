# daily_scrape.py
# Goal: run automatically once a day (via Windows Task Scheduler) to build
# a REAL time-series of the Pakistan data job market -- something that
# genuinely doesn't exist anywhere else. Each run appends today's snapshot
# to a growing history file, tagged with the date, instead of overwriting.
#
# Kept deliberately light (fewer terms, 1 page each, generous delays) so
# running this daily doesn't risk repeatedly triggering rate-limiting.

from urllib.parse import quote
import time
import random
import pandas as pd
from datetime import date
from step4_resilient_scraper import fetch_rendered_html, parse_job_listings

SEARCH_TERMS = [
    "Data Analyst",
    "Data Scientist",
    "Business Analyst",
    "Power BI",
    "Data Engineer",
]

HISTORY_FILE = "../data/job_history.csv"
today = date.today().isoformat()

all_jobs = []

for term in SEARCH_TERMS:
    encoded_term = quote(term)
    url = f"https://www.rozee.pk/job/jsearch/q/{encoded_term}/?fpn=0"

    print(f"Searching '{term}'...")
    html = fetch_rendered_html(url, max_attempts=2)

    if html is None:
        print(f"  Failed, skipping '{term}' for today.")
        continue

    jobs = parse_job_listings(html)
    for job in jobs:
        job["search_term"] = term
        job["scraped_date"] = today
    all_jobs.extend(jobs)
    print(f"  Got {len(jobs)} jobs")

    delay = random.uniform(10, 18)
    time.sleep(delay)

if all_jobs:
    new_df = pd.DataFrame(all_jobs)
    # Dedupe WITHIN today's run only (same job showing up under 2 search terms today)
    new_df = new_df.drop_duplicates(subset=["link", "scraped_date"], keep="first")

    try:
        # Append to existing history -- this is what builds the time series
        existing = pd.read_csv(HISTORY_FILE)
        combined = pd.concat([existing, new_df], ignore_index=True)
    except FileNotFoundError:
        combined = new_df  # first run ever, file doesn't exist yet

    # Dedupe across the WHOLE history, not just today's batch -- this handles
    # the case where the script gets run more than once on the same day
    # (e.g. a manual test + the scheduled run both firing today)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["link", "scraped_date"], keep="first")
    removed = before - len(combined)
    if removed > 0:
        print(f"Removed {removed} same-day duplicates (script likely ran more than once today).")

    combined.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
    print(f"\nHistory file now has {len(combined)} total rows.")
else:
    print("\nNo jobs collected today (site may be blocking or down) -- nothing appended.")