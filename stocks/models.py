# models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Company(models.Model):
    """Core company information"""
    symbol = models.CharField(max_length=200, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    isin = models.CharField(max_length=12, blank=True, null=True)
    face_value = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    # Current metrics (from ratios.json)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_pe = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    book_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    roce = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    roe = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class FinancialPeriod(models.Model):
    """Lookup table for financial periods"""
    PERIOD_TYPES = [
        ('Q', 'Quarterly'),
        ('A', 'Annual'),
        ('TTM', 'Trailing Twelve Months'),
    ]
    
    period_type = models.CharField(max_length=3, choices=PERIOD_TYPES)
    period_date = models.DateField()
    fiscal_year_end = models.DateField(null=True, blank=True)
    period_name = models.CharField(max_length=20)  # e.g., "Dec 2022", "Mar 2024"
    
    class Meta:
        db_table = 'financial_periods'
        unique_together = [['period_type', 'period_date']]
        indexes = [
            models.Index(fields=['period_type', 'period_date']),
        ]
    
    def __str__(self):
        return f"{self.period_type}: {self.period_name}"


class QuarterlyFinancial(models.Model):
    """Quarterly financial statements (from quarters table)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quarterly_financials')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE, limit_choices_to={'period_type': 'Q'})
    
    # Financial metrics
    sales = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    expenses = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    operating_profit = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    opm_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    other_income = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    interest = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    depreciation = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    profit_before_tax = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    net_profit = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    eps = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'quarterly_financials'
        unique_together = [['company', 'period']]
        ordering = ['-period__period_date']
        indexes = [
            models.Index(fields=['company', 'period']),
        ]
    
    def __str__(self):
        return f"{self.company.symbol} - Q{self.period.period_name}"


class AnnualFinancial(models.Model):
    """Annual financial statements (from profit-loss table)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='annual_financials')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE, limit_choices_to={'period_type': 'A'})
    
    # Financial metrics
    sales = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    expenses = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    operating_profit = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    opm_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    other_income = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    interest = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    depreciation = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    profit_before_tax = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    net_profit = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    eps = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dividend_payout_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'annual_financials'
        unique_together = [['company', 'period']]
        ordering = ['-period__period_date']
        indexes = [
            models.Index(fields=['company', 'period']),
        ]
    
    def __str__(self):
        return f"{self.company.symbol} - {self.period.period_name}"


class BalanceSheet(models.Model):
    """Balance sheet data"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='balance_sheets')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE, limit_choices_to={'period_type__in': ['A', 'Q']})
    
    # Equity & Liabilities
    equity_capital = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    reserves = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    borrowings = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    other_liabilities = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    total_liabilities = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    
    # Assets
    fixed_assets = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    capital_work_in_progress = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    investments = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    other_assets = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    total_assets = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    
    class Meta:
        db_table = 'balance_sheets'
        unique_together = [['company', 'period']]
        ordering = ['-period__period_date']
        indexes = [
            models.Index(fields=['company', 'period']),
        ]
    
    def __str__(self):
        return f"{self.company.symbol} - BS {self.period.period_name}"


class FinancialRatio(models.Model):
    """Financial ratios (from ratios table)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financial_ratios')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE, limit_choices_to={'period_type': 'A'})
    
    # Ratios
    debtor_days = models.IntegerField(null=True, blank=True)
    inventory_days = models.IntegerField(null=True, blank=True)
    days_payable = models.IntegerField(null=True, blank=True)
    cash_conversion_cycle = models.IntegerField(null=True, blank=True)
    working_capital_days = models.IntegerField(null=True, blank=True)
    roce_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'financial_ratios'
        unique_together = [['company', 'period']]
        ordering = ['-period__period_date']
    
    def __str__(self):
        return f"{self.company.symbol} - Ratios {self.period.period_name}"


class ShareholdingPattern(models.Model):
    """Shareholding pattern data"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shareholding_patterns')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE, limit_choices_to={'period_type': 'Q'})
    
    # Shareholding percentages
    promoters = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fii = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    dii = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    government = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    public = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    number_of_shareholders = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'shareholding_patterns'
        unique_together = [['company', 'period']]
        ordering = ['-period__period_date']
        indexes = [
            models.Index(fields=['company', 'period']),
        ]
    
    def __str__(self):
        return f"{self.company.symbol} - Shareholding {self.period.period_name}"


class PriceHistory(models.Model):
    """Historical price data"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='price_history')
    date = models.DateField(db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.BigIntegerField(null=True, blank=True)
    delivery_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'price_history'
        unique_together = [['company', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['company', 'date']),
        ]
    
    def __str__(self):
        return f"{self.company.symbol} - {self.date}: {self.price}"


class MovingAverage(models.Model):
    """Moving averages for price data"""
    MA_TYPES = [
        (50, '50 Day MA'),
        (200, '200 Day MA'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='moving_averages')
    date = models.DateField(db_index=True)
    ma_type = models.IntegerField(choices=MA_TYPES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        db_table = 'moving_averages'
        unique_together = [['company', 'date', 'ma_type']]
        indexes = [
            models.Index(fields=['company', 'ma_type', 'date']),
        ]
    
    def __str__(self):
        return f"{self.company.symbol} - {self.ma_type}D MA on {self.date}: {self.value}"


class DataSource(models.Model):
    """Track data sources and last updates"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='data_sources')
    source_type = models.CharField(max_length=50)  # e.g., 'quarterly', 'annual', 'price'
    last_updated = models.DateTimeField(auto_now=True)
    data_version = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        db_table = 'data_sources'
        unique_together = [['company', 'source_type']]