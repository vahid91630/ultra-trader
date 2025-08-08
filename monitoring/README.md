# سیستم مانیتورینگ پیشرفته Ultra-Trader

## نمای کلی

سیستم مانیتورینگ پیشرفته Ultra-Trader شامل ابزارهای جامع برای نظارت در زمان واقعی، ثبت رویدادها، تحلیل عملکرد، و هشدار هوشمند است که برای بهبود قابلیت اطمینان و عملکرد سیستم طراحی شده است.

## ویژگی‌های کلیدی

### 🔧 سیستم تلمتری پیشرفته (Enhanced Telemetry System)
- **ثبت متریک‌ها**: پایش مداوم CPU، حافظه، دیسک و اتصالات شبکه
- **ردیابی خطاها**: جمع‌آوری و تحلیل خطاهای سیستم با دسته‌بندی سطح
- **ثبت رویدادها**: ضبط رویدادهای مهم سیستم برای تحلیل
- **گزارشات سلامت**: تولید گزارشات جامع وضعیت سیستم

### 🚨 سیستم هشدار در زمان واقعی (Real-time Alert System)
- **قوانین قابل تنظیم**: تعریف شرایط سفارشی برای تریگر هشدارها
- **کانال‌های متعدد**: پشتیبانی از ایمیل، وب‌هوک، تلگرام و لاگ
- **مدیریت Cooldown**: جلوگیری از spam هشدارها
- **تاریخچه هشدارها**: ذخیره و تحلیل سابقه هشدارهای سیستم

### 📊 مانیتورینگ بهبود یافته سرویس‌ها
- **نظارت عملکرد**: ردیابی زمان پاسخ، نرخ موفقیت و خطا
- **متریک‌های کسب‌وکار**: پایش تعداد تحلیل‌ها، سیگنال‌های معاملاتی و احساسات بازار
- **تشخیص ناهنجاری**: شناسایی خودکار رفتارهای غیرعادی
- **بهینه‌سازی منابع**: نظارت بر مصرف منابع و بهینه‌سازی عملکرد

## معماری سیستم

```
monitoring/
├── telemetry_logger.py     # سیستم اصلی تلمتری
├── alert_system.py         # سیستم هشدار
├── logs/                   # لاگ‌های سیستم
│   ├── telemetry.log      # لاگ‌های عمومی
│   └── errors.log         # لاگ‌های خطا
├── telemetry.db           # دیتابیس متریک‌ها و سلامت سیستم
└── alerts.db              # دیتابیس هشدارها و قوانین
```

## نحوه استفاده

### 1. راه‌اندازی اولیه

```python
from monitoring.telemetry_logger import telemetry, MetricType, AlertLevel
from monitoring.alert_system import alert_system, AlertRule, AlertType, NotificationChannel

# سیستم به صورت خودکار راه‌اندازی می‌شود
```

### 2. ثبت متریک‌ها

```python
# ثبت متریک ساده
telemetry.record_metric("api.response_time", 0.5, MetricType.TIMER)

# ثبت متریک با تگ‌ها
telemetry.record_metric(
    "database.connections", 
    25, 
    MetricType.GAUGE, 
    tags={"database": "postgres", "pool": "main"}
)
```

### 3. ثبت خطاها

```python
# ثبت خطا
telemetry.record_error(
    AlertLevel.ERROR,
    "خطا در اتصال به دیتابیس",
    "DatabaseConnector",
    stacktrace="خطای کامل..."
)
```

### 4. ثبت رویدادها

```python
# ثبت رویداد
telemetry.record_event(
    "user_login",
    {"user_id": 123, "ip": "192.168.1.1"},
    "info",
    "AuthenticationSystem"
)
```

### 5. تعریف قوانین هشدار

```python
# تعریف قانون هشدار سفارشی
custom_rule = AlertRule(
    id="high_error_rate",
    name="نرخ خطای بالا",
    alert_type=AlertType.CUSTOM,
    condition="error_rate > 0.05",  # بیش از 5% خطا
    severity=AlertLevel.WARNING,
    channels=[NotificationChannel.EMAIL, NotificationChannel.LOG],
    cooldown_minutes=15
)

alert_system.add_rule(custom_rule)
```

### 6. دکوریتر عملکرد

```python
from monitoring.telemetry_logger import log_function_performance

@log_function_performance
def my_function():
    # کد تابع
    return "result"
```

## تنظیمات محیط

### متغیرهای محیط برای اطلاع‌رسانی ایمیل
```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=alerts@yourcompany.com
```

