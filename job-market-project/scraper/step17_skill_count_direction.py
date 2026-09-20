# step17_skill_count_direction.py
# Quick follow-up: total_skill_count was by far the most important feature --
# but which direction does it point? More skills -> more senior, or more
# skills -> more associate? A simple groupby answers this directly.

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv("../.env")
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require",
    pool_pre_ping=True,
)

jobs = pd.read_sql("""
    SELECT job_id, job_level FROM jobs
    WHERE source = 'global_linkedin' AND job_level IS NOT NULL
""", engine)
skills = pd.read_sql("""
    SELECT js.job_id, s.skill_name FROM job_skills js
    JOIN skills s ON js.skill_id = s.skill_id
    JOIN jobs j ON js.job_id = j.job_id WHERE j.source = 'global_linkedin'
""", engine)

skill_counts = skills.groupby("job_id").size().rename("total_skill_count")
data = jobs.set_index("job_id").join(skill_counts).fillna(0)

print("Average number of skills listed, by job level:")
print(data.groupby("job_level")["total_skill_count"].mean().round(1))
print("\nMedian (less sensitive to outlier postings with huge skill dumps):")
print(data.groupby("job_level")["total_skill_count"].median())