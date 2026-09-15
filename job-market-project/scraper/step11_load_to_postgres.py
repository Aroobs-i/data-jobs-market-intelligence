# step11_load_to_postgres.py
# Goal: create a normalized schema in PostgreSQL and load our two datasets
# (Pakistan live scrape + global filtered LinkedIn data) into it properly.

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# --- CONNECTION SETUP ---
# Credentials live in a .env file (never committed to git -- see .gitignore)
load_dotenv("../.env")  # adjust path if your .env is located elsewhere

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

print("Testing connection...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("Connected! PostgreSQL version:", result.fetchone()[0][:30])


# --- STEP 1: CREATE TABLES ---
# We write raw SQL here (not pandas) because CREATE TABLE with proper types,
# primary keys, and foreign keys is something SQL does directly and clearly.
create_tables_sql = """
DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS skills CASCADE;

CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL
);

CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY,
    city TEXT,
    country TEXT
);

CREATE TABLE skills (
    skill_id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE jobs (
    job_id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,          -- 'pakistan_live' or 'global_linkedin'
    job_title TEXT,
    company_id INTEGER REFERENCES companies(company_id),
    location_id INTEGER REFERENCES locations(location_id),
    job_level TEXT,
    job_type TEXT,
    first_seen DATE,
    link TEXT,
    description TEXT
);

CREATE TABLE job_skills (
    job_id INTEGER REFERENCES jobs(job_id),
    skill_id INTEGER REFERENCES skills(skill_id),
    PRIMARY KEY (job_id, skill_id)
);
"""

print("\nCreating tables (dropping old ones first if they exist)...")
with engine.begin() as conn:
    conn.execute(text(create_tables_sql))
print("Tables created.")


# --- STEP 2: LOAD AND STANDARDIZE BOTH DATASETS INTO ONE SHAPE ---
print("\nLoading source CSVs...")
pk_df = pd.read_csv("../data/rozee_all_jobs_full.csv")
global_df = pd.read_csv("../data/linkedin_data_roles_with_skills.csv")

# Standardize Pakistan data to match our target jobs table shape.
# Prefer the full description; fall back to the short snippet if a full
# fetch ever failed for a particular job.
pk_df["best_description"] = pk_df["full_description"].fillna(pk_df["description"])

pk_jobs = pd.DataFrame({
    "source": "pakistan_live",
    "job_title": pk_df["title"],
    "company_name": pk_df["company"],
    "city": pk_df["city"],
    "country": "Pakistan",
    "job_level": None,
    "job_type": None,
    "first_seen": pd.to_datetime(pk_df.get("scraped_date"), errors="coerce").dt.date,
    "link": pk_df["link"],
    "description": pk_df["best_description"],
})

# Standardize global data. job_location is like "New Haven, CT" -- we split
# on the comma to separate city from state/region.
global_df["city_parsed"] = global_df["job_location"].str.split(",").str[0].str.strip()

global_jobs = pd.DataFrame({
    "source": "global_linkedin",
    "job_title": global_df["job_title"],
    "company_name": global_df["company"],
    "city": global_df["city_parsed"],
    "country": global_df["search_country"],
    "job_level": global_df["job_level"],
    "job_type": global_df["job_type"],
    "first_seen": pd.to_datetime(global_df["first_seen"], errors="coerce").dt.date,
    "link": global_df["job_link"],
    "description": None,  # we don't have long descriptions for these
})

# Stack both into ONE combined jobs dataframe
all_jobs = pd.concat([pk_jobs, global_jobs], ignore_index=True)
all_jobs["job_id"] = all_jobs.index  # simple sequential ID, 0, 1, 2, ...
print(f"Combined {len(all_jobs)} total jobs ({len(pk_jobs)} Pakistan + {len(global_jobs)} global)")


# --- STEP 3: BUILD DIMENSION TABLES (companies, locations) ---
# pd.factorize() is a clean trick: it takes a column of repeated text values
# and returns (a) a numeric ID for each row, and (b) the list of unique
# values in the order the IDs reference them. That's EXACTLY what we need
# to build a foreign-key relationship.

print("\nBuilding companies table...")
company_codes, company_uniques = pd.factorize(all_jobs["company_name"].fillna("Unknown"))
all_jobs["company_id"] = company_codes
companies_df = pd.DataFrame({
    "company_id": range(len(company_uniques)),
    "company_name": company_uniques,
})
print(f"{len(companies_df)} unique companies")

print("Building locations table...")
# Combine city+country into one key so "Lahore, Pakistan" is distinct from
# any other "Lahore" elsewhere, then factorize that combined key.
location_key = all_jobs["city"].fillna("Unknown").astype(str) + "|" + all_jobs["country"].fillna("Unknown").astype(str)
location_codes, location_uniques = pd.factorize(location_key)
all_jobs["location_id"] = location_codes
locations_df = pd.DataFrame({
    "location_id": range(len(location_uniques)),
    "city": [u.split("|")[0] for u in location_uniques],
    "country": [u.split("|")[1] for u in location_uniques],
})
print(f"{len(locations_df)} unique locations")


# --- STEP 4: BUILD SKILLS + JOB_SKILLS TABLES (global data only, for now) ---
print("\nBuilding skills tables...")
skills_source = global_df.dropna(subset=["job_skills"]).copy()
skills_source["skills_list"] = skills_source["job_skills"].str.split(",").apply(
    lambda s: [x.strip() for x in s]
)
exploded_skills = skills_source[["job_link", "skills_list"]].explode("skills_list")
exploded_skills = exploded_skills.rename(columns={"skills_list": "skill_name"})

# Same fix as step10: normalize casing WITHOUT breaking acronyms like SQL/AWS.
# Group by lowercase, use whichever original casing was most common as canonical.
exploded_skills["skill_lower"] = exploded_skills["skill_name"].str.lower().str.strip()
canonical_casing = (
    exploded_skills.groupby("skill_lower")["skill_name"]
    .agg(lambda x: x.value_counts().idxmax())
)
exploded_skills["skill_name"] = exploded_skills["skill_lower"].map(canonical_casing)

# Force well-known acronyms to display correctly, regardless of which casing
# happened to be most common in the raw data
acronym_overrides = {
    "sql": "SQL", "aws": "AWS", "gcp": "GCP", "bi": "BI", "ai": "AI",
    "ml": "ML", "api": "API", "etl": "ETL", "r": "R", "css": "CSS",
    "html": "HTML", "vba": "VBA", "nosql": "NoSQL",
}
exploded_skills["skill_name"] = exploded_skills["skill_lower"].map(
    lambda x: acronym_overrides.get(x, canonical_casing.get(x, x))
)

skill_codes, skill_uniques = pd.factorize(exploded_skills["skill_name"])
exploded_skills["skill_id"] = skill_codes
skills_df = pd.DataFrame({
    "skill_id": range(len(skill_uniques)),
    "skill_name": skill_uniques,
})
print(f"{len(skills_df)} unique skills")

# Map job_link back to our new job_id so job_skills can reference the right job
link_to_job_id = all_jobs.set_index("link")["job_id"]
exploded_skills["job_id"] = exploded_skills["job_link"].map(link_to_job_id)
job_skills_df = exploded_skills[["job_id", "skill_id"]].dropna().drop_duplicates()
job_skills_df["job_id"] = job_skills_df["job_id"].astype(int)
print(f"{len(job_skills_df)} job-skill relationships")


# --- STEP 5: WRITE EVERYTHING TO POSTGRES ---
print("\nWriting to PostgreSQL...")
companies_df.to_sql("companies", engine, if_exists="append", index=False)
locations_df.to_sql("locations", engine, if_exists="append", index=False)
skills_df.to_sql("skills", engine, if_exists="append", index=False)

jobs_final = all_jobs[["job_id", "source", "job_title", "company_id", "location_id",
                       "job_level", "job_type", "first_seen", "link", "description"]]
jobs_final.to_sql("jobs", engine, if_exists="append", index=False)

job_skills_df.to_sql("job_skills", engine, if_exists="append", index=False)

print("\nAll done! Tables loaded:")
print(f"  companies: {len(companies_df)} rows")
print(f"  locations: {len(locations_df)} rows")
print(f"  skills: {len(skills_df)} rows")
print(f"  jobs: {len(jobs_final)} rows")
print(f"  job_skills: {len(job_skills_df)} rows")