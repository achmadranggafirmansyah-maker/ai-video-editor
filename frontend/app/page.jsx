"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [file, setFile] = useState(null);
  const [brief, setBrief] = useState("");
  const [style, setStyle] = useState("reference_fast_storytelling");
  const [aspect, setAspect] = useState("9:16");
  const [resolution, setResolution] = useState("1080p");
  const [job, setJob] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const timer = useRef(null);

  useEffect(() => () => clearInterval(timer.current), []);

  async function processVideo() {
    setError("");
    if (!file) return setError("Pilih video terlebih dahulu.");
    if (file.size > 1024 * 1024 * 1024) return setError("Maksimal ukuran video 1 GB.");

    const fd = new FormData();
    fd.append("video", file);
    fd.append("brief", brief);
    fd.append("style", style);
    fd.append("aspect_ratio", aspect);
    fd.append("resolution", resolution);

    setBusy(true);
    try {
      const r = await fetch(`${API}/api/jobs`, { method: "POST", body: fd });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Gagal membuat job.");
      poll(data.job_id);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  function poll(id) {
    clearInterval(timer.current);
    const tick = async () => {
      const r = await fetch(`${API}/api/jobs/${id}`);
      const data = await r.json();
      setJob(data);
      if (data.status === "completed" || data.status === "failed") {
        clearInterval(timer.current);
        setBusy(false);
        if (data.status === "failed") setError(data.error || "Processing gagal.");
      }
    };
    tick();
    timer.current = setInterval(tick, 1500);
  }

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <div className="eyebrow">AI VIDEO EDITOR</div>
          <h1>Turn raw footage into social-ready video.</h1>
          <p className="sub">Upload footage, tell the editor what you want, choose a style, and render.</p>
        </div>
        <div className="status"><span /> Ready</div>
      </section>

      <section className="grid">
        <div className="card">
          <label>01 · Raw video</label>
          <div className="drop">
            <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <div className="uploadIcon">↑</div>
            <strong>{file ? file.name : "Drop your video here"}</strong>
            <small>MP4, MOV, WebM, MKV · max 5 minutes / 1 GB</small>
          </div>
        </div>

        <div className="card">
          <label>02 · Editing brief</label>
          <textarea value={brief} onChange={(e) => setBrief(e.target.value)}
            placeholder="Contoh: Buat hook sekuat mungkin di 3 detik pertama, potong jeda yang tidak penting, tonjolkan kalimat penting, dan akhiri dengan CTA yang natural." />
        </div>

        <div className="card full">
          <label>03 · Editing style</label>
          <div className="options">
            <button className={style === "reference_fast_storytelling" ? "selected" : ""} onClick={() => setStyle("reference_fast_storytelling")}>
              <b>Reference — Fast Storytelling</b><span>Fast cuts · punch-ins · emphasis · social captions</span>
            </button>
            <button className={style === "clean_creator" ? "selected" : ""} onClick={() => setStyle("clean_creator")}>
              <b>Clean Creator</b><span>Clean pacing · subtle zoom · minimal emphasis</span>
            </button>
          </div>
        </div>

        <div className="card">
          <label>04 · Aspect ratio</label>
          <div className="seg">
            {["9:16", "1:1", "16:9"].map(x => <button key={x} className={aspect === x ? "selected" : ""} onClick={() => setAspect(x)}>{x}</button>)}
          </div>
        </div>

        <div className="card">
          <label>05 · Output resolution</label>
          <div className="seg">
            {["720p", "1080p", "4K"].map(x => <button key={x} className={resolution === x ? "selected" : ""} onClick={() => setResolution(x)}>{x}</button>)}
          </div>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      <button className="process" disabled={busy} onClick={processVideo}>
        {busy ? `Processing ${job?.progress || 0}%` : "Process video →"}
      </button>

      {job && (
        <section className="result card">
          <label>06 · Result</label>
          {job.status === "completed" ? (
            <>
              <video controls src={`${API}/api/jobs/${job.id}/download`} />
              <a className="download" href={`${API}/api/jobs/${job.id}/download`}>Download MP4 ↓</a>
            </>
          ) : (
            <div className="progressBox">
              <strong>{job.status === "failed" ? "Render failed" : "Rendering your video…"}</strong>
              <div className="bar"><i style={{ width: `${job.progress || 0}%` }} /></div>
              <span>{job.progress || 0}%</span>
            </div>
          )}
        </section>
      )}

      <footer>AI Video Editor · Vercel + Render + R2 architecture</footer>
    </main>
  );
}
