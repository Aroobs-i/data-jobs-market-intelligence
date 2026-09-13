# diagnostic_test.py
# Bare minimum test: can Selenium launch Chrome and load ANY page at all?

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("Step 1: Setting up Chrome options...")
options = Options()
options.page_load_strategy = "eager"  # don't wait for EVERY resource (ads, trackers) to finish

print("Step 2: Launching Chrome driver...")
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)  # fail fast instead of hanging for 120 seconds

print("Step 3: Trying to load a simple, fast site (example.com)...")
try:
    driver.get("https://example.com")
    print("SUCCESS! Page title is:", driver.title)
except Exception as e:
    print("FAILED with error:", e)

print("Step 4: Closing browser...")
driver.quit()
print("Done.")