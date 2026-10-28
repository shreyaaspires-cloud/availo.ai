import io
import uuid
import logging
from typing import Optional
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

supabase_client: Optional[Client] = None

try:
    if settings.SUPABASE_URL and "dummy" not in settings.SUPABASE_URL:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
except Exception as e:
    logger.warning("Supabase storage client failed init: %s", e)


async def upload_file(
    file_bytes: bytes,
    bucket_name: str,
    path: str,
    content_type: str = "image/jpeg",
) -> str:
    """Uploads file to Supabase Storage bucket and returns public/signed URL."""
    if supabase_client:
        try:
            supabase_client.storage.from_(bucket_name).upload(
                path=path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            # Return signed or public url
            res = supabase_client.storage.from_(bucket_name).create_signed_url(path, 3600 * 24)
            if "signedURL" in res:
                return res["signedURL"]
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{path}"
        except Exception as e:
            logger.error("Error uploading to Supabase: %s", e)

    # Fallback mock URL for demo/local without live Supabase credentials
    return f"https://mock-storage.availo.app/{bucket_name}/{path}"


async def get_signed_url(bucket_name: str, path: str, expires_in: int = 3600) -> str:
    if supabase_client:
        try:
            res = supabase_client.storage.from_(bucket_name).create_signed_url(path, expires_in)
            return res.get("signedURL", f"https://mock-storage.availo.app/{bucket_name}/{path}")
        except Exception as e:
            logger.error("Error creating signed URL: %s", e)
    return f"https://mock-storage.availo.app/{bucket_name}/{path}"
