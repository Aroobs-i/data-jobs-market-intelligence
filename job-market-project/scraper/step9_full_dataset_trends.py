# step9_full_dataset_trends.py
# Goal: analyze the FULL 1.3M row dataset for broad, scale-level patterns
# (not filtered to data roles -- this is the "big picture" layer of the project)

import pandas as pd

df = pd.read_csv("../data/linkedin_job_postings.csv")
print(f"Analyzing the full dataset: {len(df)} rows\n")

print("=== JOB TYPE DISTRIBUTION (Onsite / Remote / Hybrid) ===")
print(df["job_type"].value_counts())
print("\nAs percentages:")
print((df["job_type"].value_counts(normalize=True) * 100).round(2))

print("\n=== JOB LEVEL DISTRIBUTION ===")
print(df["job_level"].value_counts())

print("\n=== POSTINGS OVER TIME ===")
# first_seen is currently just text (a string) -- we convert it to a real
# datetime so pandas can group by day/week/month properly
df["first_seen"] = pd.to_datetime(df["first_seen"], errors="coerce")
postings_by_day = df["first_seen"].dt.date.value_counts().sort_index()
print(f"Date range: {postings_by_day.index.min()} to {postings_by_day.index.max()}")
print("\nPostings per day (first 10 days):")
print(postings_by_day.head(10))

print("\n=== TOP 15 COMPANIES BY POSTING VOLUME (full dataset) ===")
print(df["company"].value_counts().head(15))

print("\n=== TOP 15 CITIES BY POSTING VOLUME (full dataset) ===")
print(df["search_city"].value_counts().head(15))