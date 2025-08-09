#!/usr/bin/env python3
"""
Ultra Trader Backtesting Module

Simple walk-forward backtesting utility for evaluating trading strategies
and ML model performance.

Usage:
    from evaluation.backtest import BacktestEngine
    
    signals = pd.Series([1, 0, 1, -1, 0])  # 1=long, 0=flat, -1=short
    prices = pd.Series([100, 102, 104, 103, 105])
    
    engine = BacktestEngine()
    results = engine.run_backtest(signals, prices)
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Union
import warnings

warnings.filterwarnings('ignore')


class BacktestEngine:
    """
    Simple backtesting engine for walk-forward analysis.
    
    Supports long/flat and long/short strategies with basic fee modeling.
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_rate: float = 0.001,  # 0.1% per trade
        risk_free_rate: float = 0.02  # 2% annual risk-free rate
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital for backtesting
            fee_rate: Transaction fee rate (fraction of trade value)
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.risk_free_rate = risk_free_rate
    
    def run_backtest(
        self,
        signals: pd.Series,
        prices: pd.Series,
        timestamps: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """
        Run backtest on given signals and prices.
        
        Args:
            signals: Trading signals (1=long, 0=flat, -1=short)
            prices: Price series corresponding to signals
            timestamps: Optional timestamp series for time-based metrics
        
        Returns:
            Dictionary with backtest results including returns, Sharpe, drawdown
        """
        if len(signals) != len(prices):
            raise ValueError("Signals and prices must have same length")
        
        if len(signals) < 2:
            raise ValueError("Need at least 2 data points for backtesting")
        
        # Align data
        df = pd.DataFrame({
            'signal': signals.values,
            'price': prices.values,
            'timestamp': timestamps.values if timestamps is not None else range(len(signals))
        })
        
        # Remove any NaN values
        df = df.dropna()
        
        if len(df) < 2:
            raise ValueError("Insufficient data after removing NaN values")
        
        # Calculate returns
        df['price_return'] = df['price'].pct_change()
        df['signal_prev'] = df['signal'].shift(1)
        
        # Calculate strategy returns
        strategy_returns = []
        current_position = 0
        total_fees = 0
        
        for i in range(1, len(df)):
            price_return = df.iloc[i]['price_return']
            signal_prev = df.iloc[i]['signal_prev']
            signal_current = df.iloc[i]['signal']
            
            # Position change
            position_change = signal_current - current_position
            
            # Calculate fees on position changes
            if abs(position_change) > 0:
                trade_value = abs(position_change) * df.iloc[i]['price']
                fee = trade_value * self.fee_rate
                total_fees += fee
            
            # Strategy return = position * price return
            strategy_return = current_position * price_return
            strategy_returns.append(strategy_return)
            
            # Update position
            current_position = signal_current
        
        df = df.iloc[1:].copy()  # Remove first row (no return)
        df['strategy_return'] = strategy_returns
        
        # Calculate equity curve
        df['equity'] = (1 + df['strategy_return']).cumprod() * self.initial_capital
        
        # Apply fees
        fee_impact = total_fees / self.initial_capital
        df['equity'] *= (1 - fee_impact)
        
        # Calculate metrics
        results = self._calculate_metrics(df, total_fees)
        
        return results
    
    def _calculate_metrics(self, df: pd.DataFrame, total_fees: float) -> Dict[str, float]:
        """Calculate performance metrics from backtest results."""
        
        # Basic returns
        total_return = (df['equity'].iloc[-1] / self.initial_capital) - 1
        
        # Annualized returns (assuming daily data)
        n_periods = len(df)
        periods_per_year = 252  # Trading days
        if n_periods > 0:
            annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
        else:
            annualized_return = 0
        
        # Volatility
        strategy_returns = df['strategy_return'].dropna()
        if len(strategy_returns) > 1:
            volatility = strategy_returns.std() * np.sqrt(periods_per_year)
        else:
            volatility = 0
        
        # Sharpe ratio
        if volatility > 0:
            excess_return = annualized_return - self.risk_free_rate
            sharpe_ratio = excess_return / volatility
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        peak = df['equity'].expanding().max()
        drawdown = (df['equity'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # Win rate
        positive_returns = (strategy_returns > 0).sum()
        total_trades = len(strategy_returns)
        win_rate = positive_returns / total_trades if total_trades > 0 else 0
        
        # Calmar ratio (annualized return / abs(max drawdown))
        if abs(max_drawdown) > 0:
            calmar_ratio = annualized_return / abs(max_drawdown)
        else:
            calmar_ratio = 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'final_equity': df['equity'].iloc[-1],
            'total_fees': total_fees,
            'fee_impact': total_fees / self.initial_capital
        }
    
    def run_walk_forward_backtest(
        self,
        model,
        X: pd.DataFrame,
        y: pd.Series,
        prices: pd.Series,
        train_window: int = 252,
        step_size: int = 21,
        threshold: float = 0.5
    ) -> Dict[str, float]:
        """
        Run walk-forward backtest with model retraining.
        
        Args:
            model: Sklearn-compatible model
            X: Feature matrix
            y: Target series
            prices: Price series
            train_window: Number of periods for training
            step_size: Number of periods between retraining
            threshold: Probability threshold for signal generation
        
        Returns:
            Backtest results dictionary
        """
        signals = []
        
        for i in range(train_window, len(X) - step_size, step_size):
            # Training data
            X_train = X.iloc[i-train_window:i]
            y_train = y.iloc[i-train_window:i]
            
            # Test data
            X_test = X.iloc[i:i+step_size]
            
            # Remove NaN values
            train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
            X_train_clean = X_train[train_mask]
            y_train_clean = y_train[train_mask]
            
            if len(X_train_clean) < 10:  # Minimum training samples
                signals.extend([0] * step_size)
                continue
            
            # Train model
            try:
                model.fit(X_train_clean, y_train_clean)
                
                # Generate predictions
                test_mask = ~X_test.isna().any(axis=1)
                X_test_clean = X_test[test_mask]
                
                if len(X_test_clean) > 0:
                    predictions = model.predict_proba(X_test_clean)[:, 1]
                    step_signals = (predictions > threshold).astype(int)
                    
                    # Fill in signals for all test periods
                    full_step_signals = []
                    clean_idx = 0
                    for j in range(step_size):
                        if j < len(test_mask) and test_mask.iloc[j]:
                            full_step_signals.append(step_signals[clean_idx])
                            clean_idx += 1
                        else:
                            full_step_signals.append(0)  # No signal for NaN
                    
                    signals.extend(full_step_signals)
                else:
                    signals.extend([0] * step_size)
                    
            except Exception as e:
                # If training fails, use neutral signals
                signals.extend([0] * step_size)
        
        # Pad signals to match price length
        if len(signals) < len(prices):
            signals.extend([0] * (len(prices) - len(signals)))
        elif len(signals) > len(prices):
            signals = signals[:len(prices)]
        
        # Run backtest
        signals_series = pd.Series(signals, index=prices.index)
        return self.run_backtest(signals_series, prices)


def calculate_portfolio_metrics(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
    risk_free_rate: float = 0.02
) -> Dict[str, float]:
    """
    Calculate portfolio performance metrics.
    
    Args:
        returns: Portfolio return series
        benchmark_returns: Optional benchmark return series
        risk_free_rate: Annual risk-free rate
    
    Returns:
        Dictionary of performance metrics
    """
    if len(returns) == 0:
        return {}
    
    # Remove NaN values
    returns = returns.dropna()
    
    if len(returns) == 0:
        return {}
    
    # Basic metrics
    total_return = (1 + returns).prod() - 1
    
    # Annualized metrics
    periods_per_year = 252
    n_periods = len(returns)
    
    if n_periods > 0:
        annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
    else:
        annualized_return = 0
    
    volatility = returns.std() * np.sqrt(periods_per_year)
    
    # Sharpe ratio
    if volatility > 0:
        excess_return = annualized_return - risk_free_rate
        sharpe_ratio = excess_return / volatility
    else:
        sharpe_ratio = 0
    
    # Drawdown analysis
    cumulative = (1 + returns).cumprod()
    peak = cumulative.expanding().max()
    drawdown = (cumulative - peak) / peak
    max_drawdown = drawdown.min()
    
    metrics = {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown
    }
    
    # Beta and alpha if benchmark provided
    if benchmark_returns is not None:
        benchmark_returns = benchmark_returns.dropna()
        
        # Align returns
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
        
        if len(aligned_returns) > 1:
            covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
            benchmark_variance = np.var(aligned_benchmark)
            
            if benchmark_variance > 0:
                beta = covariance / benchmark_variance
                
                benchmark_annualized = (1 + aligned_benchmark.mean()) ** periods_per_year - 1
                alpha = annualized_return - (risk_free_rate + beta * (benchmark_annualized - risk_free_rate))
                
                metrics['beta'] = beta
                metrics['alpha'] = alpha
    
    return metrics


# Example usage and testing
def _demo_backtest():
    """Demonstrate backtesting functionality."""
    np.random.seed(42)
    
    # Generate sample data
    n_periods = 252  # 1 year of daily data
    
    # Price series (random walk)
    prices = [100]
    for _ in range(n_periods - 1):
        change = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% volatility
        prices.append(prices[-1] * (1 + change))
    
    prices = pd.Series(prices)
    
    # Generate some signals (simple momentum strategy)
    returns = prices.pct_change()
    signals = (returns.rolling(5).mean() > 0).astype(int)
    
    # Run backtest
    engine = BacktestEngine(initial_capital=10000, fee_rate=0.001)
    results = engine.run_backtest(signals, prices)
    
    print("Backtest Results:")
    print("-" * 40)
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    return results


if __name__ == "__main__":
    _demo_backtest()