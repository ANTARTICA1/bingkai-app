# 🖼️ Bingkai — Local Photo Manager & Remote Controller

> *"Membantu yang berserakan kembali beraturan"*

**Bingkai** adalah aplikasi manajemen foto lokal (*local-first*) modern yang membantu Anda mengelola, mencari, dan meninjau ribuan foto yang tersimpan di laptop/PC langsung melalui browser, termasuk dari smartphone (HP) yang terhubung ke jaringan Wi-Fi lokal yang sama.

Aplikasi ini **bukan cloud photo storage**. Foto asli tetap 100% tersimpan di komputer Anda. Bingkai hanya melakukan pengindeksan cerdas, membuat thumbnail terkompresi cepat, membaca metadata EXIF, dan memberikan kendali penuh melalui antarmuka web modern tanpa perlu upload ke cloud pihak ketiga.

---

## ✨ Fitur Utama (Phase 1 — Core MVP)

- **Local-First & Privasi 100%**: Tidak ada data atau foto yang dikirim ke server eksternal/cloud.
- **Remote Controller (Akses dari HP)**: Cukup sambungkan HP ke Wi-Fi yang sama untuk melihat, mencari, dan menandai foto di PC.
- **Fast Recursive Photo Scanner**: Memindai direktori komputer dan subfolder (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`).
- **Smart Change Detection**: Hanya memproses foto baru atau yang berubah berdasarkan kombinasi ukuran file, mtime, dan hash SHA-256.
- **High-Performance Thumbnail System**: Otomatis menghasilkan thumbnail WebP ringan (320x320) dengan orientasi rotasi EXIF yang tepat agar galeri memuat instan.
- **Modern Responsive Gallery**: Tampilan grid terkelompok tanggal (*Hari Ini, Kemarin, Bulan, Tahun*) dengan lazy loading dan filter cepat.
- **Full-Screen Photo Viewer**: Melihat foto resolusi asli lengkap dengan info metadata EXIF, dimensi, ukuran file, dan tombol favorit.
- **Sistem Pencarian & Sorting Cepat**: Cari instan berdasarkan nama file, subfolder, atau ekstensi file di database SQLite lokal.
- **Keamanan & Anti-Path Traversal**: Dilengkapi sistem autentikasi session dan validasi direktori terdaftar untuk mencegah manipulasi path di luar folder yang diizinkan.
- **Zero Build Frontend**: Antarmuka frontend menggunakan **Alpine.js** dan **Tailwind CSS** melalui CDN tanpa memerlukan Node.js atau proses build rumit.

---

## 🏗️ Arsitektur Sistem

```
HP / Smartphone (Wi-Fi)      Desktop Browser (Localhost)
          │                               │
          └───────────────┬───────────────┘
                          │ HTTP REST API (Fetch)
                          ▼
            [ FastAPI Backend (Python) ]
              ├── Security & Path Sanitizer
              ├── Recursive Scanner & Hasher
              └── Pillow Thumbnail Engine
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
  [ SQLite (bingkai.db) ]      [ Local File System PC ]
  - Metadata foto & folder     - Foto Asli (D:/Photos, Pictures)
  - Hash SHA-256 & EXIF        - data/thumbnails/ (Cache WebP)
  - Status Favorit & Albums    - data/trash/ (Soft-delete)
```

---

## ⚡ Pemilihan Library Frontend (CDN)

Frontend Bingkai dibangun tanpa *Node.js* atau *Webpack/Vite*, menggunakan library CDN versi terkunci:

1. **Tailwind CSS** (`v3.4.17`): Layout responsif, transisi modern, dan styling dark mode tanpa CSS compiler.
2. **Alpine.js** (`v3.14.8`): Framework reaktif mini (~15KB) untuk kontrol modal, filter galeri, form login, dan interaksi tanpa overhead framework besar.
3. **Lucide Icons** (`v0.475.0`): Icon vector minimalis dengan teks fallback.
4. **Google Fonts (Plus Jakarta Sans)**: Tipografi modern dan bersih.

> **Catatan Kemandirian Offline:** Library CDN akan otomatis di-cache oleh browser setelah pertama kali dibuka. Untuk penggunaan 100% offline tanpa internet sejak instalasi pertama, library ini dapat diunduh ke folder `frontend/vendor/` pada tahap rilis berikutnya.

---

## 📁 Struktur Project

```
bingkai-app/
├── backend/
│   ├── main.py                # Server FastAPI & endpoint routing
│   ├── config.py              # Konfigurasi sistem, direktori, & deteksi IP
│   ├── database.py            # SQLite engine (WAL mode + Foreign Keys)
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic validation schemas
│   ├── security.py            # Hashing Bcrypt, session token, validator path
│   ├── scanner.py             # Recursive filesystem scanner & EXIF reader
│   ├── thumbnail_service.py   # Kompresi & pembuatan thumbnail Pillow
│   └── photo_service.py       # Query galeri, filter, pencarian, statistik
├── frontend/
│   ├── index.html             # Antarmuka SPA responsif
│   ├── css/
│   │   └── style.css          # Styling kustom & font
│   ├── js/
│   │   ├── api.js             # Fetch API client layer
│   │   ├── gallery.js         # Pengelompokan tanggal & format galeri
│   │   └── app.js             # State management Alpine.js
│   └── assets/
│       └── logo.svg           # Logo branding Bingkai
├── data/
│   ├── bingkai.db             # File database SQLite lokal
│   ├── thumbnails/            # Cache thumbnail WebP
│   └── trash/                 # Folder soft-delete foto
├── requirements.txt           # Dependency Python minimal
├── README.md                  # Dokumentasi aplikasi
└── .gitignore                 # Exclusion data pribadi & DB
```

---

## 🚀 Panduan Menjalankan Aplikasi

### 1. Prasyarat
- Python 3.10 atau versi yang lebih baru terinstal di PC/laptop Anda.
- Tidak memerlukan Node.js atau npm.

### 2. Instalasi Dependency
Buka Terminal / PowerShell di folder project `bingkai-app`:

```bash
# Buat virtual environment (opsional tetapi disarankan)
python -m venv venv

# Aktifkan virtual environment di Windows:
venv\Scripts\activate

# Install dependency backend Python:
pip install -r requirements.txt
```

### 3. Menjalankan Server Bingkai
Jalankan perintah berikut:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📱 Cara Mengakses dari Smartphone (Remote Controller)

1. Pastikan laptop/PC Anda dan HP Anda terhubung ke **jaringan Wi-Fi yang sama**.
2. Cari tahu IP lokal laptop/PC Anda:
   - **Windows**: Buka CMD/PowerShell, ketik `ipconfig`, lalu lihat bagian `IPv4 Address` (contoh: `192.168.1.15`).
   - Atau langsung lihat pada halaman **Remote HP & Setelan** di aplikasi Bingkai.
3. Buka browser di HP (Chrome / Safari), ketikkan alamat:
   ```
   http://192.168.1.15:8000
   ```
   *(Ganti `192.168.1.15` dengan IP lokal PC Anda).*
4. Masuk dengan akun administrator default:
   - **Username**: `admin`
   - **Password**: `admin123`

---

## 🔒 Keamanan & Validasi

- **Pencegahan Directory Traversal**: API menolak semua request yang mencoba mengakses file sistem di luar folder yang telah didaftarkan (`../../Windows/System32`, dll).
- **Sanitasi File & Path**: Semua input nama file disanitasi dari null bytes (`\x00`) dan karakter kontrol berbahaya.
- **Session Aman**: Autentikasi menggunakan cookie `HttpOnly` dengan enkripsi token URLSafe bertanda tangan digital.
- **Tanpa Overwrite Fisik Tanpa Konfirmasi**: Operasi sensitif divalidasi ganda di backend dan database.

---

## 🗺️ Roadmap Prioritas Pengembangan

- [x] **Phase 1 — Core MVP** (Struktur project, SQLite ORM, Scanner Rekursif, Thumbnail Generator, Galeri Responsif CDN, Autentikasi, Remote HP).
- [ ] **Phase 2 — Management** (Fitur Move/Rename antar folder aman, Sistem Trash & Restore, Album Virtual many-to-many, Deteksi Duplikat SHA-256).
- [ ] **Phase 3 — Advanced** (Background Folder Monitoring menggunakan Watchdog, Activity Log, Full Offline Vendor Bundle).

---

## 📄 Lisensi
Dikembangkan dengan ❤️ untuk membantu foto Anda yang berserakan kembali beraturan.
