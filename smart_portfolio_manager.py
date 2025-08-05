#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدیر هوشمند سرمایه و پورتفولیو
مدیریت ولت واقعی، معاملات هوشمند، نگهداری طولانی مدت
"""

import asyncio
import ccxt
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os
import logging

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SmartPortfolioManager:
    def __init__(self):
        """راه‌اندازی مدیر هوشمند سرمایه"""
        
        # API کلیدها
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Exchange setup
        self.mexc = ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY'),
            'sandbox': False,
            'enableRateLimit': True
        })
        
        # تنظیمات سرمایه‌گذاری
        self.investment_strategy = {
            'daily_trading_percentage': 60,    # 60% برای معاملات روزانه
            'long_term_percentage': 25,        # 25% برای نگهداری طولانی
            'emergency_reserve': 15,           # 15% ذخیره اضطراری
            'max_single_trade': 10,            # حداکثر 10% در یک معامله
            'profit_threshold_hold': 15,       # اگر سود بیش از 15% بود، نگه دار
            'loss_threshold_sell': -8,         # اگر ضرر بیش از -8% بود، بفروش
            'hold_min_days': 3,                # حداقل 3 روز نگهداری
            'hold_max_days': 30                # حداکثر 30 روز نگهداری
        }
        
        # پایگاه داده
        self.init_database()
        
        # متغیرهای وضعیت
        self.current_balance = {}
        self.active_positions = {}
        self.trading_history = []
        
    def init_database(self):
        """راه‌اندازی پایگاه داده"""
        conn = sqlite3.connect('smart_portfolio.db')
        cursor = conn.cursor()
        
        # جدول ولت و موجودی
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL,
                asset TEXT NOT NULL,
                total_balance REAL NOT NULL,
                available_balance REAL NOT NULL,
                locked_balance REAL NOT NULL,
                usd_value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول موقعیت‌های فعال
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                investment_usd REAL NOT NULL,
                entry_date DATETIME NOT NULL,
                target_hold_days INTEGER NOT NULL,
                current_profit_pct REAL DEFAULT 0,
                status TEXT DEFAULT 'HOLDING',
                ai_recommendation TEXT,
                exit_price REAL,
                exit_date DATETIME,
                final_profit_pct REAL
            )
        ''')
        
        # جدول تاریخچه معاملات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                usd_amount REAL NOT NULL,
                profit_loss_pct REAL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول پیام‌های کاربر
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                sent BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ پایگاه داده پورتفولیو راه‌اندازی شد")

    async def get_real_wallet_balance(self) -> Dict[str, Any]:
        """دریافت موجودی واقعی ولت"""
        try:
            balance = self.mexc.fetch_balance()
            
            wallet_data = {
                'total_usd_value': 0,
                'assets': {},
                'trading_available': 0,
                'long_term_reserved': 0,
                'emergency_reserve': 0
            }
            
            # پردازش دارایی‌ها
            for symbol, data in balance.items():
                if isinstance(data, dict) and data.get('total', 0) > 0.001:
                    # قیمت فعلی دارایی
                    try:
                        if symbol != 'USDT':
                            ticker = self.mexc.fetch_ticker(f"{symbol}/USDT")
                            price_usd = ticker['last']
                        else:
                            price_usd = 1.0
                        
                        usd_value = data.get('total', 0) * price_usd
                        
                        wallet_data['assets'][symbol] = {
                            'total': data.get('total', 0),
                            'free': data.get('free', 0),
                            'locked': data.get('used', 0),
                            'price_usd': price_usd,
                            'usd_value': usd_value
                        }
                        
                        wallet_data['total_usd_value'] += usd_value
                        
                    except Exception as e:
                        logger.warning(f"خطا در محاسبه قیمت {symbol}: {e}")
            
            # تقسیم‌بندی سرمایه بر اساس استراتژی
            total_value = wallet_data['total_usd_value']
            
            wallet_data['trading_available'] = total_value * (self.investment_strategy['daily_trading_percentage'] / 100)
            wallet_data['long_term_reserved'] = total_value * (self.investment_strategy['long_term_percentage'] / 100)
            wallet_data['emergency_reserve'] = total_value * (self.investment_strategy['emergency_reserve'] / 100)
            
            self.current_balance = wallet_data
            
            # ذخیره در پایگاه داده
            await self.save_wallet_to_db(wallet_data)
            
            logger.info(f"💰 موجودی ولت: ${total_value:.2f}")
            logger.info(f"💼 قابل معامله: ${wallet_data['trading_available']:.2f}")
            logger.info(f"🎯 طولانی مدت: ${wallet_data['long_term_reserved']:.2f}")
            
            return wallet_data
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت موجودی: {e}")
            return {}

    async def save_wallet_to_db(self, wallet_data: Dict):
        """ذخیره موجودی در پایگاه داده"""
        conn = sqlite3.connect('smart_portfolio.db')
        cursor = conn.cursor()
        
        try:
            for symbol, data in wallet_data.get('assets', {}).items():
                cursor.execute('''
                    INSERT INTO wallet_balance 
                    (exchange, asset, total_balance, available_balance, locked_balance, usd_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    'mexc',
                    symbol,
                    data['total'],
                    data['free'],
                    data['locked'],
                    data['usd_value']
                ))
            
            conn.commit()
            logger.info("✅ موجودی در پایگاه داده ذخیره شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره موجودی: {e}")
        finally:
            conn.close()

    async def analyze_holding_strategy(self, asset: str, current_price: float, entry_price: float, days_held: int) -> Dict[str, Any]:
        """تحلیل استراتژی نگهداری با AI"""
        
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        try:
            prompt = f"""
            تحلیل استراتژی نگهداری دارایی:
            
            دارایی: {asset}
            قیمت ورود: ${entry_price:.4f}
            قیمت فعلی: ${current_price:.4f}
            سود/ضرر: {profit_pct:+.2f}%
            روزهای نگهداری: {days_held}
            
            با توجه به:
            - حد سود نگهداری: +15%
            - حد ضرر فروش: -8%
            - حداقل نگهداری: 3 روز
            - حداکثر نگهداری: 30 روز
            
            توصیه کن:
            1. HOLD (ادامه نگهداری)
            2. SELL (فروش فوری)
            3. PARTIAL_SELL (فروش بخشی)
            
            دلیل کوتاه به فارسی:
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            ai_analysis = response.choices[0].message.content
            
            # استخراج توصیه
            recommendation = "HOLD"
            if "SELL" in ai_analysis.upper():
                if "PARTIAL" in ai_analysis.upper():
                    recommendation = "PARTIAL_SELL"
                else:
                    recommendation = "SELL"
            
            # منطق اضافی بر اساس قوانین
            if profit_pct >= self.investment_strategy['profit_threshold_hold']:
                if days_held >= self.investment_strategy['hold_min_days']:
                    # سود خوب دارد، اما باید ادامه نگه داریم
                    recommendation = "HOLD_PROFIT"
            elif profit_pct <= self.investment_strategy['loss_threshold_sell']:
                # ضرر زیاد، باید بفروشیم
                recommendation = "SELL_LOSS"
            
            return {
                'recommendation': recommendation,
                'profit_pct': profit_pct,
                'ai_analysis': ai_analysis,
                'days_held': days_held,
                'should_notify_user': profit_pct >= 10 or profit_pct <= -5,
                'confidence': 0.85
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل نگهداری: {e}")
            return {
                'recommendation': 'HOLD',
                'profit_pct': profit_pct,
                'ai_analysis': 'خطا در تحلیل',
                'should_notify_user': False
            }

    async def check_active_positions(self) -> List[Dict]:
        """بررسی موقعیت‌های فعال"""
        
        conn = sqlite3.connect('smart_portfolio.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM active_positions 
            WHERE status = 'HOLDING'
            ORDER BY entry_date ASC
        ''')
        
        positions = cursor.fetchall()
        conn.close()
        
        notifications = []
        
        for pos in positions:
            asset = pos[1]
            entry_price = pos[2]
            quantity = pos[3]
            entry_date = datetime.fromisoformat(pos[5])
            days_held = (datetime.now() - entry_date).days
            
            try:
                # قیمت فعلی
                ticker = self.mexc.fetch_ticker(f"{asset}/USDT")
                current_price = ticker['last']
                
                # تحلیل استراتژی نگهداری
                analysis = await self.analyze_holding_strategy(
                    asset, current_price, entry_price, days_held
                )
                
                # به‌روزرسانی در پایگاه داده
                await self.update_position_status(pos[0], analysis, current_price)
                
                # اگر نیاز به اطلاع‌رسانی باشد
                if analysis['should_notify_user']:
                    notification = {
                        'type': 'POSITION_UPDATE',
                        'asset': asset,
                        'profit_pct': analysis['profit_pct'],
                        'recommendation': analysis['recommendation'],
                        'days_held': days_held,
                        'message': self.create_user_notification(asset, analysis)
                    }
                    notifications.append(notification)
                    
                    # ذخیره پیام در پایگاه داده
                    await self.save_notification(notification)
                
            except Exception as e:
                logger.error(f"❌ خطا در بررسی موقعیت {asset}: {e}")
        
        return notifications

    def create_user_notification(self, asset: str, analysis: Dict) -> str:
        """ایجاد پیام برای کاربر"""
        
        profit_pct = analysis['profit_pct']
        recommendation = analysis['recommendation']
        days_held = analysis['days_held']
        
        if recommendation == "HOLD_PROFIT":
            return f"""
🎯 نگهداری طولانی‌تر توصیه می‌شود!

💰 دارایی: {asset}
📈 سود فعلی: {profit_pct:+.2f}%
⏱️ روزهای نگهداری: {days_held}

🧠 تحلیل AI: سود خوبی دارید اما هنوز پتانسیل رشد بیشتر وجود دارد. صبر کنید تا سود بیشتری کسب کنید.

⚠️ عجله برای فروش نکنید!
            """.strip()
            
        elif recommendation == "SELL_LOSS":
            return f"""
🚨 هشدار ضرر - فروش توصیه می‌شود

💰 دارایی: {asset}
📉 ضرر فعلی: {profit_pct:+.2f}%
⏱️ روزهای نگهداری: {days_held}

🧠 تحلیل AI: {analysis['ai_analysis'][:100]}...

❗ توصیه: فروش برای جلوگیری از ضرر بیشتر
            """.strip()
            
        else:
            return f"""
📊 آپدیت موقعیت معاملاتی

💰 دارایی: {asset}
📊 سود/ضرر: {profit_pct:+.2f}%
⏱️ روزهای نگهداری: {days_held}

🧠 تحلیل AI: {analysis['ai_analysis'][:100]}...

💡 توصیه: {recommendation}
            """.strip()

    async def update_position_status(self, position_id: int, analysis: Dict, current_price: float):
        """به‌روزرسانی وضعیت موقعیت"""
        
        conn = sqlite3.connect('smart_portfolio.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE active_positions 
                SET current_profit_pct = ?, ai_recommendation = ?
                WHERE id = ?
            ''', (
                analysis['profit_pct'],
                analysis['recommendation'],
                position_id
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی موقعیت: {e}")
        finally:
            conn.close()

    async def save_notification(self, notification: Dict):
        """ذخیره پیام در پایگاه داده"""
        
        conn = sqlite3.connect('smart_portfolio.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_notifications 
                (message_type, title, content, priority)
                VALUES (?, ?, ?, ?)
            ''', (
                notification['type'],
                f"{notification['asset']} - {notification['recommendation']}",
                notification['message'],
                2 if 'LOSS' in notification['recommendation'] else 1
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره پیام: {e}")
        finally:
            conn.close()

    async def execute_smart_trading_cycle(self) -> Dict[str, Any]:
        """اجرای چرخه معاملاتی هوشمند"""
        
        logger.info("🚀 شروع چرخه معاملاتی هوشمند...")
        
        # دریافت موجودی ولت
        wallet = await self.get_real_wallet_balance()
        
        if not wallet:
            return {"error": "خطا در دریافت موجودی"}
        
        # بررسی موقعیت‌های فعال
        notifications = await self.check_active_positions()
        
        # نتایج
        result = {
            'wallet_summary': {
                'total_usd': wallet['total_usd_value'],
                'trading_available': wallet['trading_available'],
                'long_term_reserved': wallet['long_term_reserved'],
                'emergency_reserve': wallet['emergency_reserve']
            },
            'active_positions_checked': len(notifications),
            'user_notifications': notifications,
            'trading_available': wallet['trading_available'] > 50,  # آیا معامله جدید ممکن است
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("✅ چرخه معاملاتی کامل شد")
        
        return result

    async def get_pending_notifications(self) -> List[Dict]:
        """دریافت پیام‌های ارسال نشده"""
        
        conn = sqlite3.connect('smart_portfolio.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_notifications 
            WHERE sent = FALSE 
            ORDER BY priority DESC, timestamp DESC
            LIMIT 10
        ''')
        
        notifications = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': n[0],
                'type': n[1],
                'title': n[2],
                'content': n[3],
                'priority': n[4],
                'timestamp': n[6]
            }
            for n in notifications
        ]

# تست سیستم
async def main():
    """تست سیستم مدیریت هوشمند سرمایه"""
    
    manager = SmartPortfolioManager()
    
    print("🔍 تست سیستم مدیریت هوشمند سرمایه...")
    
    result = await manager.execute_smart_trading_cycle()
    
    print(f"\n📊 نتایج:")
    print(f"💰 کل موجودی: ${result['wallet_summary']['total_usd']:.2f}")
    print(f"💼 قابل معامله: ${result['wallet_summary']['trading_available']:.2f}")
    print(f"📊 موقعیت‌های بررسی شده: {result['active_positions_checked']}")
    print(f"📨 پیام‌های کاربر: {len(result['user_notifications'])}")
    
    # نمایش پیام‌ها
    for notif in result['user_notifications']:
        print(f"\n📢 {notif['asset']} - {notif['recommendation']}")
        print(f"   سود: {notif['profit_pct']:+.2f}%")

if __name__ == "__main__":
    asyncio.run(main())