"""
Multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

Author: tperera
Date: 2025-11-30
License: MIT
"""
from strategy_config import StrategyConfig
from data_manager import DataManager
from datetime import datetime
from datetime import timedelta
import yfinance as yf
import pandas as pd


class DataCollector:
    """Collects market and fundamental data"""
    def __init__(self, config, data_manager):
        self.config = config
        self.data_manager = data_manager

    def fetch_sp500_tickers(self):
        """Fetch S&P 500 tickers (or use predefined list)"""
        # TODO: Use a data provider to get the S & P 500tickers
        # For now, using a sample list
        sample_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
            'UNH', 'JNJ', 'V', 'WMT', 'XOM', 'JPM', 'PG', 'MA', 'HD', 'CVX',
            'ABBV', 'MRK', 'KO', 'PEP', 'COST', 'AVGO', 'LLY', 'TMO', 'ADBE',
            'MCD', 'ACN', 'CSCO', 'ABT', 'DHR', 'NKE', 'CRM', 'TXN', 'NEE',
            'LIN', 'VZ', 'PM', 'UPS', 'RTX', 'CMCSA', 'ORCL', 'INTC', 'HON',
            'QCOM', 'INTU', 'AMD', 'IBM', 'BA', 'AMGN', 'CAT', 'GE', 'LOW',
            'SBUX', 'AMAT', 'DE', 'MDLZ', 'ADP', 'GILD', 'PLD', 'ISRG', 'TJX',
            'BKNG', 'ADI', 'MMC', 'CI', 'SYK', 'ZTS', 'CVS', 'BDX', 'VRTX',
            'MO', 'CB', 'C', 'TMUS', 'DUK', 'SO', 'LRCX', 'PGR', 'BMY', 'SCHW',
            'FI', 'EOG', 'BSX', 'REGN', 'ETN', 'MMM', 'APD', 'HCA', 'WM', 'ITW'
        ]
        return sample_tickers

    def fetch_price_data(self, tickers, start_date= None, end_date = None):
        """Fetch historical price data for tickers"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        print(f"Fetching price data for {len(tickers)} tickers...")
        all_data = []
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                
                if hist.empty:
                    continue
                
                hist['ticker'] = ticker
                hist['date'] = hist.index
                hist.reset_index(drop=True, inplace=True)
                
                # Get market cap and other info
                info = stock.info
                hist['market_cap'] = info.get('marketCap', 0)
                hist['sector'] = info.get('sector', 'Unknown')
                
                all_data.append(hist)
                
            except Exception as e:
                print(f"Error fetching {ticker}: {str(e)}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.concat(all_data, ignore_index=True)
        
        # Calculate dollar volume
        df['dollar_volume'] = df['Close'] * df['Volume']
        
        # Calculate 20-day average volume
        df['avg_volume_20d'] = df.groupby('ticker')['Volume'].transform(
            lambda x: x.rolling(window=20, min_periods=1).mean()
        )
        df['avg_dollar_volume_20d'] = df.groupby('ticker')['dollar_volume'].transform(
            lambda x: x.rolling(window=20, min_periods=1).mean()
        )
        return df

    def fetch_fundamental_data(self, tickers):
        """Fetch fundamental data for tickers"""
        
        print(f"Fetching fundamental data for {len(tickers)} tickers...")
        
        fundamentals = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get financial data
                financials = stock.financials
                balance_sheet = stock.balance_sheet
                cash_flow = stock.cashflow
                
                if financials.empty or balance_sheet.empty:
                    continue
                
                # Extract TTM metrics
                fundamental_data = {
                    'ticker': ticker,
                    'date': datetime.now().date(),
                    'market_cap': info.get('marketCap', 0),
                    'enterprise_value': info.get('enterpriseValue', 0),
                    'trailing_eps': info.get('trailingEps', 0),
                    'forward_eps': info.get('forwardEps', 0),
                    'trailing_pe': info.get('trailingPE', 0),
                    'roe': info.get('returnOnEquity', 0),
                    'profit_margin': info.get('profitMargins', 0),
                    'operating_margin': info.get('operatingMargins', 0),
                    'total_debt': info.get('totalDebt', 0),
                    'total_cash': info.get('totalCash', 0),
                    'ebitda': info.get('ebitda', 0),
                    'revenue': info.get('totalRevenue', 0),
                    'net_income': None,
                    'operating_cash_flow': None,
                    'sector': info.get('sector', 'Unknown')
                }
                
                # Try to get net income and operating cash flow from financials
                if not financials.empty and 'Net Income' in financials.index:
                    fundamental_data['net_income'] = financials.loc['Net Income'].iloc[0]
                
                if not cash_flow.empty and 'Operating Cash Flow' in cash_flow.index:
                    fundamental_data['operating_cash_flow'] = cash_flow.loc['Operating Cash Flow'].iloc[0]
                
                fundamentals.append(fundamental_data)
                
            except Exception as e:
                print(f"Error fetching fundamentals for {ticker}: {str(e)}")
                continue
        
        return pd.DataFrame(fundamentals)

    def update_data(self):
        """Update all market data"""
        
        # Get universe
        tickers = self.data_manager.get_universe()
        
        if not tickers:
            print("No universe defined, fetching S&P 500...")
            tickers = self.fetch_sp500_tickers()
            self.data_manager.save_universe(tickers)
        
        # Fetch price data
        price_data = self.fetch_price_data(tickers)
        if not price_data.empty:
            self.data_manager.save_price_data(price_data)
            print(f"Saved price data: {len(price_data)} rows")
        
        # Fetch fundamental data
        fundamental_data = self.fetch_fundamental_data(tickers)
        if not fundamental_data.empty:
            self.data_manager.save_fundamental_data(fundamental_data)
            print(f"Saved fundamental data: {len(fundamental_data)} rows")

if __name__ == "__main__":
    #Example use case of Data collector
    config = StrategyConfig()
    print("✓ [1/4] Created strategy configuartion")
    data_manager = DataManager(config)
    print("✓ [2/4] Instantiated Data Manager sucessfully")
    data_collector = DataCollector(config, data_manager)
    print("✓ [3/4] Instantiated Data collector sucessfully")
    print("... collecting data ...")
    data_collector.update_data()
    print("✓ [4/4] Collected and updated data sucessfully")
