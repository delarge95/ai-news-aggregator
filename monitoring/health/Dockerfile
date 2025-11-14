FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
WORKDIR /app
COPY monitoring/health/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar scripts de health check
COPY monitoring/health/ ./

# Crear directorios para logs
RUN mkdir -p /var/log

# Hacer ejecutable el scheduler
RUN chmod +x health_cron.py

# Exponer puerto para métricas
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comandos por defecto
CMD ["python", "health_cron.py"]