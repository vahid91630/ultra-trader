#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
موتور معاملات چند بازاری ULTRA_PLUS_BOT
پوشش تمام بازارهای مالی برای حداکثر سودآوری
"""

import asyncio
import aiohttp
import requests
import ccxt
import yfinance as yf
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MultiMarketTradingEngine:
    def __init__(self):
        """راه‌اندازی موتور معاملات چند بازاری"""
        
        # API کلیدها
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.news_api_key = os.getenv('NEWS_API_KEY', 'demo')
        
        # Exchanges برای رمزارز
        self.mexc = self._setup_mexc()
        
        # تعریف بازارها
        self.markets = {
            'crypto': {
                'symbols': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT'],
                'exchange': 'mexc',
                'risk_level': 'HIGH',
                'min_investment': 10
            },
            'stocks': {
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'],
                'source': 'alpha_vantage',
                'risk_level': 'MEDIUM',
                'min_investment': 25
            },
            'forex': {
                'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD'],
                'source': 'alpha_vantage',
                'risk_level': 'MEDIUM',
                'min_investment': 50
            },
            'commodities': {
                'symbols': ['GOLD', 'SILVER', 'OIL', 'NATGAS', 'WHEAT', 'CORN'],
                'source': 'alpha_vantage',
                'risk_level': 'LOW',
                'min_investment': 30
            },
            'indices': {
                'symbols': ['^GSPC', '^IXIC', '^DJI', '^FTSE', '^GDAXI', '^N225'],
                'source': 'yahoo_finance',
                'risk_level': 'LOW',
                'min_investment': 100
            }
        }
        
        self.market_data = {}
        self.opportunities = []
        
    def _setup_mexc(self):
        """راه‌اندازی MEXC exchange"""
        try:
            return ccxt.mexc({
                'apiKey': os.getenv('MEXC_API_KEY'),
                'secret': os.getenv('MEXC_SECRET_KEY'),
                'sandbox': False,
                'enableRateLimit': True
            })
        except Exception as e:
            logger.warning(f"MEXC setup failed: {e}")
            return None

    async def scan_all_markets(self) -> Dict[str, Any]:
        """اسکن همزمان تمام بازارها"""
        logger.info("🔍 شروع اسکن جامع تمام بازارها...")
        
        # اجرای همزمان تمام بازارها
        tasks = [
            self._scan_crypto_market(),
            self._scan_stock_market(),
            self._scan_forex_market(),
            self._scan_commodities_market(),
            self._scan_indices_market()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # ترکیب نتایج
        combined_data = {}
        for i, result in enumerate(results):
            market_names = ['crypto', 'stocks', 'forex', 'commodities', 'indices']
            if isinstance(result, dict):
                combined_data[market_names[i]] = result
            else:
                logger.error(f"خطا در {market_names[i]}: {result}")
                combined_data[market_names[i]] = {}
        
        self.market_data = combined_data
        return combined_data

    async def _scan_crypto_market(self) -> Dict[str, Any]:
        """اسکن بازار رمزارز"""
        crypto_data = {}
        
        if not self.mexc:
            logger.warning("MEXC not available, using CoinGecko")
            return await self._scan_crypto_coingecko()
        
        try:
            for symbol in self.markets['crypto']['symbols']:
                try:
                    ticker = self.mexc.fetch_ticker(symbol)
                    crypto_data[symbol] = {
                        'price': ticker['last'],
                        'change_24h': ticker['percentage'],
                        'volume': ticker['quoteVolume'],
                        'high_24h': ticker['high'],
                        'low_24h': ticker['low'],
                        'market': 'crypto',
                        'opportunity_score': self._calculate_opportunity_score(ticker),
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.warning(f"خطا در دریافت {symbol}: {e}")
            
            logger.info(f"✅ رمزارز: {len(crypto_data)} دارایی اسکن شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در اسکن رمزارز: {e}")
        
        return crypto_data

    async def _scan_crypto_coingecko(self) -> Dict[str, Any]:
        """استفاده از CoinGecko برای رمزارز"""
        crypto_data = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = 'https://api.coingecko.com/api/v3/simple/price'
                params = {
                    'ids': 'bitcoin,ethereum,binancecoin,cardano,solana,polygon',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for crypto_id, info in data.items():
                            crypto_data[crypto_id] = {
                                'price': info.get('usd', 0),
                                'change_24h': info.get('usd_24h_change', 0),
                                'volume': info.get('usd_24h_vol', 0),
                                'market': 'crypto',
                                'opportunity_score': abs(info.get('usd_24h_change', 0)) / 10,
                                'timestamp': datetime.now().isoformat()
                            }
                        
                        logger.info(f"✅ CoinGecko: {len(crypto_data)} رمزارز")
        
        except Exception as e:
            logger.error(f"❌ خطا در CoinGecko: {e}")
        
        return crypto_data

    async def _scan_stock_market(self) -> Dict[str, Any]:
        """اسکن بازار سهام"""
        stock_data = {}
        
        try:
            # استفاده از yfinance برای سهام
            symbols = self.markets['stocks']['symbols']
            
            for symbol in symbols:
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="2d")
                    info = stock.info
                    
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2]
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                        
                        stock_data[symbol] = {
                            'price': current_price,
                            'change_24h': change_pct,
                            'volume': hist['Volume'].iloc[-1],
                            'market_cap': info.get('marketCap', 0),
                            'market': 'stocks',
                            'opportunity_score': abs(change_pct) / 5,
                            'timestamp': datetime.now().isoformat()
                        }
                
                except Exception as e:
                    logger.warning(f"خطا در دریافت سهم {symbol}: {e}")
            
            logger.info(f"✅ سهام: {len(stock_data)} شرکت اسکن شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در اسکن سهام: {e}")
        
        return stock_data

    async def _scan_forex_market(self) -> Dict[str, Any]:
        """اسکن بازار فارکس"""
        forex_data = {}
        
        try:
            # استفاده از exchangerate-api
            async with aiohttp.ClientSession() as session:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data['rates']
                        
                        # محاسبه جفت ارزها
                        pairs = ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD']
                        
                        for currency in pairs:
                            if currency in rates:
                                # شبیه‌سازی تغییر 24 ساعته
                                import random
                                change_24h = random.uniform(-2, 2)
                                
                                pair_name = f"{currency}/USD"
                                forex_data[pair_name] = {
                                    'price': 1/rates[currency] if currency != 'USD' else rates[currency],
                                    'change_24h': change_24h,
                                    'market': 'forex',
                                    'opportunity_score': abs(change_24h) / 2,
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        logger.info(f"✅ فارکس: {len(forex_data)} جفت ارز")
        
        except Exception as e:
            logger.error(f"❌ خطا در اسکن فارکس: {e}")
        
        return forex_data

    async def _scan_commodities_market(self) -> Dict[str, Any]:
        """اسکن بازار کالاها"""
        commodities_data = {}
        
        try:
            # قیمت‌های نمونه کالاها (در پروژه واقعی از API استفاده شود)
            commodities = {
                'GOLD': {'price': 2050, 'change': 0.8},
                'SILVER': {'price': 24.5, 'change': -0.3},
                'OIL': {'price': 82.3, 'change': 1.2},
                'NATGAS': {'price': 2.8, 'change': -1.5}
            }
            
            for commodity, data in commodities.items():
                commodities_data[commodity] = {
                    'price': data['price'],
                    'change_24h': data['change'],
                    'market': 'commodities',
                    'opportunity_score': abs(data['change']) / 2,
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"✅ کالاها: {len(commodities_data)} کالا")
            
        except Exception as e:
            logger.error(f"❌ خطا در اسکن کالاها: {e}")
        
        return commodities_data

    async def _scan_indices_market(self) -> Dict[str, Any]:
        """اسکن شاخص‌های بورس"""
        indices_data = {}
        
        try:
            symbols = self.markets['indices']['symbols']
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2]
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                        
                        indices_data[symbol] = {
                            'price': current_price,
                            'change_24h': change_pct,
                            'volume': hist['Volume'].iloc[-1],
                            'market': 'indices',
                            'opportunity_score': abs(change_pct) / 3,
                            'timestamp': datetime.now().isoformat()
                        }
                
                except Exception as e:
                    logger.warning(f"خطا در دریافت شاخص {symbol}: {e}")
            
            logger.info(f"✅ شاخص‌ها: {len(indices_data)} شاخص")
            
        except Exception as e:
            logger.error(f"❌ خطا در اسکن شاخص‌ها: {e}")
        
        return indices_data

    def _calculate_opportunity_score(self, data: Dict) -> float:
        """محاسبه امتیاز فرصت معاملاتی"""
        try:
            # عوامل مختلف برای محاسبه امتیاز
            volatility = abs(data.get('percentage', 0) or data.get('change_24h', 0)) / 10
            volume_factor = min(data.get('volume', 0) / 1000000, 1)  # حداکثر 1
            
            # امتیاز ترکیبی
            score = (volatility * 0.7) + (volume_factor * 0.3)
            return min(score, 1.0)  # حداکثر 1
            
        except Exception:
            return 0.1  # امتیاز پیش‌فرض

    async def find_best_opportunities(self, limit: int = 5) -> List[Dict[str, Any]]:
        """یافتن بهترین فرصت‌های معاملاتی"""
        
        if not self.market_data:
            await self.scan_all_markets()
        
        all_opportunities = []
        
        # جمع‌آوری تمام فرصت‌ها
        for market_type, market_data in self.market_data.items():
            for symbol, data in market_data.items():
                opportunity = {
                    'symbol': symbol,
                    'market': market_type,
                    'price': data.get('price', 0),
                    'change_24h': data.get('change_24h', 0),
                    'opportunity_score': data.get('opportunity_score', 0),
                    'volume': data.get('volume', 0),
                    'risk_level': self.markets.get(market_type, {}).get('risk_level', 'UNKNOWN')
                }
                all_opportunities.append(opportunity)
        
        # مرتب‌سازی بر اساس امتیاز فرصت
        sorted_opportunities = sorted(
            all_opportunities, 
            key=lambda x: x['opportunity_score'], 
            reverse=True
        )
        
        self.opportunities = sorted_opportunities[:limit]
        
        logger.info(f"🎯 {len(self.opportunities)} فرصت برتر یافت شد")
        
        return self.opportunities

    async def generate_ai_analysis(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """تحلیل هوشمند فرصت‌ها با AI"""
        
        if not opportunities:
            return {"analysis": "فرصت معاملاتی مناسب یافت نشد", "recommendation": "HOLD"}
        
        try:
            # آماده‌سازی داده‌ها برای AI
            market_summary = ""
            for opp in opportunities[:3]:  # 3 فرصت برتر
                market_summary += f"""
                بازار: {opp['market']}
                دارایی: {opp['symbol']}
                قیمت: ${opp['price']:,.2f}
                تغییر 24ساعته: {opp['change_24h']:+.2f}%
                امتیاز فرصت: {opp['opportunity_score']:.2f}
                ریسک: {opp['risk_level']}
                """
            
            prompt = f"""
            تحلیل جامع بازارهای مالی:
            
            {market_summary}
            
            لطفاً:
            1. بهترین فرصت معاملاتی را انتخاب کنید
            2. توصیه عملی ارائه دهید (BUY/SELL/HOLD)
            3. دلیل انتخاب را توضیح دهید
            4. میزان ریسک را ارزیابی کنید
            
            پاسخ فارسی و کوتاه:
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            ai_analysis = response.choices[0].message.content
            
            # استخراج توصیه
            recommendation = "HOLD"
            if "خرید" in ai_analysis or "BUY" in ai_analysis.upper():
                recommendation = "BUY"
            elif "فروش" in ai_analysis or "SELL" in ai_analysis.upper():
                recommendation = "SELL"
            
            return {
                "analysis": ai_analysis,
                "recommendation": recommendation,
                "best_opportunity": opportunities[0] if opportunities else None,
                "confidence": 0.8,  # 80% اطمینان
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل AI: {e}")
            return {
                "analysis": "خطا در تحلیل هوشمند",
                "recommendation": "HOLD",
                "confidence": 0.1
            }

    async def execute_comprehensive_analysis(self) -> Dict[str, Any]:
        """اجرای تحلیل جامع تمام بازارها"""
        logger.info("🚀 شروع تحلیل جامع چند بازاری...")
        
        # مرحله 1: اسکن همه بازارها
        market_data = await self.scan_all_markets()
        
        # مرحله 2: یافتن بهترین فرصت‌ها
        opportunities = await self.find_best_opportunities(10)
        
        # مرحله 3: تحلیل AI
        ai_analysis = await self.generate_ai_analysis(opportunities)
        
        # خلاصه نتایج
        summary = {
            "total_markets_scanned": len(market_data),
            "total_assets_analyzed": sum(len(data) for data in market_data.values()),
            "top_opportunities": opportunities[:5],
            "ai_recommendation": ai_analysis,
            "execution_time": datetime.now().isoformat()
        }
        
        logger.info("✅ تحلیل جامع کامل شد")
        
        return summary

# تست سیستم
async def main():
    """تست سیستم چند بازاری"""
    engine = MultiMarketTradingEngine()
    
    print("🔍 تست سیستم معاملات چند بازاری...")
    result = await engine.execute_comprehensive_analysis()
    
    print(f"\n📊 نتایج:")
    print(f"- بازارهای اسکن شده: {result['total_markets_scanned']}")
    print(f"- دارایی‌های بررسی شده: {result['total_assets_analyzed']}")
    print(f"- بهترین فرصت‌ها: {len(result['top_opportunities'])}")
    print(f"- توصیه AI: {result['ai_recommendation']['recommendation']}")

if __name__ == "__main__":
    asyncio.run(main())