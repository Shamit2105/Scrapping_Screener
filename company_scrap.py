from bs4 import BeautifulSoup
from urllib.parse import urljoin,quote

import requests,json,time,random,os,datetime,threading,queue

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    
}
#511359



session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
})

failed_lock = threading.Lock()
FAILED_FILE = "data/failed_companies.txt"


def log_failed_company(url):
    with failed_lock:
        os.makedirs("data", exist_ok=True)
        with open(FAILED_FILE, "a") as f:
            f.write(url + "\n")

rate_lock = threading.Lock()
last_request_time = 0

def throttle(min_interval=0.4):
    global last_request_time
    with rate_lock:
        now = time.time()
        wait = min_interval - (now - last_request_time)
        if wait > 0:
            time.sleep(wait)
        last_request_time = time.time()

tables = {'quarters','profit-loss','balance-sheet','ratios','shareholding'}

def safe_get(url, headers=None, params=None, timeout=15, retries=5):
    for attempt in range(retries):
        try:
            throttle()
            r = session.get(url, headers=headers, params=params, timeout=timeout)
            time.sleep(0.3)
            if r.status_code == 200:
                return r

            if r.status_code in [429, 403]:
                wait = 2 ** attempt
                print(f"[BLOCKED] {url} ({r.status_code}) → sleeping {wait}s")
                time.sleep(wait)
                continue

            print(f"[WARN] {url} status={r.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network issue {url}: {e}")
            time.sleep(2 ** attempt)

    print(f"[FAIL] {url}")
    return None



def parse_html(html):
    try:
        soup = BeautifulSoup(html,'lxml')
        return soup
    
    except Exception as e:
        print(e)
        return None


def extract_ratios(soup):
    data={}

    div = soup.find('div',class_='company-ratios')

    if not div:
        return data

    ul = div.find('ul',id='top-ratios')
    if not ul:
        return data

    li =ul.find_all('li')
    if not li:
        return data

    for i in li:
        name = i.find('span',class_='name')
        value = i.find('span',class_='number')
        data[name.text.strip()]=value.text.strip()
    return data

def extract_tables(soup, section_id):
    data = {
        "columns": [],

        "rows": []
    }

    section = soup.find("section", id=section_id)
    if not section:
        print(f"section not found: {section_id}")
        return data

    

    table = section.find("table")
    if not table:
        print("table not found inside holder")
        return data

    thead = table.find("thead")
    if thead:
        data["columns"] = [
            th.get_text(strip=True) or "Column"
            for th in thead.find_all("th")
        ]

    tbody = table.find("tbody")
    if not tbody:
        print("tbody not found")
        return data

    for tr in tbody.find_all("tr"):
        row = [td.get_text(strip=True) for td in tr.find_all("td")]
        if any(row):
            data["rows"].append(row)

    return data

def fetch_schedule(company_id, parent, section):
    base = f"https://www.screener.in/api/company/{company_id}/schedules/"
    url = f"{base}?parent={quote(parent)}&section={section}"

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.screener.in/company/{company_id}/"
    }

    r = safe_get(url, headers=headers)
    if not r:
        return None

    try:
        return r.json()
    except Exception:
        print(f"[JSON ERROR] Schedule {parent}")
        return None


def normalize_schedule(js):
    columns = set()
    for row_vals in js.values():
        columns.update(row_vals.keys())

    columns = sorted(columns)

    rows = []
    for row_name, row_vals in js.items():
        row = [row_name] + [row_vals.get(col, "") for col in columns]
        rows.append(row)

    return ["Particulars"] + columns, rows



def get_company_id(soup):
    info = soup.find("div", id="company-info")
    if not info:
        return None
    return info.get("data-company-id")

def get_schedule_names(summary_rows):
    names = []
    for row in summary_rows:
        if row and row[0].endswith("+"):
            names.append(row[0].replace("+", "").strip())
    return names

def extract_cashflow_schedules(company_id, schedule_names):
    schedules = {}

    for name in schedule_names:
        js = fetch_schedule(company_id, name, "cash-flow")
        if not js:
            continue

        schedules[name] = js  

    return schedules

def extract_price(company_id):
    url = f"https://www.screener.in/api/company/{company_id}/chart/"

    params = {
        "q": "Price-DMA50-DMA200-Volume",
        "days": "1825",
        "consolidated": "true"
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.screener.in/company/{company_id}/"
    }

    r = safe_get(url, headers=headers, params=params)
    if not r:
        return None

    try:
        return r.json()
    except Exception:
        print("[JSON ERROR] Price API")
        return None



    
NUM_WORKERS = 2

REQUEST_DELAY = 0.4

def process_company(url):
    print(f"\n[START] {url}")

    r = safe_get(url)
    if not r:
        print(f"[FAIL] Main page failed {url}")
        log_failed_company(url)
        return

    soup = parse_html(r.text)
    if not soup:
        print(f"[FAIL] Parse failed {url}")
        log_failed_company(url)
        return

    company_name = soup.find('h1').text.strip()
    company_id = get_company_id(soup)

    print(f"[INFO] Extracting {company_name}")

    # ---- RATIOS ----
    ratios = extract_ratios(soup)

    # ---- TABLES ----
    financial_data = {}
    for t in tables:
        financial_data[t] = extract_tables(soup, t)

    # ---- SCHEDULES ----
    cashflow_table = extract_tables(soup, 'cash-flow')
    schedule_names = get_schedule_names(cashflow_table["rows"])
    schedules = extract_cashflow_schedules(company_id, schedule_names)

    if schedules is None:
        print(f"[FAIL] Schedule failed {company_name}")
        log_failed_company(url)
        return

    # ---- PRICE ----
    price_data = extract_price(company_id)
    if price_data is None:
        print(f"[FAIL] Price failed {company_name}")
        log_failed_company(url)
        return

    # ---- SAVE ----
    save_company_data(company_name, ratios, financial_data, schedules, price_data)

    print(f"[DONE] {company_name}")

    time.sleep(REQUEST_DELAY)


def save_company_data(company_name, ratios, financials, schedules, price):
    safe_name = company_name.replace("/", "_").replace(" ", "_")

    base_path = os.path.join("data/raw", safe_name)
    os.makedirs(base_path, exist_ok=True)

    with open(os.path.join(base_path, "ratios.json"), "w") as f:
        json.dump(ratios, f, indent=2)

    with open(os.path.join(base_path, "tables.json"), "w") as f:
        json.dump(financials, f, indent=2)

    with open(os.path.join(base_path, "price.json"), "w") as f:
        json.dump(price, f, indent=2)



def worker(q):
    while True:
        try:
            url = q.get_nowait()
        except queue.Empty:
            break

        process_company(url)
        q.task_done()


def run_scraper(urls):
    q = queue.Queue()

    for url in urls:
        q.put(url)

    threads = []
    for _ in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(q,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    with open("companies.txt", "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    run_scraper(urls)
