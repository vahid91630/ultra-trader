#!/usr/bin/env python3
"""
Ultra Trader Dashboard - Simple and Reliable Monitoring System
داشبورد ساده و قابل اعتماد ربات پولساز وحید
"""

from flask import Flask, render_template, jsonify
import os
import json
import sqlite3
import psutil
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class UltraDashboard:
    def __init__(self):
        self.tehran_tz = pytz.timezone('Asia/Tehran')
    
    def get_system_info(self):
        """Get system resource information"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': round(psutil.cpu_percent(interval=0.1), 1),
                'memory_percent': round(memory.percent, 1),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'disk_percent': round(disk.percent, 1),
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'status': 'healthy'
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_trading_data(self):
        """Get trading data from database"""
        try:
            trading_data = {
                'total_trades': 0,
                'winning_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0,
                'current_balance': 0.0,
                'status': 'no_data'
            }
            
            # Check if trading database exists
            if os.path.exists('autonomous_trading.db'):
                conn = sqlite3.connect('autonomous_trading.db')
                cursor = conn.cursor()
                
                try:
                    # Check if trades table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
                    if cursor.fetchone():
                        # Get trading statistics
                        cursor.execute("""
                            SELECT COUNT(*) as total_trades,
                                   SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                                   SUM(profit_loss) as total_profit
                            FROM trades
                        """)
                        result = cursor.fetchone()
                        if result and result[0] > 0:
                            trading_data['total_trades'] = result[0] or 0
                            trading_data['winning_trades'] = result[1] or 0
                            trading_data['total_profit'] = round(result[2] or 0.0, 2)
                            
                            if trading_data['total_trades'] > 0:
                                trading_data['win_rate'] = round(
                                    (trading_data['winning_trades'] / trading_data['total_trades']) * 100, 1
                                )
                            trading_data['status'] = 'active'
                except Exception as e:
                    logger.error(f"Database error: {e}")
                    trading_data['status'] = 'db_error'
                finally:
                    conn.close()
            
            # Check for balance in stats file
            if os.path.exists('autonomous_trading_stats.json'):
                try:
                    with open('autonomous_trading_stats.json', 'r') as f:
                        stats = json.load(f)
                        trading_data['current_balance'] = stats.get('current_balance', 0.0)
                except Exception as e:
                    logger.error(f"Stats file error: {e}")
            
            return trading_data
            
        except Exception as e:
            logger.error(f"Error getting trading data: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_api_status(self):
        """Check API keys status"""
        api_keys = {
            'OPENAI_API_KEY': 'OpenAI',
            'NEWSAPI_KEY': 'NewsAPI', 
            'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage',
            'MEXC_API_KEY': 'MEXC Exchange',
            'BINANCE_API_KEY': 'Binance Exchange'
        }
        
        status = {}
        for key, name in api_keys.items():
            status[name] = {
                'configured': bool(os.getenv(key)),
                'status': 'active' if os.getenv(key) else 'missing'
            }
        
        return status
    
    def get_persian_time(self):
        """Get Persian date and time"""
        try:
            tehran_time = datetime.now(self.tehran_tz)
            return {
                'formatted': tehran_time.strftime('%Y/%m/%d %H:%M:%S'),
                'timestamp': tehran_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting Persian time: {e}")
            return {'formatted': 'Error', 'timestamp': datetime.now().isoformat()}

# Create dashboard instance
dashboard = UltraDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint for dashboard data"""
    try:
        data = {
            'timestamp': datetime.now().isoformat(),
            'persian_time': dashboard.get_persian_time(),
            'system_info': dashboard.get_system_info(),
            'trading_data': dashboard.get_trading_data(),
            'api_status': dashboard.get_api_status(),
            'status': 'success'
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Ultra Trader Dashboard',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Ultra Trader Dashboard on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)