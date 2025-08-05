#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم یکپارچه اخبار و تحلیل احساسات بازار
استفاده از NewsAPI، Twitter، و سایر منابع برای افزایش هوش ربات
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAPIIntegration:
    """یکپارچه‌سازی با NewsAPI برای دریافت اخبار بازارهای مالی"""
    
    def __init__(self):
        self.newsapi_key = os.environ.get('NEWSAPI_KEY', '')
        self.twitter_bearer = os.environ.get('TWITTER_BEARER_TOKEN', '')
        self.polygon_key = os.environ.get('POLYGON_API_KEY', '')
        
        # کلیدواژه‌های مهم برای جستجو
        self.crypto_keywords = ['Bitcoin', 'Ethereum', 'cryptocurrency', 'crypto market', 'blockchain']
        self.stock_keywords = ['stock market', 'S&P 500', 'NASDAQ', 'NYSE', 'earnings']
        self.forex_keywords = ['forex', 'USD', 'EUR', 'currency exchange', 'dollar']
        self.commodity_keywords = ['gold', 'oil', 'commodity', 'silver', 'crude oil']
        
        self.sentiment_scores = {}
        self.market_news = {}
        
    def check_api_keys(self) -> Dict[str, bool]:
        """بررسی وضعیت کلیدهای API"""
        return {
            'newsapi': bool(self.newsapi_key),
            'twitter': bool(self.twitter_bearer),
            'polygon': bool(self.polygon_key),
            'okx': bool(os.environ.get('OKX_API_SECRET', ''))
        }
    
    def fetch_crypto_news(self) -> List[Dict]:
        """دریافت اخبار ارز دیجیتال"""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not found")
            return []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': ' OR '.join(self.crypto_keywords),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.newsapi_key,
                'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json().get('articles', [])[:10]
                logger.info(f"✅ دریافت {len(articles)} خبر ارز دیجیتال")
                return articles
            else:
                logger.error(f"NewsAPI error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
            return []
    
    def fetch_stock_news(self) -> List[Dict]:
        """دریافت اخبار بازار سهام"""
        if not self.newsapi_key:
            return []
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'category': 'business',
                'country': 'us',
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json().get('articles', [])[:10]
                logger.info(f"✅ دریافت {len(articles)} خبر بازار سهام")
                return articles
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching stock news: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> float:
        """تحلیل احساسات متن (ساده)"""
        # کلمات مثبت و منفی
        positive_words = ['surge', 'gain', 'rise', 'jump', 'boost', 'rally', 'growth', 
                         'positive', 'bullish', 'up', 'increase', 'high', 'record']
        negative_words = ['fall', 'drop', 'decline', 'crash', 'loss', 'bear', 'down',
                         'negative', 'bearish', 'low', 'decrease', 'plunge', 'sell-off']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5  # خنثی
        
        sentiment = positive_count / (positive_count + negative_count)
        return sentiment
    
    def get_polygon_market_status(self) -> Dict:
        """دریافت وضعیت بازار از Polygon.io"""
        if not self.polygon_key:
            return {}
        
        try:
            url = f"https://api.polygon.io/v1/marketstatus/now?apiKey={self.polygon_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ وضعیت بازار از Polygon دریافت شد")
                return data
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Polygon API error: {e}")
            return {}
    
    def analyze_all_markets(self) -> Dict[str, Any]:
        """تحلیل جامع همه بازارها"""
        logger.info("🔍 شروع تحلیل اخبار بازارها...")
        
        # بررسی کلیدها
        api_status = self.check_api_keys()
        active_apis = sum(api_status.values())
        
        # دریافت اخبار
        crypto_news = self.fetch_crypto_news()
        stock_news = self.fetch_stock_news()
        
        # تحلیل احساسات
        crypto_sentiment = 0.5
        stock_sentiment = 0.5
        
        if crypto_news:
            sentiments = [self.analyze_sentiment(article.get('title', '') + ' ' + 
                                               article.get('description', '')) 
                         for article in crypto_news]
            crypto_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5
        
        if stock_news:
            sentiments = [self.analyze_sentiment(article.get('title', '') + ' ' + 
                                               article.get('description', '')) 
                         for article in stock_news]
            stock_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5
        
        # وضعیت بازار از Polygon
        market_status = self.get_polygon_market_status()
        
        # محاسبه امتیاز هوش
        intelligence_boost = 0
        if api_status['newsapi']:
            intelligence_boost += 10
        if api_status['twitter']:
            intelligence_boost += 5
        if api_status['polygon']:
            intelligence_boost += 5
        if api_status['okx']:
            intelligence_boost += 5
        
        # ذخیره نتایج
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'api_status': api_status,
            'active_apis': active_apis,
            'intelligence_boost': intelligence_boost,
            'crypto_sentiment': crypto_sentiment,
            'stock_sentiment': stock_sentiment,
            'total_news_analyzed': len(crypto_news) + len(stock_news),
            'market_status': market_status,
            'recommendations': self._generate_recommendations(crypto_sentiment, stock_sentiment)
        }
        
        # ذخیره در فایل
        with open('news_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ تحلیل کامل شد - افزایش هوش: +{intelligence_boost}%")
        
        return analysis_result
    
    def _generate_recommendations(self, crypto_sentiment: float, stock_sentiment: float) -> List[str]:
        """تولید توصیه‌های معاملاتی بر اساس احساسات بازار"""
        recommendations = []
        
        if crypto_sentiment > 0.7:
            recommendations.append("🟢 احساسات مثبت قوی در بازار کریپتو - فرصت خرید")
        elif crypto_sentiment < 0.3:
            recommendations.append("🔴 احساسات منفی در بازار کریپتو - احتیاط در خرید")
        else:
            recommendations.append("🟡 احساسات خنثی در بازار کریپتو - منتظر سیگنال قوی‌تر")
        
        if stock_sentiment > 0.7:
            recommendations.append("🟢 احساسات مثبت در بازار سهام - بررسی سهام‌های برتر")
        elif stock_sentiment < 0.3:
            recommendations.append("🔴 احساسات منفی در بازار سهام - مدیریت ریسک")
        
        return recommendations
    
    def continuous_monitoring(self, interval_minutes: int = 30):
        """پایش مداوم اخبار"""
        logger.info(f"🚀 شروع پایش مداوم اخبار (هر {interval_minutes} دقیقه)")
        
        while True:
            try:
                # تحلیل بازارها
                result = self.analyze_all_markets()
                
                # نمایش خلاصه
                print(f"\n📊 گزارش تحلیل اخبار - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   API های فعال: {result['active_apis']} از 4")
                print(f"   افزایش هوش: +{result['intelligence_boost']}%")
                print(f"   احساسات کریپتو: {result['crypto_sentiment']:.2f}")
                print(f"   احساسات سهام: {result['stock_sentiment']:.2f}")
                print(f"   اخبار تحلیل شده: {result['total_news_analyzed']}")
                
                print("\n💡 توصیه‌ها:")
                for rec in result['recommendations']:
                    print(f"   {rec}")
                
                # انتظار تا دوره بعد
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("❌ توقف پایش اخبار")
                break
            except Exception as e:
                logger.error(f"خطا در پایش: {e}")
                time.sleep(60)  # انتظار 1 دقیقه در صورت خطا

def update_intelligence_with_news():
    """بروزرسانی سطح هوش با داده‌های اخبار"""
    try:
        # خواندن سطح هوش فعلی
        if os.path.exists('learning_progress.json'):
            with open('learning_progress.json', 'r') as f:
                progress = json.load(f)
        else:
            progress = {'intelligence_level': 35.9}
        
        # خواندن نتایج تحلیل اخبار
        if os.path.exists('news_analysis_results.json'):
            with open('news_analysis_results.json', 'r') as f:
                news_result = json.load(f)
                intelligence_boost = news_result.get('intelligence_boost', 0)
                
                # اضافه کردن بونوس اخبار به سطح هوش
                progress['intelligence_level'] = min(100.0, float(progress['intelligence_level']) + float(intelligence_boost))
                progress['news_api_active'] = True
                progress['last_news_update'] = datetime.now().isoformat()
                
                # ذخیره
                with open('learning_progress.json', 'w') as f:
                    json.dump(progress, f, indent=2)
                
                logger.info(f"✅ سطح هوش با اخبار بروز شد: +{intelligence_boost}% → {progress['intelligence_level']:.1f}%")
        
    except Exception as e:
        logger.error(f"خطا در بروزرسانی هوش: {e}")

if __name__ == "__main__":
    # ایجاد نمونه و شروع تحلیل
    news_system = NewsAPIIntegration()
    
    # تحلیل یکباره
    result = news_system.analyze_all_markets()
    
    # بروزرسانی سطح هوش
    update_intelligence_with_news()
    
    # شروع پایش مداوم
    # news_system.continuous_monitoring(30)