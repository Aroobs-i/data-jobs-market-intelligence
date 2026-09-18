# step12_extract_pakistan_skills.py
# Goal: since Pakistan scraped data only has free-text descriptions (not a
# structured skills field like the global dataset), we extract skill mentions
# by checking each description against a known list of common data/analytics
# skills. Simple keyword matching -- honest and effective at this scale.

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import re

load_dotenv("../.env")
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
)

# A defined skill list to search for -- based on what showed up as common
# in the global dataset, so the comparison is apples-to-apples
SKILL_KEYWORDS = [
    "SQL", "Python", "Excel", "Tableau", "Power BI", "R", "Machine Learning",
    "Data Analysis", "Data Visualization", "Statistics", "AWS", "Azure",
    "Java", "Spark", "Data Engineering", "ETL", "Data Science",
    "Business Intelligence", "VBA", "Communication", "Project Management",
]

pk_df = pd.read_csv("../data/rozee_all_jobs_full.csv")
pk_df["best_description"] = pk_df["full_description"].fillna(pk_df["description"])
print(f"Checking {len(pk_df)} Pakistan job descriptions for skill mentions...")

pk_skill_rows = []
for _, row in pk_df.iterrows():
    description = str(row.get("best_description", ""))
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, description, re.IGNORECASE):
            pk_skill_rows.append({"link": row["link"], "skill_name": skill})

pk_skills_df = pd.DataFrame(pk_skill_rows, columns=["link", "skill_name"])
print(f"Found {len(pk_skills_df)} skill mentions across Pakistan postings")

if pk_skills_df.empty:
    print("No skill mentions found at all -- stopping here, nothing to load.")
    raise SystemExit

print("\nSkill mention counts:")
print(pk_skills_df["skill_name"].value_counts())

# --- Now link these to the existing jobs/skills tables in Postgres ---
with engine.connect() as conn:
    jobs_lookup = pd.read_sql("SELECT job_id, link FROM jobs WHERE source = 'pakistan_live'", conn)
    skills_lookup = pd.read_sql("SELECT skill_id, skill_name FROM skills", conn)

pk_skills_df = pk_skills_df.merge(jobs_lookup, on="link", how="inner")

# Some of our keywords (like "R" or "AWS") might not already exist in the
# skills table (since the global dataset may phrase things differently).
# We add any missing ones first.
existing_skill_names = set(skills_lookup["skill_name"].str.lower())
new_skills = [s for s in SKILL_KEYWORDS if s.lower() not in existing_skill_names]
if new_skills:
    next_id = skills_lookup["skill_id"].max() + 1
    new_skills_df = pd.DataFrame({
        "skill_id": range(next_id, next_id + len(new_skills)),
        "skill_name": new_skills,
    })
    new_skills_df.to_sql("skills", engine, if_exists="append", index=False)
    skills_lookup = pd.concat([skills_lookup, new_skills_df], ignore_index=True)
    print(f"Added {len(new_skills)} new skills to the skills table: {new_skills}")

# Match on lowercase to be safe, since casing might differ slightly
skills_lookup["skill_lower"] = skills_lookup["skill_name"].str.lower()
pk_skills_df["skill_lower"] = pk_skills_df["skill_name"].str.lower()
pk_skills_df = pk_skills_df.merge(
    skills_lookup[["skill_id", "skill_lower"]], on="skill_lower", how="inner"
)

final_job_skills = pk_skills_df[["job_id", "skill_id"]].drop_duplicates()
final_job_skills.to_sql("job_skills", engine, if_exists="append", index=False)
print(f"\nInserted {len(final_job_skills)} new job_skills rows for Pakistan postings")
