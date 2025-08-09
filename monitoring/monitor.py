#!/usr/bin/env python3
"""
Simple monitoring service for Ultra Trader
سرویس مانیتورینگ ساده برای ربات پولساز وحید
"""

import time
import logging
import psutil
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMonitor:
    def __init__(self):
        self.monitoring = True
        
    def check_system_health(self):
        """Check basic system health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1.0)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'status': 'healthy'
            }
            
            # Check for alerts
            if cpu_percent > 90:
                logger.warning(f"High CPU usage: {cpu_percent}%")
                health_status['status'] = 'warning'
                
            if memory.percent > 90:
                logger.warning(f"High memory usage: {memory.percent}%")
                health_status['status'] = 'warning'
                
            if disk.percent > 90:
                logger.warning(f"High disk usage: {disk.percent}%")
                health_status['status'] = 'warning'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def monitor_loop(self, interval=60):
        """Main monitoring loop"""
        logger.info("🔍 Starting system monitoring...")
        
        while self.monitoring:
            try:
                health = self.check_system_health()
                
                if health['status'] == 'healthy':
                    logger.info(f"✅ System healthy - CPU: {health['cpu_percent']}%, Memory: {health['memory_percent']}%")
                else:
                    logger.warning(f"⚠️ System status: {health['status']}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval)
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False

if __name__ == '__main__':
    monitor = SimpleMonitor()
    try:
        monitor.monitor_loop()
    except KeyboardInterrupt:
        monitor.stop()
        logger.info("Monitoring service stopped")