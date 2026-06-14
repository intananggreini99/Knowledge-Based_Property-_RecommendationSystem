# Rumaku — Sistem Rekomendasi Properti

Aplikasi rekomendasi rumah & apartemen berbasis *knowledge-based filtering*
(hard constraint → soft ranking → constraint relaxation) di atas dataset berisi
**12.946 properti**.

Repositori ini sudah disiapkan untuk **deployment terpisah**:

- **Frontend (Next.js)** → di-deploy ke **Vercel**
- **Backend (FastAPI + PostgreSQL)** → di-deploy ke **Railway**

Keduanya terhubung lewat satu environment variable (`NEXT_PUBLIC_API_URL`).

> Panduan deployment lengkap langkah-demi-langkah ada di **[PANDUAN_DEPLOY.md](./PANDUAN_DEPLOY.md)**.

---

## Arsitektur

```
                Pengguna (browser)
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Vercel — Frontend Next.js   │   app/, components/, lib/
        │   (UI, render, mode demo)     │
        └──────────────┬───────────────┘
                       │  fetch  NEXT_PUBLIC_API_URL/api/*
                       ▼
        ┌──────────────────────────────┐
        │   Railway — Backend FastAPI   │   /api/recommend, /api/evaluate, ...
        │   (mesin rekomendasi, pandas) │
        └──────────────┬───────────────┘
                       │  SQLAlchemy (DATABASE_URL)
                       ▼
        ┌──────────────────────────────┐
        │   Railway — PostgreSQL plugin │
        └──────────────────────────────┘
```

**Kenapa dipisah?** Mesin rekomendasi memakai `pandas`/`numpy` sehingga harus
tetap berjalan sebagai layanan Python — tidak bisa ikut ke dalam bundle Next.js.
Vercel menjadi tempat ideal untuk frontend, Railway untuk backend Python + database.

### Mode demo (penting)

Frontend dirancang **dua mode**:

- Jika `NEXT_PUBLIC_API_URL` terisi dan backend hidup → memanggil API sungguhan.
- Jika kosong atau backend tidak terjangkau → otomatis jatuh ke **mode demo**
  dengan contoh data bawaan + peringkat sisi-klien.

Artinya situs di Vercel **tetap berfungsi** walau backend belum dipasang.

---

## Struktur folder

```
sistem_rekomendasi_properti_deploy/
├── README.md                 ← file ini
├── PANDUAN_DEPLOY.md         ← panduan deploy Vercel + Railway
├── docker-compose.yml        ← menjalankan backend + db secara lokal
│
├── frontend/                 ← Next.js (deploy ke Vercel)
│   ├── app/                  ← App Router: layout, halaman /, /evaluation
│   ├── components/           ← Nav, Footer, MatchRing, halaman interaktif, dll.
│   ├── lib/                  ← api.js, format.js, demo.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── next.config.mjs
│   └── .env.local.example    ← contoh konfigurasi NEXT_PUBLIC_API_URL
│
└── backend/                  ← FastAPI (deploy ke Railway)
    ├── app/                  ← main.py, recommender, evaluation, dll.
    ├── data/                 ← dataset (sudah dibundel ke dalam image)
    ├── Dockerfile
    ├── railway.json
    └── requirements.txt
```

---

## Menjalankan secara lokal

### Backend + database (Docker)

```bash
docker compose up --build
# API aktif di http://localhost:8000  (dok: http://localhost:8000/docs)
```

### Frontend (Next.js)

```bash
cd frontend
cp .env.local.example .env.local
# isi: NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# UI aktif di http://localhost:3000
```

Tanpa mengisi `.env.local`, frontend tetap jalan dalam **mode demo**.

---

## Endpoint backend

| Method | Path                | Keterangan                                   |
| ------ | ------------------- | -------------------------------------------- |
| GET    | `/api/health`       | Status + jumlah record (dipakai healthcheck) |
| GET    | `/api/stats`        | Jumlah record, rentang harga, daftar kota    |
| POST   | `/api/recommend`    | Rekomendasi dari preferensi pengguna         |
| GET    | `/api/evaluate`     | Metrik NDCG/Precision/Recall/F1/CSR/VRR      |
| POST   | `/api/reload`       | Muat ulang dataset ke database               |

Teknologi: **FastAPI · SQLAlchemy · PostgreSQL · pandas/numpy** (backend),
**Next.js 14 · React 18 · Tailwind CSS 3** (frontend).
