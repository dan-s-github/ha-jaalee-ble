FROM mcr.microsoft.com/devcontainers/python:3.14

# Remove problematic yarn repository that has signing issues
RUN rm -f /etc/apt/sources.list.d/yarn.list

# Install required packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libturbojpeg0 \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv - fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:0.10.6 /uv /usr/local/bin/uv
