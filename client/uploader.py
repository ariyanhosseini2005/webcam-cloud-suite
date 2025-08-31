
# Run this on Android (Termux + pip) or on a PC with a webcam.
# Captures motion-triggered images and optional short videos, uploads to your Render server.

import cv2, time, os, io, requests, threading
from datetime import datetime
from PIL import Image

SERVER_URL = os.environ.get("SERVER_URL", "https://YOUR-RENDER-APP.onrender.com")
DEVICE_ID  = os.environ.get("DEVICE_ID", "phone1")
TOKEN      = os.environ.get("TOKEN", "token-123")
CAPTURE_VIDEO = False       # set True to record short video clips on motion
VIDEO_SECONDS  = 6

# motion detection params
SENSITIVITY = 0.5
MIN_AREA = 1200

def upload_bytes(bytes_data, filename):
    try:
        files = {"file": (filename, bytes_data)}
        data  = {"device_id": DEVICE_ID, "token": TOKEN}
        r = requests.post(f"{SERVER_URL}/api/upload", files=files, data=data, timeout=30)
        print("Upload:", r.status_code, r.text[:200])
    except Exception as e:
        print("Upload error:", e)

def upload_image(frame):
    # encode as JPEG
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok: return
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    fname = f"{DEVICE_ID}-{ts}.jpg"
    upload_bytes(buf.tobytes(), fname)

def record_and_upload(cap):
    # record small video from same capture device
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    tmpname = f"clip-{ts}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = 20.0
    ret, frame = cap.read()
    if not ret: return
    h, w = frame.shape[:2]
    out = cv2.VideoWriter(tmpname, fourcc, fps, (w, h))
    t_end = time.time() + VIDEO_SECONDS
    while time.time() < t_end:
        r, fr = cap.read()
        if not r: break
        out.write(fr)
        time.sleep(0.01)
    out.release()
    # upload file
    try:
        with open(tmpname, "rb") as f:
            data = {"device_id": DEVICE_ID, "token": TOKEN}
            files = {"file": (f"{DEVICE_ID}-{ts}.mp4", f, "video/mp4")}
            r = requests.post(f"{SERVER_URL}/api/upload", files=files, data=data, timeout=60)
            print("Video upload:", r.status_code, r.text[:200])
    except Exception as e:
        print("Video upload error:", e)
    finally:
        try: os.remove(tmpname)
        except: pass

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    bg = None
    print("Started. Press Ctrl+C to stop.")
    last_motion = 0

    # heartbeat
    def heartbeat():
        while True:
            try:
                requests.post(f"{SERVER_URL}/api/heartbeat", json={"device_id": DEVICE_ID, "token": TOKEN}, timeout=10)
            except: pass
            time.sleep(30)
    threading.Thread(target=heartbeat, daemon=True).start()

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1); continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)
        if bg is None:
            bg = gray
            continue

        diff = cv2.absdiff(bg, gray)
        thresh_val = int(25 * (1.0 - SENSITIVITY) + 5)
        _, thresh = cv2.threshold(diff, thresh_val, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion = False
        for c in contours:
            if cv2.contourArea(c) < MIN_AREA: continue
            motion = True
            break

        now = time.time()
        if motion and (now - last_motion > 2):  # avoid spamming
            last_motion = now
            print("Motion detected → uploading image")
            upload_image(frame)
            if CAPTURE_VIDEO:
                threading.Thread(target=record_and_upload, args=(cap,), daemon=True).start()

        # update background slowly
        bg = (0.9*bg + 0.1*gray).astype("uint8")

if __name__ == "__main__":
    main()
