#!/usr/bin/env python3
"""
Backtest pysystemtrade system with 2025 data
Demonstrates how to run backtests using newly downloaded 2025 futures data
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
import matplotlib.pyplot as plt
from pathlib import Path

# pysystemtrade imports
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import *
from systems.basesystem import System
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults as ewmac

def run_2025_backtest():
    """Run a complete backtest using 2025 data"""
    
    print("🚀 Starting 2025 Pysystemtrade Backtest")
    print("=" * 60)
    
    # Load data 
    data = csvFuturesSimData()
    
    # Check what instruments we have 2025 data for
    print("📊 Checking available 2025 data...")
    instruments_with_2025_data = []
    
    test_instruments = ['SP500', 'NASDAQ', 'GOLD', 'US10', 'SOFR']
    
    for instrument in test_instruments:
        try:
            prices = data.get_backadjusted_futures_price(instrument)
            # Check for 2025 data first, then fall back to recent 2024 data
            data_2025 = prices.loc[prices.index >= '2025-01-01']
            data_recent = prices.loc[prices.index >= '2024-01-01']  # Fallback to 2024
            
            if len(data_2025) >= 30:  # At least 30 days of 2025 data
                instruments_with_2025_data.append(instrument)
                print(f"✅ {instrument}: {len(data_2025)} 2025 data points")
                print(f"   📅 {data_2025.index.min().date()} to {data_2025.index.max().date()}")
            elif len(data_recent) >= 30:  # At least 30 days of 2024 data
                instruments_with_2025_data.append(instrument)
                print(f"🔄 {instrument}: {len(data_recent)} recent data points (using 2024 as demo)")
                print(f"   📅 {data_recent.index.min().date()} to {data_recent.index.max().date()}")
            else:
                print(f"⚠️  {instrument}: Only {len(data_recent)} data points (need 30+)")
                
        except Exception as e:
            print(f"❌ {instrument}: No data available - {e}")
    
    if not instruments_with_2025_data:
        print("❌ No instruments with sufficient 2025 data found!")
        print("💡 Run download_2025_data.py first to download data")
        return
    
    print(f"\n🎯 Running demo backtest with instruments: {instruments_with_2025_data}")
    print("⚠️  Using available data (2024) to demonstrate system capabilities")
    
    # Create system configuration for 2025 backtest
    config = Config({
        "trading_rules": {
            "ewmac2_8": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"],
                "Lfast": 2,
                "Lslow": 8
            },
            "ewmac4_16": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", 
                "data": ["rawdata.get_daily_prices"],
                "Lfast": 4,
                "Lslow": 16
            },
            "ewmac8_32": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"], 
                "Lfast": 8,
                "Lslow": 32
            }
        },
        "instruments": instruments_with_2025_data,
        "forecast_weights": dict([(rule_name, 1.0) for rule_name in ["ewmac2_8", "ewmac4_16", "ewmac8_32"]]),
        "forecast_div_mult_estimates": dict([(rule_name, 1.0) for rule_name in ["ewmac2_8", "ewmac4_16", "ewmac8_32"]]),
        "percentage_vol_target": 25.0,
        "notional_trading_capital": 100000,
        "base_currency": "USD",
    })
    
    # Build the system
    print("🔧 Building trading system...")
    system = System([
        Account(),
        Portfolios(), 
        PositionSizing(),
        ForecastCombine(),
        ForecastScaleCap(),
        Rules(),
        RawData()
    ], data, config)
    
    # Run 2025-specific analysis
    print("📈 Running 2025 analysis...")
    
    # 1. Show price performance for 2025
    print("\n💰 2025 Price Performance:")
    print("-" * 40)
    
    for instrument in instruments_with_2025_data[:3]:  # Top 3 instruments
        prices = system.rawdata.get_daily_prices(instrument)
        prices_2025 = prices.loc[prices.index >= '2025-01-01']
        
        if len(prices_2025) > 1:
            start_price = prices_2025.iloc[0]
            end_price = prices_2025.iloc[-1]
            return_pct = (end_price / start_price - 1) * 100
            
            print(f"{instrument:10s}: {return_pct:+6.1f}% (${start_price:.2f} → ${end_price:.2f})")
    
    # 2. Show trading signals for 2025
    print("\n📊 Current Trading Positions (2025):")
    print("-" * 40)
    
    for instrument in instruments_with_2025_data[:3]:
        try:
            position = system.portfolio.get_notional_position(instrument)
            position_2025 = position.loc[position.index >= '2025-01-01']
            
            if len(position_2025) > 0:
                current_position = position_2025.iloc[-1]
                print(f"{instrument:10s}: {current_position:+8.1f} units")
            else:
                # Try to get any recent position data
                recent_position = position.tail(5)
                if len(recent_position) > 0:
                    print(f"{instrument:10s}: {recent_position.iloc[-1]:+8.1f} units (latest available)")
                else:
                    print(f"{instrument:10s}: No position data")
        except Exception as e:
            print(f"{instrument:10s}: No position data - {e}")
    
    # 3. Show recent forecasts
    print("\n🔮 Recent Trading Signals:")
    print("-" * 40)
    
    for instrument in instruments_with_2025_data[:2]:
        try:
            # Get combined forecast (directional signal)
            forecast = system.forecastScaleCap.get_capped_forecast(instrument, "ewmac8_32")
            forecast_2025 = forecast.loc[forecast.index >= '2025-01-01']
            
            if len(forecast_2025) > 0:
                recent_forecast = forecast_2025.iloc[-1]
                signal = "LONG" if recent_forecast > 0 else "SHORT" if recent_forecast < 0 else "NEUTRAL"
                print(f"{instrument:10s}: {recent_forecast:+6.1f} ({signal})")
            else:
                # Try to get any recent forecast data
                recent_forecast = forecast.tail(5)
                if len(recent_forecast) > 0:
                    recent_val = recent_forecast.iloc[-1]
                    signal = "LONG" if recent_val > 0 else "SHORT" if recent_val < 0 else "NEUTRAL"
                    print(f"{instrument:10s}: {recent_val:+6.1f} ({signal}) (latest available)")
                else:
                    print(f"{instrument:10s}: No forecast data")
        except Exception as e:
            print(f"{instrument:10s}: No forecast data - {e}")
    
    # 4. Calculate 2025 system performance
    print("\n📊 2025 System Performance:")
    print("-" * 40)
    
    try:
        # Get account curve (cumulative returns)
        account_curve = system.accounts.portfolio()
        # Handle potential empty or NaN account curve
        if hasattr(account_curve, 'empty') and account_curve.empty:
            print("No account data available - system may not have enough data to calculate positions")
            return system
        elif hasattr(account_curve, 'isna') and account_curve.isna().all():
            print("No account data available - all values are NaN")
            return system
            
        account_2025 = account_curve.loc[account_curve.index >= '2025-01-01']
        
        if len(account_2025) > 1:
            total_return = (account_2025.iloc[-1] / account_2025.iloc[0] - 1) * 100
            volatility = account_2025.pct_change().std() * np.sqrt(252) * 100
            
            # Calculate Sharpe ratio
            returns = account_2025.pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 1 else 0
            
            print(f"Total Return (2025): {total_return:+6.1f}%")
            print(f"Annualized Volatility: {volatility:6.1f}%") 
            print(f"Sharpe Ratio: {sharpe:6.2f}")
            
            # Show max drawdown
            running_max = account_2025.expanding().max()
            drawdown = ((account_2025 - running_max) / running_max * 100)
            max_dd = drawdown.min()
            print(f"Max Drawdown: {max_dd:6.1f}%")
            
    except Exception as e:
        print(f"Could not calculate performance: {e}")
    
    # 5. Show system statistics
    print("\n🔍 System Configuration:")
    print("-" * 40)
    print(f"Trading Rules: {len(config.trading_rules)} EWMAC variants")
    print(f"Instruments: {len(instruments_with_2025_data)}")
    print(f"Vol Target: {config.percentage_vol_target}%")
    print(f"Capital: ${config.notional_trading_capital:,}")
    
    # 6. DETAILED DIAGNOSTICS - Show what actually happened
    print("\n🔍 DETAILED SYSTEM DIAGNOSTICS:")
    print("=" * 60)
    
    # Check each instrument's trading activity
    for instrument in instruments_with_2025_data[:3]:
        print(f"\n🔍 DIAGNOSTIC: {instrument}")
        print("-" * 30)
        
        try:
            # Raw prices
            prices = system.rawdata.get_daily_prices(instrument)
            prices_2025 = prices.loc[prices.index >= '2025-01-01']
            print(f"   📊 Price data: {len(prices_2025)} points")
            
            # Volatility 
            volatility = system.rawdata.daily_returns_volatility(instrument)
            vol_2025 = volatility.loc[volatility.index >= '2025-01-01']
            if len(vol_2025) > 0:
                avg_vol = vol_2025.mean() * 100
                print(f"   📈 Avg daily vol: {avg_vol:.2f}%")
            
            # Trading signals for each rule
            for rule in ['ewmac2_8', 'ewmac4_16', 'ewmac8_32']:
                try:
                    forecast = system.forecastScaleCap.get_capped_forecast(instrument, rule)
                    forecast_2025 = forecast.loc[forecast.index >= '2025-01-01']
                    if len(forecast_2025) > 0:
                        recent_signal = forecast_2025.iloc[-1]
                        signal_strength = "STRONG" if abs(recent_signal) > 15 else "WEAK"
                        direction = "LONG" if recent_signal > 0 else "SHORT"
                        print(f"   🎯 {rule}: {recent_signal:+6.1f} ({direction} {signal_strength})")
                    else:
                        print(f"   ❌ {rule}: No signals generated")
                except Exception as e:
                    print(f"   ❌ {rule}: Error - {str(e)[:50]}...")
            
            # Position sizing
            try:
                position = system.portfolio.get_notional_position(instrument)
                pos_2025 = position.loc[position.index >= '2025-01-01']
                if len(pos_2025) > 0:
                    current_pos = pos_2025.iloc[-1]
                    print(f"   💼 Position: {current_pos:+8.1f} units")
                else:
                    print(f"   ❌ Position: No positions taken")
            except Exception as e:
                print(f"   ❌ Position: Error - {str(e)[:50]}...")
                
        except Exception as e:
            print(f"   ❌ Overall diagnostic failed: {e}")
    
    # Overall system health check
    print(f"\n🏥 SYSTEM HEALTH CHECK:")
    print("-" * 30)
    
    try:
        # Check if system generated any trades at all
        total_positions = 0
        total_forecasts = 0
        
        for instrument in instruments_with_2025_data:
            try:
                position = system.portfolio.get_notional_position(instrument)
                pos_2025 = position.loc[position.index >= '2025-01-01']
                if len(pos_2025) > 0 and pos_2025.abs().max() > 0.1:
                    total_positions += 1
                    
                forecast = system.forecastScaleCap.get_capped_forecast(instrument, "ewmac8_32")
                forecast_2025 = forecast.loc[forecast.index >= '2025-01-01']
                if len(forecast_2025) > 0 and forecast_2025.abs().max() > 1.0:
                    total_forecasts += 1
            except:
                continue
                
        print(f"   📊 Instruments with positions: {total_positions}/{len(instruments_with_2025_data)}")
        print(f"   🎯 Instruments with signals: {total_forecasts}/{len(instruments_with_2025_data)}")
        
        if total_positions == 0:
            print("   ⚠️  WARNING: System generated NO positions!")
            print("   💡 Possible reasons:")
            print("      - Not enough historical data for signal generation")
            print("      - Volatility estimation requires more data")
            print("      - System configuration issue")
        else:
            print("   ✅ System is generating positions - backtesting working!")
            
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")

    # 7. Export results for further analysis
    print(f"\n💾 SAVING RESULTS:")
    print("=" * 30)
    
    try:
        account_curve = system.accounts.portfolio()
        
        # Safe check for empty data
        if hasattr(account_curve, 'empty') and account_curve.empty:
            print("❌ Account curve is empty - no positions generated")
        elif hasattr(account_curve, 'isna') and account_curve.isna().all():
            print("❌ Account curve contains only NaN values") 
        elif account_curve is None:
            print("❌ Account curve is None - system failed to generate account data")
        else:
            print(f"✅ Account curve available: {len(account_curve)} points")
            account_2025 = account_curve.loc[account_curve.index >= '2025-01-01']
            
            if len(account_2025) > 0:
                # Save to CSV for Excel analysis
                results_df = pd.DataFrame({
                    'date': account_2025.index,
                    'account_value': account_2025.values,
                    'daily_return': account_2025.pct_change().values
                })
                
                results_file = 'backtest_2025_results.csv'
                results_df.to_csv(results_file)
                print(f"✅ Account results exported: {results_file} ({len(results_df)} rows)")
            else:
                print("❌ No 2025 account data available")
                print(f"   Full account data range: {account_curve.index.min()} to {account_curve.index.max()}")
        
        # Export individual instrument data
        instruments_exported = 0
        for instrument in instruments_with_2025_data[:3]:
            try:
                prices = system.rawdata.get_daily_prices(instrument)
                prices_2025 = prices.loc[prices.index >= '2025-01-01']
                
                position = system.portfolio.get_notional_position(instrument)
                pos_2025 = position.loc[position.index >= '2025-01-01']
                
                # Combine data
                combined_data = pd.DataFrame({
                    'price': prices_2025,
                    'position': pos_2025
                })
                
                if len(combined_data.dropna()) > 10:  # Only export if significant data
                    filename = f'{instrument}_2025_detailed.csv'
                    combined_data.to_csv(filename)
                    print(f"✅ {instrument} details: {filename}")
                    instruments_exported += 1
                    
            except Exception as e:
                print(f"❌ {instrument} export failed: {str(e)[:50]}...")
        
        print(f"\n📁 FILES SAVED IN: {Path.cwd()}")
        print(f"📊 Total files exported: {instruments_exported + 1}")
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        
    # 8. Show file locations
    print(f"\n📂 RESULTS LOCATION:")
    print("=" * 30)
    current_dir = Path.cwd()
    print(f"📁 Working directory: {current_dir}")
    
    # List all CSV files we might have created
    csv_files = list(current_dir.glob("*2025*.csv"))
    if csv_files:
        print("✅ Result files found:")
        for file in csv_files:
            size_kb = file.stat().st_size / 1024
            print(f"   📄 {file.name} ({size_kb:.1f} KB)")
    else:
        print("❌ No result files found")
        
    # Show data source files too
    data_dir = Path("data/futures/adjusted_prices_csv")
    if data_dir.exists():
        clean_files = list(data_dir.glob("*CLEAN*.csv"))
        print(f"\n📊 Clean data files ({data_dir}):")
        for file in clean_files:
            size_kb = file.stat().st_size / 1024
            print(f"   📄 {file.name} ({size_kb:.1f} KB)")
            
    print(f"\n💡 NEXT STEPS:")
    print("   1. Check result CSV files in current directory")
    print("   2. Open in Excel/Python for detailed analysis") 
    print("   3. If no positions generated, try longer data history")
    print("   4. Adjust system parameters if needed")
    
    print("\n🎉 2025 Backtest Complete!")
    print("💡 Next steps:")
    print("   - Analyze results in backtest_2025_results.csv")
    print("   - Try different trading rules or parameters")
    print("   - Add more instruments with download_2025_data.py")
    
    return system

def analyze_2025_volatility():
    """Analyze 2025 market volatility vs historical periods"""
    
    print("\n📈 2025 Volatility Analysis")
    print("=" * 40)
    
    data = csvFuturesSimData()
    
    for instrument in ['SP500', 'NASDAQ', 'GOLD']:
        try:
            prices = data.get_backadjusted_futures_price(instrument)
            
            # Calculate returns and volatility for different periods
            returns = prices.pct_change(fill_method=None).dropna()
            
            # 2025 volatility 
            returns_2025 = returns.loc[returns.index >= '2025-01-01']
            vol_2025 = returns_2025.std() * np.sqrt(252) * 100 if len(returns_2025) > 30 else 0
            
            # 2024 volatility for comparison
            returns_2024 = returns.loc[(returns.index >= '2024-01-01') & (returns.index < '2025-01-01')]
            vol_2024 = returns_2024.std() * np.sqrt(252) * 100 if len(returns_2024) > 30 else 0
            
            # Long-term average (5 years)
            returns_5y = returns.loc[returns.index >= '2020-01-01']
            vol_5y = returns_5y.std() * np.sqrt(252) * 100 if len(returns_5y) > 30 else 0
            
            print(f"\n{instrument}:")
            print(f"  2025 Vol:     {vol_2025:5.1f}%")
            print(f"  2024 Vol:     {vol_2024:5.1f}%") 
            print(f"  5-Year Vol:   {vol_5y:5.1f}%")
            
            vol_change = ((vol_2025 / vol_2024) - 1) * 100 if vol_2024 > 0 else 0
            print(f"  2025 vs 2024: {vol_change:+5.1f}%")
            
        except Exception as e:
            print(f"{instrument}: Error - {e}")

if __name__ == "__main__":
    # Run the main backtest
    system = run_2025_backtest()
    
    # Run volatility analysis
    analyze_2025_volatility()