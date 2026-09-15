# step6_explore_kaggle_data.py
# Goal: load the big dataset and actually LOOK at it before assuming anything
# about its structure. This is always the first real step of any analysis --
# never assume, always inspect.

import pandas as pd

# Note: these files sit directly in data/, no subfolder.
# job_summary.csv is 5.1GB -- we are deliberately NOT loading it yet,
# since loading a file that size all at once can eat all your RAM.
# We'll deal with it later, carefully, once we know we actually need it.

df = pd.read_csv("../data/linkedin_job_postings.csv")

print("=== SHAPE (rows, columns) ===")
print(df.shape)

print("\n=== COLUMN NAMES ===")
print(df.columns.tolist())

print("\n=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== DATA TYPES + MISSING VALUES ===")
print(df.info())

print("\n=== HOW MANY UNIQUE COMPANIES, LOCATIONS, TITLES? ===")
for col in ["company", "job_location", "job_title"]:
    if col in df.columns:
        print(f"{col}: {df[col].nunique()} unique values")

print("\n=== TOP 15 SEARCH COUNTRIES (by row count) ===")
print(df["search_country"].value_counts().head(15))

print("\n=== HOW MANY ROWS ARE PAKISTAN-RELATED? ===")
pakistan_rows = df[df["search_country"].str.contains("Pakistan", case=False, na=False)]
print(f"Rows where search_country contains 'Pakistan': {len(pakistan_rows)}")

# Also check job_location text itself, in case some non-Pakistan-searched
# rows still happen to be located in Pakistan
pakistan_location_rows = df[df["job_location"].str.contains("Pakistan", case=False, na=False)]
print(f"Rows where job_location contains 'Pakistan': {len(pakistan_location_rows)}")
