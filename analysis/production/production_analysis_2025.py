#!/usr/bin/env python3
"""
PRODUCTION ANALYSIS 2025: Analyze the production backtest results
"""

import pandas as pd
import numpy as np
from datetime import datetime

from sysdata.config.configdata import Config
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system

def analyze_production_system():
    """Analyze production system results"""
    
    print("🔍 ANALYZING PRODUCTION SYSTEM PERFORMANCE")
    print("=" * 60)
    
    # Build production system with same config
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
            "ewmac2_8": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"],
                "Lfast": 2, "Lslow": 8
            },
            "ewmac4_16": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults", 
                "data": ["rawdata.get_daily_prices"],
                "Lfast": 4, "Lslow": 16
            },
            "ewmac8_32": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"], 
                "Lfast": 8, "Lslow": 32
            },
            "ewmac16_64": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"], 
                "Lfast": 16, "Lslow": 64
            },
            "ewmac32_128": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"], 
                "Lfast": 32, "Lslow": 128
            }
        },
        "instruments": ['SP500', 'NASDAQ', 'GOLD', 'US10', 'SOFR'],
        "instrument_weights": {'SP500': 0.2, 'NASDAQ': 0.2, 'GOLD': 0.2, 'US10': 0.2, 'SOFR': 0.2},
        "forecast_weights": {"ewmac2_8": 0.2, "ewmac4_16": 0.2, "ewmac8_32": 0.2, "ewmac16_64": 0.2, "ewmac32_128": 0.2},
        "forecast_div_mult_estimates": {"ewmac2_8": 1.0, "ewmac4_16": 1.0, "ewmac8_32": 1.0, "ewmac16_64": 1.0, "ewmac32_128": 1.0}
    }
    
    config = Config(config_dict)
    data = csvFuturesSimData()
    system = futures_system(data=data, config=config)
    
    print("🏭 Getting production account curve...")
    account_curve = system.accounts.portfolio()
    print(f"   ✅ Total data points: {len(account_curve)}")
    print(f"   📅 Date range: {account_curve.index[0]} to {account_curve.index[-1]}")
    
    # Convert to DataFrame for easier filtering
    # Debug the account_curve type
    print(f"   🔍 Account curve type: {type(account_curve)}")
    
    # For accountCurveGroup, we need to get the portfolio curve specifically
    if hasattr(account_curve, 'portfolio'):
        portfolio_curve = account_curve.portfolio()
        print(f"   📊 Portfolio curve: {len(portfolio_curve)} points")
        account_df = pd.DataFrame({'account_value': portfolio_curve})
    elif hasattr(account_curve, 'to_frame'):
        account_df = account_curve.to_frame()
        if len(account_df.columns) == 1:
            account_df.columns = ['account_value']
    else:
        # Direct series or array
        account_df = pd.DataFrame({'account_value': account_curve})
    
    # Filter for 2025 data properly
    print("\n📊 Filtering for 2025 data...")
    start_2025 = pd.Timestamp('2025-01-01')
    end_2025 = pd.Timestamp('2025-08-20')
    
    account_2025 = account_df[(account_df.index >= start_2025) & (account_df.index <= end_2025)]
    
    if len(account_2025) == 0:
        print("   ⚠️ No 2025 data found, using all available data")
        account_2025 = account_df
        actual_start = account_df.index[0].date()
        actual_end = account_df.index[-1].date()
    else:
        actual_start = account_2025.index[0].date()
        actual_end = account_2025.index[-1].date()
    
    print(f"   📈 Analysis period: {actual_start} to {actual_end}")
    print(f"   🔢 Data points: {len(account_2025)}")
    
    # Calculate performance metrics
    account_values = account_2025['account_value']
    returns = account_values.pct_change().dropna()
    
    if len(returns) > 1:
        print("\n🎯 PRODUCTION SYSTEM PERFORMANCE")
        print("=" * 50)
        
        # Core metrics
        total_return = (account_values.iloc[-1] / account_values.iloc[0] - 1) * 100
        annualized_return = ((account_values.iloc[-1] / account_values.iloc[0]) ** (252/len(returns)) - 1) * 100
        annualized_vol = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        
        # Drawdown analysis
        running_max = account_values.expanding().max()
        drawdown = (account_values - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Hit rate
        winning_days = (returns > 0).sum()
        hit_rate = winning_days / len(returns) * 100
        
        print(f"💰 Starting Capital: ${config_dict['notional_trading_capital']:,}")
        print(f"📊 Total Return: {total_return:.2f}%")
        print(f"📈 Annualized Return: {annualized_return:.2f}%")
        print(f"📊 Annualized Volatility: {annualized_vol:.1f}%")
        print(f"🎯 Target Volatility: {config_dict['percentage_vol_target']}%")
        print(f"⚡ Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"📉 Max Drawdown: {max_drawdown:.2f}%")
        print(f"🎯 Hit Rate: {hit_rate:.1f}%")
        
        # Risk targeting effectiveness
        vol_targeting_error = abs(annualized_vol - config_dict['percentage_vol_target'])
        print(f"🎯 Vol Targeting Error: {vol_targeting_error:.1f}%")
        
        # Compare to buy and hold
        compare_to_benchmarks(system, account_2025, actual_start, actual_end)
        
        # Export results
        export_production_results(account_2025, config_dict, actual_start, actual_end)
        
    else:
        print("   ❌ Insufficient data for analysis")

def compare_to_benchmarks(system, account_2025, start_date, end_date):
    """Compare to buy and hold benchmarks"""
    
    print(f"\n🏆 BENCHMARK COMPARISON")
    print("=" * 40)
    
    try:
        # Get benchmark data
        sp500_prices = system.rawdata.get_daily_prices('SP500')
        gold_prices = system.rawdata.get_daily_prices('GOLD')
        us10_prices = system.rawdata.get_daily_prices('US10')
        
        # Filter for same period
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        
        benchmarks = {
            'SP500': sp500_prices[(sp500_prices.index >= start_ts) & (sp500_prices.index <= end_ts)],
            'GOLD': gold_prices[(gold_prices.index >= start_ts) & (gold_prices.index <= end_ts)],
            'US10': us10_prices[(us10_prices.index >= start_ts) & (us10_prices.index <= end_ts)]
        }
        
        # System performance
        system_values = account_2025['account_value']
        system_return = (system_values.iloc[-1] / system_values.iloc[0] - 1) * 100
        system_returns = system_values.pct_change().dropna()
        system_vol = system_returns.std() * np.sqrt(252) * 100
        system_sharpe = (system_returns.mean() * 252) / (system_returns.std() * np.sqrt(252))
        
        print(f"🏭 Production System:")
        print(f"   Return: {system_return:.2f}%")
        print(f"   Volatility: {system_vol:.1f}%")
        print(f"   Sharpe: {system_sharpe:.2f}")
        
        # Benchmark performance
        for name, prices in benchmarks.items():
            if len(prices) > 1:
                bm_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                bm_returns = prices.pct_change().dropna()
                bm_vol = bm_returns.std() * np.sqrt(252) * 100
                bm_sharpe = (bm_returns.mean() * 252) / (bm_returns.std() * np.sqrt(252))
                
                excess_return = system_return - bm_return
                
                print(f"\n📊 {name} Buy & Hold:")
                print(f"   Return: {bm_return:.2f}%")
                print(f"   Volatility: {bm_vol:.1f}%") 
                print(f"   Sharpe: {bm_sharpe:.2f}")
                print(f"   System Excess: {excess_return:+.2f}%")
                
        # Equal weight portfolio benchmark
        equal_weight_returns = []
        for name, prices in benchmarks.items():
            if len(prices) > 1:
                returns = prices.pct_change().dropna()
                equal_weight_returns.append(returns)
        
        if equal_weight_returns:
            # Align all return series
            aligned_returns = pd.concat(equal_weight_returns, axis=1).dropna()
            if len(aligned_returns.columns) > 0:
                portfolio_returns = aligned_returns.mean(axis=1)  # Equal weight
                portfolio_return = (1 + portfolio_returns).prod() - 1
                portfolio_vol = portfolio_returns.std() * np.sqrt(252) * 100
                portfolio_sharpe = (portfolio_returns.mean() * 252) / (portfolio_returns.std() * np.sqrt(252))
                
                print(f"\n🎯 Equal Weight Portfolio:")
                print(f"   Return: {portfolio_return*100:.2f}%")
                print(f"   Volatility: {portfolio_vol:.1f}%")
                print(f"   Sharpe: {portfolio_sharpe:.2f}")
                print(f"   System Excess: {system_return - portfolio_return*100:+.2f}%")
        
    except Exception as e:
        print(f"   ❌ Benchmark comparison failed: {e}")

def export_production_results(account_2025, config, start_date, end_date):
    """Export production results"""
    
    print(f"\n💾 EXPORTING RESULTS")
    print("=" * 30)
    
    # Create results DataFrame
    results_df = account_2025.copy()
    results_df['daily_return'] = results_df['account_value'].pct_change()
    results_df = results_df.reset_index()
    results_df['date'] = results_df['index']
    results_df = results_df[['date', 'account_value', 'daily_return']]
    
    # Export
    filename = 'production_system_2025_results.csv'
    results_df.to_csv(filename, index=False)
    
    print(f"   ✅ Results: {filename}")
    print(f"   📊 Records: {len(results_df)}")
    print(f"   📅 Period: {start_date} to {end_date}")

if __name__ == "__main__":
    analyze_production_system()