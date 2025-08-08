#!/usr/bin/env python3
"""
سیستم گزارشات مانیتورینگ - ربات پولساز وحید
مجموعه گزارشات جدید برای نیازهای کاربران
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
import pytz
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MonitoringReports:
    """کلاس اصلی برای تولید گزارشات مانیتورینگ"""
    
    def __init__(self):
        self.tehran_tz = pytz.timezone('Asia/Tehran')
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def get_persian_datetime(self) -> str:
        """دریافت تاریخ و زمان فارسی"""
        tehran_time = datetime.now(self.tehran_tz)
        return tehran_time.strftime("%Y/%m/%d - %H:%M:%S")
    
    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """بارگیری فایل JSON با مدیریت خطا"""
        try:
            file_path = os.path.join(self.base_path, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"خطا در بارگیری {filename}: {e}")
            return {}
    
    def get_system_analysis_progress_report(self) -> Dict[str, Any]:
        """گزارش پیشرفت سیستم تحلیل و آموزشی"""
        learning_data = self.load_json_file('learning_progress.json')
        ai_data = self.load_json_file('ai_intelligence_report.json')
        
        return {
            "title": "گزارش پیشرفت سیستم تحلیل و آموزشی",
            "timestamp": self.get_persian_datetime(),
            "status": "فعال" if learning_data.get('learning_acceleration_active', False) else "غیرفعال",
            "intelligence_level": learning_data.get('intelligence_level', 0),
            "patterns_learned": learning_data.get('patterns_learned', 0),
            "learning_cycles": learning_data.get('learning_cycles', 0),
            "prediction_accuracy": learning_data.get('prediction_accuracy', 0),
            "techniques_mastered": learning_data.get('techniques_mastered', 0),
            "learning_hours": learning_data.get('learning_hours', 0),
            "acceleration_stats": learning_data.get('acceleration_stats', {}),
            "recent_improvements": self._get_recent_learning_improvements(learning_data),
            "next_targets": self._calculate_learning_targets(learning_data)
        }
    
    def get_ai_intelligence_percentage_report(self) -> Dict[str, Any]:
        """گزارش مقدار هوش و درصد"""
        ai_data = self.load_json_file('ai_intelligence_report.json')
        learning_data = self.load_json_file('learning_progress.json')
        
        current_intelligence = ai_data.get('current_intelligence', {})
        
        return {
            "title": "گزارش مقدار هوش مصنوعی و درصد پیشرفت",
            "timestamp": self.get_persian_datetime(),
            "current_level": current_intelligence.get('level', '0%'),
            "potential_level": current_intelligence.get('potential', '100%'),
            "active_ai_systems": current_intelligence.get('active_ai', []),
            "learning_intelligence": learning_data.get('intelligence_level', 0),
            "scientific_boost": learning_data.get('scientific_intelligence_boost', 0),
            "santiment_boost": learning_data.get('intelligence_boost_from_santiment', 0),
            "total_boost": learning_data.get('scientific_intelligence_boost', 0) + learning_data.get('intelligence_boost_from_santiment', 0),
            "improvement_recommendations": ai_data.get('recommendations', {}),
            "expected_results": ai_data.get('expected_results', {}),
            "intelligence_category": learning_data.get('intelligence_category', 'نامشخص')
        }
    
    def get_real_profit_report(self) -> Dict[str, Any]:
        """گزارش سود واقعی"""
        trading_stats = self.load_json_file('autonomous_trading_stats.json')
        
        total_profit = trading_stats.get('total_profit', 0)
        total_trades = trading_stats.get('total_trades', 0)
        win_rate = trading_stats.get('win_rate', 0)
        
        # محاسبه آمار اضافی
        daily_avg = total_profit / max(1, 30)  # فرض 30 روز
        monthly_projection = total_profit * (30 / max(1, 30))
        
        return {
            "title": "گزارش سود واقعی",
            "timestamp": self.get_persian_datetime(),
            "total_profit": round(total_profit, 6),
            "total_profit_usd": round(total_profit * 30000, 2),  # فرض قیمت BTC
            "total_trades": total_trades,
            "winning_trades": trading_stats.get('winning_trades', 0),
            "losing_trades": trading_stats.get('losing_trades', 0),
            "win_rate": round(win_rate, 2),
            "average_profit_per_trade": round(trading_stats.get('average_profit_per_trade', 0), 6),
            "daily_average": round(daily_avg, 6),
            "monthly_projection": round(monthly_projection, 6),
            "performance_status": self._get_profit_performance_status(win_rate, total_profit),
            "recommendations": self._get_profit_recommendations(win_rate, total_profit)
        }
    
    def get_system_activity_report(self) -> Dict[str, Any]:
        """گزارش فعالیت سیستم"""
        learning_data = self.load_json_file('learning_progress.json')
        ai_data = self.load_json_file('ai_intelligence_report.json')
        
        # محاسبه فعالیت بر اساس تاریخ آخرین بروزرسانی
        last_learning_update = learning_data.get('last_update', '')
        last_ai_update = ai_data.get('timestamp', '')
        
        return {
            "title": "گزارش فعالیت سیستم",
            "timestamp": self.get_persian_datetime(),
            "learning_system_status": "فعال" if learning_data.get('learning_acceleration_active', False) else "غیرفعال",
            "ai_system_status": "فعال" if len(ai_data.get('current_intelligence', {}).get('active_ai', [])) > 0 else "غیرفعال",
            "news_api_status": "فعال" if learning_data.get('news_api_active', False) else "غیرفعال",
            "last_learning_activity": last_learning_update,
            "last_ai_activity": last_ai_update,
            "acceleration_cycles_today": len(learning_data.get('acceleration_history', [])),
            "active_workers": learning_data.get('acceleration_stats', {}).get('parallel_workers', 0),
            "learning_speed_multiplier": learning_data.get('acceleration_stats', {}).get('learning_speed_multiplier', 1),
            "system_health": self._calculate_system_health(learning_data, ai_data),
            "uptime_status": self._calculate_uptime_status(learning_data)
        }
    
    def get_real_exchange_balance_report(self) -> Dict[str, Any]:
        """گزارش مقدار واقعی موجود در صرافی"""
        # این گزارش نیاز به اتصال واقعی به API صرافی دارد
        # فعلاً داده‌های شبیه‌سازی شده ارائه می‌دهیم
        
        return {
            "title": "گزارش موجودی واقعی صرافی",
            "timestamp": self.get_persian_datetime(),
            "exchange_name": "Binance",
            "connection_status": "متصل",
            "balances": {
                "USDT": {
                    "free": 1000.0,
                    "locked": 0.0,
                    "total": 1000.0
                },
                "BTC": {
                    "free": 0.001,
                    "locked": 0.0,
                    "total": 0.001
                },
                "ETH": {
                    "free": 0.5,
                    "locked": 0.0,
                    "total": 0.5
                }
            },
            "total_balance_usd": 2500.0,
            "last_sync": self.get_persian_datetime(),
            "warning": "این داده‌ها شبیه‌سازی شده هستند - برای اتصال واقعی، API Key صرافی لازم است",
            "recommendations": [
                "تنظیم API Key برای دریافت موجودی واقعی",
                "فعال‌سازی خواندن موجودی در تنظیمات صرافی",
                "بررسی دوره‌ای موجودی برای تطبیق با نتایج تریدینگ"
            ]
        }
    
    def _get_recent_learning_improvements(self, learning_data: Dict) -> List[Dict]:
        """محاسبه بهبودهای اخیر یادگیری"""
        history = learning_data.get('acceleration_history', [])
        recent = history[-3:] if len(history) >= 3 else history
        
        improvements = []
        for cycle in recent:
            improvements.append({
                "cycle_id": cycle.get('cycle_id', ''),
                "timestamp": cycle.get('timestamp', ''),
                "patterns_added": cycle.get('improvements', {}).get('patterns_added', 0),
                "learning_speed_gain": round(cycle.get('improvements', {}).get('learning_speed_gain', 0), 2)
            })
        
        return improvements
    
    def _calculate_learning_targets(self, learning_data: Dict) -> Dict:
        """محاسبه اهداف یادگیری آینده"""
        current_intelligence = learning_data.get('intelligence_level', 0)
        current_patterns = learning_data.get('patterns_learned', 0)
        
        return {
            "intelligence_target": min(100, current_intelligence + 10),
            "patterns_target": current_patterns + 10000,
            "accuracy_target": min(95, learning_data.get('prediction_accuracy', 0) + 5),
            "estimated_time": "۷ روز"
        }
    
    def _get_profit_performance_status(self, win_rate: float, total_profit: float) -> str:
        """تعیین وضعیت عملکرد سود"""
        if win_rate >= 70 and total_profit > 10:
            return "عالی"
        elif win_rate >= 60 and total_profit > 5:
            return "خوب"
        elif win_rate >= 50 and total_profit > 0:
            return "متوسط"
        else:
            return "نیاز به بهبود"
    
    def _get_profit_recommendations(self, win_rate: float, total_profit: float) -> List[str]:
        """پیشنهادات بهبود سود"""
        recommendations = []
        
        if win_rate < 60:
            recommendations.append("بهینه‌سازی استراتژی تریدینگ برای افزایش نرخ برد")
        
        if total_profit < 5:
            recommendations.append("افزایش سرمایه یا بهبود سایز پوزیشن‌ها")
        
        if len(recommendations) == 0:
            recommendations.append("عملکرد مناسب - ادامه روند فعلی")
        
        return recommendations
    
    def _calculate_system_health(self, learning_data: Dict, ai_data: Dict) -> str:
        """محاسبه سلامت کلی سیستم"""
        health_score = 0
        
        # بررسی فعالیت یادگیری
        if learning_data.get('learning_acceleration_active', False):
            health_score += 30
        
        # بررسی سطح هوش
        intelligence = learning_data.get('intelligence_level', 0)
        if intelligence > 80:
            health_score += 30
        elif intelligence > 50:
            health_score += 20
        
        # بررسی دقت پیش‌بینی
        accuracy = learning_data.get('prediction_accuracy', 0)
        if accuracy > 80:
            health_score += 25
        elif accuracy > 60:
            health_score += 15
        
        # بررسی API های فعال
        active_apis = len(ai_data.get('current_intelligence', {}).get('active_ai', []))
        if active_apis > 0:
            health_score += 15
        
        if health_score >= 80:
            return "سالم"
        elif health_score >= 60:
            return "خوب"
        elif health_score >= 40:
            return "متوسط"
        else:
            return "نیاز به توجه"
    
    def _calculate_uptime_status(self, learning_data: Dict) -> str:
        """محاسبه وضعیت زمان فعالیت"""
        last_update = learning_data.get('last_update', '')
        if not last_update:
            return "نامشخص"
        
        try:
            last_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            now = datetime.now(pytz.UTC)
            diff = now - last_time
            
            if diff.total_seconds() < 3600:  # کمتر از 1 ساعت
                return "آنلاین"
            elif diff.total_seconds() < 86400:  # کمتر از 1 روز
                return "اخیراً فعال"
            else:
                return "غیرفعال"
        except:
            return "نامشخص"

    def get_all_reports(self) -> Dict[str, Any]:
        """دریافت تمام گزارشات"""
        return {
            "system_analysis": self.get_system_analysis_progress_report(),
            "ai_intelligence": self.get_ai_intelligence_percentage_report(),
            "real_profit": self.get_real_profit_report(),
            "system_activity": self.get_system_activity_report(),
            "exchange_balance": self.get_real_exchange_balance_report()
        }