### متغیرهای محیط برای وب‌هوک
```bash
WEBHOOK_URL=https://your-webhook-url.com
WEBHOOK_HEADERS={"Authorization": "Bearer token"}
```

### متغیرهای محیط برای تلگرام
```bash
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

## متریک‌های پیش‌فرض

سیستم به صورت خودکار این متریک‌ها را جمع‌آوری می‌کند:

- `system.cpu_percent`: درصد استفاده از CPU
- `system.memory_percent`: درصد استفاده از حافظه
- `system.disk_percent`: درصد استفاده از دیسک
- `system.network_connections`: تعداد اتصالات شبکه

## هشدارهای پیش‌فرض

- **CPU بالا**: CPU > 80% (هشدار) / > 95% (بحرانی)
- **حافظه بالا**: Memory > 85% (هشدار) / > 95% (بحرانی)
- **دیسک بالا**: Disk > 85% (هشدار) / > 95% (بحرانی)

## API ها

### دریافت متریک‌های اخیر
```python
metrics = telemetry.get_recent_metrics("system.cpu_percent", hours=24)
```

### دریافت خلاصه خطاها
```python
error_summary = telemetry.get_error_summary(hours=24)
```

### دریافت روند سلامت سیستم
```python
health_trend = telemetry.get_system_health_trend(hours=12)
```

### تولید گزارش سلامت
```python
report = telemetry.generate_health_report()
```

### دریافت هشدارهای فعال
```python
active_alerts = alert_system.get_active_alerts()
```

### دریافت تاریخچه هشدارها
```python
alert_history = alert_system.get_alert_history(hours=48)
```

## بهینه‌سازی عملکرد

- **حافظه**: سیستم از deque برای محدود کردن متریک‌های حافظه استفاده می‌کند
- **دیتابیس**: ایندکس‌های بهینه برای جستجوی سریع
- **Thread-Safe**: تمام عملیات thread-safe هستند
- **پاکسازی خودکار**: داده‌های قدیمی به صورت خودکار پاک می‌شوند

## تست سیستم

```bash
# اجرای تست کامل
python test_enhanced_monitoring.py

# تست تلمتری
python monitoring/telemetry_logger.py

# تست سیستم هشدار
python monitoring/alert_system.py
```

## لاگ‌ها و عیب‌یابی

### محل فایل‌های لاگ
- `monitoring/logs/telemetry.log`: لاگ‌های عمومی
- `monitoring/logs/errors.log`: لاگ‌های خطا

### نظارت بر وضعیت سیستم
```python
# بررسی وضعیت
if telemetry.monitoring_active:
    print("سیستم مانیتورینگ فعال است")

# توقف مانیتورینگ
telemetry.stop_monitoring()
alert_system.stop_monitoring()
```

## مثال‌های کاربردی

### 1. مانیتورینگ API
```python
@log_function_performance
def api_endpoint():
    start_time = time.time()
    try:
        result = process_request()
        telemetry.record_metric("api.success_count", 1, MetricType.COUNTER)
        return result
    except Exception as e:
        telemetry.record_error(AlertLevel.ERROR, str(e), "API")
        telemetry.record_metric("api.error_count", 1, MetricType.COUNTER)
        raise
```

### 2. مانیتورینگ دیتابیس
```python
def database_operation():
    connection_count = get_active_connections()
    telemetry.record_metric("db.connections", connection_count)
    
    if connection_count > 100:
        telemetry.record_error(
            AlertLevel.WARNING,
            f"تعداد اتصالات دیتابیس بالا: {connection_count}",
            "DatabaseMonitor"
        )
```

### 3. مانیتورینگ کسب‌وکار
```python
def process_trade_signal():
    try:
        signal = generate_signal()
        telemetry.record_metric("trading.signals_generated", 1, MetricType.COUNTER)
        telemetry.record_event(
            "signal_generated",
            {"symbol": signal.symbol, "action": signal.action},
            "info",
            "TradingEngine"
        )
        return signal
    except Exception as e:
        telemetry.record_error(AlertLevel.ERROR, str(e), "TradingEngine")
        raise
```

## سازگاری

- Python 3.11+
- SQLite 3
- psutil
- threading
- logging

## پشتیبانی

برای راهنمایی و پشتیبانی:
1. بررسی فایل‌های لاگ در `monitoring/logs/`
2. اجرای تست‌های سیستم
3. مراجعه به documentatio کامل

---
**Ultra-Trader Enhanced Monitoring System** - نسخه 1.0