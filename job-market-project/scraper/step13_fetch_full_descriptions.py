# step13_fetch_full_descriptions.py
# Goal: our search-results scrape only got short truncated snippets.
# Now we visit each job's own detail page to get the FULL description,
# which should actually contain real skill mentions.

import pandas as pd
import time
from step4_resilient_scraper import fetch_rendered_html
from bs4 import BeautifulSoup

pk_df = pd.read_csv("../data/rozee_data_analyst_jobs.csv")
print(f"Fetching full descriptions for {len(pk_df)} Pakistan jobs...")

full_descriptions = []

for i, row in pk_df.iterrows():
    print(f"\n[{i+1}/{len(pk_df)}] Fetching: {row['title'][:50]}...")
    html = fetch_rendered_html(row["link"], max_attempts=2, wait_for_selector=None)

    if html is None:
        print("  Failed to load, skipping.")
        full_descriptions.append("")
        continue

    soup = BeautifulSoup(html, "html.parser")
    # NOTE: we don't know the exact class name for the detail page's
    # description block yet -- this is a reasonable guess based on common
    # patterns. If this comes back empty, we'll inspect a real detail page
    # in DevTools together, same as we did for the search results page.
    desc_div = soup.find("div", class_="job-detail") or soup.find("section", id="job-description")

    if desc_div:
        text = desc_div.get_text(separator=" ", strip=True)
    else:
        # Fallback: grab the whole page's visible text so we at least have
        # SOMETHING to check, even if it's not perfectly isolated
        text = soup.get_text(separator=" ", strip=True)

    full_descriptions.append(text)
    print(f"  Got {len(text)} characters")

    time.sleep(2)  # be polite between requests

pk_df["full_description"] = full_descriptions
pk_df.to_csv("../data/rozee_data_analyst_jobs_full.csv", index=False, encoding="utf-8-sig")
print("\nSaved to ../data/rozee_data_analyst_jobs_full.csv")