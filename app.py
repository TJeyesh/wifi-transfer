import streamlit as st
import socket
import os
import io
import time
import datetime
import qrcode
import threading
import http.server
import socketserver
from pathlib import Path
import json
from urllib.parse import quote, unquote

# ── Configuration ────────────────────────────────────────────────────────────
SHARED_DIR = Path(__file__).parent / "static"
SHARED_DIR.mkdir(exist_ok=True)

def _get_upload_html():
    """Return the standalone fast-upload HTML page."""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>WiFi Transfer - Fast Upload</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Inter",sans-serif;background:#0f0f1a;color:#e2e8f0;min-height:100vh;padding:1.5rem}
.container{max-width:560px;margin:0 auto}
h1{text-align:center;font-size:1.8rem;font-weight:700;
   background:linear-gradient(135deg,#6366f1,#a855f7,#ec4899);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.35rem}
.subtitle{text-align:center;color:#94a3b8;font-size:.88rem;margin-bottom:1.8rem}
.drop-zone{border:2px dashed rgba(99,102,241,.4);border-radius:16px;padding:3rem 2rem;
  text-align:center;cursor:pointer;transition:all .3s ease;
  background:rgba(30,30,46,.5);margin-bottom:1.5rem}
.drop-zone:hover,.drop-zone.dragover{border-color:#6366f1;background:rgba(99,102,241,.08);
  box-shadow:0 0 30px rgba(99,102,241,.1)}
.drop-zone .icon{font-size:3rem;margin-bottom:.75rem}
.drop-zone .text{color:#94a3b8;font-size:.95rem;line-height:1.6}
.drop-zone .browse{color:#a78bfa;text-decoration:underline;cursor:pointer}
#fileInput{display:none}
.upload-item{background:rgba(30,30,46,.65);border:1px solid rgba(99,102,241,.15);
  border-radius:12px;padding:1rem 1.25rem;margin-bottom:.75rem;
  animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}
.upload-item .filename{font-weight:500;margin-bottom:.2rem;word-break:break-all}
.upload-item .info{font-size:.78rem;color:#94a3b8;margin-bottom:.5rem}
.progress-bar{height:6px;background:rgba(99,102,241,.15);border-radius:3px;overflow:hidden;margin-bottom:.35rem}
.progress-fill{height:100%;background:linear-gradient(90deg,#6366f1,#a855f7);border-radius:3px;
  transition:width .15s ease;width:0%}
.progress-fill.done{background:linear-gradient(90deg,#22c55e,#4ade80)}
.progress-fill.error{background:linear-gradient(90deg,#ef4444,#f87171)}
.row{display:flex;justify-content:space-between;align-items:center}
.status{font-size:.8rem;color:#94a3b8}
.status.done{color:#4ade80}.status.error{color:#f87171}
.speed{font-size:.8rem;color:#a78bfa}
.back-link{display:block;text-align:center;margin-top:2rem;color:#94a3b8;font-size:.82rem}
.back-link a{color:#a78bfa;text-decoration:none}
.back-link a:hover{text-decoration:underline}
</style>
</head>
<body>
<div class="container">
  <h1>&#9889; Fast Upload</h1>
  <p class="subtitle">Direct HTTP upload &#183; Bypasses Streamlit for maximum speed</p>
  <div class="drop-zone" id="dropZone">
    <div class="icon">&#128193;</div>
    <div class="text">Drag & drop files here<br>or <span class="browse">browse to select</span></div>
  </div>
  <input type="file" id="fileInput" multiple>
  <div id="uploadList"></div>
  <div class="back-link"><a href="/">&#8592; Back to file list</a></div>
</div>
<script>
const dropZone=document.getElementById("dropZone");
const fileInput=document.getElementById("fileInput");
const uploadList=document.getElementById("uploadList");

dropZone.addEventListener("click",()=>fileInput.click());
dropZone.addEventListener("dragover",e=>{e.preventDefault();dropZone.classList.add("dragover")});
dropZone.addEventListener("dragleave",()=>dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop",e=>{e.preventDefault();dropZone.classList.remove("dragover");handleFiles(e.dataTransfer.files)});
fileInput.addEventListener("change",()=>{handleFiles(fileInput.files);fileInput.value=""});

function humanSize(b){const u=["B","KB","MB","GB"];let i=0;
  while(b>=1024&&i<u.length-1){b/=1024;i++}return b.toFixed(1)+" "+u[i]}

function handleFiles(files){for(const f of files)uploadFile(f)}

function uploadFile(file){
  const item=document.createElement("div");
  item.className="upload-item";
  item.innerHTML=`<div class="filename">&#128196; ${file.name}</div>
    <div class="info">${humanSize(file.size)}</div>
    <div class="progress-bar"><div class="progress-fill"></div></div>
    <div class="row"><span class="status">Uploading&#8230;</span><span class="speed"></span></div>`;
  uploadList.prepend(item);
  const pf=item.querySelector(".progress-fill");
  const st=item.querySelector(".status");
  const sp=item.querySelector(".speed");
  const t0=Date.now();
  const xhr=new XMLHttpRequest();
  xhr.open("POST","/upload/"+encodeURIComponent(file.name));
  xhr.upload.onprogress=e=>{
    if(e.lengthComputable){
      const pct=(e.loaded/e.total*100).toFixed(0);
      pf.style.width=pct+"%";
      const elapsed=(Date.now()-t0)/1000;
      if(elapsed>.3){sp.textContent=humanSize(e.loaded/elapsed)+"/s"}
      st.textContent=pct+"%";
    }
  };
  xhr.onload=()=>{
    if(xhr.status===200){
      pf.style.width="100%";pf.classList.add("done");
      const elapsed=(Date.now()-t0)/1000;
      sp.textContent=humanSize(file.size/elapsed)+"/s avg";
      st.textContent="\u2713 Done";st.classList.add("done");
    }else{
      pf.classList.add("error");
      st.textContent="\u2717 Error: "+xhr.statusText;st.classList.add("error");
    }
  };
  xhr.onerror=()=>{pf.classList.add("error");st.textContent="\u2717 Network error";st.classList.add("error")};
  xhr.send(file);
}
</script>
</body></html>'''


@st.cache_resource
def start_file_server(port=8502):
    class Handler(http.server.SimpleHTTPRequestHandler):
        # 256 KB read buffer for faster large file transfers
        rbufsize = 256 * 1024

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(SHARED_DIR), **kwargs)
        def log_message(self, format, *args):
            pass # suppress logging
        def handle(self):
            try:
                super().handle()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # client disconnected mid-transfer — expected
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self):
            """Serve upload page at /upload, files everywhere else."""
            if self.path in ("/upload", "/upload/"):
                html = _get_upload_html().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
            else:
                super().do_GET()

        def do_POST(self):
            """Handle direct file uploads — stream body to disk in 256 KB chunks."""
            if not self.path.startswith("/upload/"):
                self.send_error(404)
                return
            filename = unquote(self.path[len("/upload/"):])
            if not filename or "/" in filename or ".." in filename:
                self.send_error(400, "Invalid filename")
                return
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_error(400, "Empty upload")
                return

            dest = SHARED_DIR / filename
            if dest.exists():
                stem, suffix = dest.stem, dest.suffix
                ts = datetime.datetime.now().strftime("%H%M%S")
                dest = SHARED_DIR / f"{stem}_{ts}{suffix}"

            # Stream directly to disk — no buffering the whole file in RAM
            with open(dest, "wb") as f:
                remaining = content_length
                while remaining > 0:
                    chunk = self.rfile.read(min(remaining, 256 * 1024))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)

            body = json.dumps({"status": "ok", "filename": dest.name}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            """Handle CORS preflight for upload requests."""
            self.send_response(200)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

    # ThreadingTCPServer handles multiple downloads/uploads in parallel
    class ThreadedServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    try:
        httpd = ThreadedServer(("", port), Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return port
    except OSError:
        return port

FILE_SERVER_PORT = start_file_server()

st.set_page_config(
    page_title="WiFi File Transfer",
    page_icon="📡",
    layout="centered",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero header */
    .hero {
        text-align: center;
        padding: 2rem 1rem 1rem;
    }
    .hero h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .hero p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0;
    }

    /* Cards */
    .card {
        background: rgba(30, 30, 46, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
        border-color: rgba(99, 102, 241, 0.45);
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.08);
    }
    .card h3 {
        margin-top: 0;
        font-weight: 600;
        color: #e2e8f0;
    }

    /* Network info box */
    .network-info {
        background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(168,85,247,0.12));
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        text-align: center;
        margin-bottom: 0.75rem;
    }
    .network-info .url {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 1.3rem;
        font-weight: 600;
        color: #a78bfa;
        letter-spacing: 0.02em;
    }
    .network-info .label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.25rem;
    }

    /* File row */
    .file-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background: rgba(30, 30, 46, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 10px;
        margin-bottom: 0.5rem;
        transition: background 0.2s ease;
    }
    .file-row:hover {
        background: rgba(99, 102, 241, 0.08);
    }
    .file-name {
        font-weight: 500;
        color: #e2e8f0;
        word-break: break-all;
    }
    .file-meta {
        color: #94a3b8;
        font-size: 0.82rem;
    }

    /* Status badge */
    .badge-success {
        display: inline-block;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .badge-empty {
        display: inline-block;
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.82rem;
    }

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Upload area tweaks */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    div[data-testid="stFileUploader"] section {
        border: 2px dashed rgba(99, 102, 241, 0.35) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_local_ip() -> str:
    """Return the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def human_size(nbytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def make_qr(url: str):
    """Generate a QR code image for the given URL."""
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#a78bfa", back_color="#0f0f1a")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>📡 WiFi File Transfer</h1>
    <p>Seamlessly share files between devices on the same network</p>
</div>
""", unsafe_allow_html=True)

# ── Network Info ─────────────────────────────────────────────────────────────
local_ip = get_local_ip()
app_url = f"http://{local_ip}:8501"

st.markdown(f"""
<div class="card">
    <h3>🌐 Network Access</h3>
    <div class="network-info">
        <div class="label">Open this URL on any device on the same WiFi</div>
        <div class="url">{app_url}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# QR code in an expander
with st.expander("📱 Show QR Code for quick access"):
    qr_buf = make_qr(app_url)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_buf, caption="Scan to open on your phone", width="stretch")

st.markdown("---")

# ── Upload Section ───────────────────────────────────────────────────────────
fast_upload_url = f"http://{local_ip}:{FILE_SERVER_PORT}/upload"
st.markdown(f"""
<div class="card">
    <h3>⬆️ Upload Files</h3>
    <div style="margin-bottom: 0.75rem;">
        <a href="{fast_upload_url}" target="_blank" style="
            display: inline-block;
            padding: 0.5rem 1.2rem;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            color: #fff;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 600;
            transition: opacity 0.2s ease;
        ">⚡ Open Fast Upload (Direct HTTP)</a>
        <span style="color:#94a3b8; font-size:0.8rem; margin-left:0.5rem;">Bypasses Streamlit · much faster for large files</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("📱 QR Code for Fast Upload"):
    qr_upload = make_qr(fast_upload_url)
    qr_col1, qr_col2, qr_col3 = st.columns([1, 2, 1])
    with qr_col2:
        st.image(qr_upload, caption="Scan to open Fast Upload on your phone", width="stretch")

uploaded_files = st.file_uploader(
    "Drag & drop files here or click to browse",
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    # Track already-saved files to avoid duplicates on rerun
    if "saved_files" not in st.session_state:
        st.session_state.saved_files = set()

    newly_saved = 0
    for uf in uploaded_files:
        file_key = f"{uf.name}_{uf.size}"
        if file_key in st.session_state.saved_files:
            continue
        dest = SHARED_DIR / uf.name
        # Avoid overwriting — append timestamp if file exists
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            ts = datetime.datetime.now().strftime("%H%M%S")
            dest = SHARED_DIR / f"{stem}_{ts}{suffix}"
        dest.write_bytes(uf.getbuffer())
        st.session_state.saved_files.add(file_key)
        newly_saved += 1

    if newly_saved > 0:
        st.markdown(
            f'<span class="badge-success">✓ {newly_saved} file(s) uploaded successfully</span>',
            unsafe_allow_html=True,
        )
    elif len(uploaded_files) > 0:
        st.markdown(
            '<span class="badge-success">✓ Files already saved</span>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Available Files ──────────────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <h3>📂 Available Files</h3>
</div>
""", unsafe_allow_html=True)

files = sorted(SHARED_DIR.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
files = [f for f in files if f.is_file() and not f.name.startswith(".")]

if not files:
    st.markdown(
        '<span class="badge-empty">No files shared yet — upload something above!</span>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<span class="badge-success">{len(files)} file(s) available</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    for fpath in files:
        try:
            stat = fpath.stat()
        except FileNotFoundError:
            continue
        size = human_size(stat.st_size)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y  %I:%M %p")

        col_info, col_dl, col_del = st.columns([5, 1.5, 1])

        with col_info:
            st.markdown(
                f"""
                <div style="padding:4px 0;">
                    <span class="file-name">📄 {fpath.name}</span><br>
                    <span class="file-meta">{size}  ·  {mtime}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_dl:
            if fpath.exists():
                file_url = f"http://{local_ip}:{FILE_SERVER_PORT}/{quote(fpath.name)}"
                st.markdown(
                    f"""
                    <a href="{file_url}" download="{fpath.name}" target="_blank" style="
                        display: block;
                        text-align: center;
                        padding: 0.4rem;
                        background-color: rgba(99, 102, 241, 0.1);
                        color: #a78bfa;
                        border: 1px solid rgba(99, 102, 241, 0.3);
                        border-radius: 6px;
                        text-decoration: none;
                        font-size: 0.9rem;
                        font-weight: 500;
                        transition: background-color 0.2s ease;
                    ">
                        ⬇️ Download
                    </a>
                    """,
                    unsafe_allow_html=True
                )

        with col_del:
            if st.button("🗑️", key=f"rm_{fpath.name}", help=f"Delete {fpath.name}", width="stretch"):
                try:
                    fpath.unlink()
                except FileNotFoundError:
                    pass
                st.rerun()

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; color:#64748b; font-size:0.82rem;">
    Files are stored locally in the <code>static/</code> folder on the host machine.<br>
    Both devices must be on the <strong>same WiFi network</strong>.
</div>
""", unsafe_allow_html=True)
