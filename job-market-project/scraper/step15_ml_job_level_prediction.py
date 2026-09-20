# step15_ml_job_level_prediction.py
# Goal: My first real ML model. Question: can we predict whether a job is
# "Associate" or "Mid senior" level JUST from which skills it lists?
# This teaches the core ML workflow: features -> train/test split -> model
# -> evaluation -> interpretation. We use Logistic Regression -- simple,
# fast, and (importantly for a beginner) its results are directly readable:
# each skill gets a coefficient telling you exactly how it pushes the
# prediction toward "senior" or "associate".

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

load_dotenv("../.env")
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require",
    pool_pre_ping=True,
)

# --- STEP 1: GET THE DATA ---
# We only use global_linkedin jobs here, since Pakistan postings don't have
# job_level labels -- ML needs labeled examples to learn from.
print("Loading data...")
jobs = pd.read_sql("""
    SELECT job_id, job_level FROM jobs
    WHERE source = 'global_linkedin' AND job_level IS NOT NULL
""", engine)

skills = pd.read_sql("""
    SELECT js.job_id, s.skill_name
    FROM job_skills js
    JOIN skills s ON js.skill_id = s.skill_id
    JOIN jobs j ON js.job_id = j.job_id
    WHERE j.source = 'global_linkedin'
""", engine)

print(f"{len(jobs)} labeled jobs, {jobs['job_level'].value_counts().to_dict()}")

# --- STEP 2: TURN SKILLS INTO FEATURES (this is the key ML concept here) ---
# A model can't understand text like "Python" -- it needs numbers.
# We pick the top 40 most common skills and create ONE COLUMN PER SKILL,
# where 1 = "this job requires this skill", 0 = "it doesn't".
# This is called "one-hot encoding" -- turning categories into binary columns.
top_skills = skills["skill_name"].value_counts().head(40).index.tolist()
skills_filtered = skills[skills["skill_name"].isin(top_skills)]

# pivot_table reshapes "one row per (job, skill)" into "one row per job,
# one column per skill" -- exactly the wide format models need
feature_matrix = pd.crosstab(skills_filtered["job_id"], skills_filtered["skill_name"])
feature_matrix = (feature_matrix > 0).astype(int)  # 1 if present, 0 if not

# Join features with labels, keeping only jobs that have both
data = jobs.set_index("job_id").join(feature_matrix, how="inner").fillna(0)

X = data[top_skills]  # the FEATURES (inputs): which skills each job has
y = (data["job_level"] == "Mid senior").astype(int)  # the LABEL (what we predict): 1 = Mid senior, 0 = Associate

print(f"\nFinal dataset: {len(X)} jobs, {X.shape[1]} skill features")
print(f"Class balance: {y.mean()*100:.1f}% are Mid senior")

# --- STEP 3: TRAIN/TEST SPLIT ---
# We NEVER train and test on the same data -- that would be like grading a
# student on the exact questions they memorized answers to. We hold out 20%
# of the data the model never sees during training, purely for evaluation.
# stratify=y keeps the same class balance in both sets.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTraining on {len(X_train)} jobs, testing on {len(X_test)} jobs")

# --- STEP 4: TRAIN THE MODEL ---
# class_weight='balanced' matters here: ~89% of jobs are "Mid senior", so a
# lazy model could get 89% accuracy by just ALWAYS guessing "Mid senior" and
# never actually learning anything. This setting forces it to pay real
# attention to the minority class (Associate) too.
model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(X_train, y_train)

# --- STEP 5: EVALUATE ---
predictions = model.predict(X_test)
print(f"\nAccuracy: {accuracy_score(y_test, predictions):.2%}")
print("\nFull report (precision/recall matter more than accuracy given the imbalance):")
print(classification_report(y_test, predictions, target_names=["Associate", "Mid senior"]))

# --- STEP 6: INTERPRET IT -- which skills predict which level? ---
# Logistic Regression gives each feature a "coefficient". Positive = pushes
# toward Mid senior. Negative = pushes toward Associate. This is the
# genuinely interesting, explainable part -- not just a black-box prediction.
coefficients = pd.Series(model.coef_[0], index=top_skills).sort_values()

print("\n=== Top 10 skills that signal ASSOCIATE-level ===")
print(coefficients.head(10))

print("\n=== Top 10 skills that signal MID-SENIOR-level ===")
print(coefficients.tail(10))