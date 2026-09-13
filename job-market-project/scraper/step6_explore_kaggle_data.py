# step6_explore_kaggle_data.py
# Goal: load the big dataset and actually LOOK at it before assuming anything
# about its structure. This is always the first real step of any analysis --
# never assume, always inspect.

import pandas as pd

# UPDATE this path to match whatever the main postings CSV is actually called
# after you extract the zip -- check your data/ folder and adjust if needed
df = pd.read_csv("../data/linkedin-job-postings/job_postings.csv")

print("=== SHAPE (rows, columns) ===")
print(df.shape)

print("\n=== COLUMN NAMES ===")
print(df.columns.tolist())

print("\n=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== DATA TYPES + MISSING VALUES ===")
print(df.info())

print("\n=== HOW MANY UNIQUE COMPANIES, LOCATIONS, TITLES? ===")
for col in ["company_name", "location", "title"]:
    if col in df.columns:
        print(f"{col}: {df[col].nunique()} unique values")