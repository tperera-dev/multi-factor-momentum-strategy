"""
Multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

Author: tperera
Date: 2025-11-30
License: MIT
"""
from strategy_config import StrategyConfig
from factor_calculator import FactorCalculator
from data_manager import DataManager
from datetime import datetime
from data_collector import DataCollector
# import numpy as np
import pandas as pd

class PortfolioManager:
    """Manages portfolio construction and rebalancing"""
    def __init__(self, config, data_manager):
        self.config = config
        self.data_manager = data_manager

    def get_current_portfolio(self):
        """Get current portfolio holdings"""
        portfolio = self.data_manager.get_portfolio()
        if portfolio is None:
            return pd.DataFrame()
        return portfolio

    def construct_equal_weight_portfolio(self, factor_scores, capital = 1_000_000):
        """Construct equal-weighted portfolio from top ranked securities"""
        
        # Select top N
        top_securities = factor_scores.nsmallest(self.config.NUM_POSITIONS, 'rank')
        
        # Equal weight
        target_weight = 1.0 / len(top_securities)
        position_value = capital * target_weight
        
        portfolio = []
        
        for _, security in top_securities.iterrows():
            shares = position_value / security['current_price']
            
            portfolio.append({
                'ticker': security['ticker'],
                'sector': security['sector'],
                'rank': security['rank'],
                'composite_score': security['composite_score'],
                'shares': shares,
                'entry_price': security['current_price'],
                'current_price': security['current_price'],
                'market_value': shares * security['current_price'],
                'weight': target_weight,
                'entry_date': datetime.now().date(),
                'peak_price': security['current_price']
            })
        
        portfolio_df = pd.DataFrame(portfolio)
        
        # Check sector constraints
        sector_weights = portfolio_df.groupby('sector')['weight'].sum()
        print(f"\nSector allocation:")
        print(sector_weights.sort_values(ascending=False))
        
        over_concentrated = sector_weights[sector_weights > self.config.MAX_SECTOR_WEIGHT]
        if not over_concentrated.empty:
            print(f"\nWARNING: Sectors exceeding {self.config.MAX_SECTOR_WEIGHT:.0%} limit:")
            print(over_concentrated)
        
        return portfolio_df

    def generate_rebalance_trades(self, factor_scores, capital = 1_000_000):
        """Generate trades for rebalancing"""
        
        current_portfolio = self.get_current_portfolio()
        
        # Generate target portfolio
        target_portfolio = self.construct_equal_weight_portfolio(factor_scores, capital)
        
        trades = []
        
        # If no current portfolio, buy everything
        if current_portfolio.empty:
            for _, position in target_portfolio.iterrows():
                trades.append({
                    'date': datetime.now().date(),
                    'ticker': position['ticker'],
                    'action': 'BUY',
                    'shares': position['shares'],
                    'price': position['current_price'],
                    'value': position['market_value'],
                    'reason': 'Initial purchase'
                })
            
            return trades, target_portfolio
        
        # Determine sells
        current_tickers = set(current_portfolio['ticker'])
        target_tickers = set(target_portfolio['ticker'])
        
        to_sell = current_tickers - target_tickers
        
        # Check buffer zone for positions to potentially keep
        for ticker in list(to_sell):
            rank = factor_scores[factor_scores['ticker'] == ticker]['rank'].values
            if len(rank) > 0 and rank[0] <= self.config.BUFFER_RANK:
                print(f"Keeping {ticker} in buffer zone (rank {rank[0]})")
                to_sell.remove(ticker)
        
        # Generate sell orders
        for ticker in to_sell:
            position = current_portfolio[current_portfolio['ticker'] == ticker].iloc[0]
            trades.append({
                'date': datetime.now().date(),
                'ticker': ticker,
                'action': 'SELL',
                'shares': position['shares'],
                'price': position['current_price'],
                'value': position['market_value'],
                'reason': 'No longer in top ranked'
            })
        
        # Determine buys
        to_buy = target_tickers - current_tickers
        
        for ticker in to_buy:
            position = target_portfolio[target_portfolio['ticker'] == ticker].iloc[0]
            trades.append({
                'date': datetime.now().date(),
                'ticker': ticker,
                'action': 'BUY',
                'shares': position['shares'],
                'price': position['current_price'],
                'value': position['market_value'],
                'reason': 'New top-ranked position'
            })
        
        # Rebalance existing positions
        for ticker in current_tickers.intersection(target_tickers):
            current = current_portfolio[current_portfolio['ticker'] == ticker].iloc[0]
            target = target_portfolio[target_portfolio['ticker'] == ticker].iloc[0]
            
            share_diff = target['shares'] - current['shares']
            
            if abs(share_diff * target['current_price']) > 1000:  # Only if >$1k difference
                action = 'BUY' if share_diff > 0 else 'SELL'
                trades.append({
                    'date': datetime.now().date(),
                    'ticker': ticker,
                    'action': action,
                    'shares': abs(share_diff),
                    'price': target['current_price'],
                    'value': abs(share_diff * target['current_price']),
                    'reason': 'Rebalance to target weight'
                })
        
        return trades, target_portfolio

    def execute_rebalance(self, trades, target_portfolio):
        """Execute rebalancing trades"""
        
        print(f"\n{'='*60}")
        print(f"REBALANCING SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*60}")
        print(f"Total trades: {len(trades)}")
        print(f"Buys: {len([t for t in trades if t['action'] == 'BUY'])}")
        print(f"Sells: {len([t for t in trades if t['action'] == 'SELL'])}")
        
        # Display trades
        if trades:
            trades_df = pd.DataFrame(trades)
            print(f"\nTrade details:")
            print(trades_df[['ticker', 'action', 'shares', 'price', 'value', 'reason']])
            
            # Save transactions
            existing_transactions = self.data_manager.get_transactions()
            if existing_transactions is None:
                existing_transactions = pd.DataFrame()
            
            new_transactions = pd.concat([existing_transactions, trades_df], ignore_index=True)
            self.data_manager.save_transactions(new_transactions)
        
        # Update portfolio
        self.data_manager.save_portfolio(target_portfolio)
        
        print(f"\nPortfolio updated: {len(target_portfolio)} positions")
        print(f"Total portfolio value: ${target_portfolio['market_value'].sum():,.2f}")

if __name__ == "__main__":
    #Example use case of factor calculator
    config = StrategyConfig()
    print("✓ [1/8] Created strategy configuartion")
    data_manager = DataManager(config)
    print("✓ [2/8] Instantiated Portfolio Manager sucessfully")
    portfolio_manager = PortfolioManager(config, data_manager)
    print("✓ [3/8] Instantiated Data Manager sucessfully")
    factor_calculator = FactorCalculator(config, data_manager)
    print("✓ [4/8] Instantiated factor calculator sucessfully")
    data_collector = DataCollector(config, data_manager)
    print("✓ [5/8] Instantiated Data collector sucessfully")
    print("... collecting data ...")
    data_collector.update_data()
    print("✓ [6/8] Collected and updated data sucessfully")
    factors = factor_calculator.generate_composite_scores()
    print("✓ [7/8] Generated composite scores")
    capital = 1_000_000
    trades, target_portfolio = portfolio_manager.generate_rebalance_trades(factors, capital)
    print(trades)
    print("✓ [8/8] Rebalanced trades")