#!/bin/bash

# Script para configurar automáticamente los monitors en Uptime Kuma
# Este script usa la API de Uptime Kuma para crear monitors

UPTIME_KUMA_URL="http://uptime-kuma:3001"
API_KEY=""  # Dejar vacío para no usar autenticación

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para crear un monitor HTTP
create_http_monitor() {
    local name=$1
    local url=$2
    local interval=$3
    local timeout=$4
    
    echo -e "${YELLOW}Creando monitor HTTP: ${name}${NC}"
    
    if [ -n "$API_KEY" ]; then
        AUTH_HEADER="Authorization: Bearer $API_KEY"
    fi
    
    response=$(curl -s -X POST "$UPTIME_KUMA_URL/api/monitors" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "{
            \"name\": \"$name\",
            \"url\": \"$url\",
            \"type\": \"http\",
            \"interval\": $interval,
            \"timeout\": $timeout,
            \"maxRetries\": 3,
            \"resendInterval\": 0,
            \"keyword\": \"\",
            \"invertKeyword\": false,
            \"ignoreTls\": false,
            \"maxRedirects\": 10,
            \"acceptedStatuscodes\": \"200-299\"
        }")
    
    if echo "$response" | grep -q '"ok":true'; then
        echo -e "${GREEN}✓ Monitor $name creado exitosamente${NC}"
    else
        echo -e "${RED}✗ Error creando monitor $name: $response${NC}"
    fi
}

# Función para crear un monitor TCP
create_tcp_monitor() {
    local name=$1
    local host=$2
    local port=$3
    local interval=$4
    
    echo -e "${YELLOW}Creando monitor TCP: ${name}${NC}"
    
    if [ -n "$API_KEY" ]; then
        AUTH_HEADER="Authorization: Bearer $API_KEY"
    fi
    
    response=$(curl -s -X POST "$UPTIME_KUMA_URL/api/monitors" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "{
            \"name\": \"$name\",
            \"url\": \"$host:$port\",
            \"type\": \"tcp\",
            \"interval\": $interval,
            \"timeout\": 5,
            \"maxRetries\": 3,
            \"resendInterval\": 0
        }")
    
    if echo "$response" | grep -q '"ok":true'; then
        echo -e "${GREEN}✓ Monitor $name creado exitosamente${NC}"
    else
        echo -e "${RED}✗ Error creando monitor $name: $response${NC}"
    fi
}

# Función para crear un monitor de puerto TCP
create_port_monitor() {
    local name=$1
    local host=$2
    local port=$3
    local interval=$4
    
    echo -e "${YELLOW}Creando monitor de puerto: ${name}${NC}"
    
    if [ -n "$API_KEY" ]; then
        AUTH_HEADER="Authorization: Bearer $API_KEY"
    fi
    
    response=$(curl -s -X POST "$UPTIME_KUMA_URL/api/monitors" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "{
            \"name\": \"$name\",
            \"host\": \"$host\",
            \"port\": $port,
            \"type\": \"tcp-port\",
            \"interval\": $interval,
            \"timeout\": 5,
            \"maxRetries\": 3,
            \"resendInterval\": 0
        }")
    
    if echo "$response" | grep -q '"ok":true'; then
        echo -e "${GREEN}✓ Monitor $name creado exitosamente${NC}"
    else
        echo -e "${RED}✗ Error creando monitor $name: $response${NC}"
    fi
}

echo -e "${YELLOW}=== Configuración de Uptime Monitoring ===${NC}"
echo -e "${YELLOW}Esperando a que Uptime Kuma esté disponible...${NC}"

# Esperar a que Uptime Kuma esté disponible
for i in {1..30}; do
    if curl -s "$UPTIME_KUMA_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}Uptime Kuma está disponible${NC}"
        break
    fi
    echo -e "${YELLOW}Esperando... ($i/30)${NC}"
    sleep 2
done

echo -e "${YELLOW}Iniciando creación de monitores...${NC}"

# Monitors HTTP - API endpoints
create_http_monitor "AI News Backend Health" "http://backend:8000/health" 60 10
create_http_monitor "AI News Backend API" "http://backend:8000/api/v1/health" 60 10
create_http_monitor "AI News Backend Metrics" "http://backend:8000/metrics" 120 10
create_http_monitor "AI News Frontend" "http://frontend:3000" 60 10

# Monitors HTTP - External endpoints
create_http_monitor "AI News Public API" "http://localhost:8000/api/v1/articles" 60 10
create_http_monitor "AI News Search API" "http://localhost:8000/api/v1/search" 60 10

# Monitors TCP - Servicios internos
create_tcp_monitor "PostgreSQL Database" "postgres" 5432 120
create_tcp_monitor "Redis Cache" "redis" 6379 120
create_tcp_monitor "Prometheus Metrics" "prometheus" 9090 120

# Monitors de puerto - Infrastructure
create_port_monitor "cAdvisor" "cadvisor" 8080 120
create_port_monitor "Node Exporter" "node-exporter" 9100 120
create_port_monitor "Blackbox Exporter" "blackbox-exporter" 9115 120
create_port_monitor "Elasticsearch" "elasticsearch" 9200 120
create_port_monitor "Kibana" "kibana" 5601 120

# Monitors específicos para cada endpoint importante
create_http_monitor "AI News - Articles List" "http://backend:8000/api/v1/articles" 120 15
create_http_monitor "AI News - Search Endpoint" "http://backend:8000/api/v1/search" 120 15
create_http_monitor "AI News - Analytics" "http://backend:8000/api/v1/analytics" 120 15
create_http_monitor "AI News - Trending" "http://backend:8000/api/v1/trending" 120 15

echo -e "${GREEN}=== Configuración completada ===${NC}"
echo -e "${YELLOW}Puedes acceder a Uptime Kuma en: http://localhost:3001${NC}"
echo -e "${YELLOW}Dashboards: http://localhost:3000${NC}"
echo -e "${YELLOW}AlertManager: http://localhost:9093${NC}"
echo -e "${YELLOW}Prometheus: http://localhost:9090${NC}"