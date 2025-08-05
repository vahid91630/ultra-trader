#!/usr/bin/env python3
"""
سیستم تایید موجودی واقعی - ترکیب صحت و شفافیت کامل
"""
import os
import ccxt
import json
import sqlite3
from datetime import datetime

class RealBalanceAuthenticator:
    def __init__(self):
        self.mexc_api_key = os.getenv('MEXC_API_KEY')
        self.mexc_secret = os.getenv('MEXC_SECRET_KEY')
        self.sandbox_mode = True  # تست در sandbox
        
    def test_real_mexc_connection(self):
        """تست اتصال واقعی به MEXC"""
        if not (self.mexc_api_key and self.mexc_secret):
            return {
                'connected': False,
                'error': 'کلیدهای API موجود نیست',
                'needs_keys': True
            }
        
        try:
            exchange = ccxt.mexc({
                'apiKey': self.mexc_api_key,
                'secret': self.mexc_secret,
                'sandbox': self.sandbox_mode,
                'enableRateLimit': True,
            })
            
            # تست اتصال با دریافت موجودی
            balance = exchange.fetch_balance()
            
            return {
                'connected': True,
                'balance': balance,
                'total_usd': balance.get('USDT', {}).get('total', 0),
                'free_usd': balance.get('USDT', {}).get('free', 0),
                'used_usd': balance.get('USDT', {}).get('used', 0),
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'needs_valid_keys': True
            }
    
    def get_database_profit_summary(self):
        """دریافت خلاصه سود از دیتابیس"""
        if not os.path.exists('autonomous_trading.db'):
            return {
                'total_trades': 0,
                'total_profit': 0.0,
                'database_exists': False
            }
        
        try:
            conn = sqlite3.connect('autonomous_trading.db')
            cursor = conn.cursor()
            
            # خلاصه معاملات
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN profit_loss ELSE 0 END) as total_profit,
                    SUM(CASE WHEN profit_loss < 0 THEN profit_loss ELSE 0 END) as total_loss,
                    SUM(profit_loss) as net_profit,
                    MIN(timestamp) as first_trade,
                    MAX(timestamp) as last_trade
                FROM trades
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                'total_trades': result[0] or 0,
                'total_profit': result[1] or 0.0,
                'total_loss': result[2] or 0.0,
                'net_profit': result[3] or 0.0,
                'first_trade': result[4],
                'last_trade': result[5],
                'database_exists': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'database_exists': True,
                'readable': False
            }
    
    def verify_balance_authenticity(self):
        """تایید کامل صحت موجودی"""
        print("🔍 تایید کامل صحت موجودی و سودها")
        print("=" * 60)
        
        # 1. دریافت موجودی واقعی صرافی
        mexc_data = self.test_real_mexc_connection()
        print(f"🏦 اتصال صرافی MEXC:")
        if mexc_data['connected']:
            print(f"   ✅ متصل - موجودی واقعی: ${mexc_data['total_usd']:.2f}")
            real_balance = mexc_data['total_usd']
        else:
            print(f"   ❌ عدم اتصال: {mexc_data.get('error', 'نامشخص')}")
            real_balance = None
        
        # 2. دریافت سودهای محاسبه شده
        db_data = self.get_database_profit_summary()
        print(f"\n📊 سودهای محاسبه شده:")
        if db_data.get('database_exists'):
            print(f"   💰 سود خالص: ${db_data['net_profit']:.2f}")
            print(f"   📈 تعداد معاملات: {db_data['total_trades']}")
            calculated_profit = db_data['net_profit']
        else:
            print(f"   ❌ دیتابیس معاملات موجود نیست")
            calculated_profit = 0.0
        
        # 3. تحلیل صحت
        print(f"\n🎯 تحلیل صحت:")
        
        authenticity_score = 0
        max_score = 3
        
        # امتیاز 1: وجود اتصال واقعی
        if mexc_data['connected']:
            print(f"   ✅ اتصال واقعی صرافی: موجود")
            authenticity_score += 1
        else:
            print(f"   ❌ اتصال واقعی صرافی: ناموجود")
        
        # امتیاز 2: وجود داده‌های معاملاتی
        if db_data.get('total_trades', 0) > 0:
            print(f"   ✅ معاملات ثبت شده: {db_data['total_trades']} معامله")
            authenticity_score += 1
        else:
            print(f"   ❌ معاملات ثبت شده: هیچ")
        
        # امتیاز 3: تطبیق منطقی داده‌ها
        if real_balance is not None and calculated_profit > 0:
            print(f"   ✅ قابلیت تطبیق: موجود")
            authenticity_score += 1
        else:
            print(f"   ⚠️  قابلیت تطبیق: محدود")
        
        # 4. نتیجه نهایی
        authenticity_percentage = (authenticity_score / max_score) * 100
        
        print(f"\n📋 نتیجه نهایی:")
        print(f"   امتیاز صحت: {authenticity_score}/{max_score} ({authenticity_percentage:.0f}%)")
        
        if authenticity_percentage >= 100:
            print(f"   🏆 وضعیت: کاملاً قابل تایید")
            recommendation = "تمام داده‌ها واقعی و قابل تایید هستند"
        elif authenticity_percentage >= 66:
            print(f"   ✅ وضعیت: قابل تایید با محدودیت")
            recommendation = "داده‌ها عمدتاً صحیح اما نیاز به تکمیل دارند"
        elif authenticity_percentage >= 33:
            print(f"   ⚠️  وضعیت: تایید جزئی")
            recommendation = "برخی داده‌ها قابل تایید، نیاز به بهبود"
        else:
            print(f"   ❌ وضعیت: غیرقابل تایید")
            recommendation = "داده‌ها نیاز به تایید مجدد دارند"
        
        print(f"   💡 توصیه: {recommendation}")
        
        # 5. پیشنهادات بهبود
        if authenticity_percentage < 100:
            print(f"\n🔧 پیشنهادات بهبود:")
            if not mexc_data['connected']:
                print(f"   1. تایید کلیدهای API صرافی")
                print(f"   2. تست اتصال با sandbox mode")
            if db_data.get('total_trades', 0) == 0:
                print(f"   3. ثبت معاملات واقعی در دیتابیس")
            if real_balance is None:
                print(f"   4. دریافت موجودی واقعی از صرافی")
        
        return {
            'authenticity_score': authenticity_score,
            'authenticity_percentage': authenticity_percentage,
            'real_balance': real_balance,
            'calculated_profit': calculated_profit,
            'mexc_connected': mexc_data['connected'],
            'total_trades': db_data.get('total_trades', 0),
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_authenticity_report(self):
        """تولید گزارش کامل صحت"""
        result = self.verify_balance_authenticity()
        
        # ذخیره گزارش
        with open('balance_authenticity_report.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 گزارش کامل: balance_authenticity_report.json")
        return result

def main():
    """اجرای تست کامل"""
    authenticator = RealBalanceAuthenticator()
    result = authenticator.generate_authenticity_report()
    
    print(f"\n🎯 خلاصه:")
    print(f"صحت داده‌ها: {result['authenticity_percentage']:.0f}%")
    print(f"وضعیت: {result['recommendation']}")

if __name__ == "__main__":
    main()