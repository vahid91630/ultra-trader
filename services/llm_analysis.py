#!/usr/bin/env python3
"""
Ultra Trader LLM Analysis Service

Optional GPT-based analysis scaffold for market insights and model explanations.
Disabled by default; requires OPENAI_API_KEY or other provider API key.

Usage:
    from services.llm_analysis import LLMAnalyzer
    
    analyzer = LLMAnalyzer()
    analysis = analyzer.analyze_market_data(price_data, predictions)
    print(analysis)
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Graceful dependency handling
try:
    import pandas as pd
    import numpy as np
    
    # Optional LLM dependencies
    OPENAI_AVAILABLE = False
    try:
        import openai
        OPENAI_AVAILABLE = True
    except ImportError:
        logger.info("OpenAI not available. LLM analysis will be disabled.")

except ImportError as e:
    logger.error(f"Critical dependency missing: {e}")
    raise

warnings.filterwarnings('ignore')


class LLMAnalyzer:
    """
    LLM-based analysis service for trading insights.
    
    Provides market analysis, model explanations, and trading recommendations
    using large language models. Disabled by default for safety.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.3
    ):
        """
        Initialize LLM analyzer.
        
        Args:
            provider: LLM provider ("openai", "anthropic", etc.)
            model: Model name to use
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
        """
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enabled = False
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize LLM client if API key is available."""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and OPENAI_AVAILABLE:
                try:
                    self.client = openai.OpenAI(api_key=api_key)
                    self.enabled = True
                    logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")
            else:
                if not api_key:
                    logger.info("OPENAI_API_KEY not set. LLM analysis disabled.")
                if not OPENAI_AVAILABLE:
                    logger.info("OpenAI library not available. Install with: pip install openai")
        
        else:
            logger.warning(f"Provider '{self.provider}' not yet supported")
    
    def is_enabled(self) -> bool:
        """Check if LLM analysis is enabled."""
        return self.enabled
    
    def _get_fallback_message(self, analysis_type: str) -> str:
        """Get helpful fallback message when LLM is disabled."""
        messages = {
            "market": """
🤖 LLM Market Analysis (Disabled)

To enable AI-powered market analysis, set your OpenAI API key:
export OPENAI_API_KEY="your-api-key-here"

When enabled, this service provides:
• Market trend analysis
• Pattern recognition insights  
• Risk assessment summaries
• Trading opportunity identification

For now, consider these manual analysis steps:
1. Review recent price movements and volatility
2. Check correlation with broader market indices
3. Analyze volume patterns and support/resistance levels
4. Monitor relevant news and economic indicators
            """.strip(),
            
            "model": """
🤖 LLM Model Explanation (Disabled)

To enable AI-powered model explanations, set your OpenAI API key:
export OPENAI_API_KEY="your-api-key-here"

When enabled, this service provides:
• Plain-English model explanations
• Feature importance narratives
• Prediction confidence analysis
• Risk factor identification

For now, consider these analysis approaches:
1. Review SHAP feature importance plots
2. Analyze prediction distributions
3. Check model performance metrics
4. Validate predictions against market conditions
            """.strip(),
            
            "signals": """
🤖 LLM Signal Analysis (Disabled)

To enable AI-powered signal analysis, set your OpenAI API key:
export OPENAI_API_KEY="your-api-key-here"

When enabled, this service provides:
• Signal strength assessment
• Market timing insights
• Risk-adjusted recommendations
• Portfolio allocation suggestions

For now, consider these manual checks:
1. Validate signals against technical indicators
2. Check signal consistency over time
3. Analyze correlation with market conditions
4. Review backtesting performance metrics
            """.strip()
        }
        
        return messages.get(analysis_type, "LLM analysis not available. Set OPENAI_API_KEY to enable.")
    
    def analyze_market_data(
        self,
        price_data: pd.DataFrame,
        predictions: Optional[pd.Series] = None,
        timeframe: str = "daily"
    ) -> str:
        """
        Analyze market data and provide insights.
        
        Args:
            price_data: DataFrame with OHLCV data
            predictions: Optional model predictions
            timeframe: Data timeframe ("daily", "hourly", etc.)
        
        Returns:
            Market analysis string
        """
        if not self.enabled:
            return self._get_fallback_message("market")
        
        try:
            # Prepare market summary
            latest_price = price_data['close'].iloc[-1]
            price_change = price_data['close'].pct_change().iloc[-1]
            volatility = price_data['close'].pct_change().std() * 100
            
            # Create prompt
            prompt = self._create_market_analysis_prompt(
                latest_price, price_change, volatility, predictions, timeframe
            )
            
            # Get LLM response
            response = self._query_llm(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return self._get_fallback_message("market")
    
    def explain_model_predictions(
        self,
        feature_importance: pd.Series,
        predictions: pd.Series,
        model_metrics: Dict[str, float]
    ) -> str:
        """
        Explain model predictions in plain English.
        
        Args:
            feature_importance: Feature importance scores
            predictions: Model predictions
            model_metrics: Model performance metrics
        
        Returns:
            Model explanation string
        """
        if not self.enabled:
            return self._get_fallback_message("model")
        
        try:
            # Create prompt
            prompt = self._create_model_explanation_prompt(
                feature_importance, predictions, model_metrics
            )
            
            # Get LLM response
            response = self._query_llm(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Model explanation failed: {e}")
            return self._get_fallback_message("model")
    
    def analyze_trading_signals(
        self,
        signals: pd.Series,
        price_data: pd.DataFrame,
        confidence_scores: Optional[pd.Series] = None
    ) -> str:
        """
        Analyze trading signals and provide recommendations.
        
        Args:
            signals: Trading signals (1=long, 0=flat, -1=short)
            price_data: Price data for context
            confidence_scores: Optional prediction confidence scores
        
        Returns:
            Signal analysis string
        """
        if not self.enabled:
            return self._get_fallback_message("signals")
        
        try:
            # Create prompt
            prompt = self._create_signal_analysis_prompt(
                signals, price_data, confidence_scores
            )
            
            # Get LLM response
            response = self._query_llm(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Signal analysis failed: {e}")
            return self._get_fallback_message("signals")
    
    def _create_market_analysis_prompt(
        self,
        latest_price: float,
        price_change: float,
        volatility: float,
        predictions: Optional[pd.Series],
        timeframe: str
    ) -> str:
        """Create prompt for market analysis."""
        
        prompt = f"""
