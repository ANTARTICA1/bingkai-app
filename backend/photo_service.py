import math
import shutil
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_
from fastapi import HTTPException, status

from backend.config import TRASH_DIR, THUMBNAILS_DIR
from backend.models import Photo, Folder, Album, album_photos
from backend.security import sanitize_filename, validate_path_in_folders

def format_bytes(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"

def get_photos(
    db: Session,
    page: int = 1,
    limit: int = 50,
    folder_id: Optional[int] = None,
    favorite_only: bool = False,
    query: Optional[str] = None,
    sort_by: str = "date_desc",
) -> Dict[str, Any]:
    page = max(1, page)
    limit = max(1, min(limit, 200))

    base_query = db.query(Photo).filter(Photo.deleted_at == None)

    if folder_id:
        base_query = base_query.filter(Photo.folder_id == folder_id)

    if favorite_only:
        base_query = base_query.filter(Photo.favorite == True)

    if query:
        search_pattern = f"%{query.strip()}%"
        base_query = base_query.filter(
            or_(
                Photo.filename.ilike(search_pattern),
                Photo.folder_path.ilike(search_pattern),
                Photo.extension.ilike(search_pattern)
            )
        )

    if sort_by == "date_asc":
        base_query = base_query.order_by(Photo.date_taken.asc(), Photo.id.asc())
    elif sort_by == "name_asc":
        base_query = base_query.order_by(Photo.filename.asc())
    elif sort_by == "name_desc":
        base_query = base_query.order_by(Photo.filename.desc())
    elif sort_by == "size_desc":
        base_query = base_query.order_by(Photo.file_size.desc())
    elif sort_by == "size_asc":
        base_query = base_query.order_by(Photo.file_size.asc())
    else:
        base_query = base_query.order_by(Photo.date_taken.desc(), Photo.id.desc())

    total = base_query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    items = base_query.offset(offset).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

def get_photo_by_id(photo_id: int, db: Session) -> Optional[Photo]:
    return db.query(Photo).filter(Photo.id == photo_id, Photo.deleted_at == None).first()

def toggle_photo_favorite(photo_id: int, db: Session) -> Optional[Photo]:
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        return None
    photo.favorite = not photo.favorite
    db.commit()
    db.refresh(photo)
    return photo

def rename_photo(photo_id: int, new_raw_name: str, db: Session) -> Photo:
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    clean_name = sanitize_filename(new_raw_name)
    orig_ext = photo.extension.lower()
    
    if not clean_name.lower().endswith(orig_ext):
        clean_name = f"{clean_name}{orig_ext}"

    current_file_path = validate_path_in_folders(photo.file_path, db)
    if not current_file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File foto asli tidak ditemukan di disk.")

    new_file_path = current_file_path.parent / clean_name
    if new_file_path.exists() and new_file_path != current_file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File dengan nama tersebut sudah ada di folder ini.")

    try:
        current_file_path.rename(new_file_path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal mengubah nama file di disk: {e}")

    photo.filename = clean_name
    photo.file_path = str(new_file_path.resolve())
    photo.date_modified = datetime.datetime.fromtimestamp(new_file_path.stat().st_mtime)
    db.commit()
    db.refresh(photo)
    return photo

def move_photo(photo_id: int, target_folder_id: int, db: Session) -> Photo:
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    target_folder = db.query(Folder).filter(Folder.id == target_folder_id, Folder.enabled == True).first()
    if not target_folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder tujuan tidak valid atau dinonaktifkan.")

    target_dir = Path(target_folder.path).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Direktori folder tujuan tidak ditemukan di disk.")

    current_file_path = validate_path_in_folders(photo.file_path, db)
    if not current_file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File foto asli tidak ditemukan di disk.")

    dest_filename = photo.filename
    dest_path = target_dir / dest_filename
    counter = 1
    stem = Path(dest_filename).stem
    ext = photo.extension

    while dest_path.exists() and dest_path != current_file_path:
        dest_filename = f"{stem}_{counter}{ext}"
        dest_path = target_dir / dest_filename
        counter += 1

    try:
        shutil.move(str(current_file_path), str(dest_path))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memindahkan file di disk: {e}")

    photo.folder_id = target_folder.id
    photo.filename = dest_filename
    photo.folder_path = str(target_dir)
    photo.file_path = str(dest_path.resolve())
    photo.date_modified = datetime.datetime.fromtimestamp(dest_path.stat().st_mtime)
    db.commit()
    db.refresh(photo)
    return photo

def move_photo_to_trash(photo_id: int, db: Session) -> Photo:
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    current_file_path = Path(photo.file_path)
    trash_filename = f"{photo.id}_{photo.filename}"
    trash_target = TRASH_DIR / trash_filename

    if current_file_path.exists():
        try:
            shutil.move(str(current_file_path), str(trash_target))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memindahkan file ke trash: {e}")

    photo.deleted_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(photo)
    return photo

def restore_photo_from_trash(photo_id: int, db: Session) -> Photo:
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.deleted_at != None).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto di trash tidak ditemukan.")

    trash_filename = f"{photo.id}_{photo.filename}"
    trash_path = TRASH_DIR / trash_filename

    target_dir = Path(photo.folder_path).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    dest_filename = photo.filename
    dest_path = target_dir / dest_filename
    counter = 1
    stem = Path(dest_filename).stem
    ext = photo.extension

    while dest_path.exists():
        dest_filename = f"{stem}_restored_{counter}{ext}"
        dest_path = target_dir / dest_filename
        counter += 1

    if trash_path.exists():
        try:
            shutil.move(str(trash_path), str(dest_path))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memulihkan file dari trash: {e}")

    photo.filename = dest_filename
    photo.file_path = str(dest_path.resolve())
    photo.deleted_at = None
    db.commit()
    db.refresh(photo)
    return photo

def delete_photo_permanently(photo_id: int, db: Session) -> dict:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    trash_filename = f"{photo.id}_{photo.filename}"
    trash_path = TRASH_DIR / trash_filename
    if trash_path.exists():
        try:
            trash_path.unlink(missing_ok=True)
        except Exception:
            pass

    orig_path = Path(photo.file_path)
    if orig_path.exists():
        try:
            orig_path.unlink(missing_ok=True)
        except Exception:
            pass

    if photo.thumbnail_path:
        thumb_path = THUMBNAILS_DIR / photo.thumbnail_path
        if thumb_path.exists():
            try:
                thumb_path.unlink(missing_ok=True)
            except Exception:
                pass

    db.delete(photo)
    db.commit()
    return {"message": "Foto berhasil dihapus secara permanen."}

def empty_trash(db: Session) -> dict:
    trash_photos = db.query(Photo).filter(Photo.deleted_at != None).all()
    count = 0
    for p in trash_photos:
        trash_filename = f"{p.id}_{p.filename}"
        trash_path = TRASH_DIR / trash_filename
        if trash_path.exists():
            try:
                trash_path.unlink(missing_ok=True)
            except Exception:
                pass
        if p.thumbnail_path:
            thumb_path = THUMBNAILS_DIR / p.thumbnail_path
            if thumb_path.exists():
                try:
                    thumb_path.unlink(missing_ok=True)
                except Exception:
                    pass
        db.delete(p)
        count += 1

    db.commit()
    return {"message": f"Berhasil mengosongkan trash ({count} foto dihapus permanen).", "count": count}

def get_trash_photos(db: Session, page: int = 1, limit: int = 50) -> Dict[str, Any]:
    page = max(1, page)
    limit = max(1, min(limit, 200))

    base_query = db.query(Photo).filter(Photo.deleted_at != None).order_by(Photo.deleted_at.desc())
    total = base_query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    items = base_query.offset(offset).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

def get_duplicate_photos(db: Session) -> List[Dict[str, Any]]:
    dup_hashes = (
        db.query(Photo.hash, func.count(Photo.id))
        .filter(Photo.deleted_at == None)
        .group_by(Photo.hash)
        .having(func.count(Photo.id) > 1)
        .all()
    )

    results = []
    for h, cnt in dup_hashes:
        group_photos = db.query(Photo).filter(Photo.hash == h, Photo.deleted_at == None).all()
        if group_photos:
            sample = group_photos[0]
            results.append({
                "hash": h,
                "file_size": sample.file_size,
                "file_size_formatted": format_bytes(sample.file_size),
                "count": cnt,
                "items": group_photos
            })
    return results

def create_album(name: str, description: Optional[str], db: Session) -> Album:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nama album tidak boleh kosong.")

    existing = db.query(Album).filter(Album.name.ilike(clean_name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Album dengan nama tersebut sudah ada.")

    album = Album(name=clean_name, description=description.strip() if description else None)
    db.add(album)
    db.commit()
    db.refresh(album)
    return album

def get_albums(db: Session) -> List[Dict[str, Any]]:
    albums = db.query(Album).order_by(Album.created_at.desc()).all()
    results = []
    for a in albums:
        count = len(a.photos)
        results.append({
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "created_at": a.created_at,
            "photo_count": count
        })
    return results

def get_album_by_id(album_id: int, db: Session) -> Album:
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album tidak ditemukan.")
    return album

def add_photo_to_album(album_id: int, photo_id: int, db: Session) -> dict:
    album = get_album_by_id(album_id, db)
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    if photo not in album.photos:
        album.photos.append(photo)
        db.commit()
    return {"message": f"Foto '{photo.filename}' berhasil ditambahkan ke album '{album.name}'."}

def remove_photo_from_album(album_id: int, photo_id: int, db: Session) -> dict:
    album = get_album_by_id(album_id, db)
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    if photo in album.photos:
        album.photos.remove(photo)
        db.commit()
    return {"message": f"Foto '{photo.filename}' dikeluarkan dari album '{album.name}'."}

def delete_album(album_id: int, db: Session) -> dict:
    album = get_album_by_id(album_id, db)
    db.delete(album)
    db.commit()
    return {"message": f"Album '{album.name}' berhasil dihapus."}

def get_dashboard_statistics(db: Session) -> Dict[str, Any]:
    active_photos = db.query(Photo).filter(Photo.deleted_at == None)
    
    total_photos = active_photos.count()
    total_bytes = db.query(func.coalesce(func.sum(Photo.file_size), 0)).filter(Photo.deleted_at == None).scalar() or 0
    total_favorites = active_photos.filter(Photo.favorite == True).count()
    total_folders = db.query(Folder).count()
    total_trash = db.query(Photo).filter(Photo.deleted_at != None).count()

    dup_count_tuples = (
        db.query(Photo.hash, func.count(Photo.id))
        .filter(Photo.deleted_at == None)
        .group_by(Photo.hash)
        .having(func.count(Photo.id) > 1)
        .all()
    )
    total_duplicates = sum(cnt - 1 for _, cnt in dup_count_tuples)

    formats = (
        db.query(Photo.extension, func.count(Photo.id))
        .filter(Photo.deleted_at == None)
        .group_by(Photo.extension)
        .order_by(desc(func.count(Photo.id)))
        .all()
    )
    format_counts = {ext.upper().replace(".", ""): count for ext, count in formats}

    folders = db.query(Folder).all()
    largest_folders = []
    for f in folders:
        f_photos = db.query(Photo).filter(Photo.folder_id == f.id, Photo.deleted_at == None)
        f_count = f_photos.count()
        f_size = db.query(func.coalesce(func.sum(Photo.file_size), 0)).filter(Photo.folder_id == f.id, Photo.deleted_at == None).scalar() or 0
        largest_folders.append({
            "id": f.id,
            "name": f.name,
            "path": f.path,
            "photo_count": f_count,
            "size_bytes": f_size,
            "size_formatted": format_bytes(f_size)
        })
    
    largest_folders.sort(key=lambda x: x["size_bytes"], reverse=True)

    return {
        "total_photos": total_photos,
        "total_storage_bytes": total_bytes,
        "total_storage_formatted": format_bytes(total_bytes),
        "total_favorites": total_favorites,
        "total_folders": total_folders,
        "total_trash": total_trash,
        "total_duplicates": total_duplicates,
        "format_counts": format_counts,
        "largest_folders": largest_folders[:5]
    }
