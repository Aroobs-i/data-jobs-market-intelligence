-- Top 10 companies by number of postings, with their city
SELECT c.company_name, l.city, COUNT(*) AS posting_count
FROM jobs j
JOIN companies c ON j.company_id = c.company_id
JOIN locations l ON j.location_id = l.location_id
GROUP BY c.company_name, l.city
ORDER BY posting_count DESC
LIMIT 10;