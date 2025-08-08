# Ultra-Trader Production Deployment Guide

## مشکل قبلی (Development Server Warning)

قبل از این تغییرات، پروژه از سرور توسعه Flask و Streamlit استفاده می‌کرد که برای محیط تولید مناسب نبود:

```
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
```

## راه‌حل پیاده‌شده

### 1. اضافه کردن Gunicorn WSGI Server

- **Gunicorn** به عنوان سرور WSGI حرفه‌ای برای Flask اضافه شد
- تنظیمات تولید در `gunicorn.conf.py` تعریف شد
- خطای development server حل شد

### 2. بهبود Docker Configuration

**قبل:**
```dockerfile
CMD ["python", "optimized_deployment_entry.py"]
```

**بعد:**
```dockerfile 
CMD ["python", "production_deploy.py"]
```

### 3. اسکریپت مدیریت هوشمند Production

فایل `production_deploy.py` اضافه شد که:
- نوع اپلیکیشن را تشخیص می‌دهد (Flask/Streamlit)
- سرور مناسب را انتخاب می‌کنه
- Health check انجام می‌دهد
- Graceful shutdown پیاده کرده

## نحوه استفاده

### روش 1: Docker (توصیه شده)
```bash
docker build -t ultra-trader .
docker run -p 5000:5000 -e ENVIRONMENT=production ultra-trader
```

### روش 2: مستقیم
```bash
# Flask با Gunicorn
gunicorn -c gunicorn.conf.py optimized_deployment_entry:app

# یا استفاده از اسکریپت هوشمند
python production_deploy.py
```

### روش 3: انتخاب نوع اپلیکیشن
```bash
# اجرای Flask
APP_TYPE=flask python production_deploy.py

# اجرای Streamlit (اگر نیاز باشد)
APP_TYPE=streamlit python production_deploy.py
```

## متغیرهای محیطی

| متغیر | پیش‌فرض | توضیح |
|-------|---------|--------|
| `PORT` | 5000 | پورت سرور |
| `ENVIRONMENT` | production | محیط اجرا |
| `APP_TYPE` | flask | نوع اپلیکیشن |
| `GUNICORN_WORKERS` | 1 | تعداد worker های Gunicorn |

## Health Check Endpoints

- `/health` - وضعیت سلامت سیستم
- `/api/status` - وضعیت API
- `/` - صفحه اصلی

## رفع مشکلات Container Stop

### مشکلات قبلی:
1. عدم مدیریت signal ها
2. نبود health check مناسب
3. استفاده از development server

### راه‌حل:
1. **Graceful Shutdown**: مدیریت SIGTERM و SIGINT
2. **Health Monitoring**: چک دوره‌ای وضعیت
3. **Production Server**: استفاده از Gunicorn
4. **Process Management**: مدیریت هوشمند process ها

## مقایسه قبل و بعد

### قبل:
```log
WARNING: This is a development server. Do not use it in a production deployment.
Container keeps stopping...
```

### بعد:
```log
🚀 Starting Flask app with Gunicorn on port 5000
[INFO] Starting gunicorn 23.0.0
[INFO] Listening at: http://0.0.0.0:5000
✅ Application started successfully and health check passed
```

## توصیه‌های امنیتی

1. **فایروال**: فقط پورت‌های لازم را باز کنید
2. **HTTPS**: در تولید حتماً SSL استفاده کنید
3. **Environment Variables**: کلیدهای API را در فایل‌های محیطی نگه دارید
4. **Monitoring**: لاگ‌ها و metrics را کنترل کنید

## عیب‌یابی

### اگر container همچنان stop می‌شود:

1. لاگ‌ها را بررسی کنید:
```bash
docker logs [container_id]
```

2. Health check را تست کنید:
```bash
curl http://localhost:5000/health
```

3. Resources را بررسی کنید:
```bash
docker stats [container_id]
```

### برای دیباگ در development:
```bash
ENVIRONMENT=development python production_deploy.py
```

## نکات مهم

- ⚠️ هرگز در تولید از `debug=True` استفاده نکنید
- 🚀 Gunicorn برای Flask بهترین گزینه است
- 🔄 برای load balancing، workers را افزایش دهید
- 📊 Health check ها را مدام کنترل کنید
- 🛡️ همیشه graceful shutdown پیاده کنید