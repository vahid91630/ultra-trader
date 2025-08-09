#!/usr/bin/env python3
"""
Tests for Ultra Trader Dashboard
تست‌های داشبورد ربات پولساز وحید
"""

import unittest
import json
import tempfile
import os
import sys

# Add the parent directory to path so we can import dashboard
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard import app, UltraDashboard

class TestUltraDashboard(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True
        self.dashboard = UltraDashboard()
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'Ultra Trader Dashboard')
        self.assertIn('timestamp', data)
    
    def test_main_page(self):
        """Test main dashboard page"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ultra Trader Dashboard', response.data)
    
    def test_api_data_endpoint(self):
        """Test API data endpoint"""
        response = self.app.get('/api/data')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('timestamp', data)
        self.assertIn('system_info', data)
        self.assertIn('trading_data', data)
        self.assertIn('api_status', data)
        self.assertIn('persian_time', data)
    
    def test_system_info(self):
        """Test system info function"""
        info = self.dashboard.get_system_info()
        
        self.assertIn('cpu_percent', info)
        self.assertIn('memory_percent', info)
        self.assertIn('disk_percent', info)
        self.assertIn('status', info)
        
        # Check that values are reasonable
        self.assertTrue(0 <= info['cpu_percent'] <= 100)
        self.assertTrue(0 <= info['memory_percent'] <= 100)
        self.assertTrue(0 <= info['disk_percent'] <= 100)
    
    def test_api_status(self):
        """Test API status function"""
        status = self.dashboard.get_api_status()
        
        # Check that all expected APIs are listed
        expected_apis = ['OpenAI', 'NewsAPI', 'Alpha Vantage', 'MEXC Exchange', 'Binance Exchange']
        for api in expected_apis:
            self.assertIn(api, status)
            self.assertIn('configured', status[api])
            self.assertIn('status', status[api])
    
    def test_trading_data(self):
        """Test trading data function"""
        data = self.dashboard.get_trading_data()
        
        self.assertIn('total_trades', data)
        self.assertIn('winning_trades', data)
        self.assertIn('total_profit', data)
        self.assertIn('win_rate', data)
        self.assertIn('current_balance', data)
        self.assertIn('status', data)
        
        # Check data types
        self.assertIsInstance(data['total_trades'], int)
        self.assertIsInstance(data['winning_trades'], int)
        self.assertIsInstance(data['total_profit'], (int, float))
        self.assertIsInstance(data['win_rate'], (int, float))
        self.assertIsInstance(data['current_balance'], (int, float))
    
    def test_persian_time(self):
        """Test Persian time function"""
        time_data = self.dashboard.get_persian_time()
        
        self.assertIn('formatted', time_data)
        self.assertIn('timestamp', time_data)
        self.assertNotEqual(time_data['formatted'], 'Error')

class TestDashboardIntegration(unittest.TestCase):
    
    def test_trading_data_with_mock_db(self):
        """Test trading data with a mock database"""
        # Create a temporary SQLite database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create trades table with sample data
            cursor.execute('''
                CREATE TABLE trades (
                    id INTEGER PRIMARY KEY,
                    profit_loss REAL,
                    timestamp TEXT
                )
            ''')
            
            # Insert sample trades
            cursor.execute('INSERT INTO trades (profit_loss, timestamp) VALUES (?, ?)', 
                         (10.5, '2023-01-01 12:00:00'))
            cursor.execute('INSERT INTO trades (profit_loss, timestamp) VALUES (?, ?)', 
                         (-5.2, '2023-01-01 13:00:00'))
            cursor.execute('INSERT INTO trades (profit_loss, timestamp) VALUES (?, ?)', 
                         (8.3, '2023-01-01 14:00:00'))
            
            conn.commit()
            conn.close()
            
            # Temporarily replace the database path
            original_path = 'autonomous_trading.db'
            if os.path.exists(original_path):
                # Rename the original temporarily
                os.rename(original_path, original_path + '.backup')
            
            os.rename(db_path, original_path)
            
            # Test the trading data function
            dashboard = UltraDashboard()
            data = dashboard.get_trading_data()
            
            self.assertEqual(data['total_trades'], 3)
            self.assertEqual(data['winning_trades'], 2)
            self.assertAlmostEqual(data['total_profit'], 13.6, places=1)
            self.assertAlmostEqual(data['win_rate'], 66.7, places=1)
            self.assertEqual(data['status'], 'active')
            
        finally:
            # Clean up
            if os.path.exists(original_path):
                os.remove(original_path)
            if os.path.exists(original_path + '.backup'):
                os.rename(original_path + '.backup', original_path)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)