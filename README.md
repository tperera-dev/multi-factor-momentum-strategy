# multi-factor-momentum-strategy
Python implementation of a multi-factor momentum strategy combining price momentum, quality metrics, and value factors for systematic equity portfolio management.

## Overview
This strategy identifies and ranks stocks based on multiple factors:

Momentum: 12-month and 6-month price trends
Quality: Return on equity, earnings quality, and stability
Value: P/E ratio and EV/EBITDA metrics

The system automatically constructs an equal-weighted portfolio of the top 50 ranked securities, rebalances quarterly, and includes comprehensive risk management features.

## Features

Multi-Factor Scoring: Combines momentum, quality, and value factors with configurable weights
Automated Rebalancing: Quarterly portfolio rebalancing with buffer zone logic
Risk Management: Stop-loss controls, sector constraints, and position limits
Performance Tracking: Detailed reporting and analytics
No Database Required: Uses pickle files for simple data persistence

## Installation
## Basic Usage
