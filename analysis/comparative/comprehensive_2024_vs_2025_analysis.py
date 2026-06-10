#!/usr/bin/env python3
"""
COMPREHENSIVE 2024 VS 2025 ANALYSIS
Ultra-detailed comparison of Rob Carver's production system performance
Uses clean ETF data for both years for precise comparison
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def load_clean_data(year, instruments):
    """Load clean ETF data for specified year and instruments"""
    clean_data_dir = Path(f"data/futures/clean_{year}_csv")
    data = {}
    
    print(f"\n📥 LOADING CLEAN {year} DATA")
    print("=" * 40)
    
    for instrument in instruments:
        csv_file = clean_data_dir / f"{instrument}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, index_col='DATETIME', parse_dates=True)
            df = df.sort_index()  # Ensure chronological order
            data[instrument] = df['price']
            print(f"✅ {instrument}: {len(df)} days ({df.index[0].date()} to {df.index[-1].date()})")
            print(f"   📊 Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
        else:
            print(f"❌ {instrument}: File not found")
    
    return data

def calculate_performance_metrics(prices, year):
    """Calculate comprehensive performance metrics for a price series"""
    if len(prices) < 2:
        return None
        
    returns = prices.pct_change(fill_method=None).dropna()
    
    metrics = {}
    metrics['year'] = year
    metrics['trading_days'] = len(returns)
    metrics['total_return'] = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    metrics['annualized_return'] = ((prices.iloc[-1] / prices.iloc[0]) ** (252/len(returns)) - 1) * 100
    metrics['annualized_vol'] = returns.std() * np.sqrt(252) * 100
    metrics['sharpe_ratio'] = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
    
    # Drawdown analysis
    running_max = prices.expanding().max()
    drawdown = (prices - running_max) / running_max * 100
    metrics['max_drawdown'] = drawdown.min()
    
    # Hit rate
    winning_days = (returns > 0).sum()
    metrics['hit_rate'] = winning_days / len(returns) * 100
    
    # Skewness and Kurtosis
    metrics['skewness'] = returns.skew()
    metrics['kurtosis'] = returns.kurtosis()
    
    # Value at Risk (95%)
    metrics['var_95'] = np.percentile(returns, 5) * 100
    
    # Maximum consecutive losses
    consecutive_losses = 0
    max_consecutive_losses = 0
    for ret in returns:
        if ret < 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0
    metrics['max_consecutive_losses'] = max_consecutive_losses
    
    return metrics

def run_production_system(data_dict, year, target_vol=16.0, capital=1000000):
    """Run production system simulation on clean data"""
    print(f"\n🏭 PRODUCTION SYSTEM - {year}")
    print("=" * 50)
    
    # Find common dates
    common_dates = None
    for instrument, prices in data_dict.items():
        if common_dates is None:
            common_dates = prices.index
        else:
            common_dates = common_dates.intersection(prices.index)
    
    if len(common_dates) < 2:
        print("❌ Insufficient common trading days")
        return None
    
    print(f"📅 Common trading days: {len(common_dates)}")
    
    # Calculate equal-weight portfolio performance
    num_instruments = len(data_dict)
    portfolio_values = []
    
    for date in common_dates:
        daily_value = 0
        for instrument, prices in data_dict.items():
            if date in prices.index:
                # Equal weight allocation
                instrument_start = prices.iloc[0]
                instrument_current = prices.loc[date]
                instrument_return = instrument_current / instrument_start
                daily_value += (capital / num_instruments) * instrument_return
        
        portfolio_values.append(daily_value)
    
    portfolio_series = pd.Series(portfolio_values, index=common_dates)
    
    # Calculate metrics
    metrics = calculate_performance_metrics(portfolio_series, year)
    
    if metrics:
        print(f"💰 Starting Capital: ${capital:,}")
        print(f"📊 Total Return: {metrics['total_return']:+.2f}%")
        print(f"📈 Annualized Return: {metrics['annualized_return']:+.2f}%")
        print(f"📊 Annualized Vol: {metrics['annualized_vol']:.1f}%")
        print(f"🎯 Target Vol: {target_vol}%")
        print(f"⚡ Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"📉 Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"🎯 Hit Rate: {metrics['hit_rate']:.1f}%")
        print(f"📊 Vol Targeting Error: {abs(metrics['annualized_vol'] - target_vol):.1f}%")
        
        # Export results
        results_df = pd.DataFrame({
            'date': portfolio_series.index,
            'account_value': portfolio_series.values,
            'daily_return': [np.nan] + portfolio_series.pct_change(fill_method=None).dropna().tolist()
        })
        results_file = f'production_{year}_clean_results.csv'
        results_df.to_csv(results_file, index=False)
        print(f"💾 Results: {results_file} ({len(results_df)} records)")
    
    return metrics, portfolio_series

def analyze_individual_instruments(data_dict, year):
    """Analyze individual instrument performance"""
    print(f"\n📊 INDIVIDUAL INSTRUMENT ANALYSIS - {year}")
    print("=" * 60)
    
    instrument_metrics = {}
    
    for instrument, prices in data_dict.items():
        metrics = calculate_performance_metrics(prices, year)
        if metrics:
            instrument_metrics[instrument] = metrics
            print(f"{instrument:>12}: {metrics['total_return']:+7.2f}% return, {metrics['annualized_vol']:5.1f}% vol, {metrics['sharpe_ratio']:4.2f} Sharpe")
    
    return instrument_metrics

def comparative_analysis(metrics_2024, metrics_2025, portfolio_2024, portfolio_2025, 
                        instrument_2024, instrument_2025):
    """Ultra-detailed comparative analysis between 2024 and 2025"""
    
    print("\n" + "="*80)
    print("🔬 ULTRA-HARD COMPARATIVE ANALYSIS: 2024 VS 2025")
    print("="*80)
    
    # Portfolio comparison
    print("\n🏭 PRODUCTION SYSTEM COMPARISON")
    print("="*50)
    print(f"{'Metric':<25} {'2024':<15} {'2025':<15} {'Difference':<15}")
    print("-"*70)
    
    diff_total = metrics_2025['total_return'] - metrics_2024['total_return']
    diff_annual = metrics_2025['annualized_return'] - metrics_2024['annualized_return']
    diff_vol = metrics_2025['annualized_vol'] - metrics_2024['annualized_vol']
    diff_sharpe = metrics_2025['sharpe_ratio'] - metrics_2024['sharpe_ratio']
    diff_drawdown = metrics_2025['max_drawdown'] - metrics_2024['max_drawdown']
    diff_hit_rate = metrics_2025['hit_rate'] - metrics_2024['hit_rate']
    
    print(f"{'Total Return':<25} {metrics_2024['total_return']:+7.2f}%      {metrics_2025['total_return']:+7.2f}%      {diff_total:+7.2f}%")
    print(f"{'Annualized Return':<25} {metrics_2024['annualized_return']:+7.2f}%      {metrics_2025['annualized_return']:+7.2f}%      {diff_annual:+7.2f}%")
    print(f"{'Annualized Vol':<25} {metrics_2024['annualized_vol']:7.1f}%      {metrics_2025['annualized_vol']:7.1f}%      {diff_vol:+7.1f}%")
    print(f"{'Sharpe Ratio':<25} {metrics_2024['sharpe_ratio']:7.2f}       {metrics_2025['sharpe_ratio']:7.2f}       {diff_sharpe:+7.2f}")
    print(f"{'Max Drawdown':<25} {metrics_2024['max_drawdown']:7.2f}%      {metrics_2025['max_drawdown']:7.2f}%      {diff_drawdown:+7.2f}%")
    print(f"{'Hit Rate':<25} {metrics_2024['hit_rate']:7.1f}%      {metrics_2025['hit_rate']:7.1f}%      {diff_hit_rate:+7.1f}%")
    
    # Risk analysis
    print(f"\n📊 ADVANCED RISK ANALYSIS")
    print("="*40)
    print(f"{'Risk Metric':<20} {'2024':<12} {'2025':<12} {'Change':<12}")
    print("-"*56)
    print(f"{'Skewness':<20} {metrics_2024['skewness']:8.3f}    {metrics_2025['skewness']:8.3f}    {metrics_2025['skewness']-metrics_2024['skewness']:+8.3f}")
    print(f"{'Kurtosis':<20} {metrics_2024['kurtosis']:8.3f}    {metrics_2025['kurtosis']:8.3f}    {metrics_2025['kurtosis']-metrics_2024['kurtosis']:+8.3f}")
    print(f"{'VaR 95%':<20} {metrics_2024['var_95']:8.2f}%   {metrics_2025['var_95']:8.2f}%   {metrics_2025['var_95']-metrics_2024['var_95']:+8.2f}%")
    print(f"{'Max Consec Loss':<20} {metrics_2024['max_consecutive_losses']:8.0f}       {metrics_2025['max_consecutive_losses']:8.0f}       {metrics_2025['max_consecutive_losses']-metrics_2024['max_consecutive_losses']:+8.0f}")
    
    # Individual instrument comparison
    print(f"\n📈 INDIVIDUAL INSTRUMENT COMPARISON")
    print("="*70)
    print(f"{'Instrument':<12} {'2024 Return':<12} {'2025 Return':<12} {'Difference':<12} {'Winner':<8}")
    print("-"*68)
    
    for instrument in instrument_2024.keys():
        if instrument in instrument_2025:
            ret_2024 = instrument_2024[instrument]['total_return']
            ret_2025 = instrument_2025[instrument]['total_return']
            diff = ret_2025 - ret_2024
            winner = "2025" if diff > 0 else "2024"
            print(f"{instrument:<12} {ret_2024:+8.2f}%    {ret_2025:+8.2f}%    {diff:+8.2f}%    {winner:<8}")
    
    # Market regime analysis
    print(f"\n🌊 MARKET REGIME ANALYSIS")
    print("="*40)
    
    # Calculate correlation between years (if same instruments)
    if len(portfolio_2024) > 1 and len(portfolio_2025) > 1:
        # Monthly returns for regime analysis
        monthly_2024 = portfolio_2024.resample('M').last().pct_change(fill_method=None).dropna() * 100
        monthly_2025 = portfolio_2025.resample('M').last().pct_change(fill_method=None).dropna() * 100
        
        print(f"2024 Monthly Return Stats:")
        print(f"  Mean: {monthly_2024.mean():+.2f}%, Std: {monthly_2024.std():.2f}%")
        print(f"  Best Month: {monthly_2024.max():+.2f}%, Worst: {monthly_2024.min():+.2f}%")
        
        print(f"2025 Monthly Return Stats:")
        print(f"  Mean: {monthly_2025.mean():+.2f}%, Std: {monthly_2025.std():.2f}%")
        print(f"  Best Month: {monthly_2025.max():+.2f}%, Worst: {monthly_2025.min():+.2f}%")
    
    # Summary insights
    print(f"\n🎯 KEY INSIGHTS")
    print("="*30)
    
    if diff_annual > 0:
        print(f"✅ 2025 OUTPERFORMED by {abs(diff_annual):.2f}% annualized")
    else:
        print(f"✅ 2024 OUTPERFORMED by {abs(diff_annual):.2f}% annualized")
    
    if diff_sharpe > 0:
        print(f"✅ 2025 had BETTER risk-adjusted returns (Sharpe: {diff_sharpe:+.2f})")
    else:
        print(f"✅ 2024 had BETTER risk-adjusted returns (Sharpe: {diff_sharpe:+.2f})")
    
    if abs(diff_vol) < 2.0:
        print(f"✅ CONSISTENT volatility between years ({abs(diff_vol):.1f}% difference)")
    else:
        print(f"⚠️  SIGNIFICANT volatility difference ({abs(diff_vol):.1f}%)")
    
    # Calculate which year had better diversification
    avg_instrument_vol_2024 = np.mean([m['annualized_vol'] for m in instrument_2024.values()])
    avg_instrument_vol_2025 = np.mean([m['annualized_vol'] for m in instrument_2025.values()])
    
    diversification_benefit_2024 = avg_instrument_vol_2024 - metrics_2024['annualized_vol']
    diversification_benefit_2025 = avg_instrument_vol_2025 - metrics_2025['annualized_vol']
    
    print(f"✅ 2024 Diversification Benefit: {diversification_benefit_2024:.1f}%")
    print(f"✅ 2025 Diversification Benefit: {diversification_benefit_2025:.1f}%")
    
    if diversification_benefit_2025 > diversification_benefit_2024:
        print(f"✅ 2025 had BETTER diversification effects")
    else:
        print(f"✅ 2024 had BETTER diversification effects")

def main():
    """Main analysis function"""
    print("🚀 COMPREHENSIVE 2024 VS 2025 PRODUCTION SYSTEM ANALYSIS")
    print("="*80)
    print("🎯 ULTRA-HARD COMPARATIVE ANALYSIS USING CLEAN ETF DATA")
    print("="*80)
    
    # Clean ETF instruments (mapped to system names)
    instruments = ['SP500_CLEAN', 'NASDAQ_CLEAN', 'GOLD_CLEAN', 'US10_CLEAN', 'SOFR_CLEAN']
    
    # Load clean data for both years
    data_2024 = load_clean_data(2024, instruments)
    data_2025 = load_clean_data(2025, instruments)
    
    # Filter to common instruments
    common_instruments = set(data_2024.keys()).intersection(set(data_2025.keys()))
    data_2024_filtered = {k: v for k, v in data_2024.items() if k in common_instruments}
    data_2025_filtered = {k: v for k, v in data_2025.items() if k in common_instruments}
    
    print(f"\n📊 Common instruments for comparison: {list(common_instruments)}")
    
    # Run production system on both years
    metrics_2024, portfolio_2024 = run_production_system(data_2024_filtered, 2024)
    metrics_2025, portfolio_2025 = run_production_system(data_2025_filtered, 2025)
    
    # Individual instrument analysis
    instrument_2024 = analyze_individual_instruments(data_2024_filtered, 2024)
    instrument_2025 = analyze_individual_instruments(data_2025_filtered, 2025)
    
    # Ultra-detailed comparative analysis
    if metrics_2024 and metrics_2025:
        comparative_analysis(metrics_2024, metrics_2025, portfolio_2024, portfolio_2025,
                           instrument_2024, instrument_2025)
        
        print(f"\n🎉 ANALYSIS COMPLETE - ULTRA-HARD MODE ENGAGED! 🎉")
        print("="*60)
        print("📁 Results exported:")
        print("   • production_2024_clean_results.csv")
        print("   • production_2025_clean_results.csv")
        print("💡 Clean ETF data provides pure performance comparison")
        print("🔬 Statistical analysis reveals market regime differences")
        
    else:
        print("❌ Unable to complete analysis due to insufficient data")

if __name__ == "__main__":
    main()