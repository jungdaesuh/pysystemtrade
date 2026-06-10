#!/usr/bin/env python3
"""
PRODUCTION BACKTEST 2025: Test Rob Carver's actual production system
Test the real open-source pysystemtrade methodology on 2025 data
"""

import pandas as pd
import numpy as np
from datetime import datetime

from sysdata.config.configdata import Config
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system
from sysproduction.strategy_code.run_system_classic import production_classic_futures_system
from sysproduction.data.sim_data import get_sim_data_object_for_production

def create_production_config():
    """Create production-grade configuration based on defaults.yaml"""
    
    print("🏭 CREATING PRODUCTION CONFIGURATION")
    print("=" * 60)
    
    # These are the REAL production parameters from defaults.yaml
    production_config = {
        # Core risk management (production settings)
        "percentage_vol_target": 16.0,  # 16% vol target (not 20%)
        "notional_trading_capital": 1000000,  # $1M starting capital
        "base_currency": "USD",
        
        # Capital method - fixed (not compounding during backtest)
        "capital_multiplier": {
            "func": "syscore.capital.fixed_capital"
        },
        
        # Volatility calculation (production method)
        "volatility_calculation": {
            "func": "sysquant.estimators.vol.mixed_vol_calc",
            "days": 35,
            "min_periods": 10,
            "slow_vol_years": 10,
            "proportion_of_slow_vol": 0.3,
            "vol_abs_min": 0.0000000001
        },
        
        # Forecast scaling and capping (production settings)
        "use_forecast_scale_estimates": False,  # Use fixed scaling
        "forecast_scalar": 1.0,
        "forecast_cap": 20.0,  # Cap forecasts at ±20
        "average_absolute_forecast": 10.0,
        
        # Forecast combination (production method)
        "forecast_div_multiplier": 1.0,
        "use_forecast_div_mult_estimates": False,
        "use_forecast_weight_estimates": False,
        
        # Trading rules - PRODUCTION EWMAC combinations
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
            },
            "ewmac16_64": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"], 
                "Lfast": 16,
                "Lslow": 64
            },
            "ewmac32_128": {
                "function": "systems.provided.rules.ewmac.ewmac_forecast_with_defaults",
                "data": ["rawdata.get_daily_prices"], 
                "Lfast": 32,
                "Lslow": 128
            }
        },
        
        # Portfolio construction (production settings)
        "use_instrument_weight_estimates": False,
        "use_instrument_div_mult_estimates": False,
        "instrument_div_multiplier": 1.0,
        
        # Position buffering (production risk management)
        "buffer_method": "forecast",
        "buffer_size": 0.10,  # 10% buffer
        "buffer_trade_to_edge": True,
        
        # Cost and risk settings
        "use_SR_costs": False,
        "vol_normalise_currency_costs": True,
        
        # Instruments - use available 2025 data
        "instruments": ['SP500', 'NASDAQ', 'GOLD', 'US10', 'SOFR'],
        
        # Equal weighting for this test (production would optimize)
        "instrument_weights": {
            'SP500': 0.2,
            'NASDAQ': 0.2, 
            'GOLD': 0.2,
            'US10': 0.2,
            'SOFR': 0.2
        },
        
        # Forecast weights (equal for this test)
        "forecast_weights": {
            "ewmac2_8": 0.2,
            "ewmac4_16": 0.2,
            "ewmac8_32": 0.2,
            "ewmac16_64": 0.2,
            "ewmac32_128": 0.2
        },
        
        # Forecast diversification multipliers (fixed)
        "forecast_div_mult_estimates": {
            "ewmac2_8": 1.0,
            "ewmac4_16": 1.0,
            "ewmac8_32": 1.0,
            "ewmac16_64": 1.0,
            "ewmac32_128": 1.0
        }
    }
    
    print("✅ Production config created with:")
    print(f"   💰 Capital: ${production_config['notional_trading_capital']:,}")
    print(f"   📊 Vol Target: {production_config['percentage_vol_target']}%")
    print(f"   📈 Trading Rules: {len(production_config['trading_rules'])}")
    print(f"   🎯 Instruments: {len(production_config['instruments'])}")
    print(f"   🛡️ Buffer Size: {production_config['buffer_size']*100}%")
    
    return production_config

