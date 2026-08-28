# Bingkai — Local Photo Manager & Remote Controller

> "Membantu yang berserakan kembali beraturan"

Aplikasi manajemen ribuan koleksi foto lokal di komputer/laptop dengan antarmuka web modern, cepat, aman, dan dapat dikontrol dari Smartphone (Wi-Fi) maupun Stick Game (Gamepad Controller).

---

## Konsep Aplikasi

Bingkai adalah Local Photo Manager dan Remote Controller. Aplikasi ini dirancang untuk memudahkan pengguna mengelola foto yang tersimpan di harddisk komputer tanpa harus mengunggah file foto ke cloud eksternal.

Prinsip kerja utama:
1. Foto asli tetap berada di direktori lokal komputer pengguna (misalnya D:/Photos, D:/Pictures, atau C:/Users/User/Pictures).
2. Database SQLite hanya menyimpan indeks lokasi file dan metadata (tanggal pembuatan, EXIF, dimensi, ukuran file, dan hash).
3. Backend menyajikan thumbnail ringan format WebP untuk performa rendering galeri yang cepat.
4. Pengguna dapat mengontrol galeri dari browser laptop, smartphone di jaringan Wi-Fi lokal, atau menggunakan stick gamepad controller.

---

## Fitur Utama

- **Local-First dan Privasi**: Semua proses indexing, caching thumbnail, dan manajemen file berlangsung secara lokal di komputer pengguna. Tidak ada data yang dikirim keluar.
- **Gamepad dan Stick Controller Support**: Kontrol galeri foto di monitor atau layar TV menggunakan stick game USB atau Bluetooth (Xbox, PlayStation, Logitech, atau stick generik).
- **Remote Controller Smartphone**: Akses dan kelola foto dari smartphone yang terhubung ke jaringan Wi-Fi yang sama tanpa perlu menginstal aplikasi tambahan.
- **Sistem Trash dan Restore**: Penghapusan aman dengan memindahkan file ke direktori sampah khusus. Foto dapat dipulihkan kembali ke folder aslinya atau dihapus permanen.
- **Rename dan Move Aman**: Ubah nama file dan pindahkan foto antar folder terdaftar dengan proteksi pencegahan directory traversal dan penanganan konflik nama otomatis.
- **Virtual Albums**: Buat album koleksi kustom tanpa menduplikasi atau memindahkan file fisik foto di harddisk.
- **Deteksi Foto Duplikat**: Temukan file foto yang identik secara byte berdasarkan komparasi hash SHA-256 dan pilih salinan yang ingin dibersihkan.
- **Performa Tinggi**: Database SQLite dengan mode WAL (Write-Ahead Logging), session authentication berbasis cookie HttpOnly, dan generator thumbnail Pillow WebP.
- **Antarmuka Modern**: Desain glassmorphism responsif dengan dukungan Dark Mode.

---

## Panduan Penggunaan: Stick Game (Gamepad Controller)

Bingkai mendukung Gamepad API standar browser untuk mendeteksi controller yang terhubung ke laptop/PC.

Daftar Fungsi Tombol Gamepad:
- **D-Pad (Tombol Panah) / Analog Stick**: Menggeser dan memilih kartu foto di galeri.
- **Tombol A / Cross**: Membuka foto yang dipilih ke mode layar penuh (Viewer).
- **Tombol B / Circle**: Menutup mode layar penuh dan kembali ke galeri.
- **Tombol X / Square**: Menandai atau membatalkan status Favorit pada foto.
- **Tombol Y / Triangle**: Membuka dialog untuk mengubah nama file foto (Rename).
- **Tombol LB / RB**: Berpindah ke halaman galeri sebelumnya atau berikutnya.

