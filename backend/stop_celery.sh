#!/bin/bash
# Script para detener workers de Celery de forma segura

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

echo -e "${BLUE}🛑 Deteniendo Workers de Celery${NC}"
echo "================================="

# Función para detener un proceso por PID
stop_process() {
    local name=$1
    local pid_file=$PID_DIR/$name.pid
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⏹️  Deteniendo $name (PID: $pid)...${NC}"
            kill -TERM "$pid"
            
            # Esperar a que se detenga gracefully
            local timeout=10
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt $timeout ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Si aún está ejecutándose, forzar detención
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${RED}⚠️  Forzando detención de $name...${NC}"
                kill -KILL "$pid"
            fi
            
            echo -e "${GREEN}✅ $name detenido${NC}"
        else
            echo -e "${YELLOW}⚠️  $name no estaba ejecutándose${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No se encontró archivo PID para $name${NC}"
    fi
}

# Detener procesos específicos
echo -e "${BLUE}🔍 Buscando procesos específicos...${NC}"
stop_process "beat"
stop_process "flower"

# Detener workers por tipo
echo -e "${BLUE}🔍 Deteniendo workers...${NC}"
stop_process "ai_analysis"
stop_process "ai_classification"
stop_process "ai_summaries"
stop_process "news_fetch"
stop_process "general"

# Buscar y detener cualquier proceso restante de Celery
echo -e "${BLUE}🔍 Buscando procesos restantes de Celery...${NC}"
CELERY_PIDS=$(pgrep -f "celery.*celery_app" || true)

if [ -n "$CELERY_PIDS" ]; then
    echo -e "${YELLOW}⚠️  Encontrados procesos restantes de Celery${NC}"
    echo "PIDs: $CELERY_PIDS"
    
    for pid in $CELERY_PIDS; do
        echo -e "${YELLOW}⏹️  Terminando proceso $pid...${NC}"
        kill -TERM "$pid" 2>/dev/null || true
    done
    
    # Esperar un momento
    sleep 3
    
    # Verificar si aún hay procesos y forzarlos si es necesario
    REMAINING_PIDS=$(pgrep -f "celery.*celery_app" || true)
    if [ -n "$REMAINING_PIDS" ]; then
        echo -e "${RED}⚠️  Forzando detención de procesos restantes${NC}"
        echo "PIDs: $REMAINING_PIDS"
        for pid in $REMAINING_PIDS; do
            kill -KILL "$pid" 2>/dev/null || true
        done
    fi
else
    echo -e "${GREEN}✅ No hay procesos restantes de Celery${NC}"
fi

# Limpiar archivos temporales
echo -e "${BLUE}🧹 Limpiando archivos temporales...${NC}"
rm -f "$PROJECT_DIR/celerybeat-schedule"
rm -f "$PROJECT_DIR/.celerybeat-schedule.*"

# Verificar que todo esté detenido
echo -e "${BLUE}🔍 Verificando estado final...${NC}"
REMAINING=$(pgrep -f "celery.*celery_app" || true)

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✅ Todos los workers de Celery detenidos correctamente${NC}"
else
    echo -e "${RED}❌ Aún hay procesos de Celery ejecutándose:${NC}"
    echo "$REMAINING"
    echo -e "${YELLOW}💡 Puede ser necesario terminarlos manualmente${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Proceso de detención completado${NC}"
echo "================================="

# Mostrar estado de los logs
if [ -d "$PROJECT_DIR/logs" ]; then
    echo -e "${BLUE}📁 Archivos de log disponibles:${NC}"
    ls -la "$PROJECT_DIR/logs/" 2>/dev/null || echo "No hay archivos de log"
fi

# Mostrar recomendaciones
echo ""
echo -e "${BLUE}💡 Recomendaciones:${NC}"
echo "- Revisa los logs para verificar que todo se detuvo correctamente"
echo "- Para reiniciar, ejecuta: ./start_celery.sh"
echo "- Para verificar el estado, ejecuta: ./status_celery.sh"