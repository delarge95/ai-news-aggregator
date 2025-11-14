#!/bin/bash
# Script para verificar el estado de los workers de Celery

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="/workspace/ai-news-aggregator/backend"
PID_DIR="$PROJECT_DIR/pids"
LOG_DIR="$PROJECT_DIR/logs"

echo -e "${BLUE}📊 Estado de Workers de Celery${NC}"
echo "==============================="

# Verificar conexión a Redis
echo -e "${BLUE}🔌 Verificando conexión a Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis: Conectado${NC}"
    REDIS_INFO=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    echo -e "   Memoria usada: ${REDIS_INFO:-'N/A'}"
else
    echo -e "${RED}❌ Redis: No disponible${NC}"
fi

# Verificar procesos de Celery
echo -e "${BLUE}📋 Verificando procesos...${NC}"
CELERY_PROCS=$(pgrep -f "celery.*celery_app" || true)

if [ -n "$CELERY_PROCS" ]; then
    echo -e "${GREEN}✅ Procesos de Celery encontrados: $(echo $CELERY_PROCS | wc -w)${NC}"
    echo -e "${BLUE}📝 Detalle de procesos:${NC}"
    ps aux | grep -E "celery.*celery_app" | grep -v grep | while read line; do
        echo "   $line"
    done
else
    echo -e "${RED}❌ No hay procesos de Celery ejecutándose${NC}"
fi

# Verificar workers específicos
echo -e "${BLUE}👥 Verificando workers específicos...${NC}"
WORKERS=("ai_analysis" "ai_classification" "ai_summaries" "news_fetch" "general")

for worker in "${WORKERS[@]}"; do
    if [ -f "$PID_DIR/$worker.pid" ]; then
        PID=$(cat "$PID_DIR/$worker.pid")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${GREEN}✅ $worker: Ejecutándose (PID: $PID)${NC}"
        else
            echo -e "${RED}❌ $worker: PID file existe pero proceso no encontrado${NC}"
            rm -f "$PID_DIR/$worker.pid"
        fi
    else
        echo -e "${YELLOW}⚠️  $worker: No está ejecutándose${NC}"
    fi
done

# Verificar Celery Beat
echo -e "${BLUE}⏰ Verificando Celery Beat...${NC}"
if [ -f "$PID_DIR/beat.pid" ]; then
    BEAT_PID=$(cat "$PID_DIR/beat.pid")
    if kill -0 "$BEAT_PID" 2>/dev/null; then
        echo -e "${GREEN}✅ Beat: Ejecutándose (PID: $BEAT_PID)${NC}"
    else
        echo -e "${RED}❌ Beat: PID file existe pero proceso no encontrado${NC}"
        rm -f "$PID_DIR/beat.pid"
    fi
else
    echo -e "${YELLOW}⚠️  Beat: No está ejecutándose${NC}"
fi

# Verificar Flower
echo -e "${BLUE}🌐 Verificando Flower...${NC}"
if [ -f "$PID_DIR/flower.pid" ]; then
    FLOWER_PID=$(cat "$PID_DIR/flower.pid")
    if kill -0 "$FLOWER_PID" 2>/dev/null; then
        echo -e "${GREEN}✅ Flower: Ejecutándose (PID: $FLOWER_PID)${NC}"
        echo -e "   🌐 URL: http://localhost:5555"
    else
        echo -e "${RED}❌ Flower: PID file existe pero proceso no encontrado${NC}"
        rm -f "$PID_DIR/flower.pid"
    fi
else
    echo -e "${YELLOW}⚠️  Flower: No está ejecutándose${NC}"
fi

