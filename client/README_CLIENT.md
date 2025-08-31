
# Client (Android/PC Uploader)

## Android (Termux)
1) نصب Termux از F-Droid.
2) داخل Termux:
```
pkg update && pkg upgrade -y
pkg install python clang ffmpeg -y
pip install -r requirements.txt
```
3) تنظیم متغیرها:
```
export SERVER_URL="https://YOUR-RENDER-APP.onrender.com"
export DEVICE_ID="phone1"
export TOKEN="token-123"
```
4) اجرا:
```
python uploader.py
```

## Windows / Linux PC
- Python 3.10+ و وبکم نصب باشد.
```
pip install -r requirements.txt
set SERVER_URL=https://YOUR-RENDER-APP.onrender.com
set DEVICE_ID=pc1
set TOKEN=token-xyz
python uploader.py
```

## نکته
- فایل‌ها به مسیر `/api/upload` روی سرور ارسال می‌شوند.
- ویدئو را با `CAPTURE_VIDEO = True` فعال کنید.
