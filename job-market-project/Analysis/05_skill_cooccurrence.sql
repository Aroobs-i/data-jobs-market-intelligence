-- 05_skill_cooccurrence.sql
-- Goal: which skills most often appear TOGETHER in the same job posting?
-- (e.g. "jobs that want SQL also frequently want Python") -- useful for
-- answering "what should I learn alongside X?"
-- Uses a SELF-JOIN: joining job_skills to itself to find skill PAIRS.

SELECT
    s1.skill_name AS skill_a,
    s2.skill_name AS skill_b,
    COUNT(*) AS jobs_requiring_both
FROM job_skills js1
JOIN job_skills js2
    ON js1.job_id = js2.job_id           -- same job...
    AND js1.skill_id < js2.skill_id      -- ...different skill, and avoid counting
                                          -- (A,B) and (B,A) as two separate pairs
JOIN skills s1 ON js1.skill_id = s1.skill_id
JOIN skills s2 ON js2.skill_id = s2.skill_id
WHERE s1.skill_name = 'SQL'  -- change this to explore pairings with any skill
GROUP BY s1.skill_name, s2.skill_name
ORDER BY jobs_requiring_both DESC
LIMIT 15;