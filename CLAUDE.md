# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pysystemtrade is a systematic futures trading framework implementing the methodology from Rob Carver's "Systematic Trading" book. It provides both backtesting and live production trading capabilities, integrating with Interactive Brokers via the IB-insync library.

## Common Development Commands

### Installation
```bash
# Install the package (dependencies defined in pyproject.toml)
python -m pip install .

# Install in editable mode with development dependencies
python -m pip install --editable '.[dev]'
```

### Testing
```bash
# Run pytest with specific test paths (configured in pyproject.toml)
pytest

# Run slow tests
pytest --runslow

# Run with nose (legacy, via tox)
tox
```

### Code Quality
```bash
# Format code with black
black .

# Black is configured in pyproject.toml with line-length=88, target py310
```

## Architecture Overview

The system is organized into distinct layers following a data pipeline pattern:

### Core Modules
- **systems/**: Backtesting framework with stages (rawdata, forecasting, portfolio, accounts)
- **sysdata/**: Data storage abstraction layer supporting CSV, MongoDB, Arctic, and Parquet
- **sysproduction/**: Live trading production system with scheduled processes
- **sysbrokers/**: Broker integration (primarily Interactive Brokers via IB-insync)
- **sysexecution/**: Order management and execution algorithms
- **sysobjects/**: Core data structures (instruments, contracts, prices, positions)

### Key Design Patterns

1. **Data Blob Pattern**: `sysdata.data_blob.dataBlob` abstracts data sources with automatic class name resolution (e.g., `csv*`, `mongo*`, `arctic*`, `ib*`)

2. **System Stages**: Modular processing pipeline in `systems/` where each stage transforms data:
   - Raw Data → Forecasts → Portfolio Weights → Positions → Accounts

3. **Production Processes**: Scheduled scripts in `sysproduction/` handle:
   - Price updates (`run_daily_price_updates.py`)
   - Order generation (`run_strategy_order_generator.py`) 
   - Trade execution (`run_stack_handler.py`)
   - System backtests (`run_systems.py`)

### Configuration System
- YAML-based configuration in `sysdata/config/`
- Production config loading via `get_production_config()`
- Instrument and trading parameters defined in CSV files under `data/futures/csvconfig/`

### Logging
- Custom logging framework in `syslogging/` with YAML configs
- Production vs simulation logging configurations
- Database and file-based log storage

## Production Deployment

The system runs as a production trading environment with:
- Cron-scheduled processes (see `sysproduction/linux/crontab`)
- MongoDB for state management and order tracking
- Interactive Brokers API for live trading
- Automated backups and data management

Key production scripts run on schedule:
- 00:15: Stack handler (order execution)
- 07:05: Price and contract updates  
- 20:30: System backtests and signal generation
- 21:00: Cleanup and backup processes

## Data Storage

Supports multiple backends through unified interface:
- **CSV**: File-based storage for configuration and historical data
- **MongoDB**: Production state, orders, positions
- **Arctic**: High-performance time series storage (optional)
- **Parquet**: Modern columnar storage format

## Testing Notes

- Tests are organized by module with pytest configuration in `pyproject.toml`
- Slow tests require `--runslow` flag
- Test data includes price series and market data samples
- Conftest.py provides test configuration and markers