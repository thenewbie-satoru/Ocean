# 🌊 Ocean — Python Command & Control Framework (Reverse Shell)
> ⚠️ **For Educational & Ethical Use Only**  
> Ocean is a red-team-focused tool for studying C2 infrastructure, RAT behavior, and real-time data streams — to be used only in lab environments or with explicit written permission.

---

## 🔥 What is Ocean?

**Ocean** is a powerful, stealthy, and modular **Python-based C2 (Command and Control)** framework built for ethical hacking, malware simulation, and reverse shell research.

It gives red teamers and cybersecurity learners deep insight into:

- Remote shell access
- Real-time webcam, screen, and mic streaming
- Stealth persistence & obfuscation
- GUI-based multi-client visual control

---

## 🚀 Features

| Module        | Description |
|---------------|-------------|
| 🐚 Reverse Shell | Full interactive command shell from victim |
| 📸 LiveCam      | Webcam feed streamed to operator |
| 🖥️ LiveScreen   | Screen capture and display in real-time |
| 🎙️ LiveMic      | Microphone audio stream with playback |
| 🔕 Stealth Mode | Console hidden, uses `pythonw.exe` |
| 🧠 Persistence  | Adds client to Windows registry for startup |
| 🧩 Modular      | Separate stream modules, can be expanded |
| 🔧 Auto Setup   | Installs required dependencies silently |
| 🧵 Threaded     | Handles multiple client sessions at once |
| 🪟 GUI Viewer   | Tkinter-based image viewer with updates |

---

## 🛠️ Setup

### 🌐 Server (C2)
Run the server to listen for incoming clients and manage live sessions:
```bash
python listener.py
