-- 07_skill_categories.sql
-- Goal: group individual skills into broader categories (Programming,
-- Visualization, Cloud, Soft Skills, etc.) using CASE WHEN, then compare
-- category-level demand between Pakistan and Global.
-- Also demonstrates HAVING -- filtering on an AGGREGATE result, which
-- WHERE cannot do (WHERE filters rows before grouping; HAVING filters
-- groups after aggregation).

WITH categorized_skills AS (
    SELECT
        j.source,
        s.skill_name,
        CASE
            WHEN s.skill_name IN ('SQL', 'Python', 'R', 'Java', 'VBA') THEN 'Programming'
            WHEN s.skill_name IN ('Tableau', 'Power BI', 'Data Visualization') THEN 'Visualization'
            WHEN s.skill_name IN ('AWS', 'Azure', 'GCP', 'Cloud Computing') THEN 'Cloud'
            WHEN s.skill_name IN ('Machine Learning', 'Data Science', 'AI', 'Statistics') THEN 'ML/AI'
            WHEN s.skill_name IN ('Communication', 'Teamwork', 'Collaboration', 'Leadership', 'Problem Solving') THEN 'Soft Skills'
            WHEN s.skill_name IN ('Excel', 'Project Management') THEN 'Business Tools'
            ELSE 'Other'
        END AS skill_category
    FROM job_skills js
    JOIN skills s ON js.skill_id = s.skill_id
    JOIN jobs j ON js.job_id = j.job_id
)
SELECT source, skill_category, COUNT(*) AS mentions
FROM categorized_skills
WHERE skill_category != 'Other'   -- WHERE: filter rows before grouping
GROUP BY source, skill_category
HAVING COUNT(*) > 5               -- HAVING: filter AFTER grouping/aggregating
ORDER BY skill_category, source;