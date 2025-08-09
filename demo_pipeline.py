#!/usr/bin/env python3
"""
Ultra Trader ML Pipeline Demo

Demonstrates the ML pipeline functionality using mock data.
This demo works without requiring full ML dependencies installation.
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path

def create_sample_financial_data(n_samples=1000):
    """Create realistic sample financial data."""
    print("📊 Generating sample financial data...")
    
    np.random.seed(42)
    
    # Generate price series with trend and volatility
    prices = []
    price = 50000  # Starting price (like BTC)
    
    for i in range(n_samples):
        # Random walk with slight upward bias and volatility clustering
        if i < n_samples // 3:
            # Bull market phase
            change = np.random.normal(0.002, 0.015)
        elif i < 2 * n_samples // 3:
            # Sideways market
            change = np.random.normal(0.0, 0.025)
        else:
            # Volatile phase
            change = np.random.normal(0.001, 0.035)
        
        price *= (1 + change)
        prices.append(price)
    
    # Create timestamps (hourly data)
    timestamps = pd.date_range(start='2023-01-01', periods=n_samples, freq='1H')
    
    # Create OHLCV data
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        'close': prices,
        'volume': np.random.lognormal(15, 1, n_samples)
    })
    
    print(f"✅ Generated {len(df)} samples from {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"   Total return: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:.1f}%")
    
    return df

def demo_backtesting():
    """Demonstrate backtesting functionality."""
    print("\n🔬 Backtesting Demo")
    print("-" * 40)
    
    from evaluation.backtest import BacktestEngine
    
    # Create sample data
    df = create_sample_financial_data(252)  # 1 year of hourly data
    
    # Generate simple trading signals (momentum strategy)
    df['returns'] = df['close'].pct_change()
    df['sma_5'] = df['close'].rolling(5).mean()
    df['sma_20'] = df['close'].rolling(20).mean()
    
    # Long when 5-period SMA > 20-period SMA
    signals = (df['sma_5'] > df['sma_20']).astype(int)
    signals = signals.fillna(0)
    
    # Run backtest
    engine = BacktestEngine(
        initial_capital=10000,
        fee_rate=0.001,  # 0.1% trading fee
        risk_free_rate=0.02
    )
    
    results = engine.run_backtest(signals, df['close'])
    
    print("Backtest Results:")
    print(f"  Total Return: {results['total_return']:.1%}")
    print(f"  Annualized Return: {results['annualized_return']:.1%}")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {results['max_drawdown']:.1%}")
    print(f"  Win Rate: {results['win_rate']:.1%}")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Final Equity: ${results['final_equity']:.2f}")
    
    return results

def demo_llm_analysis():
    """Demonstrate LLM analysis (disabled mode)."""
    print("\n🤖 LLM Analysis Demo")
    print("-" * 40)
    
    from services.llm_analysis import LLMAnalyzer
    
    # Create sample data
    df = create_sample_financial_data(100)
    
    # Create analyzer
    analyzer = LLMAnalyzer()
    
    print(f"LLM Service Enabled: {analyzer.is_enabled()}")
    
    # Try market analysis (will show disabled message)
    analysis = analyzer.analyze_market_data(df)
    print("\nMarket Analysis Output:")
    print(analysis[:300] + "..." if len(analysis) > 300 else analysis)
    
    return analyzer

def demo_configuration():
    """Demonstrate configuration system."""
    print("\n⚙️ Configuration Demo")
    print("-" * 40)
    
    config_path = Path('configs/experiments/gbt_default.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Configuration Structure:")
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key in list(value.keys())[:3]:  # Show first 3 sub-keys
                print(f"    - {sub_key}")
            if len(value) > 3:
                print(f"    ... and {len(value) - 3} more")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nModel Type: {config.get('model_type')}")
    print(f"Data Source: {config.get('data', {}).get('source')}")
    print(f"Optuna Trials: {config.get('optuna', {}).get('n_trials')}")
    
    return config

def demo_training_pipeline_structure():
    """Show training pipeline structure without running it."""
    print("\n🏗️ Training Pipeline Structure")
    print("-" * 40)
    
    print("The training pipeline consists of these stages:")
    print("1. 📂 Data Loading")
    print("   - CSV or MongoDB data source")
    print("   - Automatic sample data generation if needed")
    
    print("2. 🔧 Feature Engineering") 
    print("   - Technical indicators (SMA, EMA, RSI, MACD, etc.)")
    print("   - Price-based features")
    print("   - Volume analysis")
    
    print("3. 🎯 Target Construction")
    print("   - Direction prediction (up/down)")
    print("   - Configurable prediction horizon")
    
    print("4. ✅ Cross-Validation")
    print("   - TimeSeriesSplit for temporal data")
    print("   - Prevents look-ahead bias")
    
    print("5. 🔍 Hyperparameter Optimization")
    print("   - Optuna Bayesian optimization")
    print("   - Model-specific parameter spaces")
    
    print("6. 🏋️ Final Training")
    print("   - LightGBM or XGBoost models")
    print("   - Early stopping and validation")
    
    print("7. 💾 Model Persistence")
    print("   - Save trained model and metadata")
    print("   - Ready for deployment")

def show_file_structure():
    """Show the complete file structure."""
    print("\n📁 File Structure")
    print("-" * 40)
    
    structure = {
        'training/': ['pipeline_gbt.py - Main training pipeline'],
        'evaluation/': ['backtest.py - Backtesting utilities'],
        'analysis/': ['explainability.py - SHAP analysis tools'],
        'configs/experiments/': ['gbt_default.yaml - Default configuration'],
        'services/': ['llm_analysis.py - Optional GPT analysis'],
        'models/': ['(auto-created) - Model artifacts'],
        'docs/': ['ML_PIPELINE.md - Complete documentation'],
        'requirements-ml.txt': ['ML dependencies'],
        '.gitignore': ['Excludes model artifacts']
    }
    
    for path, files in structure.items():
        if isinstance(files, list):
            print(f"{path}")
            for file_desc in files:
                print(f"  └── {file_desc}")
        else:
            print(f"{path} - {files}")

def main():
    """Run the complete demo."""
    print("🚀 Ultra Trader ML Pipeline Demo")
    print("=" * 50)
    print("This demo shows the ML pipeline functionality")
    print("without requiring full ML dependencies installation.")
    print("=" * 50)
    
    try:
        # Show structure
        show_file_structure()
        
        # Demo configuration
        demo_configuration()
        
        # Demo backtesting
        demo_backtesting()
        
        # Demo LLM analysis
        demo_llm_analysis()
        
        # Show training pipeline structure
        demo_training_pipeline_structure()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nNext steps:")
        print("1. Install ML dependencies: pip install -r requirements-ml.txt")
        print("2. Run training: python training/pipeline_gbt.py")
        print("3. Check saved models in models/ directory")
        print("4. Review docs/ML_PIPELINE.md for complete guide")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()