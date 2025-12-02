"""
Multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

Author: tperera
Date: 2025-11-30
License: MIT
"""
from strategy_config import StrategyConfig
from data_manager import DataManager
from data_collector import DataCollector
import numpy as np
import pandas as pd

class FactorCalculator:
    """Calculates factor scores for securities"""
    def __init__(self, config, data_manager):
        self.config = config
        self.data_manager = data_manager

    def calculate_momentum_factors(self, price_data):
        """Calculate momentum factors"""
        # Get latest price for each ticker
        latest_prices = price_data.groupby('ticker').apply(
            lambda x: x.nlargest(1, 'date')
        ).reset_index(drop=True)
        
        momentum_factors = []
        
        for ticker in latest_prices['ticker'].unique():
            ticker_data = price_data[price_data['ticker'] == ticker].sort_values('date')
            
            if len(ticker_data) < 252:  # Need at least 1 year of data
                continue
            latest = ticker_data.iloc[-1]
            
            # 12-month momentum (skip last month)
            if len(ticker_data) >= 252:
                price_12m_ago = ticker_data.iloc[-252]['Close']
                price_1m_ago = ticker_data.iloc[-21]['Close']
                momentum_12m = (price_1m_ago / price_12m_ago) - 1
            else:
                momentum_12m = np.nan
            
            # 6-month momentum (skip last month)
            if len(ticker_data) >= 126:
                price_6m_ago = ticker_data.iloc[-126]['Close']
                momentum_6m = (price_1m_ago / price_6m_ago) - 1
            else:
                momentum_6m = np.nan
            
            # 52-week high proximity
            high_52w = ticker_data['High'].tail(252).max()
            high_52w_proximity = latest['Close'] / high_52w
            
            momentum_factors.append({
                'ticker': ticker,
                'date': latest['date'],
                'current_price': latest['Close'],
                'market_cap': latest['market_cap'],
                'sector': latest['sector'],
                'avg_dollar_volume_20d': latest['avg_dollar_volume_20d'],
                'momentum_12m': momentum_12m,
                'momentum_6m': momentum_6m,
                'high_52w_proximity': high_52w_proximity
            })
        
        return pd.DataFrame(momentum_factors)

    def calculate_quality_factors(self, fundamental_data):
        """Calculate quality factors"""
        
        quality_factors = []
        
        for _, row in fundamental_data.iterrows():
            
            # ROE (already provided)
            roe = row['roe'] if pd.notna(row['roe']) else 0
            
            # Earnings quality (Operating Cash Flow / Net Income)
            if pd.notna(row['operating_cash_flow']) and pd.notna(row['net_income']) and row['net_income'] > 0:
                earnings_quality = row['operating_cash_flow'] / row['net_income']
            else:
                earnings_quality = 0
            
            # Earnings stability (use profit margin as proxy)
            earnings_stability = row['profit_margin'] if pd.notna(row['profit_margin']) else 0
            
            quality_factors.append({
                'ticker': row['ticker'],
                'roe': roe,
                'earnings_quality': earnings_quality,
                'earnings_stability': earnings_stability
            })
        
        return pd.DataFrame(quality_factors)

    def calculate_value_factors(self, fundamental_data):
        """Calculate value factors"""
        
        value_factors = []
        
        for _, row in fundamental_data.iterrows():
            
            # P/E ratio
            pe_ratio = row['trailing_pe'] if pd.notna(row['trailing_pe']) and row['trailing_pe'] > 0 else np.nan
            
            # EV/EBITDA
            if pd.notna(row['enterprise_value']) and pd.notna(row['ebitda']) and row['ebitda'] > 0:
                ev_ebitda = row['enterprise_value'] / row['ebitda']
            else:
                ev_ebitda = np.nan
            
            value_factors.append({
                'ticker': row['ticker'],
                'pe_ratio': pe_ratio,
                'ev_ebitda': ev_ebitda
            })
        
        return pd.DataFrame(value_factors)

    def generate_composite_scores(self):
        """Generate composite factor scores and rankings"""
        
        print("Calculating factor scores...")
        
        # Load data
        price_data = self.data_manager.get_price_data()
        fundamental_data = self.data_manager.get_fundamental_data()
        
        if price_data is None or fundamental_data is None:
            print("Error: Missing data. Run data collection first.")
            return pd.DataFrame()
        
        # Calculate factors
        momentum_factors = self.calculate_momentum_factors(price_data)
        quality_factors = self.calculate_quality_factors(fundamental_data)
        value_factors = self.calculate_value_factors(fundamental_data)
        
        # Merge all factors
        factors = momentum_factors.merge(quality_factors, on='ticker', how='left')
        factors = factors.merge(value_factors, on='ticker', how='left')
        
        # Filter universe
        factors = factors[
            (factors['market_cap'] >= self.config.MIN_MARKET_CAP) &
            (factors['avg_dollar_volume_20d'] >= self.config.MIN_DAILY_VOLUME) &
            (factors['current_price'] >= self.config.MIN_PRICE)
        ]
        
        # Apply quality filters
        factors = factors[
            (factors['roe'] >= 0.15) &  # Min 15% ROE
            (factors['earnings_quality'] >= 0.8)  # Min 80% earnings quality
        ]
        
        # Remove rows with missing momentum data
        factors = factors.dropna(subset=['momentum_12m', 'momentum_6m'])
        
        if factors.empty:
            print("No securities passed screening criteria")
            return pd.DataFrame()
        
        # Winsorize extreme values
        for col in ['momentum_12m', 'momentum_6m', 'roe', 'earnings_quality']:
            if col in factors.columns:
                lower = factors[col].quantile(0.05)
                upper = factors[col].quantile(0.95)
                factors[col] = factors[col].clip(lower, upper)
        
        # Convert to percentile scores
        factor_cols = ['momentum_12m', 'momentum_6m', 'high_52w_proximity', 
                    'roe', 'earnings_quality', 'earnings_stability']
        
        for col in factor_cols:
            if col in factors.columns:
                factors[f'{col}_score'] = factors[col].rank(pct=True) * 100
        
        # For valuation factors, invert (lower is better)
        for col in ['pe_ratio', 'ev_ebitda']:
            if col in factors.columns:
                factors[f'{col}_score'] = (100 - factors[col].rank(pct=True) * 100).fillna(50)
        
        # Calculate composite score
        factors['composite_score'] = (
            self.config.MOMENTUM_12M_WEIGHT * factors['momentum_12m_score'] +
            self.config.MOMENTUM_6M_WEIGHT * factors['momentum_6m_score'] +
            self.config.HIGH_52W_WEIGHT * factors['high_52w_proximity_score'] +
            self.config.ROE_WEIGHT * factors['roe_score'] +
            self.config.EARNINGS_QUALITY_WEIGHT * factors['earnings_quality_score'] +
            self.config.EARNINGS_STABILITY_WEIGHT * factors['earnings_stability_score'] +
            self.config.PE_WEIGHT * factors['pe_ratio_score'] +
            self.config.EV_EBITDA_WEIGHT * factors['ev_ebitda_score']
        )
        
        # Rank
        factors['rank'] = factors['composite_score'].rank(ascending=False, method='min').astype(int)
        factors = factors.sort_values('rank')
        
        print(f"Generated scores for {len(factors)} securities")
        print(f"\nTop 10 ranked securities:")
        print(factors[['ticker', 'rank', 'composite_score', 'sector']].head(10))
        
        return factors


if __name__ == "__main__":
    #Example use case of factor calculator
    config = StrategyConfig()
    print("✓ [1/6] Created strategy configuartion")
    data_manager = DataManager(config)
    print("✓ [2/6] Instantiated Data Manager sucessfully")
    factor_calculator = FactorCalculator(config, data_manager)
    print("✓ [3/6] Instantiated factor calculator sucessfully")
    data_collector = DataCollector(config, data_manager)
    print("✓ [4/6] Instantiated Data collector sucessfully")
    print("... collecting data ...")
    data_collector.update_data()
    print("✓ [5/6] Collected and updated data sucessfully")
    factor_calculator.generate_composite_scores()
    print("✓ [6/6] Generated composite scores")