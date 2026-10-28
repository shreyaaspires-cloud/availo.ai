import sys
from supabase import create_client
from app.config import settings

buckets = [
    settings.SUPABASE_STORAGE_BUCKET_CONDITIONS,
    settings.SUPABASE_STORAGE_BUCKET_DOCS,
    settings.SUPABASE_STORAGE_BUCKET_CONTRACTS,
]


def init_buckets():
    print("📦 Initializing Supabase Storage buckets...")
    if not settings.SUPABASE_URL or "dummy" in settings.SUPABASE_URL:
        print("⚠️ Supabase URL is unconfigured or dummy. Skipping remote bucket creation.")
        return

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        existing = client.storage.list_buckets()
        existing_names = {b.name for b in existing}

        for bucket in buckets:
            if bucket not in existing_names:
                client.storage.create_bucket(bucket, options={"public": False})
                print(f"  ✓ Created private bucket: {bucket}")
            else:
                print(f"  - Bucket already exists: {bucket}")
        print("✨ Buckets verified.")
    except Exception as e:
        print(f"❌ Error communicating with Supabase: {e}")


if __name__ == "__main__":
    init_buckets()
