import sys
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import DATA_DIR, THUMBNAILS_DIR
from backend.database import engine, Base, SessionLocal
from backend.models import User, Folder, Photo
from backend.security import get_password_hash, verify_password, create_session_token, verify_session_token
from backend.scanner import scan_folder
from backend.photo_service import get_photos, toggle_photo_favorite, get_dashboard_statistics

def run_tests():
    print("1. Inisialisasi Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("2. Uji User & Hashing Password...")
    test_user = db.query(User).filter(User.username == "admin").first()
    if not test_user:
        test_user = User(username="admin", password_hash=get_password_hash("admin123"))
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    assert verify_password("admin123", test_user.password_hash) == True, "Password verification failed"
    token = create_session_token(test_user.id, test_user.username)
    payload = verify_session_token(token)
    assert payload["username"] == "admin", "Session token payload invalid"
    print("   -> User & Auth Berhasil!")

    print("3. Buat Folder & File Gambar Dummy untuk Uji Coba...")
    test_folder_dir = DATA_DIR / "sample_photos" / "vacation_bali"
    test_folder_dir.mkdir(parents=True, exist_ok=True)

    colors = [("img_beach.jpg", "JPEG", (30, 144, 255)), ("img_sunset.png", "PNG", (255, 99, 71)), ("img_temple.webp", "WEBP", (46, 139, 87))]
    for name, fmt, color in colors:
        img_path = test_folder_dir / name
        img = Image.new("RGB", (800, 600), color=color)
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 750, 550], outline=(255, 255, 255), width=5)
        img.save(img_path, format=fmt)

    print("4. Daftarkan Folder & Jalankan Scanner...")
    folder_path_str = str(test_folder_dir.resolve())
    folder = db.query(Folder).filter(Folder.path == folder_path_str).first()
    if not folder:
        folder = Folder(path=folder_path_str, name="Liburan Bali", enabled=True)
        db.add(folder)
        db.commit()
        db.refresh(folder)

    scan_result = scan_folder(folder.id, db)
    print(f"   -> Hasil Scan: {scan_result}")
    assert scan_result["scanned_files"] == 3, f"Expected 3 files, got {scan_result['scanned_files']}"

    print("5. Verifikasi Metadata & Thumbnail...")
    photos = db.query(Photo).filter(Photo.folder_id == folder.id).all()
    assert len(photos) == 3, f"Expected 3 photos in DB, got {len(photos)}"
    for p in photos:
        print(f"   - {p.filename}: {p.width}x{p.height}px, hash={p.hash[:8]}..., thumb={p.thumbnail_path}")
        assert p.thumbnail_path is not None, f"Thumbnail path missing for {p.filename}"
        assert (THUMBNAILS_DIR / p.thumbnail_path).exists(), f"Thumbnail file not found on disk"

    print("6. Uji Favorite & Query Photos...")
    toggle_photo_favorite(photos[0].id, db)
    fav_result = get_photos(db, favorite_only=True)
    assert fav_result["total"] >= 1, "Favorite photo query failed"
    print(f"   -> Foto favorit ditemukan: {fav_result['total']}")

    print("7. Uji Dashboard Statistics...")
    stats = get_dashboard_statistics(db)
    print(f"   -> Total Photos: {stats['total_photos']}, Total Storage: {stats['total_storage_formatted']}")
    assert stats["total_photos"] >= 3, "Dashboard total photos mismatch"

    db.close()
    print("\n[SUCCESS] SEMUA PENGUJIAN FONDASI PHASE 1 BERHASIL DILALUI!")

if __name__ == "__main__":
    run_tests()