You are a professional quantitative analyst. Analyze the following market data and provide insights:

Current Market State:
- Latest Price: ${latest_price:.2f}
- Price Change: {price_change*100:.2f}%
- Volatility ({timeframe}): {volatility:.2f}%

"""
        
        if predictions is not None:
            recent_predictions = predictions.tail(10).tolist()
            prompt += f"Recent Model Predictions: {recent_predictions}\n"
        
        prompt += """
Please provide:
1. Current market sentiment assessment
2. Key risk factors to monitor
3. Potential trading opportunities
4. Risk management recommendations

Keep the analysis concise and actionable. Focus on practical insights for traders.
"""
        
        return prompt
    
    def _create_model_explanation_prompt(
        self,
        feature_importance: pd.Series,
        predictions: pd.Series,
        model_metrics: Dict[str, float]
    ) -> str:
        """Create prompt for model explanation."""
        
        top_features = feature_importance.head(10)
        recent_predictions = predictions.tail(20)
        
        prompt = f"""
You are a machine learning expert explaining a trading model to a portfolio manager.

Model Performance:
"""
        
        for metric, value in model_metrics.items():
            prompt += f"- {metric.replace('_', ' ').title()}: {value:.4f}\n"
        
        prompt += f"""

Top Important Features:
"""
        for feature, importance in top_features.items():
            prompt += f"- {feature}: {importance:.4f}\n"
        
        prompt += f"""

Recent Predictions (0=down, 1=up): {recent_predictions.tolist()}

Please explain:
1. What the model is actually learning
2. Which market factors are most influential
3. How reliable the predictions appear to be
4. Potential model limitations or biases

Use plain English and focus on practical implications for trading decisions.
"""
        
        return prompt
    
    def _create_signal_analysis_prompt(
        self,
        signals: pd.Series,
        price_data: pd.DataFrame,
        confidence_scores: Optional[pd.Series]
    ) -> str:
        """Create prompt for signal analysis."""
        
        recent_signals = signals.tail(20).tolist()
        recent_returns = price_data['close'].pct_change().tail(20).tolist()
        
        prompt = f"""
You are a trading strategist analyzing model-generated signals.

Recent Signals (1=long, 0=flat, -1=short): {recent_signals}
Corresponding Returns: {[f"{r*100:.2f}%" for r in recent_returns if not pd.isna(r)]}

"""
        
        if confidence_scores is not None:
            recent_confidence = confidence_scores.tail(20).tolist()
            prompt += f"Confidence Scores: {recent_confidence}\n"
        
        # Signal statistics
        signal_stats = {
            'Total Signals': len(signals),
            'Long Signals': (signals == 1).sum(),
            'Flat Signals': (signals == 0).sum(),
            'Short Signals': (signals == -1).sum() if (signals == -1).any() else 0
        }
        
        prompt += "Signal Distribution:\n"
        for stat, value in signal_stats.items():
            prompt += f"- {stat}: {value}\n"
        
        prompt += """

Please analyze:
1. Signal quality and consistency
2. Timing effectiveness
3. Risk-adjusted performance potential
4. Recommended position sizing or filters

