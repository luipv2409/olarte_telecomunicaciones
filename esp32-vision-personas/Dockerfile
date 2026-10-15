# ==============================================================================
# Dockerfile para esp32-vision-personas (FastAPI + YOLOv8 CPU)
# ==============================================================================
FROM python:3.11-slim

# Evita creación de archivos .pyc y fuerza salida de log inmediata
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    YOLO_CONFIG_DIR=/home/appuser/.config/Ultralytics

# Instalar dependencias del sistema mínimas requeridas por OpenCV y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios para ejecución segura
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-descargar el modelo ligero YOLOv8n durante el build para funcionamiento offline
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" && \
    mv yolov8n.pt /home/appuser/yolov8n.pt 2>/dev/null || true

# Copiar el código fuente de la aplicación
COPY app/ /app/app/

# Asignar permisos al usuario appuser
RUN chown -R appuser:appgroup /app /home/appuser

USER appuser

# El contenedor escucha internamente en el puerto 8000
EXPOSE 8000

# Verificación de salud interna
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
