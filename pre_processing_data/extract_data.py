import boto3
from datetime import datetime, timedelta
import re
from collections import defaultdict
import traceback

# Use your verified working credentials
ACCESS_KEY = "49681DS3ZCZ72FT67RLC"
SECRET_KEY = "3FpOwWdILAfVkaePQ7SOPf0aFgl9dsTCBPkNpoNL"
endpoint = "https://s3.eu-west-2.wasabisys.com"
bucket = "ecosurf-dataset"

# Use the EXACT SAME boto3 configuration that works for downloading
session = boto3.session.Session()
s3 = session.client(
    "s3",
    region_name="eu-west-2",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    endpoint_url=endpoint
)

def scan_bucket_structure():
    """
    Scan entire bucket to understand actual file structure and create accurate period dictionary
    """
    print("Scanning bucket structure...")
    
    # Dictionary to store all found files by date
    found_files = defaultdict(list)
    file_details = {}
    
    # List all prefixes (year folders)
    years = ['2019', '2020', '2021', '2022', '2023']
    
    # Pattern to match audio files
    file_pattern = re.compile(r'(\w+)_(\d{8})_(\d{6})\.(flac|wav|mp3)')
    
    try:
        for year in years:
            print(f"\nScanning year: {year}")
            
            # List all objects with this prefix - using list_objects_v2 directly
            response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{year}/")
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    filename = key.split('/')[-1]
                    
                    # Skip if not a data file
                    if not filename or not file_pattern.match(filename):
                        continue
                    
                    # Parse filename
                    match = file_pattern.match(filename)
                    if match:
                        device_id, date_str, time_str, ext = match.groups()
                        
                        # Create datetime object
                        dt_str = f"{date_str}_{time_str}"
                        dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                        
                        # Get file size and metadata
                        file_size_mb = obj['Size'] / (1024 * 1024)
                        
                        # Store file info
                        date_key = dt.strftime("%Y-%m-%d")
                        found_files[date_key].append({
                            'datetime': dt,
                            'file_path': key,
                            'device': device_id,
                            'size_mb': file_size_mb,
                            'time_str': dt.strftime("%H:%M:%S"),
                            'year': year
                        })
                        
                        # Also store in detailed dictionary
                        period_key = dt.strftime("%Y-%m-%d_%H:%M")
                        file_details[period_key] = {
                            's3_path': key,
                            'device': device_id,
                            'datetime': dt,
                            'size_mb': file_size_mb,
                            'full_date': dt_str
                        }
                
                # Handle pagination if there are more than 1000 objects
                while response.get('NextContinuationToken'):
                    response = s3.list_objects_v2(
                        Bucket=bucket, 
                        Prefix=f"{year}/",
                        ContinuationToken=response['NextContinuationToken']
                    )
                    
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            key = obj['Key']
                            filename = key.split('/')[-1]
                            
                            if not filename or not file_pattern.match(filename):
                                continue
                            
                            match = file_pattern.match(filename)
                            if match:
                                device_id, date_str, time_str, ext = match.groups()
                                dt_str = f"{date_str}_{time_str}"
                                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                                file_size_mb = obj['Size'] / (1024 * 1024)
                                
                                date_key = dt.strftime("%Y-%m-%d")
                                found_files[date_key].append({
                                    'datetime': dt,
                                    'file_path': key,
                                    'device': device_id,
                                    'size_mb': file_size_mb,
                                    'time_str': dt.strftime("%H:%M:%S"),
                                    'year': year
                                })
                                
                                period_key = dt.strftime("%Y-%m-%d_%H:%M")
                                file_details[period_key] = {
                                    's3_path': key,
                                    'device': device_id,
                                    'datetime': dt,
                                    'size_mb': file_size_mb,
                                    'full_date': dt_str
                                }
            
            print(f"  Found {len([f for date in found_files for f in found_files[date] if f['year'] == year])} files for {year}")
    
    except Exception as e:
        print(f"Error scanning bucket: {e}")
        traceback.print_exc()
        return None, None
    
    print(f"\nTotal files found across all years: {len(file_details)}")
    
    return found_files, file_details

