# Architecture Overview
## System Design Philosophy
This implementation uses a file-based persistence layer with Python pickle files instead of traditional SQL databases, providing a lightweight, zero-configuration solution ideal for research, backtesting, and small-to-medium portfolio management.

## High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                     MomentumStrategy                            │
│                  (Main Orchestrator)                            │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ├─────────────────────────────────────────────────┐
                │                                                 │
    ┌───────────▼──────────┐                        ┌─────────────▼─────────┐
    │   DataCollector      │                        │    DataManager        │
    │  (External Data)     │                        │  (Persistence Layer)  │
    │                      │                        │                       │
    │  • Yahoo Finance     │                        │  • price_data.pkl     │
    │  • Market data       │◄──────────────────────►│  • fundamentals.pkl   │
    │  • Fundamentals      │      save/load         │  • portfolio.pkl      │
    └──────────────────────┘                        │  • transactions.pkl   │
                                                    │  • universe.pkl       │
                                                    └───────────────────────┘
                │
    ┌───────────▼──────────────────────────────────────────────────┐
    │                   FactorCalculator                           │
    │              (Analytics Engine)                              │
    │                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
    │  │  Momentum    │  │   Quality    │  │    Value     │        │
    │  │  • 12M/6M    │  │  • ROE       │  │  • P/E       │        │
    │  │  • 52W High  │  │  • Earnings  │  │  • EV/EBITDA │        │
    │  └──────────────┘  └──────────────┘  └──────────────┘        │
    │                                                              │
    │  Composite Score = Σ (Factor × Weight)                       │
    └───────────────────────────┬──────────────────────────────────┘
                                │
    ┌───────────────────────────▼───────────────────────────────────┐
    │                  PortfolioManager                             │
    │             (Portfolio Construction)                          │
    │                                                               │
    │  • Rank securities by composite score                         │
    │  • Select top 50 positions                                    │
    │  • Apply equal weighting (2% each)                            │
    │  • Check sector constraints                                   │
    │  • Generate rebalancing trades                                │
    └───────────────────────────┬───────────────────────────────────┘
                                │
            ┌───────────────────┴──────────────────┐
            │                                      │
┌───────────▼──────────┐              ┌────────────▼──────────┐
│   RiskManager        │              │  PerformanceReporter  │
│  (Risk Controls)     │              │    (Analytics)        │
│                      │              │                       │
│  • Stop-loss checks  │              │  • Portfolio summary  │
│  • Position limits   │              │  • Sector allocation  │
│  • Volatility calc   │              │  • P&L reporting      │
│  • VaR estimation    │              │  • CSV export         │
└──────────────────────┘              └───────────────────────┘
```

## Data Flow

### Initialization Flow
### Rebalancing Flow
### Daily Update Flow

## Core Components
### DataManager
### FactorCalculator
### PortfolioManager
### RiskManager