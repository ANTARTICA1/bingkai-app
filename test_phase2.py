import sys
from pathlib import Path
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.main import app
from backend.config import DATA_DIR, TRASH_DIR
from backend.database import SessionLocal
from backend.models import Folder, Photo

def run_phase2_tests():
    client = TestClient(app)

    print("1. Login...")
    res_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_login.status_code == 200

    print("2. Setup Test Folders...")
    f1_dir = DATA_DIR / "sample_photos" / "folder_a"
    f2_dir = DATA_DIR / "sample_photos" / "folder_b"
    f1_dir.mkdir(parents=True, exist_ok=True)
    f2_dir.mkdir(parents=True, exist_ok=True)

    res_f1 = client.post("/api/folders", json={"path": str(f1_dir.resolve()), "name": "Folder A"})
    res_f2 = client.post("/api/folders", json={"path": str(f2_dir.resolve()), "name": "Folder B"})
    
    db = SessionLocal()
    folder_a = db.query(Folder).filter(Folder.path == str(f1_dir.resolve())).first()
    folder_b = db.query(Folder).filter(Folder.path == str(f2_dir.resolve())).first()
    db.close()

    print("3. Create Sample Photos (Including 2 Duplicates)...")
    img1 = Image.new("RGB", (200, 200), color=(255, 0, 0))
    img1.save(f1_dir / "sample_red.jpg", format="JPEG")
    img1.save(f2_dir / "sample_red_copy.jpg", format="JPEG")

    img2 = Image.new("RGB", (200, 200), color=(0, 255, 0))
    img2.save(f1_dir / "sample_green.jpg", format="JPEG")

    client.post(f"/api/folders/{folder_a.id}/scan")
    client.post(f"/api/folders/{folder_b.id}/scan")

    print("4. Test Duplicate Detection...")
    res_dup = client.get("/api/duplicates")
    assert res_dup.status_code == 200
    dups = res_dup.json()
    assert len(dups) >= 1
    assert dups[0]["count"] >= 2
    print(f"   Duplicate group detected: {dups[0]['count']} items")

    print("5. Test Rename Photo...")
    res_photos = client.get("/api/photos")
    assert res_photos.status_code == 200
    items = res_photos.json()["items"]
    target_photo = [p for p in items if "sample_green" in p["filename"]][0]

    res_rename = client.patch(f"/api/photos/{target_photo['id']}/rename", json={"name": "emerald_leaf"})
    assert res_rename.status_code == 200
    renamed = res_rename.json()
    assert renamed["filename"] == "emerald_leaf.jpg"
    assert (f1_dir / "emerald_leaf.jpg").exists()
    print("   Rename successful: emerald_leaf.jpg")

    print("6. Test Move Photo...")
    res_move = client.post(f"/api/photos/{target_photo['id']}/move", json={"target_folder_id": folder_b.id})
    assert res_move.status_code == 200
    moved = res_move.json()
    assert moved["folder_id"] == folder_b.id
    assert (f2_dir / "emerald_leaf.jpg").exists()
    assert not (f1_dir / "emerald_leaf.jpg").exists()
    print("   Move photo to Folder B successful!")

    print("7. Test Virtual Albums (Create, Add, Remove, Delete)...")
    res_album = client.post("/api/albums", json={"name": "Summer Gems", "description": "Collection of green and red colors"})
    assert res_album.status_code == 200
    album = res_album.json()
    album_id = album["id"]

    res_add = client.post(f"/api/albums/{album_id}/photos/{target_photo['id']}")
    assert res_add.status_code == 200

    res_alb_detail = client.get(f"/api/albums/{album_id}")
    assert res_alb_detail.status_code == 200
    assert len(res_alb_detail.json()["photos"]) == 1

    res_rem = client.delete(f"/api/albums/{album_id}/photos/{target_photo['id']}")
    assert res_rem.status_code == 200

    res_alb_del = client.delete(f"/api/albums/{album_id}")
    assert res_alb_del.status_code == 200
    print("   Virtual Album lifecycle successful!")

    print("8. Test Trash, Restore, and Permanent Delete...")
    res_trash = client.post(f"/api/photos/{target_photo['id']}/trash")
    assert res_trash.status_code == 200

    res_list_trash = client.get("/api/trash")
    assert res_list_trash.status_code == 200
    assert any(p["id"] == target_photo["id"] for p in res_list_trash.json()["items"])
    assert (TRASH_DIR / f"{target_photo['id']}_emerald_leaf.jpg").exists()
    print("   Soft delete to trash successful!")

    res_restore = client.post(f"/api/photos/{target_photo['id']}/restore")
    assert res_restore.status_code == 200
    assert (f2_dir / "emerald_leaf.jpg").exists()
    print("   Restore from trash successful!")

    client.post(f"/api/photos/{target_photo['id']}/trash")
    res_perm = client.delete(f"/api/photos/{target_photo['id']}/permanent")
    assert res_perm.status_code == 200
    assert not (TRASH_DIR / f"{target_photo['id']}_emerald_leaf.jpg").exists()
    print("   Permanent delete successful!")

    print("\n[SUCCESS] SEMUA PENGUJIAN PHASE 2 (TRASH, RESTORE, MOVE, RENAME, ALBUMS, DUPLICATES) BERHASIL 100%!")

if __name__ == "__main__":
    run_phase2_tests()
