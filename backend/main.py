import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session

from backend.config import (
    APP_NAME, APP_TAGLINE, APP_VERSION,
    FRONTEND_DIR, THUMBNAILS_DIR,
    get_local_ip_addresses
)
from backend.database import engine, Base, get_db
from backend.models import User, Folder, Photo
from backend.schemas import (
    UserLogin, UserOut,
    FolderCreate, FolderOut,
    PhotoOut, PhotoDetailOut, PaginatedPhotosOut,
    ScanResultOut, DashboardStatsOut, SystemInfoOut
)
from backend.security import (
    verify_password, get_password_hash,
    create_session_token, get_current_user,
    SESSION_COOKIE_NAME, SESSION_MAX_AGE,
    validate_path_in_folders
)
from backend.thumbnail_service import generate_thumbnail
from backend.scanner import scan_folder
from backend.photo_service import (
    get_photos, get_photo_by_id,
    toggle_photo_favorite, get_dashboard_statistics
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("bingkai.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Menginisialisasi database SQLite Bingkai...")
    Base.metadata.create_all(bind=engine)

    db = next(get_db())
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            default_pw = "admin123"
            admin_user = User(
                username="admin",
                password_hash=get_password_hash(default_pw)
            )
            db.add(admin_user)
            db.commit()
            logger.info("Akun admin default berhasil dibuat: Username='admin', Password='admin123'")
    finally:
        db.close()

    local_ips = get_local_ip_addresses()
    logger.info(f"=== {APP_NAME} Siap Digunakan ===")
    logger.info(f"Akses Lokal PC : http://localhost:8080")
    for ip in local_ips:
        logger.info(f"Akses Remote HP: http://{ip}:8080")

    yield
    logger.info("Server Bingkai dimatikan.")

app = FastAPI(
    title=APP_NAME,
    description=f"{APP_NAME} - {APP_TAGLINE}",
    version=APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/login", response_model=UserOut)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah."
        )

    token = create_session_token(user.id, user.username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return user

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"message": "Berhasil logout."}

@app.get("/api/auth/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/api/folders", response_model=list[FolderOut])
def list_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folders = db.query(Folder).all()
    results = []
    for f in folders:
        count = db.query(Photo).filter(Photo.folder_id == f.id, Photo.deleted_at == None).count()
        results.append(
            FolderOut(
                id=f.id,
                path=f.path,
                name=f.name,
                enabled=f.enabled,
                last_scanned=f.last_scanned,
                created_at=f.created_at,
                photo_count=count
            )
        )
    return results

@app.post("/api/folders", response_model=FolderOut)
def add_folder(
    payload: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_path = Path(payload.path.strip()).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Folder tidak ditemukan di sistem: {target_path}"
        )

    path_str = str(target_path)
    existing = db.query(Folder).filter(Folder.path == path_str).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder ini sudah terdaftar sebelumnya."
        )

    folder_name = payload.name.strip() if payload.name and payload.name.strip() else target_path.name
    if not folder_name:
        folder_name = str(target_path)

    new_folder = Folder(
        path=path_str,
        name=folder_name,
        enabled=True
    )
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)

    return FolderOut(
        id=new_folder.id,
        path=new_folder.path,
        name=new_folder.name,
        enabled=new_folder.enabled,
        last_scanned=new_folder.last_scanned,
        created_at=new_folder.created_at,
        photo_count=0
    )

@app.delete("/api/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder tidak ditemukan.")

    db.delete(folder)
    db.commit()
    return {"message": f"Folder '{folder.name}' berhasil dihapus dari monitoring aplikasi."}

@app.post("/api/folders/{folder_id}/scan", response_model=ScanResultOut)
def trigger_scan(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = scan_folder(folder_id, db)
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error saat scan folder {folder_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal melakukan scan folder.")

@app.get("/api/photos", response_model=PaginatedPhotosOut)
def list_photos(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    folder_id: Optional[int] = Query(None),
    favorite: bool = Query(False),
    q: Optional[str] = Query(None),
    sort: str = Query("date_desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_photos(
        db=db,
        page=page,
        limit=limit,
        folder_id=folder_id,
        favorite_only=favorite,
        query=q,
        sort_by=sort
    )

@app.get("/api/photos/{photo_id}", response_model=PhotoDetailOut)
def get_photo_detail(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")
    return photo

@app.post("/api/photos/{photo_id}/favorite", response_model=PhotoOut)
def toggle_favorite(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    photo = toggle_photo_favorite(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")
    return photo

@app.get("/api/photos/{photo_id}/thumbnail")
def get_photo_thumbnail(
    photo_id: int,
    db: Session = Depends(get_db)
):
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    thumb_path = None
    if photo.thumbnail_path:
        thumb_candidate = THUMBNAILS_DIR / photo.thumbnail_path
        if thumb_candidate.exists():
            thumb_path = thumb_candidate

    if not thumb_path:
        original_file = Path(photo.file_path)
        if original_file.exists():
            thumb_path = generate_thumbnail(original_file, photo.hash)
            if thumb_path:
                photo.thumbnail_path = thumb_path.name
                db.commit()

    if not thumb_path or not thumb_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail tidak tersedia.")

    media_type = "image/webp" if thumb_path.suffix.lower() == ".webp" else "image/jpeg"
    return FileResponse(
        path=thumb_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"}
    )

@app.get("/api/photos/{photo_id}/original")
def get_photo_original(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto tidak ditemukan.")

    file_path = validate_path_in_folders(photo.file_path, db)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File foto asli tidak ditemukan di disk.")

    ext = photo.extension.lower()
    media_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    media_type = media_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=photo.filename
    )

@app.get("/api/dashboard", response_model=DashboardStatsOut)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_dashboard_statistics(db)

@app.get("/api/system/info", response_model=SystemInfoOut)
def get_system_info(request: Request):
    local_ips = get_local_ip_addresses()
    port = request.url.port or 8080
    remote_urls = [f"http://{ip}:{port}" for ip in local_ips]
    return SystemInfoOut(
        app_name=APP_NAME,
        tagline=APP_TAGLINE,
        version=APP_VERSION,
        local_ips=local_ips,
        port=port,
        remote_urls=remote_urls
    )

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

@app.get("/")
def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Frontend belum tersedia</h1>", status_code=500)
    return FileResponse(index_path)
