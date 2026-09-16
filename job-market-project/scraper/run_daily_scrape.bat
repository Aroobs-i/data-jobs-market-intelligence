@echo off
cd /d "C:\Users\cw\Downloads\project\job-market-project\scraper"
python daily_scrape.py >> ../data/scrape_log.txt 2>&1