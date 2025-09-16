import { useState } from "react";



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
<a href={`${API}${f.url}`} target="_blank" rel="noreferrer">
{f.filename}
</a>
<span style={{ marginLeft: 8, opacity: 0.7 }}>
• {fmtBytes(f.size_bytes)} • {new Date(f.modified_ts * 1000).toLocaleString()}
</span>
</li>
))}
</ul>
)}


<p style={{ marginTop: 8 }}>
API health: <a href={`${API}/health`} target="_blank" rel="noreferrer">/health</a>
</p>
</div>
);