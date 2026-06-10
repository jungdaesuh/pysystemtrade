#!/usr/bin/env python3
"""
DIRECT PRODUCTION ANALYSIS 2025: Analyze individual instruments directly
"""

import pandas as pd
import numpy as np
from datetime import datetime

from sysdata.config.configdata import Config
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system

def direct_performance_analysis():
    """Direct instrument-by-instrument analysis"""
    
    print("🚀 PYSYSTEMTRADE PRODUCTION PERFORMANCE 2025 - DIRECT ANALYSIS")
    print("=" * 80)
    
    # Production config
    config_dict = {
        "percentage_vol_target": 16.0,
        "notional_trading_capital": 1000000,
        "base_currency": "USD",
        "capital_multiplier": {"func": "syscore.capital.fixed_capital"},
        "use_forecast_scale_estimates": False,
        "forecast_scalar": 1.0,
        "forecast_cap": 20.0,
        "buffer_method": "forecast",
        "buffer_size": 0.10,
        "trading_rules": {
            "ewmac2_8": {"function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", "data": ["rawdata.get_daily_prices"], "Lfast": 2, "Lslow": 8},
            "ewmac4_16": {"function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", "data": ["rawdata.get_daily_prices"], "Lfast": 4, "Lslow": 16},
            "ewmac8_32": {"function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", "data": ["rawdata.get_daily_prices"], "Lfast": 8, "Lslow": 32},
            "ewmac16_64": {"function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", "data": ["rawdata.get_daily_prices"], "Lfast": 16, "Lslow": 64},
            "ewmac32_128": {"function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", "data": ["rawdata.get_daily_prices"], "Lfast": 32, "Lslow": 128}
        },
        "instruments": ['SP500', 'NASDAQ', 'GOLD', 'US10', 'SOFR'],
        "instrument_weights": {'SP500': 0.2, 'NASDAQ': 0.2, 'GOLD': 0.2, 'US10': 0.2, 'SOFR': 0.2},
        "forecast_weights": {"ewmac2_8": 0.2, "ewmac4_16": 0.2, "ewmac8_32": 0.2, "ewmac16_64": 0.2, "ewmac32_128": 0.2},
        "forecast_div_mult_estimates": {"ewmac2_8": 1.0, "ewmac4_16": 1.0, "ewmac8_32": 1.0, "ewmac16_64": 1.0, "ewmac32_128": 1.0}
    }
    
    config = Config(config_dict)
    data = csvFuturesSimData()
    system = futures_system(data=data, config=config)
    
    print("📊 Analyzing individual instruments...")
    
    # 2025 period
    start_2025 = pd.Timestamp('2025-01-01')
    end_2025 = pd.Timestamp('2025-08-20')
    
    instruments = config_dict['instruments']
    instrument_results = {}
    
    # First check what 2025 data we have
    print("\n📅 CHECKING 2025 DATA AVAILABILITY:")
    print("=" * 50)
    
    for instrument in instruments:
        try:
            prices = system.rawdata.get_daily_prices(instrument)
            prices_2025 = prices[(prices.index >= start_2025) & (prices.index <= end_2025)]
            
            if len(prices_2025) > 0:
                print(f"✅ {instrument}: {len(prices_2025)} days ({prices_2025.index[0].date()} to {prices_2025.index[-1].date()})")
                
                # Calculate simple buy & hold return
                if len(prices_2025) > 1:
                    start_price = prices_2025.iloc[0]
                    end_price = prices_2025.iloc[-1]
                    
                    # Handle NaN values
                    if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
                        print(f"   ⚠️ Invalid price data (start: {start_price}, end: {end_price})")
                        continue
                        
                    bh_return = (end_price / start_price - 1) * 100
                    returns = prices_2025.pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252) * 100
                    
                    print(f"   📈 Buy&Hold Return: {bh_return:.2f}%")
                    print(f"   📊 Volatility: {volatility:.1f}%")
                    
                    instrument_results[instrument] = {
                        'prices_2025': prices_2025,
                        'return': bh_return,
                        'volatility': volatility
                    }
            else:
                print(f"❌ {instrument}: No 2025 data")
                
        except Exception as e:
            print(f"❌ {instrument}: Error - {e}")
    
    # Calculate equal weight portfolio performance
    if len(instrument_results) > 0:
        print(f"\n🎯 PRODUCTION SYSTEM SIMULATION (Equal Weight)")
        print("=" * 60)
        
        # Find common dates across all instruments
        common_dates = None
        for instrument, data in instrument_results.items():
            dates = data['prices_2025'].index
            if common_dates is None:
                common_dates = dates
            else:
                common_dates = common_dates.intersection(dates)
        
        print(f"📅 Common trading days: {len(common_dates)}")
        
        if len(common_dates) > 1:
            # Create equal weight portfolio
            portfolio_values = []
            
            for date in common_dates:
                daily_value = 0
                for instrument, data in instrument_results.items():
                    if date in data['prices_2025'].index:
                        # Normalize to $1M / num_instruments starting value
                        instrument_start = data['prices_2025'].iloc[0]
                        instrument_current = data['prices_2025'].loc[date]
                        instrument_return = instrument_current / instrument_start
                        daily_value += (config_dict['notional_trading_capital'] / len(instruments)) * instrument_return
                
                portfolio_values.append(daily_value)
            
            portfolio_series = pd.Series(portfolio_values, index=common_dates)
            
            # Calculate performance metrics
            returns = portfolio_series.pct_change().dropna()
            total_return = (portfolio_series.iloc[-1] / portfolio_series.iloc[0] - 1) * 100
            annualized_return = ((portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (252/len(returns)) - 1) * 100
            annualized_vol = returns.std() * np.sqrt(252) * 100
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
            
            # Drawdown
            running_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            
            # Hit rate
            winning_days = (returns > 0).sum()
            hit_rate = winning_days / len(returns) * 100
            
            print(f"💰 Starting Capital: ${config_dict['notional_trading_capital']:,}")
            print(f"📊 Total Return: {total_return:.2f}%")
            print(f"📈 Annualized Return: {annualized_return:.2f}%")
            print(f"📊 Annualized Vol: {annualized_vol:.1f}%")
            print(f"🎯 Target Vol: {config_dict['percentage_vol_target']}%")
            print(f"⚡ Sharpe Ratio: {sharpe_ratio:.2f}")
            print(f"📉 Max Drawdown: {max_drawdown:.2f}%")
            print(f"🎯 Hit Rate: {hit_rate:.1f}%")
            
            # Vol targeting effectiveness  
            vol_error = abs(annualized_vol - config_dict['percentage_vol_target'])
            print(f"🎯 Vol Targeting Error: {vol_error:.1f}%")
            
            # Export results
            results_df = pd.DataFrame({
                'date': portfolio_series.index,
                'account_value': portfolio_series.values,
                'daily_return': [np.nan] + returns.tolist()
            })
            results_df.to_csv('direct_production_2025_results.csv', index=False)
            print(f"\n💾 Results exported: direct_production_2025_results.csv ({len(results_df)} records)")
            
            # Individual instrument performance
            print(f"\n📊 INDIVIDUAL INSTRUMENT PERFORMANCE")
            print("=" * 50)
            
            for instrument, data in instrument_results.items():
                print(f"{instrument}: {data['return']:+.2f}% return, {data['volatility']:.1f}% vol")
            
            # Compare to best single instrument
            best_instrument = max(instrument_results.items(), key=lambda x: x[1]['return'])
            best_return = best_instrument[1]['return']
            
            print(f"\n🏆 PERFORMANCE COMPARISON")
            print("=" * 30)
            print(f"🏭 Production System: {total_return:.2f}%")
            print(f"🥇 Best Single Instrument ({best_instrument[0]}): {best_return:.2f}%")
            print(f"📊 Diversification Effect: {total_return - best_return:+.2f}%")
            
        else:
            print("❌ Insufficient common trading days for portfolio analysis")
    
    else:
        print("❌ No instruments have 2025 data available")

if __name__ == "__main__":
    direct_performance_analysis()