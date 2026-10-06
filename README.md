# AI Video Editor — Vercel + Render + Cloudflare R2 + OpenAI

Production-oriented starter architecture:
- `frontend/` → deploy to Vercel
- `backend/` → deploy to Render with Docker + FFmpeg
- Cloudflare R2 → object storage
- OpenAI → AI planning layer

## 1. Deploy frontend to Vercel
Import this GitHub repository into Vercel.
Set Root Directory to `frontend`.
Add:
`NEXT_PUBLIC_API_URL=https://YOUR-RENDER-SERVICE.onrender.com`

## 2. Deploy backend to Render
Create a Web Service from the same repository.
Runtime: Docker.
Dockerfile path: `backend/Dockerfile`
Root Directory: leave blank.
Add environment variables:
- `OPENAI_API_KEY`
- `R2_ENDPOINT`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app`

The backend exposes:
- GET `/health`
- POST `/api/jobs`
- GET `/api/jobs/{job_id}`
- GET `/api/jobs/{job_id}/download`

## 3. Cloudflare R2
Create a bucket and an R2 API token with object read/write access.
Use the S3-compatible endpoint as `R2_ENDPOINT`.

## 4. OpenAI
Create an API key and put it ONLY in Render environment variables.
The starter uses AI for an editing-plan layer when available; the deterministic FFmpeg pipeline still works without it.

## Important
This starter is deployable, but the advanced "match my reference video's exact editing style" engine is intentionally modular. The `style_profiles.py` file is where the reference-style rules can be expanded with transcript-driven cuts, word emphasis, punch-ins, captions, overlays, and B-roll decisions.
