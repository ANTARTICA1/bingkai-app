import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Table, Index, Text
)
from sqlalchemy.orm import relationship
from backend.database import Base

album_photos = Table(
    "album_photos",
    Base.metadata,
    Column("album_id", Integer, ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True),
    Column("photo_id", Integer, ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(1024), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    last_scanned = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    photos = relationship("Photo", back_populates="folder", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(1024), unique=True, nullable=False, index=True)
    folder_path = Column(String(1024), nullable=False)
    extension = Column(String(16), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    date_created = Column(DateTime, nullable=False)
    date_modified = Column(DateTime, nullable=False)
    date_taken = Column(DateTime, nullable=True)
    favorite = Column(Boolean, default=False, nullable=False)
    hash = Column(String(64), nullable=False)
    thumbnail_path = Column(String(1024), nullable=True)
    indexed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    folder = relationship("Folder", back_populates="photos")
    albums = relationship("Album", secondary=album_photos, back_populates="photos")

    __table_args__ = (
        Index("idx_photos_hash", "hash"),
        Index("idx_photos_date_taken", "date_taken"),
        Index("idx_photos_date_modified", "date_modified"),
        Index("idx_photos_favorite", "favorite"),
        Index("idx_photos_deleted_at", "deleted_at"),
        Index("idx_photos_folder_id", "folder_id"),
        Index("idx_photos_search", "filename", "folder_path"),
    )


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    photos = relationship("Photo", secondary=album_photos, back_populates="albums")
