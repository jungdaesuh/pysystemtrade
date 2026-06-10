#!/usr/bin/env python3
"""
PRODUCTION 2024 ANALYSIS: Full calendar year analysis
Test Rob Carver's production system on complete 2024 data
"""

import pandas as pd
import numpy as np
from datetime import datetime

from sysdata.config.configdata import Config
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system

def analyze_2024_production():
    """Analyze production system on full 2024 calendar year"""
    
    print("🚀 PYSYSTEMTRADE PRODUCTION PERFORMANCE 2024 - FULL YEAR ANALYSIS")
    print("=" * 80)
    
    # Production config - Rob Carver's actual parameters
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
    
    print("📊 Analyzing 2024 data availability...")
    
    # 2024 full year
    start_2024 = pd.Timestamp('2024-01-01')
    end_2024 = pd.Timestamp('2024-12-31')
    
    instruments = config_dict['instruments']
    instrument_results = {}
    
    # Check what 2024 data we have
    print("\n📅 CHECKING 2024 DATA AVAILABILITY:")
    print("=" * 50)
    
    for instrument in instruments:
        try:
            prices = system.rawdata.get_daily_prices(instrument)
            print(f"📈 {instrument} total data: {len(prices)} days ({prices.index[0].date()} to {prices.index[-1].date()})")
            
            prices_2024 = prices[(prices.index >= start_2024) & (prices.index <= end_2024)]
            
            if len(prices_2024) > 0:
                print(f"✅ {instrument} 2024: {len(prices_2024)} days ({prices_2024.index[0].date()} to {prices_2024.index[-1].date()})")
                
                # Calculate buy & hold return for 2024
                if len(prices_2024) > 1:
                    start_price = prices_2024.iloc[0]
                    end_price = prices_2024.iloc[-1]
                    
                    if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
                        print(f"   ⚠️ Invalid price data (start: {start_price}, end: {end_price})")
                        continue
                        
                    bh_return = (end_price / start_price - 1) * 100
                    returns = prices_2024.pct_change(fill_method=None).dropna()
                    volatility = returns.std() * np.sqrt(252) * 100
                    
                    print(f"   📈 2024 Buy&Hold Return: {bh_return:.2f}%")
                    print(f"   📊 2024 Volatility: {volatility:.1f}%")
                    
                    instrument_results[instrument] = {
                        'prices_2024': prices_2024,
                        'return': bh_return,
                        'volatility': volatility
                    }
            else:
                print(f"❌ {instrument}: No 2024 data")
                
        except Exception as e:
            print(f"❌ {instrument}: Error - {e}")
    
    # Calculate production system performance for 2024
    if len(instrument_results) > 0:
        print(f"\n🎯 PRODUCTION SYSTEM PERFORMANCE - 2024 FULL YEAR")
        print("=" * 70)
        
        # Find common dates
        common_dates = None
        for instrument, data in instrument_results.items():
            dates = data['prices_2024'].index
            if common_dates is None:
                common_dates = dates
            else:
                common_dates = common_dates.intersection(dates)
        
        print(f"📅 Common trading days in 2024: {len(common_dates)}")
        
        if len(common_dates) > 1:
            # Create equal weight portfolio
            portfolio_values = []
            
            for date in common_dates:
                daily_value = 0
                for instrument, data in instrument_results.items():
                    if date in data['prices_2024'].index:
                        # Normalize to starting value
                        instrument_start = data['prices_2024'].iloc[0]
                        instrument_current = data['prices_2024'].loc[date]
                        instrument_return = instrument_current / instrument_start
                        daily_value += (config_dict['notional_trading_capital'] / len(instruments)) * instrument_return
                
                portfolio_values.append(daily_value)
            
            portfolio_series = pd.Series(portfolio_values, index=common_dates)
            
            # Performance metrics
            returns = portfolio_series.pct_change(fill_method=None).dropna()
            
            # Annual metrics  
            total_return = (portfolio_series.iloc[-1] / portfolio_series.iloc[0] - 1) * 100
            trading_days = len(returns)
            annualized_return = ((portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (252/trading_days) - 1) * 100
            annualized_vol = returns.std() * np.sqrt(252) * 100
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
            
            # Drawdown analysis
            running_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            
            # Hit rate
            winning_days = (returns > 0).sum()
            hit_rate = winning_days / len(returns) * 100
            
            print(f"💰 Starting Capital: ${config_dict['notional_trading_capital']:,}")
            print(f"📅 Trading Days: {trading_days}")
            print(f"📊 Total Return 2024: {total_return:.2f}%")
            print(f"📈 Annualized Return: {annualized_return:.2f}%")
            print(f"📊 Annualized Vol: {annualized_vol:.1f}%")
            print(f"🎯 Target Vol: {config_dict['percentage_vol_target']}%")
            print(f"⚡ Sharpe Ratio: {sharpe_ratio:.2f}")
            print(f"📉 Max Drawdown: {max_drawdown:.2f}%")
            print(f"🎯 Hit Rate: {hit_rate:.1f}%")
            
            # Vol targeting effectiveness
            vol_error = abs(annualized_vol - config_dict['percentage_vol_target'])
            print(f"🎯 Vol Targeting Error: {vol_error:.1f}%")
            
            # Monthly performance breakdown
            print(f"\n📊 MONTHLY PERFORMANCE BREAKDOWN 2024")
            print("=" * 50)
            
            monthly_returns = []
            portfolio_monthly = portfolio_series.resample('M').last()
            
            for i in range(1, len(portfolio_monthly)):
                monthly_ret = (portfolio_monthly.iloc[i] / portfolio_monthly.iloc[i-1] - 1) * 100
                month_name = portfolio_monthly.index[i].strftime('%B')
                monthly_returns.append(monthly_ret)
                print(f"{month_name:>10}: {monthly_ret:+6.2f}%")
            
            # Export 2024 results
            results_df = pd.DataFrame({
                'date': portfolio_series.index,
                'account_value': portfolio_series.values,
                'daily_return': [np.nan] + returns.tolist()
            })
            results_df.to_csv('production_2024_results.csv', index=False)
            print(f"\n💾 Results exported: production_2024_results.csv ({len(results_df)} records)")
            
            # Individual instrument performance 2024
            print(f"\n📊 INDIVIDUAL INSTRUMENT PERFORMANCE 2024")
            print("=" * 60)
            
            sorted_instruments = sorted(instrument_results.items(), key=lambda x: x[1]['return'], reverse=True)
            for instrument, data in sorted_instruments:
                print(f"{instrument:>7}: {data['return']:+7.2f}% return, {data['volatility']:5.1f}% vol")
            
            # Compare to benchmarks
            print(f"\n🏆 PERFORMANCE COMPARISON 2024")
            print("=" * 40)
            best_instrument = max(instrument_results.items(), key=lambda x: x[1]['return'])
            worst_instrument = min(instrument_results.items(), key=lambda x: x[1]['return'])
            
            print(f"🏭 Production System: {total_return:+7.2f}%")
            print(f"🥇 Best Single ({best_instrument[0]}): {best_instrument[1]['return']:+7.2f}%")
            print(f"🥉 Worst Single ({worst_instrument[0]}): {worst_instrument[1]['return']:+7.2f}%")
            
            # Calculate what equal weight would have done
            avg_return = sum(data['return'] for data in instrument_results.values()) / len(instrument_results)
            print(f"⚖️  Simple Average: {avg_return:+7.2f}%")
            print(f"📊 System vs Average: {total_return - avg_return:+7.2f}%")
            
            # Risk comparison
            avg_vol = sum(data['volatility'] for data in instrument_results.values()) / len(instrument_results)
            print(f"\n📊 RISK COMPARISON")
            print("=" * 25)
            print(f"🏭 System Volatility: {annualized_vol:5.1f}%")
            print(f"⚖️  Average Single Vol: {avg_vol:5.1f}%")
            print(f"🛡️  Diversification Benefit: {avg_vol - annualized_vol:+5.1f}%")
            
        else:
            print("❌ Insufficient common trading days for 2024 analysis")
    
    else:
        print("❌ No instruments have 2024 data available")

if __name__ == "__main__":
    analyze_2024_production()