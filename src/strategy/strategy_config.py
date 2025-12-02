"""
Multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

Author: tperera
Date: 2025-11-30
License: MIT
"""
from pathlib import Path

class StrategyConfig:
    """Configuration parameters for the momentum strategy"""
    # Factor Weights
    MOMENTUM_12M_WEIGHT = 0.40
    MOMENTUM_6M_WEIGHT = 0.20
    HIGH_52W_WEIGHT = 0.10
    ROE_WEIGHT = 0.10
    EARNINGS_QUALITY_WEIGHT = 0.05
    EARNINGS_STABILITY_WEIGHT = 0.05
    PE_WEIGHT = 0.05
    EV_EBITDA_WEIGHT = 0.05

    # Universe Filters
    MIN_MARKET_CAP = 2_000_000_000  # $2B
    MIN_DAILY_VOLUME = 10_000_000   # $10M
    MIN_PRICE = 5.0

    # Portfolio Parameters
    NUM_POSITIONS = 50
    BUFFER_RANK = 70  # Keep positions if still in top 70
    REBALANCE_FREQUENCY = 'quarterly'  # 'monthly', 'quarterly'

    # Risk Parameters
    MAX_POSITION_WEIGHT = 0.04  # 4%
    MIN_POSITION_WEIGHT = 0.015  # 1.5%
    MAX_SECTOR_WEIGHT = 0.30    # 30%
    STOP_LOSS_HARD = -0.25      # -25%
    STOP_LOSS_TRAILING = -0.20  # -20% from peak after +30% gain

    # Data paths
    DATA_DIR = Path('data')
    PRICE_DATA_FILE = DATA_DIR / 'price_data.parquet'
    FUNDAMENTAL_DATA_FILE = DATA_DIR / 'fundamental_data.parquet'
    PORTFOLIO_FILE = DATA_DIR / 'portfolio.parquet'
    TRANSACTIONS_FILE = DATA_DIR / 'transactions.parquet'
    UNIVERSE_FILE = DATA_DIR / 'universe.parquet'