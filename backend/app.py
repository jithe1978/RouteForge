import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd


# Import your extractor function
from Extract_name_phone_address_toast import extract_order_details


DATA_ROOT = "/data" # persisted via Docker volume or EFS in ECS
UPLOAD_DIR = os.path.join(DATA_ROOT, "uploads")
OUTPUT_DIR = os.path.join(DATA_ROOT, "output")


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


app = Flask(__name__)
CORS(app) # allow requests from your React dev server


@app.route("/health", methods=["GET"])
def health():
return {"ok": True, "service": "pdf-extractor", "time": time.time()}


@app.route("/upload", methods=["POST"])
def upload():
if "file" not in request.files:
return jsonify({"ok": False, "error": "No file part"}), 400


f = request.files["file"]
if f.filename == "":
return jsonify({"ok": False, "error": "No selected file"}), 400


# Save incoming PDF
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
pdf_name = f"upload_{ts}.pdf"
pdf_path = os.path.join(UPLOAD_DIR, pdf_name)
f.save(pdf_path)


# Extract records via your script
try:
records = extract_order_details(pdf_path)
except Exception as e:
return jsonify({"ok": False, "error": f"Extractor failed: {e}"}), 500


if not records:
return jsonify({"ok": True, "records": 0, "message": "No order details were extracted."}), 200


# Save to Excel in OUTPUT_DIR
df = pd.DataFrame(records)
excel_name = f"order_details_{ts}.xlsx"
app.run(host="0.0.0.0", port=5000)