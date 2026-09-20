# step16_ml_improved.py
# Goal: two real improvements over step15, done honestly (compared side by
# side, not just assumed to be better):
# 1. A new feature: how many skills TOTAL does each posting list? (not just
#    whether specific top-40 skills appear)
# 2. A second, more powerful model type: Random Forest, which can capture
#    non-linear patterns and skill INTERACTIONS that Logistic Regression
#    can't (e.g. "Python AND Cloud together" mattering more than either alone)

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score

load_dotenv("../.env")
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require",
    pool_pre_ping=True,
)

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

# --- NEW FEATURE: total skill count per job (using ALL skills, not just top 40) ---
skill_counts = skills.groupby("job_id").size().rename("total_skill_count")

# --- Same top-40 one-hot skill features as before ---
top_skills = skills["skill_name"].value_counts().head(40).index.tolist()
skills_filtered = skills[skills["skill_name"].isin(top_skills)]
feature_matrix = pd.crosstab(skills_filtered["job_id"], skills_filtered["skill_name"])
feature_matrix = (feature_matrix > 0).astype(int)

# Combine: top-40 skill flags + total skill count, joined to labels
data = jobs.set_index("job_id").join(feature_matrix, how="inner").join(skill_counts).fillna(0)

feature_columns = top_skills + ["total_skill_count"]
X = data[feature_columns]
y = (data["job_level"] == "Mid senior").astype(int)

print(f"Dataset: {len(X)} jobs, {X.shape[1]} features (40 skills + skill count)")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- MODEL 1: Logistic Regression (same as before, but with the new feature) ---
log_model = LogisticRegression(max_iter=1000, class_weight="balanced")
log_model.fit(X_train, y_train)
log_preds = log_model.predict(X_test)
log_f1 = f1_score(y_test, log_preds, average="macro")

print("\n=== Logistic Regression (with skill count added) ===")
print(classification_report(y_test, log_preds, target_names=["Associate", "Mid senior"]))

# --- MODEL 2: Random Forest ---
# A "forest" of many decision trees, each voting on the answer. Unlike
# Logistic Regression, it can naturally capture combinations of skills
# mattering together, not just each skill independently.
rf_model = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
rf_model.fit(X_train, y_train)
rf_preds = rf_model.predict(X_test)
rf_f1 = f1_score(y_test, rf_preds, average="macro")

print("\n=== Random Forest ===")
print(classification_report(y_test, rf_preds, target_names=["Associate", "Mid senior"]))

# --- HONEST COMPARISON ---
print(f"\n=== COMPARISON ===")
print(f"Logistic Regression macro F1: {log_f1:.3f}")
print(f"Random Forest macro F1:       {rf_f1:.3f}")
print(f"Winner: {'Random Forest' if rf_f1 > log_f1 else 'Logistic Regression'}")

# --- Random Forest feature importance (different from Logistic Regression's
# coefficients -- these are UNSIGNED, just "how much this feature mattered
# overall", not which direction it pushes) ---
importances = pd.Series(rf_model.feature_importances_, index=feature_columns).sort_values(ascending=False)
print("\n=== Top 10 most important features (Random Forest) ===")
print(importances.head(10))