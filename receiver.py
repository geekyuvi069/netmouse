"""
NetMouse Lite - Universal Receiver (Mac & Windows)

Drop this ONE file on your Mac or Windows machine and run it.
It receives mouse/keyboard commands from Linux and controls this machine.

Usage:
  python3 receiver.py          (Mac / Linux)
  python  receiver.py          (Windows)

That's it. No other files needed.
"""

import socket
import threading
import time
import sys
import platform

# ─── CONFIG (edit these) ────────────────────────────────────────
PORT = 5050
BUFFER_SIZE = 4096
# ────────────────────────────────────────────────────────────────

# Auto-detect OS — no manual prompt needed
OS = platform.system()   # "Darwin" for Mac, "Windows" for Windows

try:
    from pynput.mouse import Controller as MouseController, Button
    from pynput.keyboard import Controller as KeyboardController, Key
except ImportError:
    print("ERROR: pynput not installed.")
    if OS == "Windows":
        print("Run:  pip install pynput")
    else:
        print("Run:  pip3 install pynput")
    input("\nPress Enter to exit...")
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
    base = linux_key.replace('KEY_', '').lower()
    if len(base) == 1: return base
    return None


def get_local_ip():
    """Reliably get the local LAN IP on Mac, Windows, and Linux."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


def check_mac_accessibility():
    """
    On Mac, pynput needs Accessibility access to control the mouse/keyboard.
    Try a harmless mouse.position read — if it fails, accessibility is blocked.
    """
    if OS != "Darwin":
        return
    try:
        _ = mouse.position
    except Exception:
        print("\n  !! Accessibility permission required !!")
        print("  Go to: System Settings → Privacy & Security → Accessibility")
        print("  Add Terminal (or your Python app) and enable it.")
        print("  Then restart this script.\n")
        input("Press Enter to exit...")
        sys.exit(1)


def process_message(raw, conn=None):
    """Parse and execute a single command."""
    raw = raw.strip()
    if not raw:
        return None

    parts = raw.split(':')
    msg_type = parts[0]

    try:
        # Mouse move (relative delta)
        if msg_type == 'M' and len(parts) >= 3:
            dx, dy = int(parts[1]), int(parts[2])
            mouse.move(dx, dy)

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

        # Ping -> respond with Pong
        elif msg_type == 'P':
            return "PO:\n"

        # Switch notification
        elif msg_type == 'SW' and len(parts) >= 2:
            if parts[1] == 'activate':
                print("  <- Linux is now controlling this machine")
            elif parts[1] == 'deactivate':
                print("  <- Linux released control")

        # Keyboard press/release
        elif msg_type == 'K' and len(parts) >= 3:
            target = map_key(parts[1])
            if target:
                if parts[2] == '1':
                    keyboard.press(target)
                elif parts[2] == '0':
                    keyboard.release(target)

    except Exception:
        pass

    return None


def handle_client(conn, addr):
    """Handle one Linux connection."""
    print(f"\n  + Linux connected: {addr[0]}")
    recv_buffer = ""

    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                print("  - Linux disconnected.")
                break

            recv_buffer += data.decode('utf-8', errors='ignore')

            while '\n' in recv_buffer:
                line, recv_buffer = recv_buffer.split('\n', 1)
                response = process_message(line, conn=conn)
                if response:
                    try:
                        conn.sendall(response.encode('utf-8'))
                    except Exception:
                        pass

        except ConnectionResetError:
            print("  - Connection reset.")
            break
        except Exception as e:
            print(f"  ! Error: {e}")
            break

    conn.close()


def main():
    check_mac_accessibility()

    local_ip = get_local_ip()

    if OS == "Darwin":
        os_label = "Mac"
        firewall_note = (
            "  Firewall: System Settings -> Network -> Firewall\n"
            "            Make sure it allows incoming connections on port " + str(PORT)
        )
    elif OS == "Windows":
        os_label = "Windows"
        firewall_note = (
            "  Firewall: If prompted by Windows Defender, click 'Allow access'"
        )
    else:
        os_label = OS
        firewall_note = ""

    print("=" * 46)
    print(f"   NetMouse Lite - {os_label} Receiver")
    print("   Waiting for Linux to connect...")
    print("=" * 46)
    print(f"\n  Your IP address:  {local_ip}")
    print(f"  Port:             {PORT}")
    if firewall_note:
        print(f"\n{firewall_note}")
    print(f"\n  On Linux, run:")
    print(f"  netmouse --ip {local_ip}\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(1)

    print("  Listening... (Ctrl+C to quit)\n")

    while True:
        try:
            conn, addr = server.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except KeyboardInterrupt:
            print("\n  Shutting down.")
            break

    server.close()


if __name__ == '__main__':
    main()
