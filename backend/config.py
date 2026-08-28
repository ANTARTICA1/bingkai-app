import os
import socket
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
TRASH_DIR = DATA_DIR / "trash"

DATA_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
TRASH_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "bingkai.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

SECRET_KEY_FILE = DATA_DIR / ".secret_key"
if not SECRET_KEY_FILE.exists():
    SECRET_KEY_FILE.write_text(secrets.token_urlsafe(32), encoding="utf-8")
SECRET_KEY = SECRET_KEY_FILE.read_text(encoding="utf-8").strip()

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

THUMBNAIL_SIZE = (320, 320)
THUMBNAIL_QUALITY = 82

APP_NAME = "Bingkai"
APP_TAGLINE = "Membantu yang berserakan kembali beraturan"
APP_VERSION = "0.1.0"

def get_local_ip_addresses() -> list[str]:
    ip_list = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and primary_ip not in ip_list and not primary_ip.startswith("127."):
            ip_list.append(primary_ip)
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and ip not in ip_list:
                ip_list.append(ip)
    except Exception:
        pass

    if not ip_list:
        ip_list.append("127.0.0.1")
    return ip_list
