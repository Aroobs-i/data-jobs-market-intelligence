# step14_expand_pakistan_data.py
# Goal: combine our original 16 jobs (which already have full descriptions
# from step13) with the new jobs from job_history.csv, fetching full
# descriptions ONLY for the ones we don't already have -- no wasted requests.

import pandas as pd
import time
from step4_resilient_scraper import fetch_rendered_html
from bs4 import BeautifulSoup

# All unique jobs collected so far (33 rows, from the daily scraper)
history_df = pd.read_csv("../data/job_history.csv")
history_df = history_df.drop_duplicates(subset="link", keep="first")
print(f"Total unique Pakistan jobs in history: {len(history_df)}")

# Jobs we ALREADY fetched full descriptions for (the original 16, from step13)
existing_full = pd.read_csv("../data/rozee_data_analyst_jobs_full.csv")
existing_full = existing_full[["link", "full_description"]]

# Merge: bring in full_description wherever we already have it
merged = history_df.merge(existing_full, on="link", how="left")

missing_mask = merged["full_description"].isna()
print(f"Already have full descriptions for {(~missing_mask).sum()} jobs")
print(f"Need to fetch full descriptions for {missing_mask.sum()} new jobs")

# Fetch full descriptions only for the missing ones
new_descriptions = {}
for idx, row in merged[missing_mask].iterrows():
    print(f"\nFetching: {row['title'][:50]}...")
    html = fetch_rendered_html(row["link"], max_attempts=2, wait_for_selector=None)

    if html is None:
        new_descriptions[row["link"]] = ""
        print("  Failed, leaving blank.")
        continue

    soup = BeautifulSoup(html, "html.parser")
    desc_div = soup.find("div", class_="job-detail") or soup.find("section", id="job-description")
    text = desc_div.get_text(separator=" ", strip=True) if desc_div else soup.get_text(separator=" ", strip=True)
    new_descriptions[row["link"]] = text
    print(f"  Got {len(text)} characters")
    time.sleep(3)

# Fill in the newly-fetched descriptions
for link, text in new_descriptions.items():
    merged.loc[merged["link"] == link, "full_description"] = text

merged.to_csv("../data/rozee_all_jobs_full.csv", index=False, encoding="utf-8-sig")
print(f"\nSaved {len(merged)} total Pakistan jobs (with full descriptions where available) to ../data/rozee_all_jobs_full.csv")