Provide actionable insights for portfolio implementation.
"""
        
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with given prompt."""
        if not self.enabled or not self.client:
            raise ValueError("LLM client not available")
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional quantitative analyst and trading expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                return response.choices[0].message.content
            
            else:
                raise ValueError(f"Provider {self.provider} not supported")
                
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise
    
    def generate_trading_report(
        self,
        price_data: pd.DataFrame,
        predictions: pd.Series,
        signals: pd.Series,
        backtest_results: Dict[str, float],
        feature_importance: Optional[pd.Series] = None
    ) -> str:
        """
        Generate comprehensive trading report.
        
        Args:
            price_data: Market price data
            predictions: Model predictions
            signals: Trading signals
            backtest_results: Backtesting performance metrics
            feature_importance: Optional feature importance scores
        
        Returns:
            Comprehensive trading report
        """
        if not self.enabled:
            return """
🤖 Comprehensive Trading Report (Disabled)

To enable AI-powered comprehensive reports, set your OpenAI API key:
export OPENAI_API_KEY="your-api-key-here"

When enabled, this service provides:
• Integrated market and model analysis
• Performance assessment and insights
• Risk management recommendations
• Strategic trading guidance

For manual analysis, review these components:
1. Market Data: Check recent price movements and volatility
2. Model Performance: Review prediction accuracy and feature importance
3. Signal Quality: Analyze signal distribution and timing
4. Backtest Results: Evaluate risk-adjusted returns and drawdowns
            """.strip()
        
        try:
            # Create comprehensive prompt
            prompt = self._create_comprehensive_report_prompt(
                price_data, predictions, signals, backtest_results, feature_importance
            )
            
            # Get LLM response
            response = self._query_llm(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Trading report generation failed: {e}")
            return self._get_fallback_message("market")
    
    def _create_comprehensive_report_prompt(
        self,
        price_data: pd.DataFrame,
        predictions: pd.Series,
        signals: pd.Series,
        backtest_results: Dict[str, float],
        feature_importance: Optional[pd.Series]
    ) -> str:
        """Create prompt for comprehensive trading report."""
        
        # Market summary
        latest_price = price_data['close'].iloc[-1]
        total_return = (price_data['close'].iloc[-1] / price_data['close'].iloc[0] - 1) * 100
        volatility = price_data['close'].pct_change().std() * 100 * np.sqrt(252)
        
        prompt = f"""
You are a senior portfolio manager reviewing a quantitative trading strategy. 
Provide a comprehensive analysis and recommendations.

MARKET OVERVIEW:
- Current Price: ${latest_price:.2f}
- Total Period Return: {total_return:.2f}%
- Annualized Volatility: {volatility:.2f}%

BACKTEST PERFORMANCE:
"""
        
        for metric, value in backtest_results.items():
            prompt += f"- {metric.replace('_', ' ').title()}: {value:.4f}\n"
        
        # Signal analysis
        signal_stats = {
            'Total Signals': len(signals),
            'Long %': (signals == 1).mean() * 100,
            'Flat %': (signals == 0).mean() * 100,
        }
        
        if (signals == -1).any():
            signal_stats['Short %'] = (signals == -1).mean() * 100
        
        prompt += "\nSIGNAL DISTRIBUTION:\n"
        for stat, value in signal_stats.items():
            prompt += f"- {stat}: {value:.1f}%\n" if '%' in stat else f"- {stat}: {value}\n"
        
        # Feature importance (if available)
        if feature_importance is not None:
            top_features = feature_importance.head(5)
            prompt += "\nTOP MODEL FEATURES:\n"
            for feature, importance in top_features.items():
                prompt += f"- {feature}: {importance:.4f}\n"
        
        prompt += """

REQUESTED ANALYSIS:
1. Strategy Performance Assessment (strengths/weaknesses)
2. Risk Profile Evaluation
3. Market Conditions Impact
4. Implementation Recommendations
5. Potential Improvements

Provide executive-level insights suitable for investment committee review.
Format as a professional trading strategy report.
"""
        
        return prompt


# Utility functions for integration
def create_llm_analyzer(provider: str = "openai") -> LLMAnalyzer:
    """Create and return LLM analyzer instance."""
    return LLMAnalyzer(provider=provider)


def quick_market_analysis(price_data: pd.DataFrame) -> str:
    """Quick market analysis using LLM if available."""
    analyzer = create_llm_analyzer()
    return analyzer.analyze_market_data(price_data)


def quick_model_explanation(feature_importance: pd.Series, metrics: Dict[str, float]) -> str:
    """Quick model explanation using LLM if available."""
    analyzer = create_llm_analyzer()
    predictions = pd.Series([0.6, 0.7, 0.4, 0.8, 0.3])  # Dummy predictions
    return analyzer.explain_model_predictions(feature_importance, predictions, metrics)


# Demo function
def _demo_llm_analysis():
    """Demonstrate LLM analysis with sample data."""
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = np.cumsum(np.random.randn(100) * 0.02) + 100
    
    price_data = pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'open': prices * (1 + np.random.randn(100) * 0.001),
        'high': prices * (1 + abs(np.random.randn(100)) * 0.005),
        'low': prices * (1 - abs(np.random.randn(100)) * 0.005),
        'volume': np.random.lognormal(10, 1, 100)
    })
    
    # Create analyzer
    analyzer = create_llm_analyzer()
    
    # Test market analysis
    analysis = analyzer.analyze_market_data(price_data)
    print("Market Analysis:")
    print("-" * 50)
    print(analysis)
    
    return analysis


if __name__ == "__main__":
    _demo_llm_analysis()