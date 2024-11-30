# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    libleptonica-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libgl1-mesa-glx \
    libgl1 \
    ffmpeg \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
    
# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN python -m venv /opt/venv
# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for Flask
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "app.py"]