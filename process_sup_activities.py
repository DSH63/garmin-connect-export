#!/usr/bin/env python3
"""
Filter SUP activities and process them through the SUP Analysis App
"""
import csv
import shutil
import os
from pathlib import Path
import requests
import sys

def get_sup_activity_ids(csv_path):
    """Extract activity IDs for SUP sessions from CSV"""
    sup_ids = []
    
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
                print(f"Copied: {fit_file.name}")
            else:
                print(f"Already exists: {fit_file.name}")
    
    return copied_files

def upload_to_sup_app(fit_files, app_url="http://localhost:5001/api/upload"):
    """Upload FIT files to SUP Analysis App"""
    if not fit_files:
        print("No new FIT files to upload")
        return
    
    print(f"\nUploading {len(fit_files)} FIT files to SUP Analysis App...")
    
    files = []
    try:
        for fit_file in fit_files:
            files.append(('files', (Path(fit_file).name, open(fit_file, 'rb'), 'application/octet-stream')))
        
        response = requests.post(app_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Successfully processed {result.get('processed', 0)} files")
            if result.get('errors'):
                print("Errors:")
                for error in result['errors']:
                    print(f"  - {error}")
        else:
            print(f"Upload failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to SUP Analysis App. Is it running on localhost:5001?")
    except Exception as e:
        print(f"Error uploading files: {e}")
    finally:
        # Close file handles
        for file_tuple in files:
            file_tuple[1][1].close()

def main():
    # Paths
    latest_activities_dir = "./latest_activities"
    csv_path = os.path.join(latest_activities_dir, "activities.csv")
    sup_app_dir = "/Users/Dec/Documents/Projects/Claude/Garmin/sup-analysis-app/fit_files"
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Get SUP activity IDs
    print("Identifying SUP activities...")
    sup_ids = get_sup_activity_ids(csv_path)
    print(f"Found {len(sup_ids)} SUP activities: {', '.join(sup_ids)}")
    
    # Copy FIT files
    print(f"\nCopying SUP FIT files to {sup_app_dir}...")
    copied_files = copy_sup_fit_files(latest_activities_dir, sup_app_dir, sup_ids)
    
    if copied_files:
        # Upload to SUP Analysis App
        upload_to_sup_app(copied_files)
    else:
        print("No new FIT files to process")

if __name__ == "__main__":
    main()