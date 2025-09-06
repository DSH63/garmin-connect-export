#!/usr/bin/env python3
"""
Enhanced Garmin Connect download script with .env support
"""
import os
import subprocess
import sys
from pathlib import Path

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def download_latest_activities(count=20, days_back=30):
    """Download latest activities using stored credentials"""
    load_env()
    
    username = os.environ.get('GARMIN_USERNAME')
    password = os.environ.get('GARMIN_PASSWORD')
    
    if not username or not password:
        print("Error: GARMIN_USERNAME and GARMIN_PASSWORD must be set in .env file")
        return False
    
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    cmd = [
        'python', 'gcexport.py',
        '-c', str(count),
        '-f', 'original',
        '-u',  # unzip files
        '--session', './session_data',
        '-d', './latest_activities',
        '--start_date', start_date,
        '--username', username,
        '--password', password
    ]
    
    print(f"Downloading latest {count} activities since {start_date}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Download completed successfully!")
        return True
    else:
        print(f"Download failed: {result.stderr}")
        return False

if __name__ == "__main__":
    download_latest_activities()