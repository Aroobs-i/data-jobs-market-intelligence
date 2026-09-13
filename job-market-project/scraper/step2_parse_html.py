# step2_parse_html.py
# Goal: learn how to pull structured data out of raw HTML using BeautifulSoup

from bs4 import BeautifulSoup

# Normally you'd get this HTML from the internet using requests.get(url).text
# For now we're reading it from a local file so we can practice safely
with open("../data/sample_jobs_page.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# BeautifulSoup turns that raw text into a structure we can search through
soup = BeautifulSoup(html_content, "html.parser")

# find_all() looks for every tag matching what you ask for.
# Here: every <div> with class="job-listing" -- i.e. every job posting on the page
job_listings = soup.find_all("div", class_="job-listing")

print(f"Found {len(job_listings)} job postings on this page\n")

# This list will hold our clean data -- exactly like the 'jobs' list from step1
all_jobs = []

for listing in job_listings:
    # .find() looks for ONE specific tag inside this listing
    # .text.strip() gets the visible text and removes extra whitespace
    title = listing.find("h2", class_="job-title").text.strip()
    company = listing.find("span", class_="company").text.strip()
    city = listing.find("span", class_="city").text.strip()
    salary = listing.find("span", class_="salary").text.strip()
    skills = listing.find("p", class_="skills").text.strip()

    job_data = {
        "title": title,
        "company": company,
        "city": city,
        "salary": salary,
        "skills": skills,
    }
    all_jobs.append(job_data)
    print(job_data)

print(f"\nTotal jobs collected: {len(all_jobs)}")