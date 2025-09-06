# SUP Activities Sync Setup

This setup automatically downloads your latest SUP activities from Garmin Connect and processes them through your SUP Analysis App.

## Files Created

1. **`.env`** - Contains your Garmin Connect credentials
2. **`download_latest.py`** - Downloads activities using environment variables
3. **`process_sup_activities.py`** - Filters SUP activities and copies FIT files
4. **`upload_fit_files.py`** - Uploads FIT files to SUP Analysis App
5. **`sync_sup_activities.py`** - **Main script** - Complete automation

## Quick Start

### 1. Make sure SUP Analysis App is running
```bash
cd /Users/Dec/Documents/Projects/Claude/Garmin/sup-analysis-app/backend
python app.py
```

### 2. Run the complete sync
```bash
cd /Users/Dec/Documents/Projects/Claude/Garmin/garmin-connect-export
python sync_sup_activities.py
```

This will:
- Download latest 20 activities from last 30 days
- Filter for SUP sessions only
- Copy new FIT files to the analysis app
- Process them through the backend
- Show summary of new sessions added

## Configuration

Edit the `sync_sup_activities.py` file to change:
- `count=20` - Number of recent activities to download
- `days_back=30` - How many days back to search

## Manual Steps

### Download only
```bash
python download_latest.py
```

### Process existing files
```bash
python process_sup_activities.py
```

### Upload FIT files
```bash
python upload_fit_files.py
```

## Credentials

Your Garmin Connect credentials are stored in `.env`:
```
GARMIN_USERNAME=declanhoare@mac.com
GARMIN_PASSWORD=xamcih2tukzoBenpaz
```

⚠️ **Keep this file secure and don't commit it to version control**

## Integration with gcexport

This setup uses the existing `gcexport.py` script with enhanced features:
- Environment variable support
- Automatic SUP filtering
- Integration with your SUP Analysis App
- Better error handling and progress reporting

## Troubleshooting

### "Could not connect to SUP Analysis App"
- Make sure the backend is running on localhost:5001
- Check: `curl http://localhost:5001/api/sessions`

### "Authentication failure"
- Check your credentials in `.env`
- Try running `python gcexport.py --help` to test the script

### "No SUP activities found"
- Adjust the date range in the sync script
- Check if activities are properly tagged as SUP in Garmin Connect