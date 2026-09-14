# step10_top_skills_analysis.py
# Goal: turn "Python, SQL, Excel" (one string per job) into individual skill
# counts across ALL jobs -- i.e. answer "what skills actually show up most?"

import pandas as pd

df = pd.read_csv("../data/linkedin_data_roles_with_skills.csv")
print(f"Analyzing skills across {len(df)} jobs\n")

# Drop rows with no skill data at all before we start splitting
df = df.dropna(subset=["job_skills"])

# .str.split(",") turns "Python, SQL, Excel" into ["Python", " SQL", " Excel"]
# (a LIST inside each cell). We also strip whitespace off each skill.
df["skills_list"] = df["job_skills"].str.split(",").apply(
    lambda skills: [s.strip() for s in skills]
)

# .explode() takes a column of LISTS and turns it into one row PER item in
# the list, duplicating the other columns. This is exactly what we need:
# from "one row per job" to "one row per (job, skill) pair"
exploded = df.explode("skills_list")

# Fix inconsistent capitalization ("Data Analysis" vs "data analysis") WITHOUT
# breaking acronyms like "SQL" or "AWS" (which .title() would turn into "Sql"/"Aws").
# Instead: group by the lowercase version, and use whichever original casing
# was most common as the "canonical" display version for that skill.
exploded["skill_lower"] = exploded["skills_list"].str.lower()
canonical_casing = (
    exploded.groupby("skill_lower")["skills_list"]
    .agg(lambda x: x.value_counts().idxmax())  # most frequent original casing
)
exploded["skills_list"] = exploded["skill_lower"].map(canonical_casing)
print(f"After exploding: {len(exploded)} individual (job, skill) rows")

print("\n=== TOP 30 MOST IN-DEMAND SKILLS (global data/analytics roles) ===")
top_skills = exploded["skills_list"].value_counts().head(30)
print(top_skills)

# Save this for the dashboard later -- much easier to chart from a clean
# skill-count table than to re-parse the raw comma strings every time
top_skills.to_csv("../data/top_skills_global.csv", header=["count"])
print("\nSaved to ../data/top_skills_global.csv")

print("\n=== TOP 15 SKILLS SPECIFICALLY FOR 'DATA ANALYST' TITLES ===")
analyst_only = exploded[exploded["job_title"].str.contains("data analyst", case=False, na=False)]
print(f"({analyst_only['job_link'].nunique()} unique Data Analyst postings)")
print(analyst_only["skills_list"].value_counts().head(15))