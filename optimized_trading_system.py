#!/usr/bin/env python3
"""
سیستم معاملات بهینه شده با API های رفع شده
ULTRA_PLUS_BOT - Optimized Version
"""

import os
import ccxt
import requests
import json
import asyncio
from datetime import datetime, timedelta
from openai import OpenAI

class OptimizedTradingSystem:
    def __init__(self):
        # Exchange setup
        self.mexc = ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY'),
            'sandbox': False,
            'enableRateLimit': True
        })
        
        # API clients
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.taapi_key = os.getenv('TAAPI_API_KEY')
        self.news_api_key = os.getenv('NEWSAPI_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Trading pairs
        self.crypto_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        
        print("🚀 سیستم معاملات بهینه شده آماده شد")
        
    def get_crypto_price_data(self, symbol='BTC/USDT'):
        """دریافت قیمت ارز دیجیتال از منابع مختلف"""
        try:
            # MEXC به عنوان منبع اصلی
            mexc_ticker = self.mexc.fetch_ticker(symbol)
            
            # CoinGecko به عنوان پشتیبان
            if symbol == 'BTC/USDT':
                coingecko_url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true'
            elif symbol == 'ETH/USDT':
                coingecko_url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd&include_24hr_change=true'
            else:
                coingecko_url = None
            
            backup_data = {}
            if coingecko_url:
                try:
                    cg_response = requests.get(coingecko_url, timeout=10)
                    if cg_response.status_code == 200:
                        cg_data = cg_response.json()
                        coin_key = 'bitcoin' if symbol == 'BTC/USDT' else 'ethereum'
                        backup_data = cg_data.get(coin_key, {})
                except:
                    pass
            
            return {
                'symbol': symbol,
                'mexc_price': mexc_ticker['last'],
                'mexc_change': mexc_ticker.get('percentage', 0),
                'mexc_volume': mexc_ticker.get('quoteVolume', 0),
                'backup_price': backup_data.get('usd', 0),
                'backup_change': backup_data.get('usd_24h_change', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ خطا در دریافت قیمت {symbol}: {e}")
            return None
    
    def get_advanced_technical_indicators(self, symbol='BTC/USDT'):
        """شاخص‌های فنی پیشرفته از TAAPI"""
        try:
            indicators = {}
            
            # لیست شاخص‌ها
            indicator_configs = [
                {'name': 'rsi', 'params': ''},
                {'name': 'sma', 'params': '&period=20'},
                {'name': 'sma', 'params': '&period=50'},
                {'name': 'ema', 'params': '&period=12'},
                {'name': 'ema', 'params': '&period=26'},
                {'name': 'macd', 'params': ''},
                {'name': 'stoch', 'params': ''},
                {'name': 'bbands', 'params': ''}
            ]
            
            for config in indicator_configs:
                try:
                    url = f"https://api.taapi.io/{config['name']}?secret={self.taapi_key}&exchange=binance&symbol={symbol}&interval=1h{config['params']}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if config['name'] == 'sma' and 'period=20' in config['params']:
                            indicators['sma_20'] = data.get('value', 0)
                        elif config['name'] == 'sma' and 'period=50' in config['params']:
                            indicators['sma_50'] = data.get('value', 0)
                        elif config['name'] == 'ema' and 'period=12' in config['params']:
                            indicators['ema_12'] = data.get('value', 0)
                        elif config['name'] == 'ema' and 'period=26' in config['params']:
                            indicators['ema_26'] = data.get('value', 0)
                        elif config['name'] == 'rsi':
                            indicators['rsi'] = data.get('value', 50)
                        elif config['name'] == 'macd':
                            indicators['macd'] = {
                                'macd': data.get('valueMACD', 0),
                                'signal': data.get('valueMACDSignal', 0),
                                'histogram': data.get('valueMACDHist', 0)
                            }
                        elif config['name'] == 'stoch':
                            indicators['stochastic'] = {
                                'k': data.get('valueK', 50),
                                'd': data.get('valueD', 50)
                            }
                        elif config['name'] == 'bbands':
                            indicators['bollinger'] = {
                                'upper': data.get('valueUpperBand', 0),
                                'middle': data.get('valueMiddleBand', 0),
                                'lower': data.get('valueLowerBand', 0)
                            }
                        
                except Exception as e:
                    print(f"   ⚠️ خطا در {config['name']}: {e}")
                    continue
            
            return indicators
            
        except Exception as e:
            print(f"❌ خطا در شاخص‌های فنی: {e}")
            return {}
    
    def get_market_sentiment(self):
        """تحلیل احساسات بازار از اخبار"""
        try:
            # دریافت اخبار
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
                        'sentiment_score': sentiment_score,
                        'news_count': len(articles),
                        'latest_headlines': headlines[:3],
                        'source': 'NewsAPI + OpenAI'
                    }
                    
        except Exception as e:
            print(f"❌ خطا در تحلیل احساسات: {e}")
        
        return {'sentiment_score': 50, 'news_count': 0, 'source': 'DEFAULT'}
    
    def analyze_sentiment_with_ai(self, headlines):
        """تحلیل احساسات با OpenAI"""
        try:
            text = "\\n".join(headlines)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze cryptocurrency news sentiment. Return only a number 0-100 where 0=very negative, 50=neutral, 100=very positive."
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=10
            )
            return int(response.choices[0].message.content.strip())
        except:
            return 50
    
    def get_stock_market_data(self):
        """داده‌های بازار سهام از Alpha Vantage"""
        try:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
            stock_data = {}
            
            for symbol in symbols[:2]:  # محدود کردن برای جلوگیری از rate limit
                try:
                    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}'
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'Global Quote' in data:
                            quote = data['Global Quote']
                            stock_data[symbol] = {
                                'price': float(quote.get('05. price', 0)),
                                'change': float(quote.get('09. change', 0)),
                                'change_percent': quote.get('10. change percent', '0%').replace('%', '')
                            }
                except:
                    continue
            
            return stock_data
            
        except Exception as e:
            print(f"❌ خطا در داده‌های سهام: {e}")
            return {}
    
    def calculate_optimized_signal(self, price_data, technical_data, sentiment_data):
        """محاسبه سیگنال بهینه شده"""
        
        signals = []
        confidence = 50
        reasons = []
        
        # 1. تحلیل RSI
        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            signals.append('BUY')
            confidence += 25
            reasons.append(f'RSI oversold: {rsi:.1f}')
        elif rsi > 70:
            signals.append('SELL')
            confidence += 25
            reasons.append(f'RSI overbought: {rsi:.1f}')
        
        # 2. تحلیل MACD
        macd_data = technical_data.get('macd', {})
        if macd_data:
            macd = macd_data.get('macd', 0)
            signal_line = macd_data.get('signal', 0)
            
            if macd > signal_line:
                signals.append('BUY')
                confidence += 15
                reasons.append('MACD bullish')
            else:
                signals.append('SELL')
                confidence += 15
                reasons.append('MACD bearish')
        
        # 3. تحلیل SMA
        sma_20 = technical_data.get('sma_20', 0)
        sma_50 = technical_data.get('sma_50', 0)
        current_price = price_data.get('mexc_price', 0)
        
        if sma_20 > sma_50 and current_price > sma_20:
            signals.append('BUY')
            confidence += 20
            reasons.append('SMA trend bullish')
        elif sma_20 < sma_50 and current_price < sma_20:
            signals.append('SELL')
            confidence += 20
            reasons.append('SMA trend bearish')
        
        # 4. تحلیل احساسات
        sentiment_score = sentiment_data.get('sentiment_score', 50)
        if sentiment_score > 70:
            signals.append('BUY')
            confidence += 10
            reasons.append(f'Positive sentiment: {sentiment_score}')
        elif sentiment_score < 30:
            signals.append('SELL')
            confidence += 10
            reasons.append(f'Negative sentiment: {sentiment_score}')
        
        # 5. تحلیل Bollinger Bands
        bollinger = technical_data.get('bollinger', {})
        if bollinger and current_price:
            lower_band = bollinger.get('lower', 0)
            upper_band = bollinger.get('upper', 0)
            
            if current_price < lower_band:
                signals.append('BUY')
                confidence += 15
                reasons.append('Below Bollinger lower band')
            elif current_price > upper_band:
                signals.append('SELL')
                confidence += 15
                reasons.append('Above Bollinger upper band')
        
        # تعیین سیگنال نهایی
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count and buy_count >= 2:
            final_action = 'BUY'
        elif sell_count > buy_count and sell_count >= 2:
            final_action = 'SELL'
        else:
            final_action = 'HOLD'
            confidence = max(30, min(70, confidence))
        
        return {
            'action': final_action,
            'confidence': min(95, max(10, confidence)),
            'reasons': reasons,
            'signal_counts': {'buy': buy_count, 'sell': sell_count},
            'technical_summary': {
                'rsi': rsi,
                'macd_trend': 'Bullish' if macd_data.get('macd', 0) > macd_data.get('signal', 0) else 'Bearish',
                'sma_trend': 'Bullish' if sma_20 > sma_50 else 'Bearish'
            }
        }
    
    def execute_optimized_analysis(self):
        """اجرای تحلیل بهینه شده"""
        print("🚀 شروع تحلیل بهینه شده ULTRA_PLUS_BOT...")
        print("="*60)
        
        # تحلیل احساسات بازار (یکبار)
        market_sentiment = self.get_market_sentiment()
        print(f"📰 احساسات بازار: {market_sentiment['sentiment_score']}/100")
        
        # تحلیل بازار سهام (یکبار)
        stock_data = self.get_stock_market_data()
        print(f"📈 داده‌های سهام: {len(stock_data)} نماد")
        
        analysis_results = {}
        active_signals = []
        
        for symbol in self.crypto_pairs:
            print(f"\\n📊 تحلیل {symbol}:")
            
            try:
                # دریافت قیمت
                price_data = self.get_crypto_price_data(symbol)
                if not price_data:
                    continue
                
                print(f"   💰 قیمت: ${price_data['mexc_price']:.2f} ({price_data['mexc_change']:+.2f}%)")
                
                # تحلیل فنی
                technical_data = self.get_advanced_technical_indicators(symbol)
                if technical_data.get('rsi'):
                    print(f"   📈 RSI: {technical_data['rsi']:.1f}")
                
                # محاسبه سیگنال
                signal = self.calculate_optimized_signal(price_data, technical_data, market_sentiment)
                
                # ذخیره نتایج
                analysis_results[symbol] = {
                    'price_data': price_data,
                    'technical_data': technical_data,
                    'trading_signal': signal,
                    'timestamp': datetime.now().isoformat()
                }
                
                # نمایش سیگنال
                if signal['action'] != 'HOLD':
                    print(f"   🎯 سیگنال: {signal['action']} (اعتماد: {signal['confidence']}%)")
                    print(f"   📝 دلایل: {', '.join(signal['reasons'][:2])}")
                    
                    active_signals.append({
                        'symbol': symbol,
                        'action': signal['action'],
                        'confidence': signal['confidence'],
                        'price': price_data['mexc_price']
                    })
                else:
                    print(f"   ⏸️ سیگنال: HOLD")
                    
            except Exception as e:
                print(f"   ❌ خطا: {e}")
                continue
        
        # ذخیره گزارش نهایی
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'market_sentiment': market_sentiment,
            'stock_market_data': stock_data,
            'crypto_analysis': analysis_results,
            'active_signals': active_signals,
            'summary': {
                'total_analyzed': len(analysis_results),
                'active_signals_count': len(active_signals),
                'buy_signals': sum(1 for s in active_signals if s['action'] == 'BUY'),
                'sell_signals': sum(1 for s in active_signals if s['action'] == 'SELL')
            }
        }
        
        with open('optimized_trading_report.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        # نمایش خلاصه
        self.display_optimized_summary(active_signals, final_report['summary'])
        
        return final_report
    
    def display_optimized_summary(self, active_signals, summary):
        """نمایش خلاصه بهینه شده"""
        print("\\n" + "="*60)
        print("📋 خلاصه نهایی - سیستم بهینه شده")
        print("="*60)
        
        if active_signals:
            print(f"\\n🎯 سیگنال‌های فعال ({len(active_signals)}):")
            for signal in sorted(active_signals, key=lambda x: x['confidence'], reverse=True):
                print(f"   {signal['action']} {signal['symbol']} @ ${signal['price']:.2f} (اعتماد: {signal['confidence']}%)")
        else:
            print("\\n⏸️ بازار در حالت انتظار - هیچ سیگنال قوی یافت نشد")
        
        print(f"\\n📊 آمار:")
        print(f"   📈 سیگنال خرید: {summary['buy_signals']}")
        print(f"   📉 سیگنال فروش: {summary['sell_signals']}")
        print(f"   📊 کل تحلیل شده: {summary['total_analyzed']}")
        
        print(f"\\n✅ گزارش کامل در optimized_trading_report.json ذخیره شد")

def main():
    system = OptimizedTradingSystem()
    results = system.execute_optimized_analysis()
    
    print(f"\\n🔄 سیستم بهینه شده آماده عملیات مداوم...")

if __name__ == "__main__":
    main()