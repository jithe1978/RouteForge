// src/App.jsx
import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:5000";

export default function App() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [files, setFiles] = useState([]);

  const onFileChange = (e) => setFile(e.target.files?.[0] ?? null);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) {
      setMessage("Choose a PDF first.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API_BASE}/extract`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json().catch(() => ({}));
      setMessage(data.message ?? "Uploaded & extracted.");
    } catch (err) {
      setMessage(`Upload failed: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function listOutput() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/output`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const list = Array.isArray(data?.files) ? data.files : Array.isArray(data) ? data : [];
      setFiles(list);
      setMessage(`Found ${list.length} files.`);
    } catch (err) {
      setMessage(`List failed: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>PDF → Excel Extractor</h1>

      <form onSubmit={handleUpload} style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
        <input type="file" accept="application/pdf" onChange={onFileChange} />
        <button type="submit" disabled={busy}>Upload & Extract</button>
        <button type="button" onClick={listOutput} disabled={busy}>Show Output Folder</button>
      </form>

      {message && <p style={{ marginTop: "1rem" }}>{message}</p>}

      {files.length > 0 && (
        <ul style={{ marginTop: "1rem" }}>
          {files.map((name) => (
            <li key={name}>
              <a href={`${API_BASE}/output/${encodeURIComponent(name)}`} target="_blank" rel="noreferrer">
                {name}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}