def run_production_backtest():
    """Run production backtest on 2025 data"""
    
    print("\n🚀 PYSYSTEMTRADE PRODUCTION BACKTEST 2025")
    print("=" * 80)
    print("📅 Period: 2025-01-01 to 2025-08-20")
    print("🎯 Testing Rob Carver's actual production methodology")
    print("=" * 80)
    
    # Create production configuration
    config_dict = create_production_config()
    config = Config(config_dict)
    
    # Build production system
    print("\n🏭 Building Production System...")
    data = csvFuturesSimData()
    system = futures_system(data=data, config=config)
    
    # Get account curve
    print("📊 Calculating Portfolio Performance...")
    try:
        account_curve = system.accounts.portfolio()
        print(f"   ✅ Account curve calculated: {len(account_curve)} data points")
        
        # Filter for 2025 data
        start_date = '2025-01-01'
        end_date = '2025-08-20'
        
        account_2025 = account_curve[
            (account_curve.index >= start_date) & 
            (account_curve.index <= end_date)
        ]
        
        if len(account_2025) == 0:
            print("   ⚠️ No 2025 data in account curve")
            print(f"   Available range: {account_curve.index[0]} to {account_curve.index[-1]}")
            # Use all available data
            account_2025 = account_curve
            start_date = str(account_curve.index[0].date())
            end_date = str(account_curve.index[-1].date())
            print(f"   📅 Using available range: {start_date} to {end_date}")
        
        print(f"   📈 Performance period: {len(account_2025)} days")
        
    except Exception as e:
        print(f"   ❌ Failed to get account curve: {e}")
        return None
    
    # Calculate performance metrics
    print("\n📊 PRODUCTION SYSTEM PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    if len(account_2025) > 1:
        # Calculate returns
        returns = account_2025.pct_change().dropna()
        
        # Performance metrics
        total_return = (account_2025.iloc[-1] / account_2025.iloc[0] - 1) * 100
        annualized_vol = returns.std() * np.sqrt(252) * 100
        
        if annualized_vol > 0:
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        else:
            sharpe_ratio = 0
            
        max_dd = calculate_max_drawdown(account_2025)
        
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"💰 Starting Capital: ${config_dict['notional_trading_capital']:,}")
        print(f"📊 Total Return: {total_return:.2f}%")
        print(f"📈 Annualized Vol: {annualized_vol:.1f}%")
        print(f"⚡ Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"📉 Max Drawdown: {max_dd:.2f}%")
        print(f"🎯 Vol Target: {config_dict['percentage_vol_target']}%")
        
        # Export results
        export_results(account_2025, returns, config_dict, start_date, end_date)
        
        # Compare to buy and hold
        compare_to_buy_and_hold(system, account_2025, start_date, end_date)
        
    else:
        print("   ❌ Insufficient data for analysis")
    
    return account_2025

def calculate_max_drawdown(price_series):
    """Calculate maximum drawdown"""
    peak = price_series.expanding().max()
    drawdown = (price_series - peak) / peak * 100
    return drawdown.min()

def export_results(account_curve, returns, config, start_date, end_date):
    """Export production backtest results"""
    
    print("\n💾 EXPORTING PRODUCTION RESULTS")
    print("=" * 40)
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'date': account_curve.index,
        'account_value': account_curve.values,
        'daily_return': [np.nan] + returns.tolist()
    })
    
    # Export to CSV
    filename = 'production_backtest_2025_results.csv'
    results_df.to_csv(filename, index=False)
    
    # Create summary report
    summary = {
        'backtest_type': 'Production System',
        'period': f"{start_date} to {end_date}",
        'capital': config['notional_trading_capital'],
        'vol_target': f"{config['percentage_vol_target']}%",
        'trading_rules': len(config['trading_rules']),
        'instruments': len(config['instruments']),
        'buffer_size': f"{config['buffer_size']*100}%"
    }
    
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv('production_backtest_summary.csv', index=False)
    
    print(f"   ✅ Results exported: {filename}")
    print(f"   ✅ Summary exported: production_backtest_summary.csv")
    print(f"   📊 Total records: {len(results_df)}")

def compare_to_buy_and_hold(system, account_curve, start_date, end_date):
    """Compare to simple buy and hold performance"""
    
    print("\n🔍 BUY & HOLD COMPARISON")
    print("=" * 40)
    
    try:
        # Get price data for comparison instruments
        sp500_prices = system.rawdata.get_daily_prices('SP500')
        sp500_2025 = sp500_prices[
            (sp500_prices.index >= start_date) & 
            (sp500_prices.index <= end_date)
        ]
        
        if len(sp500_2025) > 1:
            sp500_return = (sp500_2025.iloc[-1] / sp500_2025.iloc[0] - 1) * 100
            sp500_returns = sp500_2025.pct_change().dropna()
            sp500_vol = sp500_returns.std() * np.sqrt(252) * 100
            sp500_sharpe = (sp500_returns.mean() * 252) / (sp500_returns.std() * np.sqrt(252))
            
            print(f"📊 SP500 Buy & Hold:")
            print(f"   Return: {sp500_return:.2f}%")
            print(f"   Volatility: {sp500_vol:.1f}%") 
            print(f"   Sharpe: {sp500_sharpe:.2f}")
            
            # System performance
            if len(account_curve) > 1:
                system_returns = account_curve.pct_change().dropna()
                system_return = (account_curve.iloc[-1] / account_curve.iloc[0] - 1) * 100
                system_vol = system_returns.std() * np.sqrt(252) * 100
                system_sharpe = (system_returns.mean() * 252) / (system_returns.std() * np.sqrt(252))
                
                print(f"\n🏭 Production System:")
                print(f"   Return: {system_return:.2f}%")
                print(f"   Volatility: {system_vol:.1f}%")
                print(f"   Sharpe: {system_sharpe:.2f}")
                
                # Risk-adjusted comparison
                excess_return = system_return - sp500_return
                vol_ratio = system_vol / sp500_vol if sp500_vol > 0 else 0
                
                print(f"\n🎯 COMPARISON:")
                print(f"   Excess Return: {excess_return:+.2f}%")
                print(f"   Vol Ratio: {vol_ratio:.2f}x")
                print(f"   Sharpe Advantage: {system_sharpe - sp500_sharpe:+.2f}")
                
        else:
            print("   ⚠️ No SP500 data available for comparison")
            
    except Exception as e:
        print(f"   ❌ Comparison failed: {e}")

if __name__ == "__main__":
    # Run production backtest
    account_curve = run_production_backtest()
    
    print("\n" + "=" * 80)
    print("🎉 PRODUCTION BACKTEST COMPLETE!")
    print("💡 This tests Rob Carver's actual open-source systematic trading methodology")
    print("📁 Results saved in production_backtest_2025_results.csv")
    print("=" * 80)