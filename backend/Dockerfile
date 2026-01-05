FROM python:3.13-slim

WORKDIR /app

# Install git and build dependencies for face_recognition and OpenCV
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

# Install setuptools for pkg_resources, face_recognition_models first, then rest of requirements
RUN pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir git+https://github.com/ageitgey/face_recognition_models && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]