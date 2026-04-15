# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Professional Metadata
LABEL maintainer="NetMouse-Lite"
LABEL description="Wayland-compatible hardware mouse/keyboard bridge"

# Set the working directory
WORKDIR /app

# Install system dependencies required for evdev
# (We need gcc and headers to talk to your computer's USB ports)
RUN apt-get update && apt-get install -y \
    linux-libc-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install the hardware-communication library
RUN pip install --no-cache-dir evdev

# Copy the Linux sender script into the container
COPY linux_sender_raw.py .

# Command to run on container start
CMD ["python3", "linux_sender_raw.py"]
