from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
import requests
import json
import time
import random


BASE_URL = 'https://www.screener.in/market/'

all_industry_pages = {}


all_company_urls = set()

start='https://www.screener.in'

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

session = requests.Session()
session.headers.update(HEADERS)

def download_html(url, retries=3):
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=15)

            if response.status_code == 429:
                wait = 10 + attempt * 10
                print(f"[429] Sleeping {wait}s for {url}")
                time.sleep(wait)
                continue

            if response.status_code != 200:
                return None

            return response.text

        except requests.exceptions.RequestException:
            time.sleep(5 + random.uniform(0, 5))

    return None


def parse_html(html):
    try:
        soup = BeautifulSoup(html,'lxml')
        return soup
    
    except Exception as e:
        print(e)
        return None

def extract_industry_urls(soup):
    table = soup.find('table')
    if not table:
        return

    for row in table.find_all('td'):
        link = row.find('a', href=True)
        if link and '/market/' in link['href']:
            industry_url = urljoin(start, link['href'])
            all_industry_pages[industry_url] = None


    return None

def extract_company_urls(soup):
    table = soup.find('table')
    if not table:
        return []

    page_companies = []

    for row in table.find_all('td'):
        link = row.find('a', href=True)
        if link and '/company/' in link['href']:
            cur_url = urljoin(start, link['href'])
            page_companies.append(cur_url)
            all_company_urls.add(cur_url)

    return page_companies




# def get_industry_pages(url):
#     html = download_html(url)
#     if not html:
#         return 1

#     soup = parse_html(html)
#     if not soup:
#         return 1

#     pagination = soup.find('div', class_='pagination')
#     if not pagination:
#         return 1

#     page_numbers = [
#         int(a.text.strip())
#         for a in pagination.find_all('a', href=True)
#         if a.text.strip().isdigit()
#     ]

#     return max(page_numbers) if page_numbers else 1





#scrapping industries

base_html = download_html(BASE_URL)

base_soup = parse_html(base_html)

extract_industry_urls(base_soup)

time.sleep(2)

# print(len(all_industry_urls))

#scrapping all industries

MAX_PAGES_PER_INDUSTRY = 20  # safety cap

for industry_url in all_industry_pages:

    print(f"\n[INDUSTRY] {industry_url}", flush=True)
    time.sleep(random.uniform(10, 15))

    last_page_last_company = None

    for page in range(1, MAX_PAGES_PER_INDUSTRY + 1):

        if page == 1:
            page_url = industry_url
        else:
            page_url = f"{industry_url}?page={page}"

        print(f"[SCRAPING] {page_url}", flush=True)

        html = download_html(page_url)
        if not html:
            print("[STOP] download failed", flush=True)
            break

        soup = parse_html(html)
        if not soup:
            break

        page_companies = extract_company_urls(soup)

        if not page_companies:
            print("[STOP] no companies parsed", flush=True)
            break

        current_last_company = page_companies[-1]

        if current_last_company == last_page_last_company:
            print("[STOP] page content repeated — pagination end", flush=True)
            break

        last_page_last_company = current_last_company

        time.sleep(random.uniform(4, 8))




print(len(all_company_urls))

with open('companies.txt','w') as f:
    for url in all_company_urls:
        f.write(url+'\n')






