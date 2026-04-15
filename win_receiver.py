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
except ImportError:
    print("ERROR: pynput not installed.")
    print("Run:  pip install pynput")
    sys.exit(1)


mouse = MouseController()


def process_message(raw):
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
                print("  ⬅ Linux is controlling this cursor")
            elif parts[1] == 'deactivate':
                print("  ⬅ Linux released control")

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
                response = process_message(line)
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