Langkah Penggunaan Gamepad:
1. Sambungkan gamepad ke laptop/PC melalui kabel USB atau koneksi Bluetooth.
2. Buka aplikasi Bingkai di browser (http://localhost:8080).
3. Tekan salah satu tombol pada gamepad untuk mengaktifkan pendeteksian.
4. Indikator status controller dan petunjuk tombol akan tampil di layar.

---

## Panduan Penggunaan: Smartphone Remote Controller

1. Pastikan komputer dan smartphone terhubung pada jaringan Wi-Fi yang sama.
2. Buka browser di smartphone (Google Chrome, Safari, atau Firefox).
3. Masukkan alamat IP lokal komputer beserta port aplikasi, contoh:
   ```text
   http://192.168.1.2:8080
   ```
4. Masuk menggunakan akun default:
   - Username: `admin`
   - Password: `admin123`
5. Galeri foto komputer kini dapat dikontrol langsung dari smartphone.

---

## Panduan Menjalankan Aplikasi

### 1. Prasyarat Sistem
- Python versi 3.10 atau yang lebih baru.
- Sistem operasi Windows, macOS, atau Linux.

### 2. Instalasi Dependensi
Buka terminal pada folder project dan jalankan:
```bash
pip install -r requirements.txt
```

### 3. Menjalankan Server
Jalankan perintah berikut:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

Akses aplikasi melalui:
- Browser Komputer: `http://localhost:8080`
- Browser Smartphone: `http://<IP-LOKAL-KOMPUTER>:8080`

---

## Penjelasan Struktur File dan Direktori

```text
bingkai-app/
├── backend/
│   ├── __init__.py            # Inisialisasi package backend
│   ├── config.py              # Konfigurasi path direktori, secret key, dan deteksi IP lokal
│   ├── database.py            # Konfigurasi engine SQLite, sesi koneksi, dan pragma WAL mode
│   ├── models.py              # Definisi model tabel ORM (User, Folder, Photo, Album, album_photos)
│   ├── schemas.py             # Skema validasi data request dan response Pydantic
│   ├── security.py            # Hashing password Bcrypt, validasi session token, dan validasi path
│   ├── scanner.py             # Pemindai folder rekursif, ekstraksi metadata EXIF, dan hashing SHA-256
│   ├── thumbnail_service.py   # Generator thumbnail WebP berbasis Pillow dengan auto-orientasi EXIF
│   ├── photo_service.py       # Logika bisnis galeri, filter, sort, trash, move, rename, dan album
│   └── main.py                # Server FastAPI, konfigurasi CORS, autentikasi, dan routing endpoint API
├── frontend/
│   ├── index.html             # Tampilan Single Page Application utama (Alpine.js dan Tailwind CSS)
│   ├── css/
│   │   └── style.css          # Kustomisasi CSS, styling scrollbar, shimmer, dan glassmorphism
│   ├── js/
│   │   ├── api.js             # Modul komunikasi Fetch API ke backend FastAPI
│   │   ├── gallery.js         # Fungsi helper format ukuran file dan pengelompokan tanggal
│   │   └── app.js             # State management Alpine.js dan loop input Gamepad Controller
│   └── assets/
│       └── logo.svg           # Aset vector logo aplikasi Bingkai
├── data/                      # Direktori data lokal runtime (database SQLite, thumbnail cache, trash)
├── requirements.txt           # Daftar dependensi library Python yang dibutuhkan
└── README.md                  # Dokumentasi komprehensif project
```

---

## Keamanan dan Validasi

- **Pencegahan Directory Traversal**: Backend memvalidasi setiap path file agar selalu berada di dalam folder yang terdaftar.
- **Sanitasi Nama File**: Karakter berbahaya dan null bytes disaring saat proses rename dan move file.
- **Session Authentication**: Token sesi dienkripsi dengan serializer bertanda tangan waktu dan disimpan dalam cookie HttpOnly.
- **Isolasi Data**: Direktori data lokal (database, cache thumbnail, dan trash) dikecualikan dari repository git untuk menjaga privasi pengguna.
