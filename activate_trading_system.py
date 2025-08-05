#!/usr/bin/env python3
"""
فعال‌سازی سیستم معاملات ULTRA_PLUS_BOT
"""

import os
import asyncio
import logging
import ccxt
import json
from datetime import datetime
from multi_market_trading_engine import MultiMarketTradingEngine
from smart_portfolio_manager import SmartPortfolioManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class TradingSystemActivator:
    def __init__(self):
        self.mexc_api_key = os.getenv('MEXC_API_KEY')
        self.mexc_secret = os.getenv('MEXC_SECRET_KEY')
        self.trading_active = False
        
    def check_api_connection(self):
        """بررسی اتصال به exchange"""
        try:
            if not self.mexc_api_key or not self.mexc_secret:
                logger.error("❌ کلیدهای API موجود نیست")
                return False
                
            # تست اتصال MEXC
            mexc = ccxt.mexc({
                'apiKey': self.mexc_api_key,
                'secret': self.mexc_secret,
                'sandbox': False,
                'enableRateLimit': True
            })
            
            # تست دریافت موجودی
            balance = mexc.fetch_balance()
            total_balance = balance['USDT']['total'] if 'USDT' in balance else 0
            
            logger.info(f"✅ اتصال MEXC موفق - موجودی: ${total_balance:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در اتصال MEXC: {str(e)}")
            return False
    
    def get_trading_status(self):
        """دریافت وضعیت سیستم معامله"""
        status = {
            'mexc_connected': False,
            'portfolio_manager_active': False,
            'trading_engine_active': False,
            'balance_usdt': 0,
            'active_positions': 0,
            'last_trade': 'هرگز',
            'total_profit': 0
        }
        
        try:
            # بررسی اتصال MEXC
            if self.check_api_connection():
                status['mexc_connected'] = True
                
                mexc = ccxt.mexc({
                    'apiKey': self.mexc_api_key,
                    'secret': self.mexc_secret,
                    'sandbox': False
                })
                
                balance = mexc.fetch_balance()
                status['balance_usdt'] = balance['USDT']['total'] if 'USDT' in balance else 0
            
            # بررسی مدیر سرمایه
            try:
                portfolio = SmartPortfolioManager()
                status['portfolio_manager_active'] = True
                logger.info("✅ مدیر هوشمند سرمایه فعال")
            except:
                logger.warning("⚠️ مدیر سرمایه غیرفعال")
            
            # بررسی موتور معامله
            try:
                engine = MultiMarketTradingEngine()
                status['trading_engine_active'] = True
                logger.info("✅ موتور معاملات چند بازاری فعال")
            except:
                logger.warning("⚠️ موتور معامله غیرفعال")
                
        except Exception as e:
            logger.error(f"خطا در دریافت وضعیت: {e}")
        
        return status
    
    def activate_live_trading(self):
        """فعال‌سازی معاملات زنده"""
        try:
            logger.info("🚀 شروع فعال‌سازی سیستم معاملات...")
            
            # بررسی پیش‌نیازها
            if not self.check_api_connection():
                return {
                    'success': False,
                    'error': 'اتصال به exchange برقرار نشد',
                    'solution': 'کلیدهای API را بررسی کنید'
                }
            
            # راه‌اندازی موتور معاملات
            engine = MultiMarketTradingEngine()
            
            # راه‌اندازی مدیر سرمایه
            portfolio = SmartPortfolioManager()
            
            # تست معامله آزمایشی (مقدار کم)
            test_result = self.perform_test_trade()
            
            if test_result['success']:
                self.trading_active = True
                
                # ذخیره وضعیت فعال
                status = {
                    'trading_active': True,
                    'activation_time': datetime.now().isoformat(),
                    'test_trade_result': test_result,
                    'engine_status': 'active',
                    'portfolio_status': 'active'
                }
                
                with open('trading_system_status.json', 'w', encoding='utf-8') as f:
                    json.dump(status, f, ensure_ascii=False, indent=2)
                
                logger.info("✅ سیستم معاملات فعال شد")
                return {
                    'success': True,
                    'message': 'سیستم معاملات با موفقیت فعال شد',
                    'test_trade': test_result,
                    'status': 'active'
                }
            else:
                return {
                    'success': False,
                    'error': 'معامله آزمایشی ناموفق',
                    'details': test_result
                }
                
        except Exception as e:
            logger.error(f"خطا در فعال‌سازی: {e}")
            return {
                'success': False,
                'error': str(e),
                'solution': 'سیستم را مجدداً راه‌اندازی کنید'
            }
    
    def perform_test_trade(self):
        """انجام معامله آزمایشی"""
        try:
            mexc = ccxt.mexc({
                'apiKey': self.mexc_api_key,
                'secret': self.mexc_secret,
                'sandbox': False,
                'enableRateLimit': True
            })
            
            # دریافت قیمت BTC
            ticker = mexc.fetch_ticker('BTC/USDT')
            current_price = ticker['last']
            
            # محاسبه مقدار معامله آزمایشی (حداقل)
            balance = mexc.fetch_balance()
            usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
            
            if usdt_balance < 10:
                return {
                    'success': False,
                    'error': 'موجودی ناکافی برای معامله آزمایشی',
                    'required': 10,
                    'available': usdt_balance
                }
            
            # معامله آزمایشی شبیه‌سازی شده (بدون انجام معامله واقعی)
            test_amount = min(10, usdt_balance * 0.01)  # 1% یا حداکثر $10
            
            logger.info(f"🧪 معامله آزمایشی شبیه‌سازی شد: ${test_amount:.2f} در قیمت ${current_price:.2f}")
            
            return {
                'success': True,
                'type': 'simulation',
                'amount_usdt': test_amount,
                'btc_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'message': 'معامله آزمایشی موفق (شبیه‌سازی)'
            }
            
        except Exception as e:
            logger.error(f"خطا در معامله آزمایشی: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """اجرای اصلی فعال‌ساز"""
    activator = TradingSystemActivator()
    
    print("🔍 بررسی وضعیت سیستم معاملات...")
    status = activator.get_trading_status()
    
    print("📊 وضعیت فعلی:")
    print(f"   💱 اتصال MEXC: {'✅' if status['mexc_connected'] else '❌'}")
    print(f"   💼 مدیر سرمایه: {'✅' if status['portfolio_manager_active'] else '❌'}")
    print(f"   🚀 موتور معامله: {'✅' if status['trading_engine_active'] else '❌'}")
    print(f"   💰 موجودی USDT: ${status['balance_usdt']:.2f}")
    
    if status['mexc_connected']:
        print("\n🚀 فعال‌سازی سیستم معاملات...")
        result = activator.activate_live_trading()
        
        if result['success']:
            print("✅ سیستم معاملات فعال شد!")
            print(f"   📈 معامله آزمایشی: {result['test_trade']['message']}")
        else:
            print(f"❌ خطا: {result['error']}")
            if 'solution' in result:
                print(f"   💡 راه‌حل: {result['solution']}")
    else:
        print("❌ ابتدا اتصال به exchange را برقرار کنید")

if __name__ == "__main__":
    main()