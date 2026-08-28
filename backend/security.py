import re
import bcrypt
from pathlib import Path
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from fastapi import HTTPException, status, Depends, Request, Cookie
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY
from backend.database import get_db
from backend.models import User, Folder

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="bingkai-auth-session")
SESSION_COOKIE_NAME = "bingkai_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def create_session_token(user_id: int, username: str) -> str:
    return serializer.dumps({"user_id": user_id, "username": username})

def verify_session_token(token: str) -> Optional[dict]:
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data
    except (SignatureExpired, BadTimeSignature, Exception):
        return None

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi diperlukan. Silakan login terlebih dahulu.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_session_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session telah kadaluarsa atau tidak valid. Silakan login ulang.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan.",
        )
    return user

def sanitize_filename(filename: str) -> str:
    filename = filename.replace("\x00", "").replace("/", "").replace("\\", "")
    filename = re.sub(r'[\<\>\:\"\/\\\|\?\*]', '', filename)
    filename = filename.strip(". ")
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nama file tidak valid setelah disanitasi."
        )
    return filename

def validate_path_in_folders(target_path: Path | str, db: Session) -> Path:
    try:
        resolved_path = Path(target_path).resolve()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format path tidak valid: {e}"
        )

    registered_folders = db.query(Folder).filter(Folder.enabled == True).all()
    if not registered_folders:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak ada folder terdaftar di sistem."
        )

    is_allowed = False
    for folder in registered_folders:
        try:
            reg_resolved = Path(folder.path).resolve()
            if resolved_path == reg_resolved or reg_resolved in resolved_path.parents:
                is_allowed = True
                break
        except Exception:
            continue

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak: File/Folder berada di luar direktori yang diizinkan."
        )

    return resolved_path
