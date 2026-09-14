# step8_merge_skills.py
# Goal: attach actual skill requirements to our filtered data-role postings,
# using job_link as the shared key between the two files (this is exactly
# like a SQL JOIN, just done in pandas)

import pandas as pd

# Our filtered, relevant postings from step7
jobs_df = pd.read_csv("../data/linkedin_data_roles_filtered.csv")
print(f"Loaded {len(jobs_df)} filtered job postings")

# job_skills.csv is bigger (672MB) but still manageable to load fully
print("Loading job_skills.csv (this may take a bit, it's a big file)...")
skills_df = pd.read_csv("../data/job_skills.csv")
print(f"Loaded {len(skills_df)} total skill records")
print("Columns in job_skills.csv:", skills_df.columns.tolist())

# merge() is pandas' equivalent of a SQL JOIN.
# how="inner" means: keep only job_links that exist in BOTH dataframes
# (i.e. only our filtered data-roles, now with skills attached)
merged_df = jobs_df.merge(skills_df, on="job_link", how="inner")

print(f"\nAfter merging: {len(merged_df)} rows have matching skill data")
print(f"({len(merged_df)} out of {len(jobs_df)} filtered jobs had skill info available)")

print("\nSample of merged data:")
print(merged_df[["job_title", "company", "job_location"]].head())
if "job_skills" in merged_df.columns:
    print("\nExample skills entry:")
    print(merged_df["job_skills"].iloc[0])

merged_df.to_csv("../data/linkedin_data_roles_with_skills.csv", index=False, encoding="utf-8-sig")
print("\nSaved to ../data/linkedin_data_roles_with_skills.csv")