# Verificar logs
echo -e "${BLUE}📁 Verificando logs...${NC}"
if [ -d "$LOG_DIR" ]; then
    LOG_FILES=("ai_analysis.log" "ai_classification.log" "ai_summaries.log" "news_fetch.log" "general.log" "beat.log" "flower.log")
    
    for log_file in "${LOG_FILES[@]}"; do
        if [ -f "$LOG_DIR/$log_file" ]; then
            SIZE=$(du -h "$LOG_DIR/$log_file" | cut -f1)
            LAST_MOD=$(stat -c %y "$LOG_DIR/$log_file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
            echo -e "${GREEN}✅ $log_file: ${SIZE} (Última modificación: $LAST_MOD)${NC}"
        else
            echo -e "${YELLOW}⚠️  $log_file: No encontrado${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠️  Directorio de logs no encontrado${NC}"
fi

# Verificar estado de Redis (colas)
echo -e "${BLUE}📬 Verificando colas de tareas...${NC}"
if command -v redis-cli > /dev/null 2>&1; then
    # Obtener información de las colas
    QUEUES=$(redis-cli --scan --pattern "celery*" | head -10)
    if [ -n "$QUEUES" ]; then
        echo -e "${GREEN}✅ Claves de Celery encontradas en Redis:${NC}"
        echo "$QUEUES" | while read key; do
            echo "   $key"
        done
    else
        echo -e "${YELLOW}⚠️  No se encontraron claves de Celery en Redis${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  redis-cli no está disponible${NC}"
fi

# Verificar tareas recientes (si Flower está ejecutándose)
echo -e "${BLUE}📋 Verificando tareas recientes...${NC}"
if [ -f "$PID_DIR/flower.pid" ] && kill -0 "$(cat "$PID_DIR/flower.pid")" 2>/dev/null; then
    echo -e "${GREEN}✅ Flower está disponible - revisa http://localhost:5555 para tareas recientes${NC}"
else
    echo -e "${YELLOW}⚠️  Flower no está ejecutándose${NC}"
fi

# Resumen
echo ""
echo -e "${BLUE}📊 RESUMEN DEL ESTADO${NC}"
echo "======================="

TOTAL_WORKERS=0
RUNNING_WORKERS=0

for worker in "${WORKERS[@]}"; do
    TOTAL_WORKERS=$((TOTAL_WORKERS + 1))
    if [ -f "$PID_DIR/$worker.pid" ] && kill -0 "$(cat "$PID_DIR/$worker.pid")" 2>/dev/null; then
        RUNNING_WORKERS=$((RUNNING_WORKERS + 1))
    fi
done

BEAT_RUNNING=false
if [ -f "$PID_DIR/beat.pid" ] && kill -0 "$(cat "$PID_DIR/beat.pid")" 2>/dev/null; then
    BEAT_RUNNING=true
fi

FLOWER_RUNNING=false
if [ -f "$PID_DIR/flower.pid" ] && kill -0 "$(cat "$PID_DIR/flower.pid")" 2>/dev/null; then
    FLOWER_RUNNING=true
fi

echo -e "Workers: ${RUNNING_WORKERS}/${TOTAL_WORKERS}"
echo -e "Beat: $([ "$BEAT_RUNNING" = true ] && echo -e "${GREEN}Ejecutándose${NC}" || echo -e "${RED}Detenido${NC}")"
echo -e "Flower: $([ "$FLOWER_RUNNING" = true ] && echo -e "${GREEN}Ejecutándose${NC}" || echo -e "${RED}Detenido${NC}")"
echo -e "Redis: ${RED}❌ No disponible${NC}"

if [ "$RUNNING_WORKERS" -eq "$TOTAL_WORKERS" ] && [ "$BEAT_RUNNING" = true ]; then
    echo ""
    echo -e "${GREEN}🎉 Sistema Celery completamente operacional${NC}"
elif [ "$RUNNING_WORKERS" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Sistema Celery parcialmente operacional${NC}"
    echo -e "${BLUE}💡 Para reiniciar completamente, ejecuta:${NC}"
    echo "   ./stop_celery.sh && ./start_celery.sh"
else
    echo ""
    echo -e "${RED}❌ Sistema Celery no está ejecutándose${NC}"
    echo -e "${BLUE}💡 Para iniciar, ejecuta:${NC}"
    echo "   ./start_celery.sh"
fi