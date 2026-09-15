-- 06_pakistan_vs_global_percentage.sql
-- Goal: raw counts are misleading here -- Global has ~12,368 jobs, Pakistan
-- has ~16-33. A skill with 5 Pakistan mentions could be MORE significant
-- than 500 Global mentions, percentage-wise. We normalize to % of each
-- source's own job postings, so the comparison is actually fair.

WITH job_counts_per_source AS (
    -- Total jobs per source, needed as the denominator for percentages
    SELECT source, COUNT(*) AS total_jobs
    FROM jobs
    GROUP BY source
),
skill_counts_per_source AS (
    SELECT
        j.source,
        s.skill_name,
        COUNT(DISTINCT js.job_id) AS jobs_mentioning_skill
    FROM job_skills js
    JOIN skills s ON js.skill_id = s.skill_id
    JOIN jobs j ON js.job_id = j.job_id
    GROUP BY j.source, s.skill_name
)
SELECT
    sc.source,
    sc.skill_name,
    sc.jobs_mentioning_skill,
    jc.total_jobs,
    ROUND(100.0 * sc.jobs_mentioning_skill / jc.total_jobs, 1) AS pct_of_postings
FROM skill_counts_per_source sc
JOIN job_counts_per_source jc ON sc.source = jc.source
WHERE sc.skill_name IN ('SQL', 'Python', 'Excel', 'Power BI', 'Tableau', 'Machine Learning')
ORDER BY sc.skill_name, sc.source;