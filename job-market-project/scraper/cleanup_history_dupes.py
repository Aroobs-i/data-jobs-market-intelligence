# cleanup_history_dupes.py
# One-time fix: removes duplicate (link, scraped_date) rows that got into
# job_history.csv before we fixed the dedup bug in daily_scrape.py

import pandas as pd

df = pd.read_csv("../data/job_history.csv")
print(f"Before cleanup: {len(df)} rows")

df = df.drop_duplicates(subset=["link", "scraped_date"], keep="first")
print(f"After cleanup: {len(df)} rows")

df.to_csv("../data/job_history.csv", index=False, encoding="utf-8-sig")
print("Saved cleaned file.")