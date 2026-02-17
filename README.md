Financial Data Scraping & Processing Pipeline
Overview

This project implements a scalable and fault-tolerant financial data scraping pipeline for extracting structured company-level data from Screener. The system is designed to collect financial statements, ratios, cash flow schedules, and historical price data for thousands of publicly listed companies.

The architecture focuses on reliability, controlled concurrency, structured storage, and resumability to support large-scale data collection suitable for downstream analytics, database ingestion, and quantitative modeling.

Features
1. Scalable Multi-Threaded Scraping

Controlled concurrency using Python threading and queue-based worker architecture.

Configurable number of worker threads.

Efficient I/O-bound performance optimization.

2. Global Rate Limiting and Throttling

Centralized throttle mechanism to limit requests per second.

Prevents HTTP 429 (Too Many Requests) and 403 blocks.

Smooth traffic shaping across multiple threads.

3. Robust Retry Mechanism

Exponential backoff strategy for network errors and rate-limiting responses.

Graceful handling of connection failures.

Automatic retries for transient failures.

4. Multi-Endpoint Data Collection

For each company, the scraper collects data from three distinct sources:

Official HTML company page (financial tables and ratios)

Cashflow schedules API endpoint

Historical price data API endpoint

Each endpoint is handled independently to ensure modularity and resilience.

5. Structured Data Storage

Data is stored in a modular directory structure:

data/raw/<company_name>/
    ratios.json
    tables.json
    price.json


This design enables:

Independent component updates

Clean separation of financial and price data

Easy database ingestion

6. Failure Logging and Resume Support

Failed company URLs are logged in a separate file.

Enables selective reprocessing without re-scraping successful companies.

Prevents redundant network requests.

7. Idempotent Design

Existing company folders can be skipped to avoid duplication.

Suitable for incremental weekly updates.

Project Structure
project/
│
├── companies.txt
├── scraper.py
├── data/
│   ├── raw/
│   └── failed_companies.txt


companies.txt – List of company URLs to scrape.

scraper.py – Main scraping script.

data/raw/ – Directory containing structured company data.

failed_companies.txt – List of failed company URLs for retry.

Installation
1. Clone the Repository
git clone <repository-url>
cd <repository-name>

2. Create Virtual Environment
python -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt


Required libraries include:

requests

beautifulsoup4

lxml

Usage
Step 1: Add Company URLs

Populate companies.txt with one company URL per line by running scrapper_screener.py
python scrapper_screener.py

Step 2: Run the Company Scraper
python company_scrap.py


The scraper will:

Process companies using controlled multi-threading.

Apply global request throttling.

Extract financial tables, ratios, schedules, and price data.

Save structured JSON files under data/raw/.

Log failed URLs to data/failed_companies.txt.

Reprocessing Failed Companies

To retry failed companies:

Open data/failed_companies.txt

Replace companies.txt content with failed URLs

Clear failed_companies.txt

Run the scraper again

This ensures only incomplete companies are retried.

Configuration

You can modify these parameters inside the script:

NUM_WORKERS = 2
REQUEST_DELAY = 0.4


Recommended values for stable scraping:

1–2 worker threads

0.4–0.6 second throttle interval

Increasing concurrency may result in connection refusal or rate limiting.

Design Considerations

The scraper avoids aggressive parallelism to reduce server blocking.

API endpoints are rate-limited more strictly than HTML pages.

The architecture supports incremental updates and database ingestion.

Data storage is modular to allow selective re-fetch of price or schedule data.

Future Improvements

Database ingestion pipeline (PostgreSQL integration)

Incremental price updates

Async I/O implementation

Distributed scraping with task queues

Automated scheduling via cron or Airflow

Disclaimer

This project is intended for educational and research purposes. Users are responsible for complying with the terms of service of the data source and applicable laws.
