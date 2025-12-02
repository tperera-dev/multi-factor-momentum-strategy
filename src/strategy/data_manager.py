"""
Multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

Author: tperera
Date: 2025-11-30
License: MIT
"""
# import pickle
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
        # Convert DataFrame timezone-aware columns to naive
        # if isinstance(data, pd.DataFrame):
        #     data = self._convert_timezone_to_naive(data)
        # elif isinstance(data, list):
        #     # If it's a list, just save it directly
        #     pass
        # with open(filename, 'wb') as f:
        #     pickle.dump(data, f)
        if isinstance(data, pd.DataFrame):
            data.to_parquet(filename, engine='pyarrow', compression='snappy', index=False)
        elif isinstance(data, list):
            # Convert list to DataFrame first
            pd.DataFrame({'ticker': data}).to_parquet(filename, engine='pyarrow', index=False)

    def _convert_timezone_to_naive(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert timezone-aware datetime columns to timezone-naive"""
        if df is None or df.empty:
            return df
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        # Convert datetime index if it has timezone
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        # Convert datetime columns if they have timezone
        for col in df.columns:
            if isinstance(df[col].dtype, pd.DatetimeTZDtype):
                df[col] = df[col].dt.tz_localize(None)
            elif df[col].dtype == 'object':
                # Check if it's a datetime column stored as object
                try:
                    if pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df[col], errors='coerce')):
                        df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)
                except:
                    pass
        # Handle 'date' column specifically if it exists
        if 'date' in df.columns:
            if isinstance(df['date'].dtype, pd.DatetimeTZDtype):
                df['date'] = df['date'].dt.tz_localize(None)
            elif not pd.api.types.is_datetime64_any_dtype(df['date']):
                try:
                    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                except:
                    pass
        return df

    def load_data(self, filename):
        """Load DataFrame from pickle file"""
        if not filename.exists():
            return None
        return pd.read_parquet(filename, engine='pyarrow')
        # with open(filename, 'rb') as f:
        #     return pickle.load(f)

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
        # return data if data is not None else []
        if data is None:
            return []
        return data['ticker'].tolist()  # Extract list from DataFrame

    def save_universe(self, tickers):
        """Save universe tickers"""
        self.save_data(tickers, self.config.UNIVERSE_FILE)