
import os, io, uuid, mimetypes
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.db import engine, SessionLocal, Base
from utils.models import Media

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")
PORT = int(os.environ.get("PORT", "10000"))
STORAGE_DIR = os.environ.get("STORAGE_DIR", "./static/uploads")
DEVICE_TOKENS = os.environ.get("DEVICE_TOKENS", "device1:token-123")

# parse tokens: "id1:tok1, id2:tok2"
def parse_tokens(s):
    out = {}
    for part in s.split(","):
        part = part.strip()
        if not part: continue
        if ":" in part:
            did, tok = part.split(":", 1)
            out[did.strip()] = tok.strip()
    return out

TOKENS = parse_tokens(DEVICE_TOKENS)
ALLOWED_EXT = {"jpg","jpeg","png","mp4","mov","mkv","avi","webm"}

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ensure storage
os.makedirs(STORAGE_DIR, exist_ok=True)

# DB init
Base.metadata.create_all(bind=engine)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","")
        p = request.form.get("password","")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["user"] = u
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="نام کاربری یا رمز عبور اشتباه است.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def root():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = SessionLocal()
    recent = db.query(Media).order_by(Media.created_at.desc()).limit(50).all()
    counts = {
        "images": db.query(Media).filter(Media.media_type=="image").count(),
        "videos": db.query(Media).filter(Media.media_type=="video").count(),
        "total": db.query(Media).count()
    }
    db.close()
    return render_template("dashboard.html", items=recent, counts=counts, devices=list(TOKENS.keys()))

@app.route("/gallery")
@login_required
def gallery():
    db = SessionLocal()
    items = db.query(Media).order_by(Media.created_at.desc()).all()
    db.close()
    return render_template("gallery.html", items=items)

@app.route("/media/<path:fname>")
@login_required
def media_file(fname):
    return send_from_directory(STORAGE_DIR, fname)

# ------------- API -------------
@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id")
    token = data.get("token")
    if not device_id or not token or TOKENS.get(device_id) != token:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    # could store last_seen later
    return jsonify({"ok": True, "ts": datetime.utcnow().isoformat()+"Z"})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    device_id = request.form.get("device_id") or request.headers.get("X-Device-Id")
    token = request.form.get("token") or request.headers.get("X-Auth-Token")
    if not device_id or not token or TOKENS.get(device_id) != token:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"ok": False, "error": "no file"}), 400

    filename = secure_filename(file.filename or f"upload-{uuid.uuid4().hex}")
    ext = filename.rsplit(".",1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify({"ok": False, "error": "bad extension"}), 400

    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    outname = f"{device_id}-{ts}-{uuid.uuid4().hex}.{ext}"
    outpath = os.path.join(STORAGE_DIR, outname)
    file.save(outpath)

    media_type = "video" if ext in {"mp4","mov","mkv","avi","webm"} else "image"
    mime = mimetypes.guess_type(outname)[0] or "application/octet-stream"

    db = SessionLocal()
    rec = Media(device_id=device_id, filename=outname, media_type=media_type, mime=mime)
    db.add(rec); db.commit(); db.refresh(rec); db.close()

    return jsonify({"ok": True, "id": rec.id, "url": f"/media/{outname}", "media_type": media_type})

@app.route("/api/list", methods=["GET"])
def api_list():
    auth = request.headers.get("X-Admin-Auth")
    if auth != ADMIN_PASSWORD:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    db = SessionLocal()
    items = db.query(Media).order_by(Media.created_at.desc()).limit(200).all()
    out = [{
        "id": m.id, "device_id": m.device_id, "filename": m.filename,
        "type": m.media_type, "created_at": m.created_at.isoformat()+"Z"
    } for m in items]
    db.close()
    return jsonify({"ok": True, "items": out})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
