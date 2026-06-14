# Panduan Deploy — Vercel (Frontend) + Railway (Backend)

Dokumen ini memandu Anda men-deploy aplikasi **Rumaku** ke produksi:

- **Backend FastAPI + PostgreSQL** → **Railway**
- **Frontend Next.js** → **Vercel**

Estimasi waktu: ±20–30 menit. Tidak perlu kartu kredit untuk paket gratis/hobby
(Railway memberi kredit awal; Vercel punya Hobby tier).

---

## Ringkasan & urutan

Urutan yang disarankan:

1. **Push kode ke GitHub** (satu repo berisi folder `frontend/` dan `backend/`).
2. **Deploy backend dulu ke Railway** → dapatkan URL publik backend.
3. **Deploy frontend ke Vercel** dengan mengisi `NEXT_PUBLIC_API_URL` = URL backend.
4. **(Opsional) Perketat CORS** di backend ke domain Vercel Anda.

> 💡 Frontend punya **mode demo** bawaan. Jadi kalau Anda ingin, frontend bisa
> di-deploy lebih dulu dan tetap berfungsi (memakai contoh data) sampai backend siap.

---

## Langkah 0 — Push ke GitHub

Dari dalam folder `sistem_rekomendasi_properti_deploy/`:

```bash
git init
git add .
git commit -m "Rumaku: frontend Next.js + backend FastAPI"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA-REPO.git
git push -u origin main
```

Cukup **satu repository** saja — Railway akan memakai folder `backend/`, Vercel
memakai folder `frontend/`.

---

## Bagian A — Deploy Backend ke Railway

### A1. Buat project dari GitHub

