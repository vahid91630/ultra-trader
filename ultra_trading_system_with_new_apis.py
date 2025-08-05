#!/usr/bin/env python3
"""
سیستم معاملات فوق پیشرفته با API های جدید و تحلیل عمیق
ULTRA_PLUS_BOT - Enhanced Trading System
"""

import os
import ccxt
import requests
import json
import asyncio
from datetime import datetime, timedelta
import yfinance as yf
from openai import OpenAI
import time

class UltraTradingSystem:
    def __init__(self):
        # Exchange setup
        self.mexc = ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY'),
            'sandbox': False,
            'enableRateLimit': True
        })
        
        # API keys
        self.taapi_key = os.getenv('TAAPI_API_KEY')
        self.tokenmetrik_key = os.getenv('TOKENMETRIK_API_KEY')
        self.news_api_key = os.getenv('NEWSAPI_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Trading pairs
        self.crypto_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        
        print("🚀 سیستم معاملات فوق پیشرفته آماده شد")
        
    def get_enhanced_technical_analysis(self, symbol='BTC/USDT'):
        """تحلیل فنی پیشرفته با TAAPI"""
        try:
            indicators = {}
            
            # RSI
            try:
                rsi_url = f'https://api.taapi.io/rsi?secret={self.taapi_key}&exchange=binance&symbol={symbol}&interval=1h'
                rsi_response = requests.get(rsi_url, timeout=15)
                if rsi_response.status_code == 200:
                    indicators['rsi'] = rsi_response.json().get('value', 50)
                    print(f"   ✅ RSI: {indicators['rsi']:.1f}")
            except Exception as e:
                print(f"   ⚠️ RSI خطا: {e}")
                indicators['rsi'] = 50
            
            # SMA های مختلف
            for period in [20, 50, 200]:
                try:
                    sma_url = f'https://api.taapi.io/sma?secret={self.taapi_key}&exchange=binance&symbol={symbol}&interval=1h&period={period}'
                    sma_response = requests.get(sma_url, timeout=15)
                    if sma_response.status_code == 200:
                        indicators[f'sma_{period}'] = sma_response.json().get('value', 0)
                        print(f"   ✅ SMA{period}: ${indicators[f'sma_{period}']:.2f}")
                except Exception as e:
                    print(f"   ⚠️ SMA{period} خطا: {e}")
                    indicators[f'sma_{period}'] = 0
            
            # MACD
            try:
                macd_url = f'https://api.taapi.io/macd?secret={self.taapi_key}&exchange=binance&symbol={symbol}&interval=1h'
                macd_response = requests.get(macd_url, timeout=15)
                if macd_response.status_code == 200:
                    macd_data = macd_response.json()
                    indicators['macd'] = {
                        'macd': macd_data.get('valueMACD', 0),
                        'signal': macd_data.get('valueMACDSignal', 0),
                        'histogram': macd_data.get('valueMACDHist', 0)
                    }
                    print(f"   ✅ MACD: {indicators['macd']['macd']:.2f}")
            except Exception as e:
                print(f"   ⚠️ MACD خطا: {e}")
                indicators['macd'] = {'macd': 0, 'signal': 0, 'histogram': 0}
            
            # Stochastic
            try:
                stoch_url = f'https://api.taapi.io/stoch?secret={self.taapi_key}&exchange=binance&symbol={symbol}&interval=1h'
                stoch_response = requests.get(stoch_url, timeout=15)
                if stoch_response.status_code == 200:
                    stoch_data = stoch_response.json()
                    indicators['stochastic'] = {
                        'k': stoch_data.get('valueK', 50),
                        'd': stoch_data.get('valueD', 50)
                    }
                    print(f"   ✅ Stochastic K: {indicators['stochastic']['k']:.1f}")
            except Exception as e:
                print(f"   ⚠️ Stochastic خطا: {e}")
                indicators['stochastic'] = {'k': 50, 'd': 50}
                
            return indicators
            
        except Exception as e:
            print(f"❌ خطای کلی در تحلیل فنی: {e}")
            return {
                'rsi': 50,
                'sma_20': 0,
                'sma_50': 0,
                'sma_200': 0,
                'macd': {'macd': 0, 'signal': 0, 'histogram': 0},
                'stochastic': {'k': 50, 'd': 50}
            }
    
    def get_tokenmetrics_score(self, symbol='bitcoin'):
        """دریافت امتیاز از TokenMetrics با روش‌های مختلف"""
        try:
            # روش اول: Header Authorization
            headers = {
                'Authorization': f'Bearer {self.tokenmetrik_key}',
                'Content-Type': 'application/json'
            }
            url = f'https://api.tokenmetrics.com/v1/tokens/{symbol}'
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'score': data.get('score', 50),
                    'grade': data.get('grade', 'C'),
                    'recommendation': data.get('recommendation', 'HOLD')
                }
            
            # روش دوم: Query Parameter
            url_param = f'https://api.tokenmetrics.com/v1/tokens/{symbol}?api_key={self.tokenmetrik_key}'
            response2 = requests.get(url_param, timeout=15)
            
            if response2.status_code == 200:
                data = response2.json()
                return {
                    'score': data.get('score', 50),
                    'grade': data.get('grade', 'C'),
                    'recommendation': data.get('recommendation', 'HOLD')
                }
            
            print(f"   ⚠️ TokenMetrics خطا: {response.status_code} - {response.text[:100]}")
            
        except Exception as e:
            print(f"   ⚠️ TokenMetrics exception: {e}")
        
        # مقدار پیش‌فرض
        return {'score': 50, 'grade': 'C', 'recommendation': 'HOLD'}
    
    def get_coindesk_alternative_data(self):
        """دریافت اطلاعات Bitcoin از منابع جایگزین"""
        try:
            # CoinGecko API (رایگان)
            coingecko_url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true'
            cg_response = requests.get(coingecko_url, timeout=10)
            
            if cg_response.status_code == 200:
                cg_data = cg_response.json()
                btc_data = cg_data.get('bitcoin', {})
                
                return {
                    'price': btc_data.get('usd', 0),
                    'change_24h': btc_data.get('usd_24h_change', 0),
                    'source': 'CoinGecko'
                }
            
            # Fallback: CoinDesk free API
            coindesk_url = 'https://api.coindesk.com/v1/bpi/currentprice.json'
            cd_response = requests.get(coindesk_url, timeout=10)
            
            if cd_response.status_code == 200:
                cd_data = cd_response.json()
                return {
                    'price': cd_data.get('bpi', {}).get('USD', {}).get('rate_float', 0),
                    'change_24h': 0,
                    'source': 'CoinDesk'
                }
                
        except Exception as e:
            print(f"   ⚠️ خطا در دریافت داده قیمت: {e}")
        
        return {'price': 0, 'change_24h': 0, 'source': 'MEXC'}
    
    def calculate_ultra_signal(self, symbol, price_data, technical_data, tokenmetrics_data):
        """محاسبه سیگنال فوق پیشرفته"""
        
        signals = []
        confidence = 50
        reasons = []
        
        # 1. تحلیل RSI
        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            signals.append('BUY')
            confidence += 20
            reasons.append(f'RSI خرید بیش از حد: {rsi:.1f}')
        elif rsi > 70:
            signals.append('SELL')
            confidence += 20
            reasons.append(f'RSI فروش بیش از حد: {rsi:.1f}')
        elif 40 < rsi < 60:
            confidence += 5
            reasons.append('RSI متعادل')
        
        # 2. تحلیل SMA
        sma_20 = technical_data.get('sma_20', 0)
        sma_50 = technical_data.get('sma_50', 0)
        sma_200 = technical_data.get('sma_200', 0)
        current_price = price_data.get('current_price', 0)
        
        if sma_20 > sma_50 > sma_200 and current_price > sma_20:
            signals.append('BUY')
            confidence += 25
            reasons.append('روند صعودی قوی (SMA)')
        elif sma_20 < sma_50 < sma_200 and current_price < sma_20:
            signals.append('SELL')
            confidence += 25
            reasons.append('روند نزولی قوی (SMA)')
        
        # 3. تحلیل MACD
        macd_data = technical_data.get('macd', {})
        macd = macd_data.get('macd', 0)
        signal_line = macd_data.get('signal', 0)
        histogram = macd_data.get('histogram', 0)
        
        if macd > signal_line and histogram > 0:
            signals.append('BUY')
            confidence += 15
            reasons.append('MACD صعودی')
        elif macd < signal_line and histogram < 0:
            signals.append('SELL')
            confidence += 15
            reasons.append('MACD نزولی')
        
        # 4. تحلیل Stochastic
        stoch_data = technical_data.get('stochastic', {})
        k = stoch_data.get('k', 50)
        d = stoch_data.get('d', 50)
        
        if k < 20 and d < 20:
            signals.append('BUY')
            confidence += 10
            reasons.append('Stochastic خرید بیش از حد')
        elif k > 80 and d > 80:
            signals.append('SELL')
            confidence += 10
            reasons.append('Stochastic فروش بیش از حد')
        
        # 5. تحلیل TokenMetrics
        tm_score = tokenmetrics_data.get('score', 50)
        tm_rec = tokenmetrics_data.get('recommendation', 'HOLD')
        
        if tm_rec == 'BUY' or tm_score > 70:
            signals.append('BUY')
            confidence += 15
            reasons.append(f'TokenMetrics: {tm_rec} (Score: {tm_score})')
        elif tm_rec == 'SELL' or tm_score < 30:
            signals.append('SELL')
            confidence += 15
            reasons.append(f'TokenMetrics: {tm_rec} (Score: {tm_score})')
        
        # 6. تحلیل حجم و نوسانات
        price_change = price_data.get('price_change_24h', 0)
        if abs(price_change) > 5:
            if price_change > 0:
                confidence += 5
                reasons.append(f'نوسانات مثبت: +{price_change:.1f}%')
            else:
                confidence -= 5
                reasons.append(f'نوسانات منفی: {price_change:.1f}%')
        
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
            'technical_score': {
                'rsi': rsi,
                'macd_signal': 'صعودی' if macd > signal_line else 'نزولی',
                'sma_trend': 'صعودی' if sma_20 > sma_50 else 'نزولی',
                'stochastic': 'خرید بیش از حد' if k < 20 else 'فروش بیش از حد' if k > 80 else 'متعادل'
            },
            'tokenmetrics': tokenmetrics_data
        }
    
    def execute_ultra_analysis(self):
        """اجرای تحلیل فوق پیشرفته"""
        print("🚀 شروع تحلیل فوق پیشرفته ULTRA_PLUS_BOT...")
        print("="*60)
        
        analysis_results = {}
        active_signals = []
        
        for symbol in self.crypto_pairs:
            print(f"\n📊 تحلیل جامع {symbol}:")
            
            try:
                # دریافت قیمت فعلی از MEXC
                ticker = self.mexc.fetch_ticker(symbol)
                price_data = {
                    'symbol': symbol,
                    'current_price': ticker['last'],
                    'price_change_24h': ticker.get('percentage', 0),
                    'volume': ticker.get('quoteVolume', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"   💰 قیمت فعلی: ${price_data['current_price']:.2f}")
                print(f"   📈 تغییر 24 ساعته: {price_data['price_change_24h']:+.2f}%")
                
                # تحلیل فنی پیشرفته
                print(f"   🔍 تحلیل فنی...")
                technical_data = self.get_enhanced_technical_analysis(symbol)
                
                # TokenMetrics (فقط برای BTC و ETH)
                tokenmetrics_data = {'score': 50, 'grade': 'C', 'recommendation': 'HOLD'}
                if symbol == 'BTC/USDT':
                    tokenmetrics_data = self.get_tokenmetrics_score('bitcoin')
                elif symbol == 'ETH/USDT':
                    tokenmetrics_data = self.get_tokenmetrics_score('ethereum')
                
                # محاسبه سیگنال نهایی
                signal = self.calculate_ultra_signal(symbol, price_data, technical_data, tokenmetrics_data)
                
                # ذخیره نتایج
                analysis_results[symbol] = {
                    'price_data': price_data,
                    'technical_analysis': technical_data,
                    'tokenmetrics': tokenmetrics_data,
                    'trading_signal': signal
                }
                
                # نمایش سیگنال
                if signal['action'] != 'HOLD':
                    print(f"   🎯 سیگنال: {signal['action']} (اعتماد: {signal['confidence']}%)")
                    active_signals.append({
                        'symbol': symbol,
                        'action': signal['action'],
                        'confidence': signal['confidence'],
                        'price': price_data['current_price']
                    })
                else:
                    print(f"   ⏸️ سیگنال: HOLD (انتظار)")
                
                # فاصله بین درخواست‌ها
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ خطا در تحلیل {symbol}: {e}")
                continue
        
        # ذخیره نتایج کامل
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_results': analysis_results,
            'active_signals': active_signals,
            'market_summary': self.generate_market_summary(analysis_results)
        }
        
        with open('ultra_trading_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        # نمایش خلاصه نهایی
        self.display_final_summary(active_signals, analysis_results)
        
        return final_report
    
    def generate_market_summary(self, analysis_results):
        """تولید خلاصه بازار"""
        total_symbols = len(analysis_results)
        buy_signals = sum(1 for data in analysis_results.values() 
                         if data.get('trading_signal', {}).get('action') == 'BUY')
        sell_signals = sum(1 for data in analysis_results.values() 
                          if data.get('trading_signal', {}).get('action') == 'SELL')
        
        avg_confidence = sum(data.get('trading_signal', {}).get('confidence', 0) 
                           for data in analysis_results.values()) / total_symbols if total_symbols > 0 else 0
        
        return {
            'total_analyzed': total_symbols,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': total_symbols - buy_signals - sell_signals,
            'average_confidence': avg_confidence,
            'market_sentiment': 'صعودی' if buy_signals > sell_signals else 'نزولی' if sell_signals > buy_signals else 'متعادل'
        }
    
    def display_final_summary(self, active_signals, analysis_results):
        """نمایش خلاصه نهایی"""
        print("\n" + "="*60)
        print("📋 خلاصه نهایی تحلیل ULTRA_PLUS_BOT")
        print("="*60)
        
        if active_signals:
            print(f"\n🎯 سیگنال‌های فعال ({len(active_signals)}):")
            for signal in sorted(active_signals, key=lambda x: x['confidence'], reverse=True):
                print(f"   {signal['action']} {signal['symbol']} @ ${signal['price']:.2f} (اعتماد: {signal['confidence']}%)")
        else:
            print("\n⏸️ هیچ سیگنال فعالی یافت نشد - بازار در حالت انتظار")
        
        # آمار کلی
        market_summary = self.generate_market_summary(analysis_results)
        print(f"\n📊 آمار بازار:")
        print(f"   📈 سیگنال‌های خرید: {market_summary['buy_signals']}")
        print(f"   📉 سیگنال‌های فروش: {market_summary['sell_signals']}")
        print(f"   ⏸️ حالت انتظار: {market_summary['hold_signals']}")
        print(f"   🎯 میانگین اعتماد: {market_summary['average_confidence']:.1f}%")
        print(f"   🌊 احساسات بازار: {market_summary['market_sentiment']}")
        
        print(f"\n✅ گزارش کامل در ultra_trading_analysis.json ذخیره شد")

def main():
    system = UltraTradingSystem()
    results = system.execute_ultra_analysis()
    
    # اجرای تحلیل مداوم (اختیاری)
    print(f"\n🔄 سیستم آماده تحلیل مداوم...")

if __name__ == "__main__":
    main()