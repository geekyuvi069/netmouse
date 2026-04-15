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
