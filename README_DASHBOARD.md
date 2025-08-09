# Ultra Trader Dashboard
## ربات پولساز وحید - داشبورد مانیتورینگ

A simple, clean, and reliable monitoring dashboard for the Ultra Trader system.

### Features
- 🖥️ **System Monitoring**: Real-time CPU, memory, and disk usage
- 💰 **Trading Data**: Live trading statistics and performance metrics  
- 🔑 **API Status**: Monitor API key configuration and connectivity
- 🕒 **Persian Time**: Display current Persian date and time
- 📊 **Health Check**: Built-in health monitoring endpoints

### Quick Start

1. **Install Dependencies**
   ```bash
   pip install flask psutil python-dotenv
   ```

2. **Run the Dashboard**
   ```bash
   python dashboard.py
   ```

3. **Access the Dashboard**
   - Open your browser to: http://localhost:5000
   - Health check: http://localhost:5000/health
   - API data: http://localhost:5000/api/data

### API Endpoints

- `GET /` - Main dashboard page
- `GET /api/data` - JSON data for dashboard
- `GET /health` - Health check endpoint

### Testing

Run the test suite:
```bash
python test_dashboard.py
```

### Configuration

The dashboard automatically detects:
- Trading database (`autonomous_trading.db`)
- Trading statistics (`autonomous_trading_stats.json`)
- API keys from environment variables

### Architecture

The new dashboard is built with:
- **Flask** for the web framework (simple and reliable)
- **Pure HTML/CSS/JavaScript** for the frontend (no complex dependencies)
- **psutil** for system monitoring
- **SQLite** for trading data access

### Key Improvements

✅ **Simplified Architecture**: Single Flask app instead of multiple conflicting systems
✅ **Clean Code**: Removed 1,000+ lines of complex, buggy code
✅ **Reliable Monitoring**: Simple, robust system resource monitoring
✅ **Responsive Design**: Works on desktop and mobile
✅ **Error Handling**: Graceful error handling and recovery
✅ **Test Coverage**: Comprehensive test suite with 8 tests
✅ **Persian Support**: Full RTL and Persian date support

### Old vs New

**Before**: Multiple conflicting dashboard implementations (Streamlit + Flask), complex HTML templates with extensive JavaScript, missing dependencies, empty monitoring files

**After**: Single, clean Flask dashboard with simple HTML template, reliable monitoring, comprehensive tests, and proper error handling.

---

**Created by**: AI Assistant for vahid91630/ultra-trader
**Date**: August 2025