# step7_filter_data_roles.py
# Goal: this dataset has ~1.35M rows of EVERY job type. We only care about
# data/analytics-related roles, so we filter down using keyword matching
# on job_title -- this is a very common real-world data cleaning step.

import pandas as pd

df = pd.read_csv("../data/linkedin_job_postings.csv")
print(f"Starting with {len(df)} total rows (all job types)")

# Keywords that indicate a data/analytics-relevant role.
# We search case-insensitively, and .str.contains with a "|" (OR) pattern
# checks if ANY of these substrings appear in the title.
data_role_keywords = (
    r"data analyst|data scientist|business analyst|data engineer|"
    r"bi analyst|business intelligence|machine learning|ml engineer|"
    r"analytics|data science|reporting analyst"
)

mask = df["job_title"].str.contains(data_role_keywords, case=False, na=False, regex=True)
data_df = df[mask].copy()

print(f"Filtered down to {len(data_df)} data/analytics-related rows")
print(f"That's {len(data_df) / len(df) * 100:.2f}% of the full dataset")

print("\nTop 20 most common job titles in this filtered set:")
print(data_df["job_title"].value_counts().head(20))

print("\nBreakdown by country:")
print(data_df["search_country"].value_counts())

# Save this smaller, focused dataset -- much more manageable to work with
data_df.to_csv("../data/linkedin_data_roles_filtered.csv", index=False, encoding="utf-8-sig")
print(f"\nSaved filtered dataset to ../data/linkedin_data_roles_filtered.csv")