import os
import time
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ExifTags
from sqlalchemy.orm import Session

from backend.config import SUPPORTED_EXTENSIONS
from backend.models import Folder, Photo
from backend.thumbnail_service import generate_thumbnail

logger = logging.getLogger("bingkai.scanner")

EXIF_DATETIME_TAGS = {"DateTimeOriginal", "DateTimeDigitized", "DateTime"}
EXIF_TAGS_MAP = {v: k for k, v in ExifTags.TAGS.items() if v in EXIF_DATETIME_TAGS}

def compute_file_hash(file_path: Path, chunk_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_image_metadata(file_path: Path) -> Tuple[Optional[int], Optional[int], Optional[datetime.datetime]]:
    width = None
    height = None
    date_taken = None

    try:
        with Image.open(file_path) as img:
            width, height = img.size
            exif_data = img.getexif()
            if exif_data:
                for tag_name in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]:
                    tag_id = EXIF_TAGS_MAP.get(tag_name)
                    if tag_id and tag_id in exif_data:
                        date_str = str(exif_data[tag_id]).strip()
                        try:
                            date_taken = datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                            break
                        except Exception:
                            pass
    except Exception as e:
        logger.debug(f"Tidak dapat membaca EXIF untuk {file_path}: {e}")

    return width, height, date_taken

def scan_folder(folder_id: int, db: Session) -> dict:
    start_time = time.time()
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise ValueError(f"Folder dengan ID {folder_id} tidak ditemukan.")

    folder_root = Path(folder.path).resolve()
    if not folder_root.exists() or not folder_root.is_dir():
        raise ValueError(f"Direktori fisik folder tidak ditemukan: {folder.path}")

    scanned_count = 0
    indexed_new = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    existing_photos_map = {
        p.file_path: p for p in db.query(Photo).filter(Photo.folder_id == folder_id).all()
    }

    for root, _, files in os.walk(folder_root):
        root_path = Path(root)
        for filename in files:
            file_path = root_path / filename
            ext = file_path.suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            scanned_count += 1
            file_path_str = str(file_path.resolve())

            try:
                stat_info = file_path.stat()
                file_size = stat_info.st_size
                mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime)
                ctime = datetime.datetime.fromtimestamp(stat_info.st_ctime)

                existing = existing_photos_map.get(file_path_str)

                if existing and existing.file_size == file_size:
                    if abs((existing.date_modified - mtime).total_seconds()) < 1.0:
                        skipped_count += 1
                        continue

                file_hash = compute_file_hash(file_path)
                width, height, date_taken = extract_image_metadata(file_path)
                
                thumb_path = generate_thumbnail(file_path, file_hash)
                thumb_str = str(thumb_path.name) if thumb_path else None

                if existing:
                    existing.filename = filename
                    existing.folder_path = str(root_path)
                    existing.extension = ext
                    existing.file_size = file_size
                    existing.width = width or existing.width
                    existing.height = height or existing.height
                    existing.date_modified = mtime
                    existing.date_taken = date_taken or existing.date_taken
                    existing.hash = file_hash
                    existing.thumbnail_path = thumb_str
                    existing.deleted_at = None
                    updated_count += 1
                else:
                    new_photo = Photo(
                        folder_id=folder.id,
                        filename=filename,
                        file_path=file_path_str,
                        folder_path=str(root_path),
                        extension=ext,
                        file_size=file_size,
                        width=width,
                        height=height,
                        date_created=ctime,
                        date_modified=mtime,
                        date_taken=date_taken or mtime,
                        favorite=False,
                        hash=file_hash,
                        thumbnail_path=thumb_str,
                        indexed_at=datetime.datetime.utcnow(),
                        deleted_at=None
                    )
                    db.add(new_photo)
                    existing_photos_map[file_path_str] = new_photo
                    indexed_new += 1

                if (indexed_new + updated_count) % 100 == 0:
                    db.commit()

            except Exception as file_err:
                logger.error(f"Gagal memproses file {file_path}: {file_err}")
                error_count += 1
                continue

    folder.last_scanned = datetime.datetime.utcnow()
    db.commit()

    elapsed = round(time.time() - start_time, 2)
    logger.info(
        f"Scan selesai untuk folder '{folder.name}' dalam {elapsed}s: "
        f"{indexed_new} baru, {updated_count} diperbarui, {skipped_count} dilewati, {error_count} error."
    )

    return {
        "folder_id": folder_id,
        "scanned_files": scanned_count,
        "indexed_new": indexed_new,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": error_count,
        "elapsed_seconds": elapsed,
        "message": f"Scan selesai dalam {elapsed} detik: {indexed_new} foto baru diindeks."
    }
