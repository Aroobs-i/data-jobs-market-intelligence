-- Top 15 skills by how many jobs mention them
SELECT s.skill_name, COUNT(*) AS job_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
GROUP BY s.skill_name
ORDER BY job_count DESC
LIMIT 15;