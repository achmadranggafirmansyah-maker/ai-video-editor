# AI Video Editor — MVP

Web app sederhana untuk workflow: upload video mentah (maks 5 menit) → brief → pilih style → rasio → resolusi → proses → preview → download MP4.

## Jalankan

1. Install Python 3.10+ dan FFmpeg.
2. Buka folder project.
3. `pip install -r requirements.txt`
4. `uvicorn app:app --reload`
5. Buka `http://127.0.0.1:8000`

## Catatan penting

Versi ini adalah **MVP processing engine**: backend benar-benar menerima dan meng-encode video dengan rasio/resolusi yang dipilih serta memberi preset punch-in ringan. Untuk mencapai editing otomatis yang benar-benar meniru video referensi (pemilihan highlight, jump-cut berdasarkan ucapan, caption otomatis, B-roll/screenshot, emphasis, beat/SFX, dan lain-lain), perlu ditambahkan pipeline AI/video-analysis pada endpoint `/api/edit`.

Struktur UI dan API sengaja dibuat agar pipeline AI tersebut bisa dipasang tanpa mengubah alur utama.
