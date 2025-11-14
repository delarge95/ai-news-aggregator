#!/bin/bash
# Script para iniciar workers de Celery para AI News Aggregator

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="/workspace/ai-news-aggregator/backend"
CELERY_APP="celery_app:celery_app"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Crear directorios necesarios
mkdir -p "$LOG_DIR" "$PID_DIR"

echo -e "${BLUE}🚀 Iniciando Workers de Celery para AI News Aggregator${NC}"
echo "=================================================="

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}🛑 Deteniendo workers de Celery...${NC}"
    pkill -f "celery.*$CELERY_APP" || true
    pkill -f "flower.*$CELERY_APP" || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verificar que Redis esté disponible
echo -e "${BLUE}🔍 Verificando conexión a Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Redis no está disponible${NC}"
    echo "Por favor, asegúrate de que Redis esté ejecutándose"
    exit 1
fi
echo -e "${GREEN}✅ Redis disponible${NC}"

# Verificar variables de entorno
echo -e "${BLUE}🔍 Verificando configuración...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Advertencia: OPENAI_API_KEY no está configurada${NC}"
    echo "Las funciones de análisis usarán métodos de fallback"
else
    echo -e "${GREEN}✅ OpenAI API key configurada${NC}"
fi

# Limpiar procesos anteriores
echo -e "${BLUE}🧹 Limpiando procesos anteriores...${NC}"
pkill -f "celery.*$CELERY_APP" || true
pkill -f "flower.*$CELERY_APP" || true
sleep 2

# Crear scripts de inicio para diferentes tipos de workers
cat > "$PROJECT_DIR/start_workers.sh" << 'EOF'
#!/bin/bash

# Worker para análisis de IA
celery -A celery_app:celery_app worker \
    --loglevel=info \
    --queues=ai_analysis \
    --concurrency=3 \
    --hostname=ai_analysis@%h \
    --logfile=logs/ai_analysis.log \
    --pidfile=pids/ai_analysis.pid &

# Worker para clasificación de temas
celery -A celery_app:celery_app worker \
    --loglevel=info \
    --queues=ai_classification \
    --concurrency=2 \
    --hostname=ai_classification@%h \
    --logfile=logs/ai_classification.log \
    --pidfile=pids/ai_classification.pid &

# Worker para generación de resúmenes
celery -A celery_app:celery_app worker \
    --loglevel=info \
    --queues=ai_summaries \
    --concurrency=2 \
    --hostname=ai_summaries@%h \
    --logfile=logs/ai_summaries.log \
    --pidfile=pids/ai_summaries.pid &

# Worker para obtención de noticias
celery -A celery_app:celery_app worker \
    --loglevel=info \
    --queues=news_fetch \
    --concurrency=2 \
    --hostname=news_fetch@%h \
    --logfile=logs/news_fetch.log \
    --pidfile=pids/news_fetch.pid &

# Worker para tareas generales y monitoreo
celery -A celery_app:celery_app worker \
    --loglevel=info \
    --queues=default,maintenance \
    --concurrency=1 \
    --hostname=general@%h \
    --logfile=logs/general.log \
    --pidfile=pids/general.pid &

EOF

chmod +x "$PROJECT_DIR/start_workers.sh"

# Iniciar Celery Beat para tareas programadas
echo -e "${BLUE}⏰ Iniciando Celery Beat (scheduled tasks)...${NC}"
celery -A celery_app:celery_app beat \
    --loglevel=info \
    --logfile=logs/beat.log \
    --pidfile=pids/beat.pid \
    --scheduler=celery.beat.PersistentScheduler \
    --schedule="$PROJECT_DIR/celerybeat-schedule" &

BEAT_PID=$!
echo $BEAT_PID > "$PID_DIR/beat.pid"

# Esperar un momento para que Beat se inicie
sleep 3

# Iniciar los workers
echo -e "${BLUE}👥 Iniciando workers especializados...${NC}"
"$PROJECT_DIR/start_workers.sh"

# Esperar a que los workers se inicien
sleep 5

# Verificar que los workers estén ejecutándose
echo -e "${BLUE}🔍 Verificando estado de los workers...${NC}"
WORKER_COUNT=$(pgrep -f "celery.*$CELERY_APP" | wc -l)

if [ "$WORKER_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ $WORKER_COUNT workers iniciados exitosamente${NC}"
else
    echo -e "${RED}❌ Error: No se detectaron workers ejecutándose${NC}"
    exit 1
fi

# Iniciar Flower para monitoreo (opcional)
if command -v flower > /dev/null; then
    echo -e "${BLUE}📊 Iniciando Flower para monitoreo...${NC}"
    celery -A celery_app:celery_app flower \
        --port=5555 \
        --logfile=logs/flower.log \
        --pidfile=pids/flower.pid &
    
    FLOWER_PID=$!
    echo $FLOWER_PID > "$PID_DIR/flower.pid"
    echo -e "${GREEN}✅ Flower disponible en http://localhost:5555${NC}"
fi

# Mostrar resumen
echo ""
echo -e "${GREEN}🎉 Workers de Celery iniciados exitosamente${NC}"
echo "=================================================="
echo -e "${BLUE}📊 Workers activos:${NC}"
ps aux | grep -E "celery.*$CELERY_APP" | grep -v grep || echo "No hay workers activos"
echo ""
echo -e "${BLUE}📁 Logs disponibles en:${NC}"
echo "  - AI Analysis: $LOG_DIR/ai_analysis.log"
echo "  - AI Classification: $LOG_DIR/ai_classification.log"
echo "  - AI Summaries: $LOG_DIR/ai_summaries.log"
echo "  - News Fetch: $LOG_DIR/news_fetch.log"
echo "  - General: $LOG_DIR/general.log"
echo "  - Beat: $LOG_DIR/beat.log"
echo ""
if [ -f "$PID_DIR/flower.pid" ]; then
    echo -e "${BLUE}🌐 Monitoreo web (Flower):${NC}"
    echo "  - URL: http://localhost:5555"
    echo "  - PID: $(cat $PID_DIR/flower.pid 2>/dev/null || echo 'N/A')"
    echo ""
fi

echo -e "${BLUE}📋 Procesos en ejecución:${NC}"
echo -e "  - Beat PID: $(cat $PID_DIR/beat.pid 2>/dev/null || echo 'N/A')"
echo -e "  - Workers: $WORKER_COUNT procesos"
echo ""
echo -e "${YELLOW}💡 Para detener todos los workers, presiona Ctrl+C${NC}"
echo ""

# Mantener el script ejecutándose
while true; do
    sleep 30
    
    # Verificar que los workers aún estén ejecutándose
    current_workers=$(pgrep -f "celery.*$CELERY_APP" | wc -l)
    if [ "$current_workers" -eq 0 ]; then
        echo -e "${RED}❌ Error: No hay workers ejecutándose. Reiniciando...${NC}"
        "$PROJECT_DIR/start_workers.sh"
    fi
done