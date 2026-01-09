# ARCHIV-IT Installation Guide

> Personal Archive for Artists
>
> **Start here:** Open `WELCOME_TESTERS.html` in your browser for the complete overview.

---

## Requirements

- **Mac** (Intel or Apple Silicon)
- **Python 3.10+** (check: `python3 --version`)
- **8GB RAM** minimum
- **5GB disk space**

---

## Install

### Step 1: Download

Unzip the ARCHIV-IT folder wherever you want.

### Step 2: Open Terminal

Press `Cmd + Space`, type `Terminal`, hit Enter.

### Step 3: Navigate to folder

```bash
cd /path/to/ARCHIVIT_01
```

Replace `/path/to/` with actual location.

**Tip:** Type `cd ` then drag the folder into Terminal.

### Step 4: Run installer

```bash
./install.sh
```

Wait for dependencies to install (2-5 minutes).

### Step 5: Start server

```bash
./start_server.sh
```

### Step 6: Open browser

Go to: **http://localhost:5001**

---

## Features to Test

| Feature | URL | What it does |
|---------|-----|--------------|
| Gallery | `/` | Browse your archive |
| Semantic Network | `/semantic-network` | 3D force-directed graph of connections |
| Tag Network | `/tag-cloud` | Interactive tag visualization |
| Point Cloud | `/point-cloud` | 5 different 3D visualization paradigms |
| Visual Translator | `/visual-translator` | AI-powered image analysis |
| Add Content | `/add-content` | Import from URLs with image extraction |
| Search | `/search` | Semantic search across your archive |
| Blockchain Tracker | `/blockchain-tracker` | Track NFT holdings and provenance |

---

## Importing Content

### From URL
1. Go to `/add-content`
2. Paste any URL
3. Check "Extract images" if wanted
4. Click Import

### From Google Drive (optional)
1. Go to `/setup`
2. Connect Google Drive
3. Select folder to sync

---

## Stopping the Server

Press `Ctrl + C` in Terminal.

---

## Troubleshooting

### "command not found"
```bash
chmod +x install.sh start_server.sh
```

### "port already in use"
```bash
lsof -ti:5001 | xargs kill -9
```

### Python not found
Install from: https://www.python.org/downloads/

### Still stuck?
Contact Gisel directly.

---

## iPad / Mobile Testing

ARCHIV-IT can be accessed from iPad or other devices on your local network.

### Setup

1. Start the server on your Mac:
   ```bash
   ./start_server.sh
   ```

2. Note the **NETWORK** URL shown in the terminal:
   ```
   NETWORK: http://192.168.x.x:5001
   ```

3. On your iPad, open Safari and enter that URL.

### Requirements

- iPad and Mac must be on the **same WiFi network**
- Mac firewall must allow incoming connections on port 5001
- Keep the Mac terminal running while testing

### Best Features for iPad

| Feature | Why it works well |
|---------|-------------------|
| `/semantic-network` | Touch to rotate 3D graph |
| `/edition-constellation` | Spatial visualization designed for touch |
| `/point-cloud` | Immersive 3D experience |
| `/visual-translator-v2` | Visual Grid with swipe navigation |

### Touch Controls

- **Drag** - Rotate 3D views
- **Pinch** - Zoom in/out
- **Tap** - Select nodes or items
- **Swipe** - Navigate between items

### Troubleshooting iPad Connection

**Can't connect?**
1. Check both devices are on same WiFi
2. Try disabling Mac firewall temporarily
3. Verify the IP address is correct (run `ipconfig getifaddr en0` on Mac)

---

## After Testing

Please fill out **TESTER_FEEDBACK.md** with your experience.
