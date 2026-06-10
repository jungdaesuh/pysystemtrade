#!/usr/bin/env python3
"""
Clean 2024 & 2025 data using ONLY Alpha Vantage ETF prices 
Removes data corruption caused by mixing index and ETF price scales
Downloads both years for comprehensive comparison analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def clean_alpha_vantage_data():
    """Create clean datasets using only Alpha Vantage ETF data from 2024 & 2025"""
    
    print("🧹 CLEANING 2024 & 2025 DATA - ETF PRICES ONLY")
    print("=" * 60)
    print("💡 Ultra-hard analysis: Clean ETF data for both years")
    
    # Download fresh Alpha Vantage data without mixing with historical data
    from alternative_downloaders_2025 import download_alpha_vantage_data
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        print("❌ Need ALPHA_VANTAGE_API_KEY in .env file")
        return False
    
    import requests
    import time
    
    # Clean Alpha Vantage instruments - ETF prices only
    instruments = {
        'SP500_CLEAN': 'SPY',    # SPDR S&P 500 ETF 
        'NASDAQ_CLEAN': 'QQQ',   # Invesco QQQ (Nasdaq-100 ETF)  
        'GOLD_CLEAN': 'GLD',     # SPDR Gold Shares ETF
        'US10_CLEAN': 'TLT',     # iShares 20+ Year Treasury Bond ETF
        'SOFR_CLEAN': 'BIL',     # SPDR Bloomberg Barclays 1-3 Month T-Bill ETF
    }
    
    # Target years for analysis
    years = [2024, 2025]
    
    for year in years:
        print(f"\n🎯 PROCESSING {year} DATA")
        print("=" * 40)
        
        for instrument, symbol in instruments.items():
            print(f"\n📥 Downloading {instrument} ({symbol}) for {year}...")
            
            try:
                url = 'https://www.alphavantage.co/query'
                params = {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'outputsize': 'full',  # Get full data
                    'apikey': api_key
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if 'Error Message' in data:
                    print(f"   ❌ Error: {data['Error Message']}")
                    continue
                    
                if 'Note' in data:
                    print(f"   ⚠️  Rate limit: {data['Note']}")
                    time.sleep(60)  # Wait longer for rate limit
                    continue
                
                time_series = data.get('Time Series (Daily)', {})
                
                if not time_series:
                    print(f"   ❌ No time series data for {instrument}")
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.index = pd.to_datetime(df.index)
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                
                # Filter to specific year ONLY
                start_date = f'{year}-01-01'
                end_date = f'{year}-12-31'
                df_year = df[(df.index >= start_date) & (df.index <= end_date)]
                
                if len(df_year) == 0:
                    print(f"   ❌ No {year} data for {instrument}")
                    continue
                
                # Use close prices - pure ETF prices
                price_data = df_year['close'].astype(float)
                
                # Save to year-specific directory
                csv_dir = Path(f"data/futures/clean_{year}_csv")
                csv_dir.mkdir(parents=True, exist_ok=True)
                csv_file = csv_dir / f"{instrument}.csv"
                
                price_df = pd.DataFrame({'price': price_data})
                price_df.index.name = 'DATETIME'
                
                # Save clean data for this year
                price_df.to_csv(csv_file)
                
                print(f"   ✅ {len(price_data)} points for {instrument} {year}")
                print(f"   📅 Range: {price_data.index.min().date()} to {price_data.index.max().date()}")
                print(f"   💰 Price: ${price_data.iloc[0]:.2f} → ${price_data.iloc[-1]:.2f}")
                
                # Calculate year performance
                year_return = (price_data.iloc[-1] / price_data.iloc[0] - 1) * 100
                print(f"   📈 {year} Return: {year_return:+.2f}%")
                
                # Calculate volatility 
                returns = price_data.pct_change(fill_method=None).dropna()
                if len(returns) > 30:
                    daily_vol = returns.std()
                    annual_vol = daily_vol * np.sqrt(252) * 100
                    print(f"   📊 {year} Volatility: {annual_vol:.1f}%")
                
                print(f"   💾 → {csv_file}")
                
                time.sleep(12)  # Rate limit: 5 calls per minute
                
            except Exception as e:
                print(f"   ❌ Error downloading {instrument}: {e}")
    
    print(f"\n✅ CLEAN DATA CREATED FOR BOTH 2024 & 2025!")
    print(f"📁 2024 data → data/futures/clean_2024_csv/")
    print(f"📁 2025 data → data/futures/clean_2025_csv/") 
    print(f"💡 Next: Run ultra-hard comparative analysis")
    return True

if __name__ == "__main__":
    clean_alpha_vantage_data()