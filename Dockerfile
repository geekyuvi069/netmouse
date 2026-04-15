# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for evdev
RUN apt-get update && apt-get install -y \
    linux-libc-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python-evdev
RUN pip install --no-cache-dir evdev

# Copy the Linux sender script into the container
COPY linux_sender_raw.py .

# Command to run on container start
CMD ["python3", "linux_sender_raw.py"]
