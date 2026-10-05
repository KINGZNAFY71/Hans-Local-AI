# Local Python AI Agent with Ollama & iOS Network Access

This repository contains a local Python AI Agent built with **Pydantic AI** and powered by **Ollama**. It is configured to run locally on your Windows PC and expose its inference endpoint across your local Wi-Fi network so you can interact with it directly from your iPhone (via iOS clients like **Enchanted** or **Reins**).

---

## 1. Architecture Overview

```
+--------------------------------------------------------------------------+
|                     Your Local Wi-Fi Network (LAN)                       |
|                                                                          |
|   +--------------------------+           +---------------------------+   |
|   |  iPhone Client           |           |  Other Local Devices      |   |
|   |  - Enchanted (App Store) |           |  (iPad, Mac, Browser)     |   |
|   |  - Reins                 |           |                           |   |
|   +------------+-------------+           +-------------+-------------+   |
|                |                                       |                 |
|                |  HTTP Requests to port 11434          |                 |
|                +-------------------+-------------------+                 |
|                                    |                                     |
|   Windows Host Machine             v                                     |
|   +------------------------------------------------------------------+   |
|   | Windows Defender Firewall: Inbound TCP 11434 Allowed             |   |
|   |                                                                  |   |
|   | Ollama Daemon: Bound to OLLAMA_HOST=0.0.0.0:11434                |   |
|   | Model: qwen2.5:latest (or llama3.2:latest)                       |   |
|   |                                                                  |   |
|   | Local Python AI Agent (`agent.py`)                               |   |
|   |   - Framework: Pydantic AI (Ollama/OpenAI compatible /v1)        |   |
|   |   - Interactive terminal REPL with session memory                |   |
|   |   - Integrated Tools:                                            |   |
|   |       1. `get_system_time`   (System timestamp & timezone)       |   |
|   |       2. `calculate`         (Safe AST math evaluator)           |   |
|   |       3. `save_note`         (Writes markdown to ./notes/)       |   |
|   |       4. `read_note`         (Reads markdown from ./notes/)      |   |
|   |       5. `list_notes`        (Lists notes in directory)          |   |
|   +------------------------------------------------------------------+   |
+--------------------------------------------------------------------------+
```

---

## 2. Quickstart Checklist

- [ ] **Python 3.10+** and **Ollama** installed on your Windows PC.
- [ ] Pull target model: `ollama pull qwen2.5` (or `llama3.2`).
- [ ] Bind Ollama to `0.0.0.0:11434` and configure Windows Firewall.
- [ ] Find your PC's local Wi-Fi IPv4 address (e.g. `192.168.1.50`).
- [ ] Connect your iPhone to the same Wi-Fi and configure Enchanted / Reins.
- [ ] Launch `python agent.py` to test the terminal AI Agent.

---

## 3. Step 1: Install Prerequisites (Windows)

If you haven't installed Python or Ollama yet, open **PowerShell** and run:

