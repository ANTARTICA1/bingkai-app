import math
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_

from backend.models import Photo, Folder

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

def get_dashboard_statistics(db: Session) -> Dict[str, Any]:
    active_photos = db.query(Photo).filter(Photo.deleted_at == None)
    
    total_photos = active_photos.count()
    total_bytes = db.query(func.coalesce(func.sum(Photo.file_size), 0)).filter(Photo.deleted_at == None).scalar() or 0
    total_favorites = active_photos.filter(Photo.favorite == True).count()
    total_folders = db.query(Folder).count()

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
        "format_counts": format_counts,
        "largest_folders": largest_folders[:5]
    }
