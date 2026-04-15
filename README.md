# NetMouse Lite

```text
 ███╗   ██╗███████╗████████╗███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗
 ████╗  ██║██╔════╝╚══██╔══╝████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝
 ██╔██╗ ██║█████╗     ██║   ██╔████╔██║██║   ██║██║   ██║███████╗█████╗  
 ██║╚██╗██║██╔══╝     ██║   ██║╚██╔╝██║██║   ██║██║   ██║╚════██║██╔══╝  
 ██║ ╚████║███████╗   ██║   ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████╗
 ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
```

**A high-performance, Wayland-bypassing hardware mouse bridge.**

Control your Windows machine using your Linux mouse and keyboard. Specifically designed to bypass Wayland security restrictions by reading directly from raw hardware input via Docker.

## Project Structure

This directory only needs 3 files:
- `win_receiver.py` (Runs on Windows to accept commands)
- `linux_sender_raw.py` (Runs on Linux to capture mouse/keyboard)
- `Dockerfile` (Used to run the Linux side easily)

---

## 1. Windows Setup (The Receiver)

Copy `win_receiver.py` to your Windows PC.

1. Open Command Prompt.
2. Install the mouse controller library:
   ```cmd
   pip install pynput
   ```
3. Run the script:
   ```cmd
   python win_receiver.py
   ```
*(Take note of the IP address it prints out!)*

> [!IMPORTANT]
> **Run as Administrator:** On Windows, you MUST run your Command Prompt or PowerShell as **Administrator**. If you don't, Windows security will block the mouse from moving over the Taskbar, the Start Menu, or the Task Manager.

### 🚀 Pro Tip: Windows "Easy Run" Shortcut
To run the receiver from any terminal by just typing `netmouse`, do this:

1. Create a folder `C:\Tools`.
2. Create a file `C:\Tools\netmouse.cmd` and paste this (fix the paths to match your desktop):
   ```batch
   @echo off
   cd /d C:\Users\YOUR_NAME\Desktop\live_mouse
   pip install pynput
   python win_receiver.py
   pause
   ```
3. Add it to your System Path (run once in Admin CMD):
   ```cmd
   setx PATH "%PATH%;C:\Tools"
   ```
4. Now you can just type `netmouse` in any Windows CMD/PowerShell to start!

---

## 2. Linux Setup (The Sender)

We use Docker on Linux to bypass Wayland's strict security blocks.

1. Open Terminal in this directory.
2. Build the Docker Image:
   ```bash
   sudo docker build -t netmouse-linux .
   ```
3. Set up the alias shortcut (Run this once):
   ```bash
   echo 'alias netmouse="sudo docker run --rm -it --device /dev/input:/dev/input netmouse-linux"' >> ~/.bashrc
   source ~/.bashrc
   ```

## 3. How to Use
1. Just open any terminal on Linux and type:
   ```bash
   netmouse
   ```
2. It will ask you for your Windows IP. Type it in and press Enter.
3. It will ask: `Enable keyboard sharing? [Y/n]`. Type `Y` if you want to control the Windows keyboard, or `n` if you only want to share your mouse.
4. Press **F8** on your keyboard to instantly transfer your hardware over to the Windows screen (your Linux cursor and keyboard will safely lock to prevent accidental local typing).
5. Press **F8** again to instantly unlock your hardware and bring it back to Linux.

---

## 🚀 Roadmap / Future Plans
- [ ] **macOS Support**: Port the receiver to macOS using `pynput` and Accessibility permissions.
- [ ] **Linux Receiver**: Implement a `uinput` based receiver for Wayland-to-Wayland control.
- [ ] **Encryption (TLS)**: Secure the TCP stream with SSL/TLS to prevent local network sniffing.
- [ ] **Authentication**: Add a "Secret Key" pairing system to prevent unauthorized connections on public WiFi.
- [ ] **Clipboard Sharing**: Sync text and images between systems automatically.
- [ ] **Edge-Jumping**: Auto-switch systems when the mouse hits the monitor edge.
