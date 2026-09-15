-- 04_top_skill_per_city.sql
-- Goal: for EACH city, find its single most in-demand skill.
-- This uses a WINDOW FUNCTION (RANK) -- a step up from simple GROUP BY,
-- and a very common "top N per group" interview question.

WITH skill_counts_by_city AS (
    -- First: count how many times each skill appears in each city
    SELECT
        l.city,
        s.skill_name,
        COUNT(*) AS mentions,
        RANK() OVER (
            PARTITION BY l.city           -- restart the ranking for each city
            ORDER BY COUNT(*) DESC        -- rank by mention count, highest first
        ) AS skill_rank
    FROM job_skills js
    JOIN skills s ON js.skill_id = s.skill_id
    JOIN jobs j ON js.job_id = j.job_id
    JOIN locations l ON j.location_id = l.location_id
    WHERE l.city IS NOT NULL AND l.city != 'Unknown'
    GROUP BY l.city, s.skill_name
)
-- Then: only keep rank 1 (the top skill) per city
SELECT city, skill_name, mentions
FROM skill_counts_by_city
WHERE skill_rank = 1
ORDER BY mentions DESC
LIMIT 25;