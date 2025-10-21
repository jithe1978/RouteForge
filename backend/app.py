# app.py
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from flask_cors import CORS
import os, uuid, subprocess

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/extract")
def extract():
    f = request.files.get("file")
    if not f:
        return ("No file", 400)

    # Save uploaded PDF
    in_path = os.path.join(OUTPUT_DIR, f"in-{uuid.uuid4().hex}.pdf")
    f.save(in_path)

    # Date-stamped Excel name with collision handling
    stamp = datetime.now().strftime("%Y-%m-%d")
    base = f"order_details_{stamp}.xlsx"
    out_path = os.path.join(OUTPUT_DIR, base)
    n = 2
    while os.path.exists(out_path):
        out_path = os.path.join(OUTPUT_DIR, f"order_details_{stamp}({n}).xlsx")
        n += 1

    try:
        cmd = ["python", "Extract_name_phone_address_toast.py", "--input", in_path, "--output", out_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd="/app")
        if proc.returncode != 0:
            return (f"Extractor failed:\n{proc.stderr or proc.stdout}", 500)
        return jsonify({"message": "Uploaded & extracted.", "output": os.path.basename(out_path)})
    except subprocess.TimeoutExpired:
        return ("Extractor timed out", 504)
    except Exception as e:
        return (f"Server error: {e}", 500)

@app.get("/output")
def list_output():
    return jsonify({"files": sorted(os.listdir(OUTPUT_DIR))})

@app.get("/output/<path:name>")
def download_output(name):
    return send_from_directory(OUTPUT_DIR, name, as_attachment=True)