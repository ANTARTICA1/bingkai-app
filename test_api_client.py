import sys
from pathlib import Path
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.main import app

def test_api():
    client = TestClient(app)

    print("1. Testing Health & System Info...")
    res = client.get("/api/system/info")
    assert res.status_code == 200, f"Failed system info: {res.text}"
    print(f"   System Info: {res.json()['app_name']} - IPs: {res.json()['local_ips']}")

    print("2. Testing Login Endpoint...")
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200, f"Failed login: {res.text}"
    assert "bingkai_session" in client.cookies, "Cookie not set"
    print(f"   Login success: {res.json()['username']}")

    print("3. Testing Folders Endpoint...")
    res = client.get("/api/folders")
    assert res.status_code == 200, f"Failed list folders: {res.text}"
    folders = res.json()
    print(f"   Folders retrieved: {len(folders)}")

    print("4. Testing Photos Endpoint (Pagination)...")
    res = client.get("/api/photos?page=1&limit=10")
    assert res.status_code == 200, f"Failed list photos: {res.text}"
    data = res.json()
    assert "items" in data
    print(f"   Photos found: {data['total']}, Items in page: {len(data['items'])}")

    if data["items"]:
        photo_id = data["items"][0]["id"]
        print(f"5. Testing Thumbnail Streaming for Photo ID {photo_id}...")
        res_thumb = client.get(f"/api/photos/{photo_id}/thumbnail")
        assert res_thumb.status_code == 200, f"Failed thumbnail stream: {res_thumb.status_code}"
        assert "image/" in res_thumb.headers.get("content-type", "")
        print(f"   Thumbnail streamed successfully! Content-Type: {res_thumb.headers.get('content-type')}")

        print(f"6. Testing Original Photo Streaming for Photo ID {photo_id}...")
        res_orig = client.get(f"/api/photos/{photo_id}/original")
        assert res_orig.status_code == 200, f"Failed original stream: {res_orig.status_code}"
        print(f"   Original photo streamed successfully! Size: {len(res_orig.content)} bytes")

    print("7. Testing Dashboard Endpoint...")
    res_dash = client.get("/api/dashboard")
    assert res_dash.status_code == 200, f"Failed dashboard: {res_dash.text}"
    print(f"   Dashboard stats: {res_dash.json()['total_storage_formatted']}")

    print("8. Testing SPA Index.html Serving...")
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "Bingkai" in res_html.text
    print("   SPA index.html served successfully!")

    print("\n[SUCCESS] SEMUA ENDPOINT REST API DAN FRONTEND SERVING 100% BEKERJA!")

if __name__ == "__main__":
    test_api()
