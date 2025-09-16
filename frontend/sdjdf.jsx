import { useState } from "react";


const onSubmit = async (e) => {
e.preventDefault();
setStatus("Uploading …");
if (!file) { setStatus("Pick a PDF first."); return; }


const form = new FormData();
form.append("file", file);


try {
const res = await fetch(`${API}/upload`, { method: "POST", body: form });
const data = await res.json();
if (!data.ok) {
setStatus(`Error: ${data.error || data.message}`);
} else if (data.records === 0) {
setStatus("Uploaded, but no records found in that PDF.");
} else {
const link = `${API}${data.excel_url}`;
setStatus(`Done. ${data.records} rows written. `);
// refresh outputs list after successful upload
await fetchOutputs();
// Optionally open the file automatically:
// window.open(link, "_blank");
}
} catch (err) {
setStatus(`Network or server error: ${err.message}`);
}
};


const fetchOutputs = async () => {
setLoadingOutputs(true);
try {
const res = await fetch(`${API}/outputs`);
const data = await res.json();
if (data.ok) {
setOutputs(data.files || []);
} else {
setOutputs([]);
}
} catch (e) {
setOutputs([]);
} finally {
setLoadingOutputs(false);
}
};


return (
<div style={{ maxWidth: 620, margin: "2rem auto", fontFamily: "system-ui, sans-serif" }}>
<h1>PDF → Excel Extractor</h1>


<form onSubmit={onSubmit}>
<input
type="file"
accept="application/pdf"
onChange={(e) => setFile(e.target.files?.[0] || null)}
/>
<div style={{ marginTop: 12, display: "flex", gap: 8 }}>
<button type="submit">Upload & Extract</button>
<button type="button" onClick={fetchOutputs}>
{loadingOutputs ? "Loading…" : "Show Output Folder"}
</button>
</div>
</form>


{status && <p style={{ marginTop: 16 }}>{status}</p>}


<hr style={{ margin: "1rem 0" }} />


<h2 style={{ marginBottom: 8 }}>Output Files</h2>
{outputs.length === 0 ? (
<p style={{ opacity: 0.8 }}>No Excel files yet. Click “Show Output Folder”.</p>
) : (
<ul>
{outputs.map((f) => (
<li key={f.url} style={{ marginBottom: 6 }}>
}