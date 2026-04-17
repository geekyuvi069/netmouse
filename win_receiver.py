"""
NetMouse Lite - Windows Receiver (Standalone)

Drop this ONE file on your Windows machine and run it.
It receives mouse commands from your Linux machine and moves the Windows cursor.

Usage:
  python win_receiver.py

That's it. No other files needed on Windows.
"""

import socket
import threading
import time
import sys

# ─── CONFIG (edit these) ────────────────────────────────────────
PORT = 5050              # Must match Linux side
BUFFER_SIZE = 4096
# ────────────────────────────────────────────────────────────────

try:
    from pynput.mouse import Controller as MouseController, Button
    from pynput.keyboard import Controller as KeyboardController, Key
except ImportError:
    print("ERROR: pynput not installed.")
    print("Run:  pip install pynput")
    sys.exit(1)


mouse = MouseController()
keyboard = KeyboardController()

LINUX_KEY_MAP = {
    'KEY_SPACE': Key.space,
    'KEY_ENTER': Key.enter,
    'KEY_BACKSPACE': Key.backspace,
    'KEY_TAB': Key.tab,
    'KEY_ESC': Key.esc,
    'KEY_LEFTSHIFT': Key.shift,
    'KEY_RIGHTSHIFT': Key.shift_r,
    'KEY_LEFTCTRL': Key.ctrl,
    'KEY_RIGHTCTRL': Key.ctrl_r,
    'KEY_LEFTALT': Key.alt,
    'KEY_RIGHTALT': Key.alt_gr,
    'KEY_LEFTMETA': Key.cmd,
    'KEY_RIGHTMETA': Key.cmd_r,
    'KEY_DELETE': Key.delete,
    'KEY_CAPSLOCK': Key.caps_lock,
    'KEY_UP': Key.up,
    'KEY_DOWN': Key.down,
    'KEY_LEFT': Key.left,
    'KEY_RIGHT': Key.right,
    'KEY_F1': Key.f1, 'KEY_F2': Key.f2, 'KEY_F3': Key.f3, 'KEY_F4': Key.f4,
    'KEY_F5': Key.f5, 'KEY_F6': Key.f6, 'KEY_F7': Key.f7, 'KEY_F8': Key.f8,
    'KEY_F9': Key.f9, 'KEY_F10': Key.f10, 'KEY_F11': Key.f11, 'KEY_F12': Key.f12,
}

SYMBOL_MAP = {
    'KEY_MINUS': '-', 'KEY_EQUAL': '=', 'KEY_LEFTBRACE': '[', 'KEY_RIGHTBRACE': ']',
    'KEY_BACKSLASH': '\\', 'KEY_SEMICOLON': ';', 'KEY_APOSTROPHE': "'",
    'KEY_GRAVE': '`', 'KEY_COMMA': ',', 'KEY_DOT': '.', 'KEY_SLASH': '/'
}

def map_key(linux_key):
    if linux_key in LINUX_KEY_MAP: return LINUX_KEY_MAP[linux_key]
    if linux_key in SYMBOL_MAP: return SYMBOL_MAP[linux_key]
    # Standard letters/numbers (e.g. KEY_A -> a)
    base = linux_key.replace('KEY_', '').lower()
    if len(base) == 1: return base
    return None


def process_message(raw, conn=None):
    """Parse and execute a single command."""
    raw = raw.strip()
    if not raw:
        return

    parts = raw.split(':')
    msg_type = parts[0]

    try:
        # Mouse move (relative delta)
        if msg_type == 'M' and len(parts) >= 3:
            dx, dy = int(parts[1]), int(parts[2])
            mouse.move(dx, dy)
            
            # Edge-Return logic: if mouse hits Left Edge (x=0), jump back to Linux
            if mouse.position[0] <= 0 and conn:
                try:
                    conn.sendall(b"SW:release\n")
                    print("  ⬅ Edge Jump: Returning control to Linux")
                except Exception:
                    pass

        # Click
        elif msg_type == 'C' and len(parts) >= 3:
            btn_map = {'l': Button.left, 'r': Button.right, 'm': Button.middle}
            btn = btn_map.get(parts[1], Button.left)
            if parts[2] == 'p':
                mouse.press(btn)
            else:
                mouse.release(btn)

        # Scroll
        elif msg_type == 'S' and len(parts) >= 3:
            dx, dy = int(parts[1]), int(parts[2])
            mouse.scroll(dx, dy)

        # Ping → respond with Pong
        elif msg_type == 'P':
            return "PO:\n"

        # Switch notification
        elif msg_type == 'SW' and len(parts) >= 2:
            if parts[1] == 'activate':
                print("  ⬅ Linux is controlling this sys")
            elif parts[1] == 'deactivate':
                print("  ⬅ Linux released control")
                
        # Keyboard press
        elif msg_type == 'K' and len(parts) >= 3:
            target = map_key(parts[1])
            if target:
                if parts[2] == '1':
                    keyboard.press(target)
                elif parts[2] == '0':
                    keyboard.release(target)

    except (ValueError, IndexError):
        pass  # Ignore corrupted packets

    return None


def handle_client(conn, addr):
    """Handle one connection from Linux."""
    print(f"✓ Linux connected: {addr[0]}")
    recv_buffer = ""

    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                print("✗ Linux disconnected.")
                break

            recv_buffer += data.decode('utf-8', errors='ignore')

            # Process complete messages (newline-delimited)
            while '\n' in recv_buffer:
                line, recv_buffer = recv_buffer.split('\n', 1)
                response = process_message(line, conn=conn)
                if response:
                    try:
                        conn.sendall(response.encode('utf-8'))
                    except Exception:
                        pass

        except ConnectionResetError:
            print("✗ Connection reset.")
            break
        except Exception as e:
            print(f"⚠ Error: {e}")
            break

    conn.close()


def main():
    print("╔══════════════════════════════════════════╗")
    print("║   NetMouse Lite - Windows Receiver       ║")
    print("║   Waiting for Linux to connect...        ║")
    print("╚══════════════════════════════════════════╝")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(1)

    # Show local IPs for easy setup
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
        print(f"\n  Windows IP: {local_ip}")
    except Exception:
        print(f"\n  Hostname: {hostname}")
    print(f"  Port: {PORT}")
    print(f"\n  On Linux, open terminal and run:")
    print(f"  netmouse\n")

    while True:
        try:
            conn, addr = server.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Handle in thread so server keeps listening after disconnect
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            print("\nShutting down.")
            break

    server.close()


if __name__ == '__main__':
    main()
