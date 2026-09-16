-- 08_company_hiring_depth.sql
-- Goal: which companies post the MOST jobs, and what's their most-requested
-- skill? Chains TWO CTEs together (one feeding into the next), plus a
-- window function -- a realistic "multi-step analysis in one query" example.

WITH company_job_counts AS (
    -- Step 1: how many postings does each company have?
    SELECT c.company_id, c.company_name, COUNT(*) AS posting_count
    FROM jobs j
    JOIN companies c ON j.company_id = c.company_id
    GROUP BY c.company_id, c.company_name
    HAVING COUNT(*) >= 3   -- only companies with real hiring volume, not one-offs
),
company_top_skill AS (
    -- Step 2: for those companies, find their single most-requested skill
    -- (this CTE uses the FIRST CTE as if it were a normal table)
    SELECT
        cjc.company_name,
        cjc.posting_count,
        s.skill_name,
        ROW_NUMBER() OVER (
            PARTITION BY cjc.company_name
            ORDER BY COUNT(*) DESC
        ) AS skill_rank
    FROM company_job_counts cjc
    JOIN jobs j ON j.company_id = cjc.company_id
    JOIN job_skills js ON js.job_id = j.job_id
    JOIN skills s ON js.skill_id = s.skill_id
    GROUP BY cjc.company_name, cjc.posting_count, s.skill_name
)
SELECT company_name, posting_count, skill_name AS top_requested_skill
FROM company_top_skill
WHERE skill_rank = 1
ORDER BY posting_count DESC
LIMIT 20;