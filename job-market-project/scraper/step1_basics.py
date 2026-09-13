# step1_basics.py
# Goal: understand variables, strings, and functions using OUR project's actual data

# A variable just stores a value with a name you choose
job_title = "Data Analyst"
company = "Systems Limited"
city = "Rawalpindi"
salary_min = 60000
salary_max = 90000

# f-strings (the f before the quote) let you drop variables straight into text
print(f"Found job: {job_title} at {company} in {city}")
print(f"Salary range: PKR {salary_min} - {salary_max}")

# A function is a reusable block of code. Here's one that formats a job posting
def format_job(title, company, city, salary_min, salary_max):
    return f"{title} | {company} | {city} | PKR {salary_min}-{salary_max}"

# Now let's use it on a few different job postings (this is a list of dictionaries -
# a very common way to hold structured data in Python before it becomes a table)
jobs = [
    {"title": "Data Analyst", "company": "Systems Limited", "city": "Lahore", "min": 60000, "max": 90000},
    {"title": "Junior Data Scientist", "company": "Afiniti", "city": "Islamabad", "min": 80000, "max": 120000},
    {"title": "BI Analyst", "company": "Netsol", "city": "Karachi", "min": 70000, "max": 100000},
]

for job in jobs:
    print(format_job(job["title"], job["company"], job["city"], job["min"], job["max"]))