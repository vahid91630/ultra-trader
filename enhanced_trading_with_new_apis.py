#!/usr/bin/env python3
"""
سیستم معاملات تقویت شده با API های جدید
"""

import os
import ccxt
import requests
import json
import asyncio
from datetime import datetime, timedelta
import yfinance as yf
from openai import OpenAI

class EnhancedTradingSystem:
    def __init__(self):
        # Exchange setup
        self.mexc = ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY'),
            'sandbox': False,
            'enableRateLimit': True
        })
        
        # API keys
        self.news_api_key = os.getenv('NEWSAPI_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Trading settings
        self.crypto_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        self.stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        
    def get_enhanced_market_analysis(self):
        """تحلیل جامع بازار با API های جدید"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'crypto_analysis': {},
            'stock_analysis': {},
            'news_sentiment': {},
            'trading_signals': []
        }
        
        # تحلیل ارزهای دیجیتال
        print("📊 تحلیل ارزهای دیجیتال...")
        for pair in self.crypto_pairs:
            try:
                ticker = self.mexc.fetch_ticker(pair)
                ohlcv = self.mexc.fetch_ohlcv(pair, '1h', limit=24)
                
                # محاسبه شاخص‌های فنی
                prices = [candle[4] for candle in ohlcv]
                sma_6 = sum(prices[-6:]) / 6
                sma_12 = sum(prices[-12:]) / 12
                rsi = self.calculate_rsi(prices)
                
                analysis['crypto_analysis'][pair] = {
                    'price': ticker['last'],
                    'change_24h': ticker.get('percentage', 0),
                    'volume': ticker.get('quoteVolume', 0),
                    'sma_6': sma_6,
                    'sma_12': sma_12,
                    'rsi': rsi,
                    'signal': self.generate_crypto_signal(ticker, sma_6, sma_12, rsi)
                }
                
                print(f"   ✅ {pair}: ${ticker['last']:.2f} ({ticker.get('percentage', 0):+.2f}%)")
                
            except Exception as e:
                print(f"   ❌ خطا در {pair}: {e}")
        
        # تحلیل سهام با Alpha Vantage
        print("📈 تحلیل بازار سهام...")
        for symbol in self.stock_symbols:
            try:
                stock_data = self.get_stock_data(symbol)
                if stock_data:
                    analysis['stock_analysis'][symbol] = stock_data
                    print(f"   ✅ {symbol}: ${stock_data['price']:.2f}")
            except Exception as e:
                print(f"   ❌ خطا در {symbol}: {e}")
        
        # تحلیل اخبار
        print("📰 تحلیل احساسات اخبار...")
        news_sentiment = self.analyze_news_sentiment()
        analysis['news_sentiment'] = news_sentiment
        
        # تولید سیگنال‌های معاملاتی
        analysis['trading_signals'] = self.generate_trading_signals(analysis)
        
        return analysis
    
    def get_stock_data(self, symbol):
        """دریافت داده سهام از Alpha Vantage"""
        try:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    return {
                        'price': float(quote.get('05. price', 0)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                        'volume': int(quote.get('06. volume', 0))
                    }
        except Exception as e:
            print(f"خطا در دریافت {symbol}: {e}")
        return None
    
    def analyze_news_sentiment(self):
        """تحلیل احساسات اخبار"""
        try:
            # دریافت اخبار Bitcoin
            url = f'https://newsapi.org/v2/everything?q=bitcoin+cryptocurrency&pageSize=10&sortBy=publishedAt&apiKey={self.news_api_key}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                news_data = response.json()
                articles = news_data.get('articles', [])
                
                if articles:
                    # تحلیل احساسات با OpenAI
                    headlines = [article['title'] for article in articles[:5]]
                    sentiment_score = self.analyze_sentiment_with_ai(headlines)
                    
                    return {
                        'total_articles': len(articles),
                        'sentiment_score': sentiment_score,
                        'latest_headlines': headlines[:3]
                    }
        except Exception as e:
            print(f"خطا در تحلیل اخبار: {e}")
        
        return {'sentiment_score': 50, 'total_articles': 0}
    
    def analyze_sentiment_with_ai(self, headlines):
        """تحلیل احساسات با هوش مصنوعی"""
        try:
            text = "\\n".join(headlines)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "Analyze the sentiment of cryptocurrency news headlines. Return a score from 0-100 where 0 is very negative, 50 is neutral, and 100 is very positive. Respond only with the number."
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=10
            )
            return int(response.choices[0].message.content.strip())
        except:
            return 50
    
    def calculate_rsi(self, prices, period=14):
        """محاسبه RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_crypto_signal(self, ticker, sma_6, sma_12, rsi):
        """تولید سیگنال معاملاتی ارز دیجیتال"""
        price = ticker['last']
        change = ticker.get('percentage', 0)
        
        # شرایط خرید
        if (sma_6 > sma_12 and  # روند صعودی
            rsi < 70 and          # خرید بیش از حد نشده
            change > 1):          # تغییر مثبت
            return 'BUY'
        
        # شرایط فروش
        elif (sma_6 < sma_12 and  # روند نزولی
              rsi > 30 and        # فروش بیش از حد نشده
              change < -1):       # تغییر منفی
            return 'SELL'
        
        return 'HOLD'
    
    def generate_trading_signals(self, analysis):
        """تولید سیگنال‌های نهایی معاملاتی"""
        signals = []
        
        # سیگنال‌های ارز دیجیتال
        for pair, data in analysis['crypto_analysis'].items():
            if data['signal'] in ['BUY', 'SELL']:
                confidence = self.calculate_signal_confidence(data, analysis['news_sentiment'])
                
                signals.append({
                    'type': 'crypto',
                    'symbol': pair,
                    'action': data['signal'],
                    'price': data['price'],
                    'confidence': confidence,
                    'reason': f"SMA: {data['signal']}, RSI: {data['rsi']:.1f}, News: {analysis['news_sentiment']['sentiment_score']}"
                })
        
        # مرتب‌سازی بر اساس اعتماد
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        return signals[:3]  # بهترین 3 سیگنال
    
    def calculate_signal_confidence(self, crypto_data, news_sentiment):
        """محاسبه اعتماد سیگنال"""
        base_confidence = 60
        
        # اضافه کردن بر اساس RSI
        if 30 < crypto_data['rsi'] < 70:
            base_confidence += 10
        
        # اضافه کردن بر اساس احساسات اخبار
        news_score = news_sentiment.get('sentiment_score', 50)
        if crypto_data['signal'] == 'BUY' and news_score > 60:
            base_confidence += 15
        elif crypto_data['signal'] == 'SELL' and news_score < 40:
            base_confidence += 15
        
        # اضافه کردن بر اساس حجم تغییرات
        change = abs(crypto_data.get('change_24h', 0))
        if 2 < change < 10:
            base_confidence += 10
        
        return min(95, base_confidence)
    
    def execute_enhanced_trading(self):
        """اجرای معاملات تقویت شده"""
        print("🚀 شروع سیستم معاملات تقویت شده...")
        
        # دریافت تحلیل جامع
        analysis = self.get_enhanced_market_analysis()
        
        # نمایش سیگنال‌ها
        signals = analysis['trading_signals']
        print(f"\\n🎯 {len(signals)} سیگنال معاملاتی یافت شد:")
        
        for i, signal in enumerate(signals, 1):
            print(f"   {i}. {signal['action']} {signal['symbol']}")
            print(f"      💰 قیمت: ${signal['price']:.2f}")
            print(f"      🎯 اعتماد: {signal['confidence']}%")
            print(f"      📝 دلیل: {signal['reason']}")
        
        # ذخیره تحلیل
        with open('enhanced_trading_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\\n✅ تحلیل کامل در enhanced_trading_analysis.json ذخیره شد")
        return analysis

def main():
    system = EnhancedTradingSystem()
    analysis = system.execute_enhanced_trading()
    
    # خلاصه نهایی
    crypto_count = len(analysis['crypto_analysis'])
    stock_count = len(analysis['stock_analysis'])
    signal_count = len(analysis['trading_signals'])
    
    print(f"\\n📊 خلاصه تحلیل:")
    print(f"   🪙 ارزهای تحلیل شده: {crypto_count}")
    print(f"   📈 سهام تحلیل شده: {stock_count}")
    print(f"   🎯 سیگنال‌های فعال: {signal_count}")
    print(f"   📰 احساسات اخبار: {analysis['news_sentiment']['sentiment_score']}/100")

if __name__ == "__main__":
    main()