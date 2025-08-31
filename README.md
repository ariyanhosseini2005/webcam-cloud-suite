
# Webcam Cloud Suite (Render Server + Client Uploader)

## Deploy on Render
- Push this repo to GitHub.
- On Render: New → Web Service → connect repo.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn -b 0.0.0.0:10000 app:app`
- Add a **Disk** (1GB) mounted at `/data`.
- Set env vars:
  - `SECRET_KEY` (random)
  - `ADMIN_USERNAME` / `ADMIN_PASSWORD`
  - `DEVICE_TOKENS` e.g. `phone1:token-123, pc1:token-xyz`
  - `STORAGE_DIR` = `/data/uploads`
  - `DATABASE_URL` = `sqlite:////data/webcam.db` (or Postgres URL)

## Features
- Secure login dashboard (gallery + stats)
- API: `/api/upload` (multipart)
- API: `/api/heartbeat`
- Stores to persistent disk
- Supports multiple devices (token-based)

## Client
Check `client/README_CLIENT.md` and run `client/uploader.py` on Android (Termux) or PC.
