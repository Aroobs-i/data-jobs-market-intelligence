# step3_selenium_scraper.py
# Goal: use Selenium to load the JS-rendered page, then parse it like before

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup, NavigableString
import time

# Set up Chrome to run normally (visible) so you can watch it work the first time.
# Once we trust it, we can add options.add_argument("--headless=new") to hide the window.
options = Options()
options.page_load_strategy = "eager"  # move on once the HTML is ready, don't wait for every ad/tracker
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)  # fail fast instead of hanging for 120s

url = "https://www.rozee.pk/job/jsearch/q/Data%20Analyst"

try:
    driver.get(url)
except TimeoutException:
    # "eager" already got us the HTML we need even if some background stuff is still loading.
    # We catch this instead of crashing, and just continue.
    print("Page took a while (probably ads/trackers) - continuing anyway, we likely have what we need.")

# INTELLIGENT WAIT instead of a blind sleep: this checks the page every fraction of a
# second and continues the MOMENT the condition is true, instead of guessing a fixed delay.
# We wait for at least one job title (h3.s-18) to actually exist in the page.
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h3.s-18"))
    )
    print("Job listings detected on page - proceeding.")
except TimeoutException:
    print("Job listings never appeared within 20s.")
    print("Saving a screenshot and page snapshot so we can see what actually happened...")
    driver.save_screenshot("../data/debug_screenshot.png")
    with open("../data/debug_page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Saved ../data/debug_screenshot.png and ../data/debug_page_source.html")

# Now that the page is fully rendered, grab its HTML -- same as before, but now
# it contains the actual job data instead of an empty shell
html_content = driver.page_source

# Close the browser window, we have what we need
driver.quit()

# From here it's exactly what you already know from step2
soup = BeautifulSoup(html_content, "html.parser")

job_listings = soup.find_all("div", class_="job")
print(f"Found {len(job_listings)} job listings\n")

all_jobs = []

for listing in job_listings:
    # h3 with class "s-18" holds the title (in its "title" attribute AND inside <a><bdi>)
    title_tag = listing.find("h3", class_="s-18")
    if not title_tag:
        continue  # skip anything that doesn't match a real job card

    title = title_tag.get("title", "").strip()

    link_tag = title_tag.find("a")
    link = link_tag.get("href", "").strip() if link_tag else ""
    if link.startswith("//"):
        link = "https:" + link  # the site uses protocol-relative links

    # The company/city block looks like:
    # <div class="cname"><bdi class="float-left">
    #   <a>Company Name</a> "Multiple Cities" <a>", Pakistan"</a>
    # </bdi></div>
    # Company = text of the FIRST <a>. City = the loose text NOT inside any <a>.
    company = ""
    city = ""
    cname_div = listing.find("div", class_="cname")
    if cname_div:
        bdi_tag = cname_div.find("bdi", class_="float-left")
        if bdi_tag:
            links = bdi_tag.find_all("a")
            if links:
                company = links[0].get_text(strip=True).rstrip(",").strip()
            # NavigableString = raw text sitting directly in the tag, not inside a child tag.
            # This grabs the city text that sits BETWEEN the two <a> tags.
            loose_text = [t.strip() for t in bdi_tag.contents if isinstance(t, NavigableString)]
            city = " ".join(t for t in loose_text if t).strip(", ").strip()

    # Short description snippet, useful later for extracting mentioned skills
    description = ""
    jbody_div = listing.find("div", class_="jbody")
    if jbody_div:
        bdi_desc = jbody_div.find("bdi")
        if bdi_desc:
            description = bdi_desc.get_text(strip=True)

    job_data = {
        "title": title,
        "company": company,
        "city": city,
        "description": description,
        "link": link,
    }
    all_jobs.append(job_data)
    print(job_data)

print(f"\nTotal jobs collected: {len(all_jobs)}")

# --- Turn our list of dictionaries into a real pandas DataFrame (a table) ---
import pandas as pd

df = pd.DataFrame(all_jobs)
print("\nFirst few rows as a table:")
print(df.head())

print("\nBasic info about our dataset:")
print(df.info())

# Save it so we have a permanent file, not just terminal output
df.to_csv("../data/rozee_data_analyst_jobs.csv", index=False, encoding="utf-8-sig")
print("\nSaved to ../data/rozee_data_analyst_jobs.csv")