# # File: test_s3_full.py
"""
COMPLETE S3 CONNECTION TEST
Run: python test_s3_full.py
"""
import boto3
import json
import os
import sys
from datetime import datetime

def test_credentials():
    """Test if credentials file exists and is valid"""
    print("=" * 60)
    print("🔍 TEST 1: Checking Credentials File")
    print("=" * 60)
    
    # Check possible locations
# In test_s3_full.py, update the cred_paths list:
    cred_paths = [
        'credentials.json',  # Current directory
        os.path.join(os.getcwd(), 'credentials.json'),
        os.path.join(os.getcwd(), 'M2_PFE_ECOSURF', 'credentials.json'),  # ADD THIS
        os.path.join(os.path.dirname(os.getcwd()), 'credentials.json'),
        os.path.join(os.path.expanduser('~'), '.config', 'ecosurf', 'credentials.json'),
        'data/credentials.json',
        '../credentials.json'
    ]
    
    creds = None
    found_path = None
    
    for cp in cred_paths:
        abs_path = os.path.abspath(cp)
        exists = os.path.exists(cp)
        print(f"  📁 {abs_path}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
        
        if exists and creds is None:
            try:
                with open(cp, 'r') as f:
                    creds = json.load(f)
                found_path = cp
                print(f"  ✅ Loaded from: {cp}")
            except json.JSONDecodeError as e:
                print(f"  ❌ Invalid JSON in {cp}: {e}")
            except Exception as e:
                print(f"  ❌ Error reading {cp}: {e}")
    
    if not creds:
        print("\n❌ CRITICAL: No valid credentials file found!")
        print("Please create credentials.json with:")
        print('''
{
    "ACCESS_KEY": "49681DS3ZCZ72FT67RLC",
    "SECRET_KEY": "3FpOwWdILAfVkaePQ7SOPf0aFgl9dsTCBPkNpoNL",
    "endpoint": "https://s3.eu-west-2.wasabisys.com",
    "region": "eu-west-2",
    "bucket": "ecosurf-dataset"
}
        ''')
        return None
    
    print("\n✅ Credentials loaded successfully!")
    print(f"   Path: {found_path}")
    print(f"   Keys: {list(creds.keys())}")
    
    # Validate required keys
    required = ['ACCESS_KEY', 'SECRET_KEY', 'endpoint', 'region', 'bucket']
    missing = [key for key in required if key not in creds]
    if missing:
        print(f"❌ Missing keys: {missing}")
        return None
    
    return creds

def test_s3_connection(creds):
    """Test S3 connection"""
    print("\n" + "=" * 60)
    print("🌐 TEST 2: Testing S3 Connection")
    print("=" * 60)
    
    try:
        print(f"  🔗 Endpoint: {creds['endpoint']}")
        print(f"  🌍 Region: {creds['region']}")
        print(f"  📦 Bucket: {creds['bucket']}")
        print(f"  🔑 Access Key: {creds['ACCESS_KEY'][:10]}...")
        
        # Create S3 client
        session = boto3.session.Session()
        s3 = session.client(
            's3',
            region_name=creds['region'],
            aws_access_key_id=creds['ACCESS_KEY'],
            aws_secret_access_key=creds['SECRET_KEY'],
            endpoint_url=creds['endpoint']
        )
        
        print("  ⏳ Connecting to S3...")
        
        # Test 2.1: List buckets (basic connection)
        response = s3.list_buckets()
        buckets = [b['Name'] for b in response['Buckets']]
        
        print(f"  ✅ Connected to S3!")
        print(f"  📊 Available buckets: {len(buckets)}")
        for bucket in buckets[:5]:  # Show first 5
            print(f"     • {bucket}")
        if len(buckets) > 5:
            print(f"     • ... and {len(buckets)-5} more")
        
        return s3
        
    except Exception as e:
        print(f"  ❌ S3 Connection Failed: {type(e).__name__}")
        print(f"  Error: {e}")
        return None

def test_bucket_access(s3, creds):
    """Test access to specific bucket"""
    print("\n" + "=" * 60)
    print("📂 TEST 3: Testing Bucket Access")
    print("=" * 60)
    
    bucket = creds['bucket']
    
    try:
        # Test 3.1: Check if bucket exists
        print(f"  🔍 Checking bucket: {bucket}")
        s3.head_bucket(Bucket=bucket)
        print(f"  ✅ Bucket exists: {bucket}")
        
        # Test 3.2: List objects
        print(f"  📋 Listing objects (first 10)...")
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=10)
        
        if 'Contents' in response:
            objects = response['Contents']
            print(f"  ✅ Found {len(objects)} objects")
            
            # Show objects
            for i, obj in enumerate(objects, 1):
                size_mb = obj['Size'] / (1024 * 1024)
                modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M')
                print(f"     {i:2d}. {obj['Key'][:50]}... ({size_mb:.1f} MB) - {modified}")
            
            # Test 3.3: Try to download first small file
            print(f"\n  ⬇️ Testing download...")
            small_objects = [o for o in objects if o['Size'] < 10 * 1024 * 1024]  # < 10MB
            
            if small_objects:
                test_obj = small_objects[0]
                print(f"  Testing with: {test_obj['Key']}")
                
                try:
                    import tempfile
                    import soundfile as sf
                    import io
                    
                    # Download to memory
                    response = s3.get_object(Bucket=bucket, Key=test_obj['Key'])
                    audio_bytes = response['Body'].read()
                    
                    print(f"  ✅ Downloaded: {len(audio_bytes):,} bytes")
                    
                    # Try to read as audio
                    print(f"  🎵 Testing audio read...")
                    
                    # Method 1: Try librosa from bytes
                    try:
                        import librosa
                        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, duration=2.0)
                        print(f"  ✅ Librosa can read audio!")
                        print(f"     Samples: {len(audio):,}, SR: {sr} Hz")
                        print(f"     Duration: {len(audio)/sr:.1f}s")
                    except Exception as e:
                        print(f"  ⚠️ Librosa failed: {type(e).__name__}")
                    
                    # Method 2: Try soundfile from temp file
                    try:
                        with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as tmp:
                            tmp.write(audio_bytes)
                            tmp_path = tmp.name
                        
                        audio, sr = sf.read(tmp_path)
                        os.unlink(tmp_path)
                        print(f"  ✅ SoundFile can read audio!")
                        print(f"     Samples: {len(audio):,}, SR: {sr} Hz")
                        print(f"     Duration: {len(audio)/sr:.1f}s")
                    except Exception as e:
                        print(f"  ⚠️ SoundFile failed: {type(e).__name__}")
                    
                except Exception as e:
                    print(f"  ❌ Download test failed: {e}")
            else:
                print(f"  ⚠️ No small files to test download")
                
        else:
            print(f"  ⚠️ Bucket exists but is empty or no permissions")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Bucket access failed: {type(e).__name__}")
        print(f"  Error: {e}")
        return False

