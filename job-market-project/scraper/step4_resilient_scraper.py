# step4_resilient_scraper.py
# Goal: same scraper as before, but built to survive real-world flakiness
# (slow pages, occasional freezes, timeouts) using retries -- exactly how
# production scrapers are actually written.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import time


def make_driver():
    """Creates a fresh Chrome driver. We'll call this again if one dies mid-scrape."""
    options = Options()
    options.page_load_strategy = "eager"
    # Headless = no visible window = lighter on your machine's resources,
    # which can also mean fewer render freezes. Comment this out if you
    # want to watch it work again.
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    return driver


def fetch_rendered_html(url, max_attempts=3, wait_for_selector="h3.s-18"):
    """
    Tries up to max_attempts times to load a page and get its fully-rendered HTML.
    Returns the HTML string, or None if every attempt failed.
    This retry pattern is the core of resilient scraping.

    wait_for_selector: CSS selector to wait for before considering the page
    "ready". Defaults to the search-results page's job title element, but
    pass a DIFFERENT selector (or None) when scraping a different page type,
    like an individual job's detail page.
    """
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}: loading {url}")
        driver = None
        try:
            driver = make_driver()
            try:
                driver.get(url)
            except TimeoutException:
                print("  Page load timed out, but continuing (page may still be usable).")

            if wait_for_selector:
                WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            else:
                # No specific element to wait for -- just give the page a
                # few seconds to run its JavaScript
                time.sleep(4)

            html = driver.page_source
            driver.quit()
            print("  Success.")
            return html

        except (TimeoutException, WebDriverException) as e:
            print(f"  Attempt {attempt} failed: {type(e).__name__}")
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass  # driver may already be dead, that's fine
            if attempt < max_attempts:
                wait_time = 5 * attempt  # wait longer after each failure (5s, then 10s...)
                print(f"  Retrying in {wait_time}s...")
                time.sleep(wait_time)

    print("All attempts failed.")
    return None


def parse_job_listings(html):
    """Takes rendered HTML, returns a list of job dictionaries. Same logic as before."""
    soup = BeautifulSoup(html, "html.parser")
    job_listings = soup.find_all("div", class_="job")
    all_jobs = []

    for listing in job_listings:
        title_tag = listing.find("h3", class_="s-18")
        if not title_tag:
            continue

        title = title_tag.get("title", "").strip()

        link_tag = title_tag.find("a")
        link = link_tag.get("href", "").strip() if link_tag else ""
        if link.startswith("//"):
            link = "https:" + link

        company, city = "", ""
        cname_div = listing.find("div", class_="cname")
        if cname_div:
            bdi_tag = cname_div.find("bdi", class_="float-left")
            if bdi_tag:
                links = bdi_tag.find_all("a")
                if links:
                    company = links[0].get_text(strip=True).rstrip(",").strip()
                loose_text = [t.strip() for t in bdi_tag.contents if isinstance(t, NavigableString)]
                city = " ".join(t for t in loose_text if t).strip(", ").strip()

        description = ""
        jbody_div = listing.find("div", class_="jbody")
        if jbody_div:
            bdi_desc = jbody_div.find("bdi")
            if bdi_desc:
                description = bdi_desc.get_text(strip=True)

        all_jobs.append({
            "title": title,
            "company": company,
            "city": city,
            "description": description,
            "link": link,
        })

    return all_jobs


if __name__ == "__main__":
    url = "https://www.rozee.pk/job/jsearch/q/Data%20Analyst"

    html = fetch_rendered_html(url)

    if html is None:
        print("Could not load the page after multiple attempts. Try again later,")
        print("or check your internet connection.")
    else:
        jobs = parse_job_listings(html)
        print(f"\nParsed {len(jobs)} job listings.")

        df = pd.DataFrame(jobs)
        print("\nFirst few rows:")
        print(df.head())

        df.to_csv("../data/rozee_data_analyst_jobs.csv", index=False, encoding="utf-8-sig")
        print("\nSaved to ../data/rozee_data_analyst_jobs.csv")
