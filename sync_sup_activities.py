#!/usr/bin/env python3
"""
Complete SUP Activities Sync Script

This script:
1. Downloads latest activities from Garmin Connect
2. Filters for SUP sessions only
3. Processes FIT files through the SUP Analysis App
"""

import os
import subprocess
import sys
import csv
import shutil
import requests
from pathlib import Path
from datetime import datetime, timedelta

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print("❌ No .env file found. Please create one with GARMIN_USERNAME and GARMIN_PASSWORD")
        return False
    return True

def download_activities(count=200, start_date='2024-07-01'):
    """Download activities from Garmin Connect since July 1, 2024"""
    username = os.environ.get('GARMIN_USERNAME')
    password = os.environ.get('GARMIN_PASSWORD')
    
    if not username or not password:
        print("❌ GARMIN_USERNAME and GARMIN_PASSWORD must be set in .env file")
        return False
    
    # Use fixed start date: July 1, 2025
    # start_date is now a parameter with default value
    
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
    
    print(f"📥 Downloading up to {count} activities since {start_date}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Download completed successfully!")
        return True
    else:
        print(f"❌ Download failed: {result.stderr}")
        return False

def get_sup_activity_ids(csv_path):
    """Extract activity IDs for SUP sessions from CSV"""
    sup_ids = []
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return sup_ids
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Activity Type'] == 'Stand Up Paddleboarding':
                sup_ids.append(row['Activity ID'])
    
    return sup_ids

def copy_sup_fit_files(source_dir, target_dir, sup_ids):
    """Copy SUP FIT files to target directory"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)
    
    copied_files = []
    
    for activity_id in sup_ids:
        fit_file = source_path / f"activity_{activity_id}.fit"
        if fit_file.exists():
            target_file = target_path / f"activity_{activity_id}.fit"
            if not target_file.exists():
                shutil.copy2(fit_file, target_file)
                copied_files.append(str(target_file))
                print(f"📄 Copied: {fit_file.name}")
            else:
                print(f"⏭️  Already exists: {fit_file.name}")
    
    return copied_files

def upload_to_sup_app(fit_dir, app_url="http://localhost:5001/api/upload"):
    """Upload FIT files to SUP Analysis App"""
    
    fit_files = list(Path(fit_dir).glob("activity_*.fit"))
    
    if not fit_files:
        print(f"❌ No FIT files found in {fit_dir}")
        return False
    
    print(f"🚀 Uploading {len(fit_files)} FIT files to SUP Analysis App...")
    
    files = []
    try:
        for fit_file in fit_files:
            files.append(('files', (fit_file.name, open(fit_file, 'rb'), 'application/octet-stream')))
        
        response = requests.post(app_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            processed = result.get('processed', 0)
            total_files = len(fit_files)
            
            print(f"✅ Successfully processed {processed}/{total_files} files")
            
            if result.get('files'):
                print("📊 New sessions added:")
                for file in result['files']:
                    print(f"  - {file}")
            
            if result.get('errors'):
                print(f"⚠️  {len(result['errors'])} files had errors:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(result['errors']) > 5:
                    print(f"  - ... and {len(result['errors']) - 5} more")
            
            return True
        else:
            print(f"❌ Upload failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to SUP Analysis App.")
        print("💡 Please start the backend: cd sup-analysis-app/backend && python app.py")
        return False
    except Exception as e:
        print(f"❌ Error uploading files: {e}")
        return False
    finally:
        # Close file handles
        for file_tuple in files:
            if len(file_tuple) > 1 and len(file_tuple[1]) > 1:
                file_tuple[1][1].close()

def get_session_count(app_url="http://localhost:5001/api/sessions"):
    """Get current session count from SUP Analysis App"""
    try:
        response = requests.get(app_url)
        if response.status_code == 200:
            sessions = response.json()
            return len(sessions)
    except:
        pass
    return 0

def main():
    """Main sync function"""
    print("🏄‍♂️ SUP Activities Sync Started")
    print("=" * 50)
    
    # Load environment variables
    if not load_env():
        return False
    
    # Get initial session count
    initial_count = get_session_count()
    if initial_count > 0:
        print(f"📊 Current sessions in database: {initial_count}")
    
    # Download activities
    if not download_activities():
        return False
    
    # Process SUP activities
    csv_path = "./latest_activities/activities.csv"
    sup_ids = get_sup_activity_ids(csv_path)
    
    if not sup_ids:
        print("❌ No SUP activities found")
        return False
    
    print(f"🏄‍♂️ Found {len(sup_ids)} SUP activities")
    
    # Copy FIT files
    fit_dir = "/Users/Dec/Documents/Projects/Claude/Garmin/sup-analysis-app/fit_files"
    copied_files = copy_sup_fit_files("./latest_activities", fit_dir, sup_ids)
    
    if copied_files:
        print(f"📁 Copied {len(copied_files)} new FIT files")
    else:
        print("📁 No new FIT files to copy")
    
    # Upload to SUP Analysis App
    if not upload_to_sup_app(fit_dir):
        return False
    
    # Get final session count
    final_count = get_session_count()
    if final_count > initial_count:
        new_sessions = final_count - initial_count
        print(f"✅ Added {new_sessions} new SUP sessions!")
        print(f"📊 Total sessions in database: {final_count}")
    
    print("=" * 50)
    print("🏄‍♂️ SUP Activities Sync Completed!")
    print("🌐 View your sessions at: http://localhost:3000")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Sync cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)