import os
import django
import json
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orm.settings')
django.setup()

from stocks.models import (
    Company, FinancialPeriod, QuarterlyFinancial,
    BalanceSheet, ShareholdingPattern,
    FinancialRatio, AnnualFinancial,
    PriceHistory, MovingAverage
)

print("Django setup successful")


class Importer:

    def __init__(self):
        self.period_cache = {}

    def parse_date(self, period_str, period_type='Q'):
        month_map = {
            'Mar': 3, 'Jun': 6, 'Sep': 9, 'Dec': 12,
            'Jan': 1, 'Feb': 2, 'Apr': 4, 'May': 5,
            'Jul': 7, 'Aug': 8, 'Oct': 10, 'Nov': 11
        }

        try:
            parts = period_str.split()
            if len(parts) == 2:
                month = month_map.get(parts[0], 3)

                # clean year
                year_str = ''.join(filter(str.isdigit, parts[1]))
                year = int(year_str)

                if period_type == 'Q':
                    return date(year, month, 1)
                else:
                    return date(year, 3, 31)

        except:
            return None

        return None

    def get_or_create_period(self, period_name, period_type='Q'):
        key = (period_name, period_type)

        if key in self.period_cache:
            return self.period_cache[key]

        period_date = self.parse_date(period_name, period_type)
        if period_date is None:
            return None

        period, _ = FinancialPeriod.objects.get_or_create(
            period_type=period_type,
            period_date=period_date,
            defaults={'period_name': period_name}
        )

        self.period_cache[key] = period
        return period

    def clean_value(self, value):
        if not value:
            return None

        try:
            value = str(value).replace(',', '').replace('%', '')
            return Decimal(value)
        except:
            return None

    def process_company(self, company_dir):
        try:
            print("Processing:", company_dir.name)

            with open(company_dir / 'tables.json') as f:
                tables = json.load(f)

            with open(company_dir / 'ratios.json') as f:
                ratios = json.load(f)

            with open(company_dir / 'price.json') as f:
                price = json.load(f)

            company, _ = Company.objects.get_or_create(
                symbol=company_dir.name[:100],
                defaults={'name': company_dir.name.replace('_', ' ')}
            )

            self.import_quarterly(company, tables['quarters'])
            self.import_annual(company, tables['profit-loss'])
            self.import_price(company, price)

            print(f"Done: {company_dir.name}")

        except Exception as e:
            print(f"Skipped {company_dir.name}: {e}")

    def import_quarterly(self, company, data):
        cols = data['columns'][1:]
        rows = data['rows']

        objs = []

        for row in rows:
            metric = row[0]
            values = row[1:]

            for i, period_name in enumerate(cols):
                if i >= len(values) or not values[i]:
                    continue

                period = self.get_or_create_period(period_name, 'Q')
                if not period:
                    continue

                val = self.clean_value(values[i])

                obj = QuarterlyFinancial(company=company, period=period)

                if metric == 'Sales+':
                    obj.sales = val
                elif metric == 'Net Profit+':
                    obj.net_profit = val

                objs.append(obj)

        QuarterlyFinancial.objects.bulk_create(objs, batch_size=1000, ignore_conflicts=True)

    def import_annual(self, company, data):
        cols = data['columns'][1:]
        rows = data['rows']

        objs = []

        for row in rows:
            metric = row[0]
            values = row[1:]

            for i, period_name in enumerate(cols):
                if i >= len(values) or not values[i]:
                    continue

                period = self.get_or_create_period(period_name, 'A')
                if not period:
                    continue

                val = self.clean_value(values[i])

                obj = AnnualFinancial(company=company, period=period)

                if metric == 'Sales+':
                    obj.sales = val
                elif metric == 'Net Profit+':
                    obj.net_profit = val

                objs.append(obj)

        AnnualFinancial.objects.bulk_create(objs, batch_size=1000, ignore_conflicts=True)

    def import_price(self, company, price_data):
        objs = []

        for dataset in price_data['datasets']:
            if dataset['metric'] != 'Price':
                continue

            for value in dataset['values']:
                try:
                    dt = datetime.strptime(value[0], '%Y-%m-%d').date()
                    price_val = Decimal(str(value[1]))

                    objs.append(
                        PriceHistory(
                            company=company,
                            date=dt,
                            price=price_val
                        )
                    )
                except:
                    continue

        PriceHistory.objects.bulk_create(objs, batch_size=1000, ignore_conflicts=True)


if __name__ == "__main__":
    BASE_DIR = Path('/home/shamit/Desktop/scrapscreener/data/raw')

    importer = Importer()

    dirs = [d for d in BASE_DIR.iterdir() if d.is_dir()]

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(importer.process_company, dirs)