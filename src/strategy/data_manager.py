"""
Multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

Author: tperera
Date: 2025-11-30
License: MIT
"""
import pickle
import pandas as pd
from strategy_config import StrategyConfig

class DataManager:
    """Manages data storage and retrieval using pickle files"""
    def __init__(self, config):
        self.config = config
        self._ensure_data_directory()
        
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        self.config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def save_data(self, data, filename):
        """Save DataFrame to pickle file"""
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    def load_data(self, filename):
        """Load DataFrame from pickle file"""
        if not filename.exists():
            return None
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def get_price_data(self):
        """Load price data"""
        return self.load_data(self.config.PRICE_DATA_FILE)

    def save_price_data(self, df):
        """Save price data"""
        self.save_data(df, self.config.PRICE_DATA_FILE)

    def get_fundamental_data(self):
        """Load fundamental data"""
        return self.load_data(self.config.FUNDAMENTAL_DATA_FILE)

    def save_fundamental_data(self, df):
        """Save fundamental data"""
        self.save_data(df, self.config.FUNDAMENTAL_DATA_FILE)

    def get_portfolio(self):
        """Load portfolio holdings"""
        return self.load_data(self.config.PORTFOLIO_FILE)

    def save_portfolio(self, df):
        """Save portfolio holdings"""
        self.save_data(df, self.config.PORTFOLIO_FILE)

    def get_transactions(self):
        """Load transaction history"""
        return self.load_data(self.config.TRANSACTIONS_FILE)

    def save_transactions(self, df):
        """Save transaction history"""
        self.save_data(df, self.config.TRANSACTIONS_FILE)

    def get_universe(self):
        """Load universe tickers"""
        data = self.load_data(self.config.UNIVERSE_FILE)
        return data if data is not None else []

    def save_universe(self, tickers):
        """Save universe tickers"""
        self.save_data(tickers, self.config.UNIVERSE_FILE)