def check_specific_file(filename):
    """
    Check if a specific file exists and get its details
    """
    print(f"\nChecking specific file: {filename}")
    
    # Try to find the file using the same working method
    try:
        # Search in a broader prefix first
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="2023/",  # Based on your filename, start with 2023
            MaxKeys=1000
        )
        
        found = False
        if 'Contents' in response:
            for obj in response.get('Contents', []):
                if filename in obj['Key']:
                    print(f"✓ FOUND: {obj['Key']}")
                    print(f"  Size: {obj['Size'] / (1024*1024):.2f} MB")
                    print(f"  Last Modified: {obj['LastModified']}")
                    found = True
                    break
        
        if not found:
            print(f"✗ NOT FOUND: {filename} in initial search")
            # Try a more general search
            response = s3.list_objects_v2(
                Bucket=bucket,
                Prefix="",
                MaxKeys=1000
            )
            
            if 'Contents' in response:
                for obj in response.get('Contents', []):
                    if filename in obj['Key']:
                        print(f"✓ FOUND (in broader search): {obj['Key']}")
                        print(f"  Size: {obj['Size'] / (1024*1024):.2f} MB")
                        found = True
                        break
        
        if not found:
            print(f"✗ NOT FOUND: {filename} anywhere in first 1000 objects")
        return found
        
    except Exception as e:
        print(f"Error searching for file: {e}")
        return False

def create_period_dictionary(file_details):
    """
    Create a clean dictionary for navigation
    Format: "YYYY-MM-DD_HH:MM" -> "s3://bucket/path/to/file.flac"
    """
    period_dict = {}
    
    for period_key, info in sorted(file_details.items()):
        # Create clean entry
        period_dict[period_key] = {
            's3_uri': f"s3://{bucket}/{info['s3_path']}",
            'device': info['device'],
            'date': info['datetime'].strftime("%Y-%m-%d"),
            'time': info['datetime'].strftime("%H:%M:%S"),
            'size_mb': info['size_mb'],
            'full_timestamp': info['full_date']
        }
    
    print(f"\nCreated period dictionary with {len(period_dict)} entries")
    return period_dict

def main():
    """
    Main function to scan bucket and create period dictionary
    """
    print("="*60)
    print("ECOSURF DATASET SCANNER (ADAPTED CONFIG)")
    print("="*60)
    
    # First check the specific file you mentioned
    check_specific_file("S4A09112_20230411_173000.flac")
    
    # Scan entire bucket
    found_files, file_details = scan_bucket_structure()
    
    if not found_files:
        print("Failed to scan bucket. Check credentials and connectivity.")
        return
    
    # Create the final period dictionary
    period_dict = create_period_dictionary(file_details)
    
    # Save dictionary to file for later use
    import json
    import pickle
    
    # Save as JSON (readable)
    with open('period_locations.json', 'w') as f:
        json.dump(period_dict, f, indent=2, default=str)
    
    # Save as pickle (for Python)
    with open('period_locations.pkl', 'wb') as f:
        pickle.dump(period_dict, f)
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"1. Total periods found: {len(period_dict)}")
    if period_dict:
        print(f"2. Date range: {min(period_dict.keys())} to {max(period_dict.keys())}")
        
        # Count by device
        device_counts = {}
        for info in period_dict.values():
            device = info['device']
            device_counts[device] = device_counts.get(device, 0) + 1
        
        print(f"3. Files by device:")
        for device, count in sorted(device_counts.items()):
            print(f"   - {device}: {count} files")
    
    print(f"\n4. Data saved to:")
    print(f"   - period_locations.json (human-readable)")
    print(f"   - period_locations.pkl (Python object)")
    
    # Show sample of the dictionary
    print(f"\n5. Sample entries (first 5):")
    if period_dict:
        for i, (key, value) in enumerate(list(period_dict.items())[:5]):
            print(f"   {key}: {value['device']} - {value['s3_uri']}")
    else:
        print("   No entries found.")

if __name__ == "__main__":
    main()