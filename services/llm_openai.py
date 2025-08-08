"""
OpenAI Service Layer for Ultra Trader
Provides robust wrapper over OpenAI Chat Completions with retry logic and error handling.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI service wrapper with configuration management and utility methods."""
    
    def __init__(self):
        """Initialize OpenAI service with environment-based configuration."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL")  # For Azure/other providers
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "30"))
        
        self.client = None
        self.available = False
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not installed. GPT features will be disabled.")
            return
            
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. GPT features will be disabled.")
            return
            
        try:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
                
            self.client = OpenAI(**kwargs)
            self.available = True
            logger.info(f"OpenAI service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.available
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get configuration status for dashboard display."""
        return {
            "available": self.available,
            "has_api_key": bool(self.api_key),
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "base_url": self.base_url,
            "openai_installed": OPENAI_AVAILABLE
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make a request to OpenAI with retry logic."""
        if not self.available:
            raise RuntimeError("OpenAI service not available")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise
    
    def chat(self, prompt: str, system: Optional[str] = None, tools: Optional[List] = None) -> str:
        """
        General chat completion method.
        
        Args:
            prompt: User prompt/question
            system: Optional system message to set context
            tools: Optional tools for function calling (not implemented yet)
            
        Returns:
            Generated response text
        """
        if not self.available:
            return "❌ OpenAI service not available. Please check API key configuration."
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            return self._make_request(messages)
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"
    
    def summarize_news(self, text: str) -> str:
        """
        Summarize news text with trading focus.
        
        Args:
            text: News article or text to summarize
            
        Returns:
            Trading-focused summary
        """
        system_prompt = """You are a professional trading analyst. Summarize the given news with focus on:
- Market impact and price implications
- Key financial metrics or events
- Potential trading opportunities or risks
- Sentiment (bullish/bearish/neutral)

Keep the summary concise and actionable for traders."""

        prompt = f"Summarize this news for trading analysis:\n\n{text}"
        return self.chat(prompt, system_prompt)
    
    def sentiment(self, text: str) -> str:
        """
        Analyze sentiment of news or market text.
        
        Args:
            text: Text to analyze for sentiment
            
        Returns:
            Sentiment analysis with reasoning
        """
        system_prompt = """You are a market sentiment analyst. Analyze the sentiment of the given text and provide:
- Overall sentiment: Bullish, Bearish, or Neutral (with confidence %)
- Key sentiment drivers
- Potential market impact
- Brief reasoning

Format as structured analysis."""

        prompt = f"Analyze the market sentiment of this text:\n\n{text}"
        return self.chat(prompt, system_prompt)
    
    def explain_signals(self, context_json: str) -> str:
        """
        Explain trading signals with context.
        
        Args:
            context_json: JSON string with signal context (price, indicators, etc.)
            
        Returns:
            Detailed explanation of signals
        """
        system_prompt = """You are a trading signal analyst. Given trading data and signals, explain:
- What the signals indicate
- Why they might be significant
- Potential entry/exit points
- Risk considerations
- Market context and assumptions

Provide clear, educational explanations suitable for both beginners and experienced traders."""

        prompt = f"Explain these trading signals and context:\n\n{context_json}"
        return self.chat(prompt, system_prompt)
    
    def risk_assessment(self, context_json: str) -> str:
        """
        Provide risk assessment based on context.
        
        Args:
            context_json: JSON string with market/portfolio context
            
        Returns:
            Risk assessment and recommendations
        """
        system_prompt = """You are a risk management specialist. Analyze the given trading context and provide:
- Risk level assessment (Low/Medium/High)
- Key risk factors identified
- Risk mitigation suggestions
- Position sizing recommendations
- Stop-loss and take-profit levels if applicable

Focus on practical risk management for the given scenario."""

        prompt = f"Assess the risks in this trading context:\n\n{context_json}"
        return self.chat(prompt, system_prompt)


# Global service instance
openai_service = OpenAIService()


def get_openai_service() -> OpenAIService:
    """Get the global OpenAI service instance."""
    return openai_service