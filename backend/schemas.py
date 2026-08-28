import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class FolderCreate(BaseModel):
    path: str
    name: Optional[str] = None

class FolderOut(BaseModel):
    id: int
    path: str
    name: str
    enabled: bool
    last_scanned: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    photo_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class PhotoOut(BaseModel):
    id: int
    folder_id: int
    filename: str
    folder_path: str
    extension: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    date_created: datetime.datetime
    date_modified: datetime.datetime
    date_taken: Optional[datetime.datetime] = None
    favorite: bool
    hash: str
    thumbnail_path: Optional[str] = None
    indexed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class PhotoDetailOut(PhotoOut):
    file_path: str

class PaginatedPhotosOut(BaseModel):
    items: List[PhotoOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ScanResultOut(BaseModel):
    folder_id: int
    scanned_files: int
    indexed_new: int
    updated: int
    skipped: int
    errors: int
    elapsed_seconds: float
    message: str

class DashboardStatsOut(BaseModel):
    total_photos: int
    total_storage_bytes: int
    total_storage_formatted: str
    total_favorites: int
    total_folders: int
    format_counts: dict
    largest_folders: list

class SystemInfoOut(BaseModel):
    app_name: str
    tagline: str
    version: str
    local_ips: List[str]
    port: int
    remote_urls: List[str]