def test_sample_s3_uris(creds):
    """Test with actual S3 URIs from your app"""
    print("\n" + "=" * 60)
    print("🔗 TEST 4: Testing S3 URI Parsing")
    print("=" * 60)
    
    # Sample S3 URIs (replace with actual ones from your app)
    sample_uris = [
        "s3://ecosurf-dataset/20200221/device_20200221_090000.flac",
        "s3://ecosurf-dataset/20200221/device_20200221_090100.flac",
        "s3://ecosurf-dataset/20200222/device_20200222_100000.flac"
    ]
    
    print("  Testing S3 URI parsing...")
    
    for uri in sample_uris:
        print(f"\n  🔗 URI: {uri}")
        
        if uri.startswith('s3://'):
            without_protocol = uri[5:]  # Remove 's3://'
            parts = without_protocol.split('/', 1)
            
            if len(parts) == 2:
                bucket_name, s3_path = parts
                print(f"     Bucket: {bucket_name}")
                print(f"     Path: {s3_path}")
                
                # Verify bucket matches credentials
                if bucket_name != creds['bucket']:
                    print(f"     ⚠️ WARNING: Bucket mismatch!")
                    print(f"        URI bucket: {bucket_name}")
                    print(f"        Creds bucket: {creds['bucket']}")
            else:
                print(f"     ❌ Invalid S3 URI format")
        else:
            print(f"     ❌ Not an S3 URI")

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("🚀 ECOSURF S3 CONNECTION TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Credentials
    creds = test_credentials()
    if not creds:
        print("\n❌ TEST FAILED: Cannot proceed without credentials")
        return False
    
    # Test 2: S3 Connection
    s3 = test_s3_connection(creds)
    if not s3:
        print("\n❌ TEST FAILED: Cannot connect to S3")
        return False
    
    # Test 3: Bucket Access
    bucket_ok = test_bucket_access(s3, creds)
    if not bucket_ok:
        print("\n⚠️ WARNING: Cannot access bucket, but connection works")
    
    # Test 4: S3 URI Parsing
    test_sample_s3_uris(creds)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if s3 and bucket_ok:
        print("✅ ALL TESTS PASSED!")
        print("\nYour S3 connection should work in the application.")
        print("If you still get errors, check:")
        print("1. The actual S3 URIs in period_locations.json")
        print("2. File paths in the URIs")
        print("3. Audio file format (librosa supports .flac)")
    elif s3:
        print("⚠️ PARTIAL SUCCESS")
        print("S3 connection works but bucket access failed.")
        print("Check bucket name and permissions.")
    else:
        print("❌ TESTS FAILED")
        print("Fix the issues above before running the app.")
    
    return s3 is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)