1. Masuk ke [railway.app](https://railway.app) → **New Project**.
2. Pilih **Deploy from GitHub repo** → pilih repository Anda.
   (Jika pertama kali, hubungkan akun GitHub Anda lebih dulu.)
3. Railway membuat satu **service** dari repo tersebut.

### A2. Arahkan service ke folder `backend/`

Karena repo berisi frontend **dan** backend (monorepo), beri tahu Railway folder
mana yang harus dibangun:

1. Klik service tadi → tab **Settings**.
2. Cari **Root Directory** → isi dengan **`backend`**.
3. Simpan. Railway akan otomatis menemukan **`backend/Dockerfile`** dan
   membangun image dengan builder Dockerfile.

> Dataset (`backend/data/`) sudah dibundel ke dalam image, jadi **tidak perlu
> volume**. Image akan berisi 12.946 properti siap pakai.

### A3. Tambahkan database PostgreSQL

1. Di kanvas project, klik **New** (atau **+ Create**) → **Database** → **Add PostgreSQL**.
2. Railway membuat service Postgres (biasanya bernama **`Postgres`**) yang otomatis
   menyediakan variabel koneksi (`DATABASE_URL`, `PGHOST`, dst.).

### A4. Sambungkan backend ke database

Backend membaca variabel `DATABASE_URL`. Hubungkan ke service Postgres:

1. Buka service **backend** → tab **Variables** → **New Variable**.
2. Tambahkan:

   | Name            | Value                          |
   | --------------- | ------------------------------ |
   | `DATABASE_URL`  | `${{Postgres.DATABASE_URL}}`   |
   | `CORS_ORIGINS`  | `*`  (sementara; diperketat nanti) |

   `${{Postgres.DATABASE_URL}}` adalah **referensi variabel** Railway yang menunjuk
   ke service Postgres Anda. (Sesuaikan `Postgres` bila nama service-nya berbeda.)

> **Tidak perlu set `PORT`.** Railway menyuntikkan `PORT` otomatis, dan Dockerfile
> kita sudah `--port ${PORT}`.
>
> **Tidak perlu mengubah format URL.** Railway memberi `postgresql://…`, dan aplikasi
> otomatis mengubahnya menjadi `postgresql+psycopg2://…` yang dibutuhkan SQLAlchemy.

### A5. Buat domain publik

Agar frontend (di Vercel) bisa memanggil backend:

1. Service backend → **Settings** → **Networking** → **Generate Domain**
   (atau **Public Networking**).
2. Anda akan mendapat URL seperti:
   `https://nama-anda-production.up.railway.app`
   **Catat URL ini** — inilah `NEXT_PUBLIC_API_URL` untuk Vercel.

### A6. Deploy & verifikasi

1. Railway otomatis men-deploy setiap kali ada perubahan/penyimpanan.
   Buka tab **Deployments** → **View Logs** untuk memantau.
2. **Boot pertama agak lama** (±1–3 menit) karena aplikasi menyeed 12.946 baris ke
   PostgreSQL. Ini wajar dan hanya terjadi sekali.
3. Setelah hijau, buka di browser:
   - `https://…up.railway.app/api/health` → harus mengembalikan `{"status":"ok", …}`
   - `https://…up.railway.app/docs` → dokumentasi interaktif FastAPI

> **Healthcheck (opsional).** File `backend/railway.json` sudah menyetel
> `healthcheckPath: /api/health`. Bila Railway tidak otomatis membacanya (karena
> posisinya di subfolder), Anda bisa mengaturnya manual di **Settings → Deploy →
> Healthcheck Path** = `/api/health`. Ini opsional; tanpa itu pun deploy tetap jalan.

---

## Bagian B — Deploy Frontend ke Vercel

### B1. Import repository

1. Masuk ke [vercel.com](https://vercel.com) → **Add New…** → **Project**.
2. **Import Git Repository** → pilih repo yang sama.

### B2. Atur Root Directory ke `frontend/`

1. Di layar konfigurasi project, cari **Root Directory** → klik **Edit** →
   pilih folder **`frontend`**.
2. **Framework Preset** akan otomatis terdeteksi sebagai **Next.js**
   (Build Command `next build` dan Output `.next` terisi otomatis — biarkan default).

### B3. Isi environment variable

Pada bagian **Environment Variables**, tambahkan:

| Key                   | Value                                                |
| --------------------- | ---------------------------------------------------- |
| `NEXT_PUBLIC_API_URL` | `https://nama-anda-production.up.railway.app`        |

Ketentuan penting:

- **Tanpa garis miring (`/`) di akhir.** Benar: `https://x.up.railway.app`.
- Awalan **`NEXT_PUBLIC_`** wajib agar variabel terbaca di sisi browser.
- Centang lingkungan **Production** (boleh juga Preview & Development).

### B4. Deploy

1. Klik **Deploy**. Tunggu build selesai (±1–2 menit).
2. Buka URL Vercel Anda (mis. `https://rumaku.vercel.app`).
3. Cek badge di kanan atas navigasi:
   - **"Terhubung API"** (hijau) → frontend berhasil bicara dengan backend Railway. 🎉
   - **"Mode demo (contoh data)"** (emas) → frontend jalan, tapi belum menjangkau
     backend (lihat *Troubleshooting*).

> ⚠️ **`NEXT_PUBLIC_*` ditanam saat build, bukan saat runtime.** Jika nanti Anda
> mengganti nilai `NEXT_PUBLIC_API_URL`, lakukan **Redeploy** di Vercel agar
> perubahan ikut ter-build. Mengubah variabel saja tanpa redeploy tidak berefek.

---

## Bagian C — Perketat CORS (opsional, disarankan)

Setelah tahu domain Vercel Anda, batasi backend agar hanya menerima dari domain itu:

1. Railway → service **backend** → **Variables** → ubah:

   | Name            | Value                                   |
   | --------------- | --------------------------------------- |
   | `CORS_ORIGINS`  | `https://rumaku.vercel.app`             |

   (Bisa lebih dari satu, pisahkan dengan koma:
   `https://rumaku.vercel.app,https://rumaku-git-main-user.vercel.app`)
2. Railway akan otomatis redeploy. Selesai.

Untuk proyek tugas, membiarkan `CORS_ORIGINS=*` juga boleh — keduanya berfungsi.

---

## Troubleshooting

**Frontend tetap "Mode demo" padahal backend hidup**
- Pastikan `NEXT_PUBLIC_API_URL` benar (https, tanpa `/` di akhir) lalu **Redeploy**
  Vercel (ingat: variabel ditanam saat build).
- Pastikan backend punya **domain publik** (Bagian A5) dan
  `…/api/health` bisa dibuka dari browser.
- Lihat **Console** browser (F12). Jika ada error **CORS**, set `CORS_ORIGINS` ke
  domain Vercel (Bagian C) atau `*`, lalu redeploy backend.

**Deploy backend gagal / service crash di Railway**
- Pastikan `DATABASE_URL` mereferensi Postgres: `${{Postgres.DATABASE_URL}}`.
- Lihat **Deploy Logs**. Boot pertama menyeed database — beri waktu 1–3 menit.
- Pastikan **Root Directory = `backend`** sehingga Dockerfile ditemukan.

**Permintaan pertama lambat / 502 sesaat**
- Cold start + seeding database. Tunggu beberapa detik dan coba lagi
  `…/api/health`.

**Error skema database (`postgres://` / driver psycopg2)**
- Sudah ditangani otomatis oleh `app/config.py` (`postgres://` & `postgresql://`
  → `postgresql+psycopg2://`). Cukup pastikan `DATABASE_URL` berasal dari plugin
  Postgres Railway.

**Build Vercel gagal**
- Pastikan **Root Directory = `frontend`**.
- Jalankan `npm install && npm run build` di lokal untuk memastikan build bersih
  sebelum push.

---

## Checklist akhir

Backend (Railway)
- [ ] Service dibuat dari GitHub, **Root Directory = `backend`**
- [ ] **PostgreSQL** ditambahkan ke project
- [ ] `DATABASE_URL = ${{Postgres.DATABASE_URL}}`
- [ ] `CORS_ORIGINS` di-set (`*` atau domain Vercel)
- [ ] **Domain publik** dibuat (Generate Domain)
- [ ] `…/api/health` mengembalikan `status: ok`

Frontend (Vercel)
- [ ] Project di-import, **Root Directory = `frontend`**
- [ ] Framework terdeteksi **Next.js**
- [ ] `NEXT_PUBLIC_API_URL` = URL Railway (tanpa `/` di akhir)
- [ ] Deploy sukses, badge **"Terhubung API"** muncul

Selesai — aplikasi Anda sudah live di Vercel dengan backend di Railway. 🚀
