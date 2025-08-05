#!/usr/bin/env python3
"""
سیستم موجودی یکپارچه - بدون تداخل، با دقت کامل
"""
import os
import json
import sqlite3
from datetime import datetime
from real_balance_authenticator import RealBalanceAuthenticator

class UnifiedBalanceSystem:
    def __init__(self):
        self.authenticator = RealBalanceAuthenticator()
        
    def get_unified_balance_data(self):
        """دریافت داده‌های موجودی یکپارچه"""
        
        # 1. تایید صحت داده‌ها
        auth_result = self.authenticator.verify_balance_authenticity()
        
        # 2. دریافت موجودی واقعی (اگر ممکن باشد)
        real_mexc = self.authenticator.test_real_mexc_connection()
        
        # 3. دریافت سودهای محاسبه شده
        db_profit = self.authenticator.get_database_profit_summary()
        
        # 4. ترکیب داده‌ها با اولویت صحت
        if real_mexc['connected']:
            # حالت ایده‌آل: موجودی واقعی موجود است
            current_balance = real_mexc['total_usd']
            balance_source = 'real_exchange'
            balance_verified = True
        else:
            # حالت محدود: استفاده از محاسبات
            if db_profit.get('database_exists'):
                # فرض: موجودی اولیه + سود = موجودی فعلی
                assumed_initial = 100.98  # محاسبه: 104.07 - 3.09
                current_balance = assumed_initial + db_profit['net_profit']
                balance_source = 'calculated'
                balance_verified = False
            else:
                current_balance = 0.0
                balance_source = 'none'
                balance_verified = False
        
        return {
            'balance_data': {
                'current_balance': current_balance,
                'balance_source': balance_source,
                'balance_verified': balance_verified,
                'last_update': datetime.now().isoformat()
            },
            'profit_data': {
                'total_profit': db_profit.get('net_profit', 0.0),
                'total_trades': db_profit.get('total_trades', 0),
                'profit_verified': db_profit.get('database_exists', False)
            },
            'exchange_data': {
                'mexc_connected': real_mexc['connected'],
                'mexc_balance': real_mexc.get('total_usd', 0.0) if real_mexc['connected'] else None,
                'connection_error': real_mexc.get('error') if not real_mexc['connected'] else None
            },
            'authenticity': {
                'score': auth_result['authenticity_score'],
                'percentage': auth_result['authenticity_percentage'],
                'recommendation': auth_result['recommendation']
            }
        }
    
    def format_balance_display(self, unified_data):
        """فرمت نمایش موجودی با شفافیت کامل"""
        balance_data = unified_data['balance_data']
        profit_data = unified_data['profit_data']
        authenticity = unified_data['authenticity']
        
        # نمایش اصلی
        display = {
            'current_balance_usd': f"${balance_data['current_balance']:.2f}",
            'total_profit_usd': f"${profit_data['total_profit']:.2f}",
            'total_trades': profit_data['total_trades'],
            'authenticity_score': f"{authenticity['percentage']:.0f}%"
        }
        
        # شفافیت کامل در منبع داده‌ها
        if balance_data['balance_source'] == 'real_exchange':
            display['balance_status'] = "✅ واقعی (از صرافی)"
        elif balance_data['balance_source'] == 'calculated':
            display['balance_status'] = "⚠️ محاسبه شده (نیاز تایید)"
        else:
            display['balance_status'] = "❌ نامشخص"
        
        # وضوح کامل در صحت سودها
        if profit_data['profit_verified']:
            display['profit_status'] = "✅ تایید شده (از دیتابیس)"
        else:
            display['profit_status'] = "❌ تایید نشده"
        
        return display
    
    def generate_transparency_report(self):
        """تولید گزارش شفافیت کامل"""
        unified_data = self.get_unified_balance_data()
        formatted_display = self.format_balance_display(unified_data)
        
        report = {
            'raw_data': unified_data,
            'display_format': formatted_display,
            'transparency_notes': {
                'data_sources': [
                    f"موجودی: {unified_data['balance_data']['balance_source']}",
                    f"سودها: {'دیتابیس واقعی' if unified_data['profit_data']['profit_verified'] else 'نامشخص'}",
                    f"اتصال صرافی: {'فعال' if unified_data['exchange_data']['mexc_connected'] else 'غیرفعال'}"
                ],
                'verification_status': unified_data['authenticity']['recommendation'],
                'user_should_know': [
                    "موجودی نمایش داده شده از کدام منبع است",
                    "آیا سودها واقعاً به موجودی اضافه شده‌اند",
                    "چه مراحلی برای تایید کامل نیاز است"
                ]
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # ذخیره گزارش
        with open('unified_balance_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report

def main():
    """تست سیستم یکپارچه"""
    print("🔄 سیستم موجودی یکپارچه")
    print("=" * 50)
    
    system = UnifiedBalanceSystem()
    unified_data = system.get_unified_balance_data()
    formatted_display = system.format_balance_display(unified_data)
    
    print("💰 نمایش موجودی:")
    for key, value in formatted_display.items():
        print(f"   {key}: {value}")
    
    print(f"\n📊 صحت کلی: {unified_data['authenticity']['percentage']:.0f}%")
    print(f"💡 توصیه: {unified_data['authenticity']['recommendation']}")
    
    # تولید گزارش شفافیت
    transparency_report = system.generate_transparency_report()
    print(f"\n📄 گزارش کامل: unified_balance_report.json")

if __name__ == "__main__":
    main()