### Install Python & Ollama via Winget:
```powershell
winget install -e --id Python.Python.3.12
winget install -e --id Ollama.Ollama
```
*(Alternatively, download the official installer directly from [ollama.com/download/windows](https://ollama.com/download/windows)).*

After installation, close and reopen your PowerShell terminal.

---

## 4. Step 2: Download Your Preferred Local Model

Choose a lightweight, high-performance model suitable for tool calling and reasoning:

```powershell
# Recommended: Qwen 2.5 (strong reasoning and tool-calling capabilities)
ollama pull qwen2.5

# Alternative: Llama 3.2 (Meta's lightweight model)
ollama pull llama3.2
```

---

## 5. Step 3: Configure Ollama to Bind to `0.0.0.0` (Local Network Access)

By default, Ollama only listens on `127.0.0.1` (localhost). To accept connections from your iPhone on the same Wi-Fi, it must bind to `0.0.0.0:11434`.

### Option A: Use the Provided Helper Script (Recommended for Quick Runs)
Run the bundled PowerShell script:
```powershell
.\start_ollama.ps1
```
This script sets `OLLAMA_HOST=0.0.0.0:11434`, sets CORS headers `OLLAMA_ORIGINS=*`, checks your firewall, displays your local IP, and launches the server.

### Option B: Make It Permanent Across Windows Restarts
To make Ollama always bind to `0.0.0.0` whenever your computer starts:
1. Open PowerShell and run:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
   [System.Environment]::SetEnvironmentVariable('OLLAMA_ORIGINS', '*', 'User')
   ```
2. Quit the Ollama tray icon in your Windows taskbar (right-click Ollama in the system tray -> **Quit Ollama**).
3. Relaunch Ollama from the Windows Start menu.

### Open Inbound Port 11434 in Windows Firewall
Open an **Administrator PowerShell** window and run:
```powershell
New-NetFirewallRule -DisplayName "Ollama Local Network Access" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```

---

## 6. Step 4: Find Your Laptop's Local IPv4 Address

To connect from your iPhone, you need the laptop's Wi-Fi IP address.

### Method 1: Run the Built-in Diagnostic Script
```powershell
python test_connection.py
```
This script automatically scans your network adapters and displays:
```
[1] Detecting Laptop Local Network (IPv4) Addresses:
    - Wi-Fi / LAN IP: http://192.168.1.85:11434

    Use this address on your iPhone: http://192.168.1.85:11434
```

### Method 2: Standard Windows Command
Run `ipconfig` in PowerShell:
```powershell
ipconfig
```
Look for **Wireless LAN adapter Wi-Fi** -> **IPv4 Address** (e.g. `192.168.1.85`).

---

## 7. Step 5: Configure Your Mobile iOS Client (iPhone)

Make sure your iPhone is connected to the **same Wi-Fi network** as your laptop.

### Test in iPhone Safari First:
1. Open Safari on your iPhone.
2. Navigate to: `http://<laptop-ip>:11434` (e.g. `http://192.168.1.85:11434`).
3. You should see a simple webpage stating:
   ```
   Ollama is running
   ```
   *(If it loads, your network binding and firewall are configured perfectly!)*

### Option A: Setup in "Enchanted" (Recommended App)
1. Download **[Enchanted](https://apps.apple.com/app/enchanted-llm/id6474381920)** for free from the iOS App Store.
2. Open **Enchanted** on your iPhone.
3. Tap the **Settings** gear icon.
4. Under **Ollama Server** / **Host URL**, enter:
   ```
   http://192.168.1.85:11434
   ```
   *(Replace `192.168.1.85` with your actual laptop IP).*
5. Tap **Refresh Models**. Your pulled models (`qwen2.5:latest` or `llama3.2`) will appear in the list.
6. Select your model and begin chatting with zero latency from your iPhone!

### Option B: Setup in "Reins"
1. Install **Reins** from the App Store.
2. Go to **Settings** -> **Add Provider** -> **Ollama**.
3. Set the Endpoint URL to `http://<laptop-ip>:11434`.
4. Tap **Connect** and select the active model.

---

## 8. Step 6: Run the Local Python AI Agent

### 1. Set Up Python Virtual Environment:
```powershell
# Navigate to this project folder
cd c:\xampp\htdocs\KINGZ

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`):
Check the `.env` file to ensure the model name matches what you pulled:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest
NOTES_DIR=./notes
```

### 3. Launch the Agent:
```powershell
python agent.py
```

---

## 9. Step 7: Interacting with the Agent & Local Tools

Once launched, the interactive REPL will appear:

```
=================================================================
      LOCAL PYTHON AI AGENT (Ollama + Pydantic AI)
=================================================================
  * Ollama Host : http://localhost:11434
  * Active Model: qwen2.5:latest
  * Notes Folder: C:\xampp\htdocs\KINGZ\notes
-----------------------------------------------------------------
  Special Commands:
    /help   - Show available commands and tool information
    /tools  - List available local tools
    /clear  - Clear conversation history
    /notes  - List markdown notes in ./notes/
    exit    - Quit the agent loop
=================================================================

You > What is today's date and the current system time?
```

### Try These Prompt Examples to Test Local Tools:

| Tool | Prompt Example | What Happens |
| :--- | :--- | :--- |
| **System Time** | `"What is the current time and day of the week?"` | Agent calls `get_system_time()` and reports exact local timestamp. |
| **Safe Calculator** | `"Calculate (145 * 28) + (sqrt(144) * 10)"` | Agent evaluates the math via AST without security vulnerabilities. |
| **Save Markdown Note** | `"Save a note titled 'Kingz Project' with summary of our network setup."` | Agent creates `notes/kingz_project.md` with headers and timestamp. |
| **List Notes** | `"What notes do I have saved?"` | Agent lists all notes in `./notes/`. |
| **Read Note** | `"Read the note titled Kingz Project"` | Agent reads and presents the markdown content. |

---

## 10. Troubleshooting & Common Issues

| Symptom | Probable Cause | Fix |
| :--- | :--- | :--- |
| **iPhone says "Connection Refused" or timed out** | Ollama is still running on `127.0.0.1` or blocked by Firewall. | 1. Run `.\start_ollama.ps1` to ensure `OLLAMA_HOST=0.0.0.0:11434`.<br>2. Run the Firewall rule command in Admin PowerShell.<br>3. Verify by opening `http://<laptop-ip>:11434` in iPhone Safari. |
| **iPhone can't reach laptop IP, but laptop can** | "AP Isolation" or "Guest Network" enabled on your Wi-Fi router. | Log into your Wi-Fi router and disable **AP Isolation / Client Isolation**, or ensure both devices are connected to the main Wi-Fi (not Guest Wi-Fi). |
| **Laptop IP changed** | DHCP assigned a new IP address to your laptop. | Run `python test_connection.py` to see your new IP, then update the URL in your iPhone app. (You can also set a DHCP static reservation in your router). |
| **`python agent.py` says model not found** | Model hasn't been pulled in Ollama. | Run `ollama pull qwen2.5:latest` or update `OLLAMA_MODEL` in `.env`. |
| **Windows Network Profile is Public** | Windows Firewall blocks inbound connections on Public networks. | In Windows Settings -> **Network & Internet** -> **Wi-Fi** -> Click your network name and set **Network Profile Type** to **Private**. |
#   H a n s - L o c a l - A I  
 