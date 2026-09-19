# app.py
# The dashboard. Run with: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

st.set_page_config(
    page_title="Data Analytics Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- DATABASE ---
# Works both locally (.env file) and on Streamlit Cloud (st.secrets) --
# st.secrets is how Streamlit Cloud securely stores credentials without
# ever putting them in your GitHub repo.
if hasattr(st, "secrets") and "DB_HOST" in st.secrets:
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
    db_user = st.secrets["DB_USER"]
    db_password = st.secrets["DB_PASSWORD"]
else:
    load_dotenv("../.env")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require",
    pool_pre_ping=True,
)

@st.cache_data(ttl=3600)  # refresh from the database every hour, not just on app restart
def load_jobs():
    return pd.read_sql("""
        SELECT j.job_id, j.source, j.job_title, j.job_level, j.job_type, j.first_seen,
               c.company_name, l.city, l.country
        FROM jobs j
        LEFT JOIN companies c ON j.company_id = c.company_id
        LEFT JOIN locations l ON j.location_id = l.location_id
    """, engine)

@st.cache_data(ttl=3600)
def load_skills():
    return pd.read_sql("""
        SELECT j.job_id, j.source, s.skill_name
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.skill_id
        JOIN jobs j ON js.job_id = j.job_id
    """, engine)

jobs_df = load_jobs()
skills_df = load_skills()

@st.cache_data(ttl=3600)
def load_pk_raw():
    # Now reads directly from the database instead of a local CSV file --
    # this is what makes the dashboard actually reflect new daily scrapes
    # automatically, since daily_scrape.py writes straight to this database.
    return pd.read_sql("""
        SELECT search_term, first_seen AS scraped_date
        FROM jobs
        WHERE source = 'pakistan_live'
    """, engine)

pk_raw_df = load_pk_raw()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT_COLORS = ["#4fc3f7", "#ff9800", "#66bb6a", "#ef5350", "#ab47bc"]

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filters")
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
source_choice = st.sidebar.radio("Data Source", ["All", "Pakistan (live)", "Global (LinkedIn)"])
source_map = {"All": None, "Pakistan (live)": "pakistan_live", "Global (LinkedIn)": "global_linkedin"}
selected_source = source_map[source_choice]

if selected_source:
    filtered_jobs = jobs_df[jobs_df["source"] == selected_source]
    filtered_skills = skills_df[skills_df["source"] == selected_source]
else:
    filtered_jobs = jobs_df
    filtered_skills = skills_df

# --- HEADER ---
st.title("📊 Data Analytics Job Market Intelligence")
st.caption("Live-updating analysis of data & analytics roles, benchmarked against the global market")

# --- KPI CARDS (native Streamlit metrics -- clean, no custom HTML/CSS needed) ---
kpi_cols = st.columns(4)
kpi_cols[0].metric("Total Jobs", f"{len(filtered_jobs):,}")
kpi_cols[1].metric("Unique Companies", f"{filtered_jobs['company_name'].nunique():,}")
kpi_cols[2].metric("Unique Cities", f"{filtered_jobs['city'].nunique():,}")
kpi_cols[3].metric("Skills Tracked", f"{filtered_skills['skill_name'].nunique():,}")

st.write("")

# --- TABBED LAYOUT ---
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🛠 Skills", "🏢 Companies & Geography", "🇵🇰 Pakistan vs Global"])

with tab1:
    if selected_source == "pakistan_live":
        # Global-only fields (job_type, job_level) don't exist for Pakistan.
        # Show what we DO have and what's actually meaningful: which search
        # terms are surfacing jobs, and how postings are accumulating over
        # time thanks to the daily scraper.
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Postings by Search Term")
            if "search_term" in pk_raw_df.columns:
                term_counts = pk_raw_df["search_term"].value_counts().reset_index()
                term_counts.columns = ["search_term", "count"]
                fig = px.bar(term_counts, x="count", y="search_term", orientation="h",
                             color="count", color_continuous_scale="Blues", template=PLOTLY_TEMPLATE)
                fig.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Search term data not available.")
        with col_b:
            st.subheader("Postings Collected Over Time")
            if "scraped_date" in pk_raw_df.columns:
                daily_counts = pk_raw_df.groupby("scraped_date").size().reset_index(name="new_postings")
                # Treat dates as discrete category labels, not a continuous
                # timeline -- with only a few days of data, a continuous
                # datetime axis produces nonsense sub-second tick marks
                daily_counts["scraped_date"] = daily_counts["scraped_date"].astype(str)
                fig = px.bar(daily_counts, x="scraped_date", y="new_postings",
                             color_discrete_sequence=["#4fc3f7"], template=PLOTLY_TEMPLATE)
                fig.update_xaxes(type="category")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("This grows automatically each day the scheduled scraper runs.")
            else:
                st.info("Date tracking not available.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Job Type Distribution")
            type_counts = filtered_jobs["job_type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            fig = px.pie(type_counts, values="count", names="type", hole=0.5,
                         template=PLOTLY_TEMPLATE, color_discrete_sequence=ACCENT_COLORS)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Job Level Distribution")
            level_counts = filtered_jobs["job_level"].value_counts().reset_index()
            level_counts.columns = ["level", "count"]
            fig = px.pie(level_counts, values="count", names="level", hole=0.5,
                         template=PLOTLY_TEMPLATE, color_discrete_sequence=ACCENT_COLORS)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Postings by Country")
    # A simple bar chart, not a map -- with only a handful of countries in
    # this data, a bar chart reads cleanly. A world map/treemap either looks
    # mostly empty or (with many small cities) turns into unreadable clutter.
    country_counts = filtered_jobs["country"].dropna()
    country_counts = country_counts[country_counts != ""].value_counts().reset_index()
    country_counts.columns = ["country", "count"]
    fig_country = px.bar(country_counts, x="country", y="count", color="count",
                          color_continuous_scale="Blues", template=PLOTLY_TEMPLATE)
    st.plotly_chart(fig_country, use_container_width=True)

