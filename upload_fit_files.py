#!/usr/bin/env python3
"""
Upload FIT files to SUP Analysis App
"""
import requests
import os
from pathlib import Path

def upload_fit_files_to_app(fit_dir="/Users/Dec/Documents/Projects/Claude/Garmin/sup-analysis-app/fit_files", 
                           app_url="http://localhost:5001/api/upload"):
    """Upload all FIT files in directory to SUP Analysis App"""
    
    fit_files = list(Path(fit_dir).glob("activity_*.fit"))
    
    if not fit_files:
        print(f"No FIT files found in {fit_dir}")
        return
    
    print(f"Found {len(fit_files)} FIT files to upload...")
    
    files = []
    try:
        for fit_file in fit_files:
            files.append(('files', (fit_file.name, open(fit_file, 'rb'), 'application/octet-stream')))
        
        print(f"Uploading to {app_url}...")
        response = requests.post(app_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully processed {result.get('processed', 0)} files")
            if result.get('files'):
                print("Processed files:")
                for file in result['files']:
                    print(f"  - {file}")
            if result.get('errors'):
                print("❌ Errors:")
                for error in result['errors']:
                    print(f"  - {error}")
        else:
            print(f"❌ Upload failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to SUP Analysis App. Is it running on localhost:5001?")
    except Exception as e:
        print(f"❌ Error uploading files: {e}")
    finally:
        # Close file handles
        for file_tuple in files:
            if len(file_tuple) > 1 and len(file_tuple[1]) > 1:
                file_tuple[1][1].close()

if __name__ == "__main__":
    upload_fit_files_to_app()