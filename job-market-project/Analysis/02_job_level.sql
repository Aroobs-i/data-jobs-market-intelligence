-- Skill demand broken down by job level (Associate vs Mid-senior)
SELECT j.job_level, s.skill_name, COUNT(*) AS job_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
JOIN jobs j ON js.job_id = j.job_id
WHERE j.job_level IS NOT NULL
GROUP BY j.job_level, s.skill_name
ORDER BY j.job_level, job_count DESC;