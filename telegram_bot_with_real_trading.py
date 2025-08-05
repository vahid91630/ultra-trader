#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام با قابلیت معاملات واقعی
@ULTRA_PLUS_BOT - نسخه نهایی
"""

import os
import asyncio
import logging
import ccxt
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UltraPlusBotWithTrading:
    def __init__(self):
        self.token = os.getenv('ULTRA_Plus_Bot')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # راه‌اندازی MEXC (تنها exchange فعال)
        self.mexc = ccxt.mexc({
            'apiKey': os.getenv('MEXC_API_KEY'),
            'secret': os.getenv('MEXC_SECRET_KEY'),
            'sandbox': False,
            'enableRateLimit': True
        })
        
        # تنظیمات امنیتی
        self.min_trade = 10  # حداقل $10
        self.max_trade = 50  # حداکثر $50 (امن)
        
        # Import portfolio manager
        try:
            from smart_portfolio_manager import SmartPortfolioManager
            self.portfolio_manager = SmartPortfolioManager()
            logger.info("✅ مدیر هوشمند سرمایه متصل شد")
        except Exception as e:
            logger.warning(f"⚠️ خطا در اتصال مدیر سرمایه: {e}")
            self.portfolio_manager = None
        
        logger.info("🚀 ربات تلگرام با معاملات واقعی آماده شد")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور شروع"""
        keyboard = [
            [InlineKeyboardButton("💰 قیمت‌ها", callback_data="prices"),
             InlineKeyboardButton("🧠 تحلیل", callback_data="analysis")],
            [InlineKeyboardButton("💼 موجودی", callback_data="balance"),
             InlineKeyboardButton("⚡ معامله", callback_data="trade")],
            [InlineKeyboardButton("📊 توصیه‌ها", callback_data="recommendations"),
             InlineKeyboardButton("📰 اخبار", callback_data="news")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_msg = """
🤖 سلام! من ULTRA_PLUS_BOT هستم

🌍 **سیستم چند بازاری جامع:**
• 🪙 رمزارزها: Bitcoin, Ethereum, BNB و بیشتر
• 📈 بازار سهام: شرکت‌های بزرگ آمریکایی  
• 💱 فارکس: جفت ارزهای اصلی
• 🥇 کالاها: طلا، نقره، نفت، گاز
• 📊 شاخص‌ها: S&P 500, NASDAQ, و بیشتر
• 🧠 تحلیل هوش مصنوعی همه بازارها
• ⚡ **معاملات واقعی چند بازاری**

⚠️ **توجه**: معاملات واقعی با پول واقعی انجام می‌شود!

از منوی زیر انتخاب کنید:
        """
        
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

    async def get_real_prices(self):
        """دریافت قیمت‌های واقعی"""
        try:
            btc = self.mexc.fetch_ticker('BTC/USDT')
            eth = self.mexc.fetch_ticker('ETH/USDT')
            bnb = self.mexc.fetch_ticker('BNB/USDT')
            
            return {
                'BTC': btc,
                'ETH': eth, 
                'BNB': bnb
            }
        except Exception as e:
            logger.error(f"خطا در دریافت قیمت: {e}")
            return None

    async def get_account_balance(self):
        """دریافت موجودی واقعی با مدیریت هوشمند"""
        try:
            if self.portfolio_manager:
                # استفاده از مدیر هوشمند سرمایه
                wallet_data = await self.portfolio_manager.get_real_wallet_balance()
                
                if wallet_data:
                    return {
                        'smart_portfolio': True,
                        'total_usd_value': wallet_data['total_usd_value'],
                        'trading_available': wallet_data['trading_available'],
                        'long_term_reserved': wallet_data['long_term_reserved'],
                        'emergency_reserve': wallet_data['emergency_reserve'],
                        'assets': wallet_data['assets'],
                        'strategy_breakdown': {
                            'daily_trading': f"{wallet_data['trading_available']:.2f} USDT (60%)",
                            'long_term_holds': f"{wallet_data['long_term_reserved']:.2f} USDT (25%)",
                            'emergency_fund': f"{wallet_data['emergency_reserve']:.2f} USDT (15%)"
                        }
                    }
            
            # روش قدیمی در صورت مشکل
            balance = self.mexc.fetch_balance()
            
            # فیلتر دارایی‌های مثبت
            assets = {}
            total_usd = 0
            
            for symbol, data in balance.items():
                if isinstance(data, dict) and data.get('total', 0) > 0.001:  # حداقل 0.001
                    try:
                        if symbol != 'USDT':
                            ticker = self.mexc.fetch_ticker(f"{symbol}/USDT")
                            price = ticker['last']
                        else:
                            price = 1.0
                        
                        usd_value = data.get('total', 0) * price
                        total_usd += usd_value
                        
                        assets[symbol] = {
                            'total': data.get('total', 0),
                            'free': data.get('free', 0),
                            'price_usd': price,
                            'usd_value': usd_value
                        }
                        
                    except Exception as e:
                        logger.warning(f"خطا در محاسبه قیمت {symbol}: {e}")
            
            return {
                'smart_portfolio': False,
                'total_usd_value': total_usd,
                'assets': assets
            }
            
        except Exception as e:
            logger.error(f"خطا در دریافت موجودی: {e}")
            return None

    async def ai_market_analysis(self, symbol):
        """تحلیل بازار با AI"""
        try:
            ticker = self.mexc.fetch_ticker(symbol)
            
            prompt = f"""
تحلیل {symbol}:
قیمت: ${ticker['last']:,.2f}
تغییر 24ساعته: {ticker['percentage']:+.2f}%
حجم: ${ticker['quoteVolume']:,.0f}

توصیه کوتاه (خرید/فروش/نگهداری) با دلیل:
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"خطا در تحلیل: {str(e)[:50]}"

    async def execute_real_trade(self, symbol, side, amount_usd):
        """اجرای معامله واقعی"""
        try:
            if amount_usd < self.min_trade or amount_usd > self.max_trade:
                return f"❌ مبلغ باید بین ${self.min_trade}-${self.max_trade} باشد"
            
            # دریافت قیمت فعلی
            ticker = self.mexc.fetch_ticker(symbol)
            price = ticker['last']
            
            # محاسبه مقدار
            if side == 'buy':
                quantity = amount_usd / price
            else:
                # برای فروش نیاز به موجودی
                balance = self.mexc.fetch_balance()
                symbol_name = symbol.split('/')[0]
                available = balance.get(symbol_name, {}).get('free', 0)
                quantity = min(amount_usd / price, available)
                
                if quantity <= 0:
                    return f"❌ موجودی {symbol_name} کافی نیست"
            
            # اجرای سفارش
            order = self.mexc.create_market_order(symbol, side, quantity)
            
            return f"""
✅ **معامله انجام شد!**

📊 جزئیات:
• نماد: {symbol}
• نوع: {'خرید' if side == 'buy' else 'فروش'}
• مقدار: {quantity:.6f}
• قیمت: ${price:,.2f}
• ارزش: ${quantity * price:.2f}
• شناسه: {order['id']}
• زمان: {datetime.now().strftime('%H:%M:%S')}
            """
            
        except Exception as e:
            return f"❌ خطا در معامله: {str(e)[:100]}"

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش دکمه‌ها"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "prices":
                await query.edit_message_text("🔄 دریافت قیمت‌های واقعی...")
                
                prices = await self.get_real_prices()
                if prices:
                    msg = "💰 **قیمت‌های لحظه‌ای MEXC:**\n\n"
                    for symbol, data in prices.items():
                        trend = "🟢" if data['percentage'] >= 0 else "🔴"
                        msg += f"{trend} **{symbol}**: ${data['last']:,.2f}\n"
                        msg += f"   تغییر: {data['percentage']:+.2f}%\n\n"
                    
                    msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}"
                else:
                    msg = "❌ خطا در دریافت قیمت‌ها"
                
                await query.edit_message_text(msg, parse_mode='Markdown')
                
            elif query.data == "balance":
                await query.edit_message_text("🔄 بررسی ولت هوشمند...")
                
                balance = await self.get_account_balance()
                
                if balance and balance.get('smart_portfolio'):
                    # نمایش مدیریت هوشمند سرمایه
                    msg = f"""
💼 **ولت هوشمند شما:**

💰 **کل موجودی:** ${balance['total_usd_value']:.2f}

📊 **تقسیم‌بندی هوشمند:**
• 💼 معاملات روزانه: ${balance['trading_available']:.2f} (%60)
• 🎯 نگهداری طولانی: ${balance['long_term_reserved']:.2f} (%25)  
• 🛡️ ذخیره اضطراری: ${balance['emergency_reserve']:.2f} (%15)

**دارایی‌های شما:**
                    """
                    
                    # نمایش دارایی‌ها
                    for symbol, data in balance['assets'].items():
                        if data['usd_value'] > 0.1:
                            msg += f"• {symbol}: {data['total']:.6f} (${data['usd_value']:.2f})\n"
                    
                    # دکمه‌های اضافی
                    keyboard = [
                        [InlineKeyboardButton("📊 بررسی موقعیت‌ها", callback_data="check_positions")],
                        [InlineKeyboardButton("📈 پیام‌های هوشمند", callback_data="smart_notifications")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
                    
                elif balance:
                    # نمایش ساده موجودی
                    msg = "💼 **موجودی MEXC:**\n\n"
                    total_usd = balance.get('total_usd_value', 0)
                    
                    for symbol, data in balance.get('assets', {}).items():
                        if isinstance(data, dict) and data.get('usd_value', 0) > 0.1:
                            msg += f"• **{symbol}**: {data['total']:.6f} (${data['usd_value']:.2f})\n"
                            msg += f"  قابل معامله: {data.get('free', 0):.6f}\n\n"
                    
                    msg += f"💰 **کل ارزش**: ~${total_usd:.2f}"
                    
                    await query.edit_message_text(msg, parse_mode='Markdown')
                    
                else:
                    msg = "❌ خطا در دریافت موجودی"
                    await query.edit_message_text(msg, parse_mode='Markdown')
                
            elif query.data == "analysis":
                await query.edit_message_text("🧠 تحلیل هوشمند...")
                
                analysis_btc = await self.ai_market_analysis('BTC/USDT')
                analysis_eth = await self.ai_market_analysis('ETH/USDT')
                
                msg = f"""
🧠 **تحلیل AI:**

**Bitcoin:**
{analysis_btc}

**Ethereum:**  
{analysis_eth}

⚠️ این تحلیل فقط مشاوره است.
                """
                
                await query.edit_message_text(msg, parse_mode='Markdown')
                
            elif query.data == "trade":
                keyboard = [
                    [InlineKeyboardButton("🟢 خرید $10 BTC", callback_data="buy_btc_10"),
                     InlineKeyboardButton("🟢 خرید $20 ETH", callback_data="buy_eth_20")],
                    [InlineKeyboardButton("🔴 فروش $10 BTC", callback_data="sell_btc_10"),
                     InlineKeyboardButton("🔴 فروش $20 ETH", callback_data="sell_eth_20")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                msg = """
⚡ **معاملات واقعی:**

⚠️ **هشدار**: معاملات با پول واقعی انجام می‌شود!

• حداقل معامله: $10
• حداکثر معامله: $50
• Exchange: MEXC
• نوع سفارش: بازار (فوری)

معامله موردنظر را انتخاب کنید:
                """
                
                await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
                
            # بررسی موقعیت‌های فعال
            elif query.data == "check_positions":
                await query.edit_message_text("🔍 بررسی موقعیت‌های فعال...")
                
                if self.portfolio_manager:
                    result = await self.portfolio_manager.execute_smart_trading_cycle()
                    notifications = result.get('user_notifications', [])
                    
                    if notifications:
                        msg = "📊 **موقعیت‌های شما:**\n\n"
                        for notif in notifications[:3]:  # نمایش 3 مورد اول
                            msg += f"🎯 **{notif['asset']}**\n"
                            msg += f"📈 سود: {notif['profit_pct']:+.2f}%\n"
                            msg += f"💡 توصیه: {notif['recommendation']}\n"
                            msg += f"⏱️ {notif['days_held']} روز نگهداری\n\n"
                    else:
                        msg = "✅ شما موقعیت فعالی ندارید\n\n💡 برای شروع معامله از منوی اصلی استفاده کنید"
                    
                else:
                    msg = "❌ سیستم مدیریت موقعیت در دسترس نیست"
                
                await query.edit_message_text(msg, parse_mode='Markdown')
            
            # پیام‌های هوشمند
            elif query.data == "smart_notifications":
                await query.edit_message_text("📨 دریافت پیام‌های هوشمند...")
                
                if self.portfolio_manager:
                    notifications = await self.portfolio_manager.get_pending_notifications()
                    
                    if notifications:
                        msg = "📨 **پیام‌های هوشمند:**\n\n"
                        for notif in notifications[:3]:
                            priority_icon = "🚨" if notif['priority'] >= 2 else "💡"
                            msg += f"{priority_icon} **{notif['title']}**\n"
                            msg += f"{notif['content'][:100]}...\n\n"
                    else:
                        msg = "✅ پیام جدیدی نداری!\\n\\n🎯 سیستم هوشمند همه چیز را کنترل می‌کند"
                else:
                    msg = "❌ سیستم پیام‌رسانی در دسترس نیست"
                
                await query.edit_message_text(msg, parse_mode='Markdown')
            
            # معاملات واقعی
            elif query.data.startswith(('buy_', 'sell_')):
                await query.edit_message_text("⚡ در حال اجرای معامله واقعی...")
                
                parts = query.data.split('_')
                side = parts[0]  # buy/sell
                symbol = f"{parts[1].upper()}/USDT"  # BTC/USDT
                amount = int(parts[2])  # 10, 20
                
                result = await self.execute_real_trade(symbol, side, amount)
                await query.edit_message_text(result, parse_mode='Markdown')
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطا: {str(e)[:100]}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پیام‌های متنی"""
        text = update.message.text.lower()
        
        if 'قیمت' in text or 'price' in text:
            prices = await self.get_real_prices()
            if prices:
                msg = "💰 قیمت‌های فعلی:\n"
                for symbol, data in prices.items():
                    msg += f"{symbol}: ${data['last']:,.2f} ({data['percentage']:+.1f}%)\n"
            else:
                msg = "❌ خطا در دریافت قیمت"
            await update.message.reply_text(msg)
            
        elif 'موجودی' in text or 'balance' in text:
            balance = await self.get_account_balance()
            if balance:
                msg = "💼 موجودی شما:\n"
                for symbol, data in balance.items():
                    msg += f"{symbol}: {data['total']:.6f}\n"
            else:
                msg = "❌ خطا در دریافت موجودی"
            await update.message.reply_text(msg)
            
        else:
            await update.message.reply_text(
                "برای شروع /start بفرستید\n"
                "یا یکی از کلمات: قیمت، موجودی، تحلیل"
            )

    def run(self):
        """اجرای ربات"""
        if not self.token:
            print("❌ توکن تلگرام موجود نیست")
            return
            
        app = Application.builder().token(self.token).build()
        
        # اضافه کردن handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CallbackQueryHandler(self.button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        print("🚀 ربات ULTRA_PLUS_BOT با معاملات واقعی شروع شد")
        print("⚡ قابلیت معاملات MEXC فعال")
        print("="*50)
        
        # اجرای ربات
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    bot = UltraPlusBotWithTrading()
    bot.run()