# Brinex B2B Web Scraper

This Python script automates scraping product stock data from a B2B e-commerce portal using Selenium and saves the data to Google Sheets.

## Features
- Keyword-based product scraping
- Google Sheets API integration
- Email notification via Google Apps Script
- `.env` support for secure credentials
- Modular and configurable

## Setup

1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on `.env.example`.

3. Download and place your `service_account.json` for Google Sheets API.

## Running the Script

```bash
python scraper.py
```

## Notes
- Make sure ChromeDriver is installed and matches your Chrome version.
- `GOOGLE_SCRIPT_URL` should be your published Google Apps Script endpoint.
- Logs and outputs are shown in terminal.

---

**Disclaimer:** This script respects robots.txt rules. Make sure you have permission to scrape the website you use this on.
