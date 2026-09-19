# daily_scrape.py
# Runs automatically once a day (Windows Task Scheduler) and writes new
# Pakistan job postings DIRECTLY to the cloud (Neon) database, so the
# deployed dashboard actually updates itself with no manual steps.
# Also keeps appending to the local job_history.csv as a backup/log.

from urllib.parse import quote
import time
import random
import re
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from step4_resilient_scraper import fetch_rendered_html, parse_job_listings

SEARCH_TERMS = ["Data Analyst", "Data Scientist", "Business Analyst", "Power BI", "Data Engineer"]
HISTORY_FILE = "../data/job_history.csv"
today = date.today().isoformat()

# Same skill keyword list used in step12, kept in sync for consistent extraction
SKILL_KEYWORDS = [
    "SQL", "Python", "Excel", "Tableau", "Power BI", "R", "Machine Learning",
    "Data Analysis", "Data Visualization", "Statistics", "AWS", "Azure",
    "Java", "Spark", "Data Engineering", "ETL", "Data Science",
    "Business Intelligence", "VBA", "Communication", "Project Management",
]

# --- SCRAPE TODAY'S JOBS (same as before) ---
all_jobs = []
for term in SEARCH_TERMS:
    encoded_term = quote(term)
    url = f"https://www.rozee.pk/job/jsearch/q/{encoded_term}/?fpn=0"
    print(f"Searching '{term}'...")
    html = fetch_rendered_html(url, max_attempts=2)
    if html is None:
        print(f"  Failed, skipping '{term}' for today.")
        continue
    jobs = parse_job_listings(html)
    for job in jobs:
        job["search_term"] = term
        job["scraped_date"] = today
    all_jobs.extend(jobs)
    print(f"  Got {len(jobs)} jobs")
    time.sleep(random.uniform(10, 18))

if not all_jobs:
    print("\nNo jobs collected today -- nothing to upload.")
    raise SystemExit

new_df = pd.DataFrame(all_jobs).drop_duplicates(subset=["link", "scraped_date"], keep="first")

# --- STILL keep the local CSV log as a backup/audit trail ---
try:
    existing = pd.read_csv(HISTORY_FILE)
    combined = pd.concat([existing, new_df], ignore_index=True)
except FileNotFoundError:
    combined = new_df
combined = combined.drop_duplicates(subset=["link", "scraped_date"], keep="first")
combined.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
print(f"Local history file updated: {len(combined)} total rows")

# --- NOW: upload today's NEW jobs directly to Neon ---
load_dotenv("../.env")
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require",
    pool_pre_ping=True,
)

with engine.connect() as conn:
    existing_links = pd.read_sql("SELECT link FROM jobs WHERE source = 'pakistan_live'", conn)["link"].tolist()

truly_new = new_df[~new_df["link"].isin(existing_links)].copy()
print(f"\n{len(truly_new)} of today's jobs are new to the database (rest already exist).")

if truly_new.empty:
    print("Nothing new to insert. Done.")
    raise SystemExit

with engine.begin() as conn:
    next_job_id = conn.execute(text("SELECT COALESCE(MAX(job_id), -1) + 1 FROM jobs")).scalar()

    for i, row in truly_new.reset_index(drop=True).iterrows():
        job_id = next_job_id + i

        result = conn.execute(
            text("SELECT company_id FROM companies WHERE company_name = :name"),
            {"name": row["company"]},
        ).fetchone()
        if result:
            company_id = result[0]
        else:
            company_id = conn.execute(text("SELECT COALESCE(MAX(company_id), -1) + 1 FROM companies")).scalar()
            conn.execute(
                text("INSERT INTO companies (company_id, company_name) VALUES (:id, :name)"),
                {"id": company_id, "name": row["company"]},
            )

        city = row.get("city") or "Unknown"
        result = conn.execute(
            text("SELECT location_id FROM locations WHERE city = :city AND country = 'Pakistan'"),
            {"city": city},
        ).fetchone()
        if result:
            location_id = result[0]
        else:
            location_id = conn.execute(text("SELECT COALESCE(MAX(location_id), -1) + 1 FROM locations")).scalar()
            conn.execute(
                text("INSERT INTO locations (location_id, city, country) VALUES (:id, :city, 'Pakistan')"),
                {"id": location_id, "city": city},
            )

        conn.execute(
            text("""INSERT INTO jobs (job_id, source, job_title, company_id, location_id,
                    first_seen, link, description, search_term)
                    VALUES (:job_id, 'pakistan_live', :title, :company_id, :location_id,
                    :first_seen, :link, :description, :search_term)
                    ON CONFLICT (link) DO NOTHING"""),
            {
                "job_id": job_id, "title": row["title"], "company_id": company_id,
                "location_id": location_id, "first_seen": row["scraped_date"],
                "link": row["link"], "description": row.get("description", ""),
                "search_term": row["search_term"],
            },
        )

        description = str(row.get("description", ""))
        for skill in SKILL_KEYWORDS:
            if re.search(r"\b" + re.escape(skill) + r"\b", description, re.IGNORECASE):
                result = conn.execute(
                    text("SELECT skill_id FROM skills WHERE skill_name = :name"), {"name": skill}
                ).fetchone()
                if result:
                    skill_id = result[0]
                else:
                    skill_id = conn.execute(text("SELECT COALESCE(MAX(skill_id), -1) + 1 FROM skills")).scalar()
                    conn.execute(
                        text("INSERT INTO skills (skill_id, skill_name) VALUES (:id, :name)"),
                        {"id": skill_id, "name": skill},
                    )
                conn.execute(
                    text("""INSERT INTO job_skills (job_id, skill_id) VALUES (:job_id, :skill_id)
                            ON CONFLICT DO NOTHING"""),
                    {"job_id": job_id, "skill_id": skill_id},
                )

print(f"\nUploaded {len(truly_new)} new jobs directly to the cloud database.")
print("The live dashboard will reflect this automatically -- no manual steps needed.")
