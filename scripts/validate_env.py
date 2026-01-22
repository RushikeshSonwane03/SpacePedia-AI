import os
import sys
from urllib.parse import urlparse

def check_env(key, required=True, secure=False):
    val = os.environ.get(key)
    if not val:
        if required:
            print(f"❌ MISSING: '{key}' is required.")
            return False
        else:
            print(f"⚠️  WARNING: '{key}' is not set (optional).")
            return True
    
    if secure:
        print(f"✅ FOUND: '{key}' (Length: {len(val)})")
    else:
        print(f"✅ FOUND: '{key}' = {val}")
    return True

def validate_db_url(url):
    try:
        if "localhost" in url:
             print("❌ CRITICAL: DATABASE_URL points to 'localhost'. Any deployment will fail.")
             return False
        if "supa" in url and "pooler" not in url and ".co:5432" in url:
             print("⚠️  ADVICE: For Supabase in serverless/lambdas, consider using the Transaction Pooler (port 6543) if available.")
        return True
    except:
        return False

def main():
    print("🔍 Starting Environment Validation for SpacePedia AI...")
    print("-" * 50)
    
    all_good = True
    
    # Critical Secrets
    all_good &= check_env("DATABASE_URL", secure=True)
    if os.environ.get("DATABASE_URL"):
        all_good &= validate_db_url(os.environ.get("DATABASE_URL"))
        
    all_good &= check_env("GROQ_API_KEY", secure=True)
    all_good &= check_env("GEMINI_API_KEY", secure=True)
    
    # Config
    check_env("ENVIRONMENT", required=False)
    
    print("-" * 50)
    if all_good:
        print("✅ Environment looks GOOD for deployment!")
        sys.exit(0)
    else:
        print("❌ Environment has critical ISSUES. Fix before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
