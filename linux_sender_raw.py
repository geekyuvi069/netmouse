"""
NetMouse Lite - Linux Sender (Wayland Native using evdev)

This reads directly from hardware /dev/input devices, completely 
bypassing Wayland's security blocks. 

Requires root:
  sudo python3 linux_sender_raw.py --ip <WINDOWS_IP>
"""

import socket
import sys
import argparse
import time
import select

try:
    import evdev
    from evdev import ecodes
except ImportError:
    print("ERROR: python-evdev is required. Run: sudo pip3 install evdev")
    sys.exit(1)

PORT = 5050

class LinuxSenderRaw:
    def __init__(self, windows_ip, enable_keyboard=False):
        self.windows_ip = windows_ip
        self.enable_keyboard = enable_keyboard
        self.sock = None
        self.connected = False
        self.sending = False
        self.running = True
        
        # Find mouse and keyboard devices
        self.mouse_devs = []
        self.keyboard_devs = []
        self._find_devices()

    def _find_devices(self):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for dev in devices:
            # Filter out devices that are obviously audio equipment (headphones/earphones)
            name = dev.name.lower()
            if any(word in name for word in ["audio", "headset", "headphones", "speakers"]):
                continue

            caps = dev.capabilities()
            if ecodes.EV_REL in caps and ecodes.REL_X in caps[ecodes.EV_REL]:
                self.mouse_devs.append(dev)
            if ecodes.EV_KEY in caps and ecodes.KEY_ENTER in caps[ecodes.EV_KEY]:
                # Exclude devices that are just power buttons etc.
                if len(caps[ecodes.EV_KEY]) > 20: 
                    self.keyboard_devs.append(dev)
        
        if not self.mouse_devs:
            print("⚠ Warning: No mice found in /dev/input! Are you running with sudo?")

    def connect(self, retry_sleep=3):
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                # Enable TCP Keep-Alive to prevent silent disconnections
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                print(f"⏳ Connecting to Windows ({self.windows_ip}:{PORT})...")
                self.sock.connect((self.windows_ip, PORT))
                self.connected = True
                print(f"✓ Connected! Press F8 to toggle control ON/OFF.\n")
                return True
            except Exception as e:
                # If we are in a hurry (retry_sleep=0), don't wait for the loop, just return fail
                if retry_sleep == 0:
                    return False
                print(f"✗ Connection failed: {e}. Retrying in {retry_sleep}s...")
                time.sleep(retry_sleep)
        return False

    def send_failsafe_ungrab(self):
        self.sending = False
        for dev in self.mouse_devs + self.keyboard_devs:
            try: dev.ungrab()
            except Exception: pass

    def send(self, msg):
        if not self.connected: return False
        try:
            self.sock.sendall(msg.encode('utf-8'))
            self.last_send_time = time.time()
            return True
        except Exception:
            print("\n⚠ Connection lost! Failsafe triggered: Unlocking all devices.")
            self.connected = False
            self.send_failsafe_ungrab()
            return False

    def start(self):
        banner = """
\033[96m ███╗   ██╗███████╗████████╗███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗
 ████╗  ██║██╔════╝╚══██╔══╝████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝
 ██╔██╗ ██║█████╗     ██║   ██╔████╔██║██║   ██║██║   ██║███████╗█████╗  
 ██║╚██╗██║██╔══╝     ██║   ██║╚██╔╝██║██║   ██║██║   ██║╚════██║██╔══╝  
 ██║ ╚████║███████╗   ██║   ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████╗\033[0m
 
\033[92m ⚡ A high-performance, Wayland-bypassing hardware mouse bridge \033[0m

 \033[93m[ HOW TO USE ]\033[0m
  \033[1m[F8]\033[0m     - Toggle Control ON/OFF (Locks Linux mouse & connects to Windows)
  \033[1m[Ctrl+C]\033[0m - Exit NetMouse securely

 \033[93m[ DETAILS ]\033[0m
  Mode: Direct evdev hardware interception (Wayland immune)
  Port: """ + str(PORT) + """ (TCP)
"""
        print(banner)
        
        if not self.mouse_devs and not self.keyboard_devs:
            print("ERROR: No input devices found. MUST RUN WITH SUDO: sudo python3 linux_sender_raw.py")
            return
            
        if not self.connect():
            return
            
        all_devs = self.mouse_devs + self.keyboard_devs
        fd_to_dev = {dev.fd: dev for dev in all_devs}
        
        dx, dy = 0, 0
        self.last_send_time = time.time()
        
        # Initial FD sync
        all_monitored_fds = list(fd_to_dev.keys())
        if self.sock: all_monitored_fds.append(self.sock.fileno())

        try:
            while self.running:
                if not self.connected:
                    self.connect()
                    # Re-sync fd list if connection was lost/re-established
                    all_monitored_fds = list(fd_to_dev.keys())
                    if self.sock: all_monitored_fds.append(self.sock.fileno())
                    self.last_send_time = time.time()

                # Heartbeat: Send a ping if idle for 10 seconds to keep connection alive
                if self.connected and time.time() - self.last_send_time > 10:
                    self.send("P:\n")

                r, w, x = select.select(all_monitored_fds, [], [], 0.01)
                
                for fd in r:
                    if self.sock and fd == self.sock.fileno():
                        try:
                            data = self.sock.recv(1024).decode('utf-8')
                            if not data:
                                print("\n⚠ Connection closed by Windows.")
                                self.connected = False
                                self.send_failsafe_ungrab()
                                break
                            if "SW:release" in data:
                                if self.sending:
                                    self.sending = False
                                    print("\r\033[K  ◼  OFF:  Back to Linux (Edge Jump)")
                                    self.send_failsafe_ungrab()
                        except Exception:
                            self.connected = False
                            self.send_failsafe_ungrab()
                        continue

                    dev = fd_to_dev.get(fd)
                    if not dev: continue
                    
                    try:
                        events = dev.read()
                    except (OSError, IOError) as e:
                        if e.errno == 19: # No such device (unplugged)
                            print(f"\r\033[K⚠ Device disconnected: {dev.name}")
                            del fd_to_dev[fd]
                            # Update select list
                            all_monitored_fds = list(fd_to_dev.keys())
                            if self.sock: all_monitored_fds.append(self.sock.fileno())
                            continue
                        raise e

                    for event in events:
                        # Mouse Movement
                        if event.type == ecodes.EV_REL:
                            if event.code == ecodes.REL_X:
                                dx += event.value
                            elif event.code == ecodes.REL_Y:
                                dy += event.value
                            # Scroll
                            elif event.code == ecodes.REL_WHEEL:
                                if self.sending: self.send(f"S:0:{event.value}\n")

                        # Button / Key Clicks
                        elif event.type == ecodes.EV_KEY:
                            # F8 Toggle (Trigger on RELEASE '0' to prevent Linux TTY auto-repeat infinitely spamming the pressed key)
                            if event.code == ecodes.KEY_F8 and event.value == 0:
                                # Proactive check: If connection is dead, try to recover instantly
                                if not self.connected:
                                    self.connect(retry_sleep=0) 
                                    all_monitored_fds = list(fd_to_dev.keys())
                                    if self.sock: all_monitored_fds.append(self.sock.fileno())

                                self.sending = not self.sending
                                if self.sending:
                                    # If sending the activation fails, try one instant reconnect and retry
                                    if not self.send("SW:activate\n"):
                                        print("⚡ First attempt failed. Attempting instant recovery...")
                                        if self.connect(retry_sleep=0):
                                            all_monitored_fds = list(fd_to_dev.keys())
                                            if self.sock: all_monitored_fds.append(self.sock.fileno())
                                            if self.send("SW:activate\n"):
                                                self.sending = True  # Success!

                                    if self.sending:
                                        # \r\033[K clears the terminal line (hides the ^[[19~ garbage)
                                        print("\r\033[K  🖱️  ON:   Controlling Windows (Linux hardware locked)")
                                        # Lock the mouse so Linux doesn't move or click
                                        for m_dev in self.mouse_devs:
                                            try: m_dev.grab()
                                            except Exception as e: print(f"Grab error: {e}")
                                        if self.enable_keyboard:
                                            for k_dev in self.keyboard_devs:
                                                try: k_dev.grab()
                                                except Exception: pass
                                    else:
                                        print("\r\033[K  ✗ Failed to connect. Please check Windows receiver.")
                                else:
                                    self.send("SW:deactivate\n")
                                    print("\r\033[K  ◼  OFF:  Back to Linux")
                                    # Release the mouse back to Linux
                                    for m_dev in self.mouse_devs:
                                        try: m_dev.ungrab()
                                        except Exception: pass
                                    if self.enable_keyboard:
                                        for k_dev in self.keyboard_devs:
                                            try: k_dev.ungrab()
                                            except Exception: pass
                            
                            # Mouse buttons
                            elif self.sending:
                                if event.code == ecodes.BTN_LEFT:
                                    self.send(f"C:l:{'p' if event.value else 'r'}\n")
                                elif event.code == ecodes.BTN_RIGHT:
                                    self.send(f"C:r:{'p' if event.value else 'r'}\n")
                                elif event.code == ecodes.BTN_MIDDLE:
                                    self.send(f"C:m:{'p' if event.value else 'r'}\n")
                                elif self.enable_keyboard and event.code != ecodes.KEY_F8:
                                    if event.value in [0, 1]:  # 0=release, 1=press
                                        key_name = ecodes.KEY[event.code]
                                        if isinstance(key_name, list):
                                            key_name = key_name[0]
                                        self.send(f"K:{key_name}:{event.value}\n")

                # Send accumulated mouse deltas (rate limited by the select loop)
                if self.sending and (dx != 0 or dy != 0):
                    # Apply speed multiplier to make it faster on Windows
                    send_dx = int(dx * self.sensitivity)
                    send_dy = int(dy * self.sensitivity)
                    self.send(f"M:{send_dx}:{send_dy}\n")
                    dx, dy = 0, 0

        except KeyboardInterrupt:
            pass
        finally:
            if self.sock: self.sock.close()
            print("\nBye!")


import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default=os.environ.get('WINDOWS_IP'), help='Windows machine IP address')
    parser.add_argument('--speed', type=float, default=float(os.environ.get('MOUSE_SPEED', 2.5)), help='Mouse speed multiplier (default: 2.5)')
    args = parser.parse_args()

    if not args.ip:
        args.ip = input("Enter Windows IP Address: ").strip()
        if not args.ip:
            print("ERROR: IP address is required.")
            sys.exit(1)
            
    kb_ans = input("Enable keyboard sharing? [Y/n]: ").strip().lower()
    enable_kb = False if kb_ans == 'n' else True

    sender = LinuxSenderRaw(args.ip, enable_keyboard=enable_kb)
    sender.sensitivity = args.speed
    sender.start()