with tab2:
    st.subheader("Top In-Demand Skills")
    all_skills_sorted = filtered_skills["skill_name"].value_counts().index.tolist()
    skill_count = st.slider("Number of top skills to show", 5, 30, 15)
    top_skills = filtered_skills["skill_name"].value_counts().head(skill_count).reset_index()
    top_skills.columns = ["skill", "count"]
    fig = px.bar(top_skills, x="count", y="skill", orientation="h",
                 color="count", color_continuous_scale="Blues", template=PLOTLY_TEMPLATE)
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Skill Categories")
    category_map = {
        "SQL": "Programming", "Python": "Programming", "R": "Programming", "Java": "Programming", "VBA": "Programming",
        "Tableau": "Visualization", "Power BI": "Visualization", "Data Visualization": "Visualization",
        "AWS": "Cloud", "Azure": "Cloud", "GCP": "Cloud",
        "Machine Learning": "ML/AI", "Data Science": "ML/AI", "Statistics": "ML/AI",
        "Communication": "Soft Skills", "Teamwork": "Soft Skills", "Collaboration": "Soft Skills",
        "Leadership": "Soft Skills", "Problem Solving": "Soft Skills",
        "Excel": "Business Tools", "Project Management": "Business Tools",
    }
    cat_df = filtered_skills.copy()
    cat_df["category"] = cat_df["skill_name"].map(category_map).fillna("Other")
    cat_df = cat_df[cat_df["category"] != "Other"]
    cat_counts = cat_df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(cat_counts, x="category", y="count", color="category",
                 color_discrete_sequence=ACCENT_COLORS, template=PLOTLY_TEMPLATE)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top 10 Hiring Companies")
        top_companies = filtered_jobs["company_name"].value_counts().head(10).reset_index()
        top_companies.columns = ["company", "count"]
        fig = px.bar(top_companies, x="count", y="company", orientation="h",
                     color="count", color_continuous_scale="Oranges", template=PLOTLY_TEMPLATE)
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Top 10 Cities")
        city_series = filtered_jobs["city"].dropna()
        city_series = city_series[city_series.str.strip() != ""]
        top_cities = city_series.value_counts().head(10).reset_index()
        top_cities.columns = ["city", "count"]
        if not top_cities.empty:
            fig = px.bar(top_cities, x="count", y="city", orientation="h",
                         color="count", color_continuous_scale="Greens", template=PLOTLY_TEMPLATE)
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No city data available for this source.")

with tab4:
    st.subheader("Skill Demand: Pakistan vs Global (% of each source's postings)")
    job_counts_per_source = jobs_df.groupby("source")["job_id"].nunique()
    skill_pct = (
        skills_df.groupby(["source", "skill_name"])["job_id"].nunique().reset_index(name="jobs_with_skill")
    )
    skill_pct["total_jobs"] = skill_pct["source"].map(job_counts_per_source)
    skill_pct["pct"] = (skill_pct["jobs_with_skill"] / skill_pct["total_jobs"] * 100).round(1)

    key_skills = ["SQL", "Python", "Excel", "Power BI", "Tableau", "Machine Learning"]
    compare_df = skill_pct[skill_pct["skill_name"].isin(key_skills)]

    fig = px.bar(compare_df, x="skill_name", y="pct", color="source", barmode="group",
                 labels={"pct": "% of Postings", "skill_name": ""},
                 color_discrete_sequence=["#4fc3f7", "#ff9800"], template=PLOTLY_TEMPLATE)
    st.plotly_chart(fig, use_container_width=True)

    st.info("💡 **Key insight**: Pakistan's data-analyst market leans heavily on Excel and Power BI, "
            "while the global market has shifted decisively toward SQL, Python, and Machine Learning.")

st.divider()

# --- INTERACTIVE DATA EXPLORER (real interactivity: live search + sortable table) ---
with st.expander("🔎 Explore the raw job data"):
    search_term = st.text_input("Search by job title or company")
    display_df = filtered_jobs[["job_title", "company_name", "city", "country", "job_level", "job_type"]]
    if search_term:
        mask = (
            display_df["job_title"].str.contains(search_term, case=False, na=False)
            | display_df["company_name"].str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=350)
    st.caption(f"Showing {len(display_df):,} of {len(filtered_jobs):,} jobs — click any column header to sort.")

st.caption("Data sources: live-scraped Rozee.pk postings (auto-updates daily via scheduled scraper) "
           "+ 1.3M-row global LinkedIn dataset (Kaggle)")
