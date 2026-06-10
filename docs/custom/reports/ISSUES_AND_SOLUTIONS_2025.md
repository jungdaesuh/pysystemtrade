# Pysystemtrade 2025 Backtest Issues and Solutions

## Overview
This document details the issues encountered during the 2025 backtest implementation and their solutions. These fixes resolved critical pandas boolean comparison errors that prevented CSV export of backtest results.

## Issue 1: FX File Missing DATETIME Column Headers

### Problem
- **Error**: `KeyError: 'DATETIME'` when reading FX price files
- **Location**: `/data/futures/fx_prices_csv/*.csv`
- **Root Cause**: FX CSV files had unnamed index columns instead of 'DATETIME' column headers
- **Impact**: System couldn't load FX data, breaking currency conversions

### Investigation
```python
# Found through forensic analysis in sysdata/csv/csv_spot_fx.py:83-85
fx_data = pd_readcsv(
    filename, date_format=date_format, date_index_name=date_column
)
# Expected 'DATETIME' column but found unnamed index
```

### Solution
Created `fix_fx_headers.py` to add DATETIME column names:
```python
def fix_fx_headers():
    fx_dir = Path("data/futures/fx_prices_csv")
    for fx_file in fx_dir.glob("*.csv"):
        df = pd.read_csv(fx_file, index_col=0, parse_dates=True)
        if df.index.name != 'DATETIME':
            df.index.name = 'DATETIME'
            df.to_csv(fx_file)
```

**Files Fixed**: 
- EURUSD.csv
- CADUSD.csv
- GBPUSD.csv
- AUDUSD.csv
- JPYUSD.csv

## Issue 2: EWMAC Trading Rule Configuration Error

### Problem
- **Error**: `ValueError: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all()`
- **Location**: `systems/provided/rules/ewmac.py:120` in `ewmac()` function
- **Root Cause**: Volatility data was incorrectly passed as the `Lfast` parameter instead of an integer
- **Impact**: Trading rules couldn't calculate, preventing position generation and export

### Investigation
Traced through forensic analysis:
```python
# In ewmac.py line 120:
fast_ewma = price.ewm(span=Lfast, min_periods=1).mean()
# Lfast was a pandas Series instead of integer 8

# Found Lfast contained volatility data:
# Lfast type: <class 'pandas.core.series.Series'>, shape: (164,)
```

### Root Cause Analysis
The configuration incorrectly included volatility in the `data` parameter:
```python
# INCORRECT - caused volatility to be passed as second positional arg
"ewmac8_32": {
    "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
    "data": ["rawdata.get_daily_prices", "rawdata.daily_returns_volatility"],  # ❌
    "Lfast": 8,
    "Lslow": 32
}
```

The function signature expects:
```python
def ewmac_forecast_with_defaults(price, vol, Lfast=64, Lslow=256):
    # vol parameter is unused - volatility calculated internally
    ans = ewmac_calc_vol(price, Lfast=Lfast, Lslow=Lslow)
```

### Solution
Removed volatility from the `data` array in `backtest_2025.py`:
```python
# CORRECT - only pass price data
"ewmac8_32": {
    "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
    "data": ["rawdata.get_daily_prices"],  # ✅ Only price, no volatility
    "Lfast": 8,
    "Lslow": 32
}
```

Applied to all three trading rules:
- ewmac2_8
- ewmac4_16  
- ewmac8_32

## Issue 3: US10 Treasury Data Corruption (Previously Fixed)

### Problem
- Negative values (-71.24) in 1982 US10 Treasury yield data
- Invalid for interest rate data which should be positive

### Solution
Cleaned in `clean_treasury_data.py`:
```python
# Remove obviously incorrect negative values
mask = (df['price'] > 0) & (df['price'] < 30)
df_clean = df[mask].copy()
```

## Forensic Tools Created

### 1. `forensic_trace.py`
- Component-by-component failure tracing
- Identified FX data loading issues

### 2. `forensic_simple.py` 
- Simplified tracing that found KeyError: 'DATETIME'

### 3. `forensic_export.py`
- Tested exact export logic with boolean operations
- Isolated the pandas boolean comparison error

### 4. `forensic_deep.py`
- Monkey-patched pd.Series.__bool__ to trace exact error location
- Found error in ewm() span comparison

### 5. `forensic_ewmac.py`
- Analyzed EWMAC inputs and outputs
- Confirmed individual instruments worked

### 6. `forensic_params.py`
- Traced EWMAC parameter types
- Discovered Lfast was Series instead of int

## Testing Commands

```bash
# Test individual components
python forensic_simple.py

# Fix FX headers
python fix_fx_headers.py

# Run full backtest
python backtest_2025.py

# Verify export
ls -la backtest_2025_results.csv
head backtest_2025_results.csv
```

## Final Result
✅ Backtest runs successfully with 5 instruments  
✅ CSV export creates `backtest_2025_results.csv`  
✅ Account values and daily returns properly calculated  
✅ System ready for 2025 trading analysis

## Key Learnings

1. **FX Data Requirements**: Pysystemtrade expects 'DATETIME' as the index column name in all CSV files
2. **EWMAC Configuration**: The `data` parameter should only contain price data source, not volatility
3. **Forensic Analysis**: Creating targeted diagnostic scripts is essential for debugging complex pandas errors
4. **Boolean Comparison Errors**: Often indicate wrong data types being passed to functions expecting scalars

## Files Modified
- `/data/futures/fx_prices_csv/*.csv` (5 files) - Added DATETIME headers
- `backtest_2025.py` - Fixed trading rule configurations
- `data/futures/adjusted_prices_csv/US10.csv` - Cleaned negative values (previous fix)

## Files Created
- `fix_fx_headers.py` - Utility to fix FX file headers
- `forensic_*.py` (6 files) - Diagnostic tools for debugging
- `backtest_2025_results.csv` - Successfully exported results
- `ISSUES_AND_SOLUTIONS_2025.md` - This documentation