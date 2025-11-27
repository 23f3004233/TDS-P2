FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ALL Chromium dependencies
RUN apt-get update && apt-get install -y \
    # Browser dependencies
    wget \
    gnupg \
    ca-certificates \
    # Chromium runtime dependencies
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxshmfence1 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxcb1 \
    libxkbfile1 \
    libxslt1.1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-gl1.0-0 \
    libopus0 \
    libwebpdemux2 \
    libwoff1 \
    libharfbuzz-icu0 \
    libhyphen0 \
    libmanette-0.2-0 \
    libflite1 \
    libgles2 \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    # PDF processing
    poppler-utils \
    # Image processing
    tesseract-ocr \
    libtesseract-dev \
    # Audio/Video processing
    ffmpeg \
    libsm6 \
    libxext6 \
    # Build tools
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser ONLY (not deps, we installed them manually)
RUN playwright install chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/quiz_solver && \
    chmod 777 /tmp/quiz_solver

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]