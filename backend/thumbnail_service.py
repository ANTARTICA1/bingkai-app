import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageOps, ImageFile

from backend.config import THUMBNAILS_DIR, THUMBNAIL_SIZE, THUMBNAIL_QUALITY

ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger("bingkai.thumbnails")

def generate_thumbnail(original_path: Path, photo_hash: str) -> Optional[Path]:
    if not original_path.exists() or not original_path.is_file():
        logger.warning(f"File foto asli tidak ditemukan: {original_path}")
        return None

    thumb_filename = f"thumb_{photo_hash}.webp"
    thumb_path = THUMBNAILS_DIR / thumb_filename

    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return thumb_path

    try:
        with Image.open(original_path) as img:
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "LA"):
                pass
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            img.save(
                thumb_path,
                format="WEBP",
                quality=THUMBNAIL_QUALITY,
                method=4
            )

        return thumb_path
    except Exception as e:
        logger.error(f"Gagal membuat thumbnail untuk {original_path}: {e}")
        try:
            with Image.open(original_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.BILINEAR)
                fallback_path = THUMBNAILS_DIR / f"thumb_{photo_hash}.jpg"
                img.save(fallback_path, format="JPEG", quality=75)
                return fallback_path
        except Exception as fallback_err:
            logger.error(f"Fallback thumbnail juga gagal untuk {original_path}: {fallback_err}")
            return None
