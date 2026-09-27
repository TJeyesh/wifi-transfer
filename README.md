# WiFi File Transfer 📡

Seamlessly transfer files between devices on the same WiFi network. No cables, no cloud, no accounts — just a URL.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-brightgreen)

## ✨ Features

- **📱 Cross-device** — Share files between your phone, laptop, and desktop
- **⚡ Fast Upload** — Direct HTTP upload endpoint bypasses Streamlit for maximum speed
- **📷 QR Code** — Scan to open on your phone instantly
- **🔒 Local only** — Files never leave your network
- **🎨 Beautiful UI** — Modern dark theme with glassmorphism
- **💻 Cross-platform** — Works on macOS, Windows, and Linux

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/wifi-transfer.git
cd wifi-transfer
```

### 2. Run

**Option A — Python launcher (all platforms):**
```bash
python run.py start
```

**Option B — Shell script (macOS/Linux):**
```bash
chmod +x server.sh
./server.sh start
```

**Option C — Batch file (Windows):**
```
Double-click server.bat
```
Or from Command Prompt:
```cmd
server.bat start
```

That's it! The script will:
1. Create a virtual environment (if needed)
2. Install dependencies automatically
3. Start the server
4. Print the URL to open on other devices

### 3. Transfer files

1. Open the **Network URL** on any device connected to the same WiFi
2. Upload files via drag & drop, or use the **⚡ Fast Upload** for large files
3. Download files from the file list

## 📋 Commands

| Command | Description |
|---------|-------------|
| `python run.py start` | Start the server |
| `python run.py stop` | Stop the server |
| `python run.py restart` | Restart the server |
| `python run.py status` | Check if the server is running |
| `python run.py install` | Install/update dependencies |

Or run `python run.py` with no arguments for an interactive menu.

## 🏗️ Architecture

| Component | Port | Purpose |
|-----------|------|---------|
| Streamlit App | 8501 | Main UI — file list, QR codes, Streamlit uploader |
| File Server | 8502 | Direct HTTP downloads + Fast Upload endpoint |

### Fast Upload (Port 8502)

For large files, the **Fast Upload** page at `http://<your-ip>:8502/upload` bypasses Streamlit entirely:
- Raw HTTP POST — no multipart encoding overhead
- Streams directly to disk in 256 KB chunks
- Multi-threaded — parallel uploads/downloads
- Real-time speed indicator and progress bars

## 📁 Project Structure

```
wifi-transfer/
├── app.py              # Main Streamlit application
├── run.py              # Cross-platform Python launcher
├── server.sh           # macOS/Linux shell script
├── server.bat          # Windows batch script
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── config.toml     # Streamlit configuration
└── static/             # Uploaded files are stored here (git-ignored)
```

## ⚙️ Requirements

- **Python 3.8+** — [Download Python](https://www.python.org/downloads/)
- Both devices must be on the **same WiFi network**

### Windows Notes

- Make sure to check **"Add Python to PATH"** during Python installation
- If you see a Windows Firewall prompt, click **Allow** to let devices connect
- Use `server.bat` for the simplest experience (just double-click)

### macOS Notes

- If macOS blocks the app, go to System Settings → Privacy & Security → Allow
- The server uses ports 8501 and 8502 — make sure they're not in use

## 📄 License

MIT
