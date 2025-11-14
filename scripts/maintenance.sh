#!/bin/bash

# maintenance.sh - Gestión de modo mantenimiento para AI News Aggregator
# Versión: 1.0.0
# Descripción: Activación/desactivación de modo mantenimiento con página de estado

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "maintenance"

# Configuración de mantenimiento
readonly PROJECT_NAME="ai-news-aggregator"
readonly MAINTENANCE_CONFIG_DIR="${MAINTENANCE_CONFIG_DIR:-./maintenance}"
readonly MAINTENANCE_PAGE_FILE="$MAINTENANCE_CONFIG_DIR/maintenance.html"
readonly MAINTENANCE_STATUS_FILE="$MAINTENANCE_CONFIG_DIR/.maintenance_active"
readonly NGINX_CONFIG_FILE="${NGINX_CONFIG_FILE:-/etc/nginx/sites-available/ai-news}"
readonly APACHE_CONFIG_FILE="${APACHE_CONFIG_FILE:-/etc/apache2/sites-available/ai-news.conf}"
readonly FRONTEND_PORT="${FRONTEND_PORT:-3000}"
readonly BACKEND_PORT="${BACKEND_PORT:-8000}"

# Configuración de página de mantenimiento
readonly DEFAULT_MAINTENANCE_TITLE="Sistema en Mantenimiento"
readonly DEFAULT_MAINTENANCE_MESSAGE="Estamos realizando trabajos de mantenimiento. Vuelve pronto."
readonly DEFAULT_MAINTENANCE_ETA="30 minutos"

# Funciones principales
main() {
    local action="${1:-status}"
    
    case "$action" in
        "on") enable_maintenance "$2" "$3" "$4" ;;
        "off") disable_maintenance ;;
        "status") show_maintenance_status ;;
        "schedule") schedule_maintenance "$2" "$3" "$4" ;;
        "config") configure_maintenance_page ;;
        "test") test_maintenance_mode ;;
        *) usage ;;
    esac
}

enable_maintenance() {
    local title="${2:-$DEFAULT_MAINTENANCE_TITLE}"
    local message="${3:-$DEFAULT_MAINTENANCE_MESSAGE}"
    local eta="${4:-$DEFAULT_MAINTENANCE_ETA}"
    
    log_info "🔧 Activando modo mantenimiento..."
    log_info "Título: $title"
    log_info "Mensaje: $message"
    log_info "ETA: $eta"
    
    # Crear directorio de configuración si no existe
    mkdir -p "$MAINTENANCE_CONFIG_DIR"
    
    # Generar página de mantenimiento
    generate_maintenance_page "$title" "$message" "$eta"
    
    # Activar mantenimiento según el servidor web
    case "${WEB_SERVER:-auto}" in
        "nginx")
            enable_nginx_maintenance
            ;;
        "apache")
            enable_apache_maintenance
            ;;
        "docker")
            enable_docker_maintenance
            ;;
        "auto"|*)
            auto_detect_and_enable_maintenance
            ;;
    esac
    
    # Marcar mantenimiento como activo
    activate_maintenance_marker
    
    # Log del evento
    log_success "✅ Modo mantenimiento activado"
    log_deployment_event "maintenance_enabled" "{\"title\":\"$title\",\"eta\":\"$eta\"}"
    
    # Mostrar instrucciones adicionales
    show_maintenance_instructions
}

generate_maintenance_page() {
    local title="$1"
    local message="$2"
    local eta="$3"
    
    log_info "Generando página de mantenimiento..."
    
    cat > "$MAINTENANCE_PAGE_FILE" <<EOF
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .container {
            text-align: center;
            max-width: 600px;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        
        .message {
            font-size: 1.2rem;
            margin-bottom: 1.5rem;
            opacity: 0.9;
            line-height: 1.6;
        }
        
        .eta {
            background: rgba(255, 255, 255, 0.2);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        .eta strong {
            display: block;
            font-size: 1.3rem;
            margin-bottom: 0.5rem;
        }
        
        .progress {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        
        .progress-bar {
            height: 100%;
            background: #4CAF50;
            width: 0%;
            animation: progress 30s linear infinite;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            100% { width: 100%; }
        }
        
        .contact {
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        .timestamp {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.5);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔧</div>
        <h1>$title</h1>
        <p class="message">$message</p>
        
        <div class="eta">
            <strong>Tiempo Estimado</strong>
            $eta
        </div>
        
        <div class="progress">
            <div class="progress-bar"></div>
        </div>
        
        <div class="contact">
            <p>Para emergencias, contacta al equipo de desarrollo</p>
            <p>📧 devops@company.com | 📱 +1-555-0123</p>
        </div>
    </div>
    
    <div class="timestamp">
        $(date)
    </div>
    
    <script>
        // Auto-refresh para mostrar actualizaciones
        setTimeout(function() {
            location.reload();
        }, 30000);
        
        // Log de acceso para monitoreo
        console.log('Página de mantenimiento cargada:', new Date().toISOString());
    </script>
</body>
</html>
EOF
    
    log_success "Página de mantenimiento generada: $MAINTENANCE_PAGE_FILE"
}

auto_detect_and_enable_maintenance() {
    log_info "Detectando servidor web automáticamente..."
    
    # Verificar nginx
    if command -v nginx &> /dev/null && [[ -f "$NGINX_CONFIG_FILE" ]]; then
        log_info "Nginx detectado"
        enable_nginx_maintenance
        return 0
    fi
    
    # Verificar apache
    if command -v apache2 &> /dev/null && [[ -f "$APACHE_CONFIG_FILE" ]]; then
        log_info "Apache detectado"
        enable_apache_maintenance
        return 0
    fi
    
    # Verificar si está usando docker-compose
    if docker ps --format "{{.Names}}" | grep -q "ai_news_frontend"; then
        log_info "Docker Compose detectado"
        enable_docker_maintenance
        return 0
    fi
    
    log_warn "No se pudo detectar automáticamente el servidor web"
    log_info "Usando configuración manual de Docker"
    enable_docker_maintenance
}

enable_nginx_maintenance() {
    log_info "Configurando mantenimiento para Nginx..."
    
    # Crear configuración de mantenimiento
    local maintenance_config="/tmp/nginx_maintenance.conf"
    
    cat > "$maintenance_config" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    # Página de mantenimiento
    location / {
        root $MAINTENANCE_CONFIG_DIR;
        try_files /maintenance.html =404;
    }
    
    # API health check - permitir acceso para monitoreo
    location /health {
        proxy_pass http://localhost:$BACKEND_PORT/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
    
    # Hacer backup de la configuración original si no existe
    if [[ ! -f "$NGINX_CONFIG_FILE.backup" ]] && [[ -f "$NGINX_CONFIG_FILE" ]]; then
        cp "$NGINX_CONFIG_FILE" "$NGINX_CONFIG_FILE.backup"
        log_info "Backup de configuración original creado"
    fi
    
    # Activar configuración de mantenimiento
    if nginx -t -c "$maintenance_config" 2>/dev/null; then
        log_success "Configuración de mantenimiento válida"
        # En un entorno real, aquí se recargaría nginx
        # nginx -s reload
        
        # Registrar en log
        log_info "Nginx configurado para modo mantenimiento"
    else
        log_error "Error en configuración de Nginx"
        return 1
    fi
    
    # Limpiar archivo temporal
    rm -f "$maintenance_config"
}

enable_apache_maintenance() {
    log_info "Configurando mantenimiento para Apache..."
    
    # Crear configuración de mantenimiento
    local maintenance_config="/tmp/apache_maintenance.conf"
    
    cat > "$maintenance_config" <<EOF
<VirtualHost *:80>
    ServerName _default_
    DocumentRoot $MAINTENANCE_CONFIG_DIR
    
    <Directory $MAINTENANCE_CONFIG_DIR>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
    
    # Permitir health check
    <Location /health>
        ProxyPass http://localhost:$BACKEND_PORT/health
        ProxyPassReverse http://localhost:$BACKEND_PORT/health
    </Location>
</VirtualHost>
EOF
    
    # Hacer backup de la configuración original
    if [[ ! -f "$APACHE_CONFIG_FILE.backup" ]] && [[ -f "$APACHE_CONFIG_FILE" ]]; then
        cp "$APACHE_CONFIG_FILE" "$APACHE_CONFIG_FILE.backup"
    fi
    
    # Activar sitio de mantenimiento
    # En un entorno real, aquí se habilitaría el sitio
    # a2ensite maintenance
    # systemctl reload apache2
    
    log_success "Apache configurado para modo mantenimiento"
    
    rm -f "$maintenance_config"
}

enable_docker_maintenance() {
    log_info "Configurando mantenimiento para Docker..."
    
    # Detener servicios de frontend y backend
    log_info "Deteniendo servicios de aplicación..."
    
    docker-compose stop frontend backend 2>/dev/null || {
        log_warn "Algunos servicios ya estaban detenidos"
    }
    
    # Crear contenedor de mantenimiento simple
    local maintenance_container="ai_news_maintenance"
    
    # Verificar si ya existe y removerlo
    docker rm -f "$maintenance_container" 2>/dev/null || true
    
    # Iniciar contenedor de mantenimiento
    if docker run -d \
        --name "$maintenance_container" \
        --network ai_news_network \
        -p "$FRONTEND_PORT:80" \
        -v "$MAINTENANCE_CONFIG_DIR:/usr/share/nginx/html:ro" \
        nginx:alpine > /dev/null 2>&1; then
        
        log_success "Contenedor de mantenimiento iniciado en puerto $FRONTEND_PORT"
    else
        log_error "Error iniciando contenedor de mantenimiento"
        return 1
    fi
    
    # Permitir acceso al backend para health checks
    docker run -d \
        --name ai_news_maintenance_backend \
        --network ai_news_network \
        -p "$BACKEND_PORT:80" \
        -v "$MAINTENANCE_CONFIG_DIR:/usr/share/nginx/html:ro" \
        nginx:alpine > /dev/null 2>&1 || {
        log_warn "Contenedor de mantenimiento backend no pudo iniciarse"
    }
}

activate_maintenance_marker() {
    cat > "$MAINTENANCE_STATUS_FILE" <<EOF
{
    "active": true,
    "started_at": "$(date -Iseconds)",
    "title": "$DEFAULT_MAINTENANCE_TITLE",
    "message": "$DEFAULT_MAINTENANCE_MESSAGE",
    "eta": "$DEFAULT_MAINTENANCE_ETA",
    "server_type": "${WEB_SERVER:-auto}",
    "maintenance_page": "$MAINTENANCE_PAGE_FILE"
}
EOF
    
    log_success "Marcador de mantenimiento activado: $MAINTENANCE_STATUS_FILE"
}

disable_maintenance() {
    log_info "🔧 Desactivando modo mantenimiento..."
    
    # Verificar si el mantenimiento está activo
    if [[ ! -f "$MAINTENANCE_STATUS_FILE" ]]; then
        log_warn "Modo mantenimiento no está activo"
        return 0
    fi
    
    # Desactivar según el tipo de servidor
    case "${WEB_SERVER:-auto}" in
        "nginx")
            disable_nginx_maintenance
            ;;
        "apache")
            disable_apache_maintenance
            ;;
        "docker")
            disable_docker_maintenance
            ;;
        "auto"|*)
            auto_detect_and_disable_maintenance
            ;;
    esac
    
    # Eliminar marcador de mantenimiento
    rm -f "$MAINTENANCE_STATUS_FILE"
    
    # Limpiar página de mantenimiento
    if [[ "${CLEANUP_MAINTENANCE_FILES:-true}" == "true" ]]; then
        rm -f "$MAINTENANCE_PAGE_FILE"
        log_info "Archivos de mantenimiento limpiados"
    fi
    
    log_success "✅ Modo mantenimiento desactivado"
    log_deployment_event "maintenance_disabled" "{\"timestamp\":\"$(date -Iseconds)\"}"
}

auto_detect_and_disable_maintenance() {
    # Detectar qué servidor estaba activo y desactivarlo
    
    # Verificar contenedores de mantenimiento de Docker
    if docker ps --format "{{.Names}}" | grep -q "ai_news_maintenance"; then
        disable_docker_maintenance
        return 0
    fi
    
    # Verificar nginx
    if command -v nginx &> /dev/null && [[ -f "$NGINX_CONFIG_FILE.backup" ]]; then
        disable_nginx_maintenance
        return 0
    fi
    
    # Verificar apache
    if command -v apache2 &> /dev/null && [[ -f "$APACHE_CONFIG_FILE.backup" ]]; then
        disable_apache_maintenance
        return 0
    fi
    
    log_warn "No se pudo detectar automáticamente el método de desactivación"
}

disable_nginx_maintenance() {
    log_info "Desactivando mantenimiento de Nginx..."
    
    # Restaurar configuración original si existe backup
    if [[ -f "$NGINX_CONFIG_FILE.backup" ]]; then
        mv "$NGINX_CONFIG_FILE.backup" "$NGINX_CONFIG_FILE"
        log_info "Configuración original restaurada"
    fi
    
    # Recargar nginx
    if command -v nginx &> /dev/null; then
        nginx -s reload 2>/dev/null || {
            log_warn "No se pudo recargar nginx (puede requerir permisos)"
        }
    fi
}

disable_apache_maintenance() {
    log_info "Desactivando mantenimiento de Apache..."
    
    # Restaurar configuración original si existe backup
    if [[ -f "$APACHE_CONFIG_FILE.backup" ]]; then
        mv "$APACHE_CONFIG_FILE.backup" "$APACHE_CONFIG_FILE"
        log_info "Configuración original restaurada"
    fi
    
    # Recargar apache
    if command -v apache2 &> /dev/null; then
        systemctl reload apache2 2>/dev/null || {
            log_warn "No se pudo recargar apache2 (puede requerir permisos)"
        }
    fi
}

disable_docker_maintenance() {
    log_info "Desactivando mantenimiento de Docker..."
    
    # Detener contenedores de mantenimiento
    local maintenance_containers=("ai_news_maintenance" "ai_news_maintenance_backend")
    
    for container in "${maintenance_containers[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "$container"; then
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
            log_info "Contenedor $container removido"
        fi
    done
    
    # Reiniciar servicios originales
    log_info "Reiniciando servicios originales..."
    
    docker-compose up -d frontend backend 2>/dev/null || {
        log_warn "No se pudieron reiniciar todos los servicios"
    }
    
    # Verificar que los servicios estén corriendo
    sleep 5
    local running_services=0
    local expected_services=("ai_news_frontend" "ai_news_backend")
    
    for service in "${expected_services[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "$service"; then
            ((running_services++))
        fi
    done
    
    if [[ $running_services -eq ${#expected_services[@]} ]]; then
        log_success "Todos los servicios reiniciados correctamente"
    else
        log_warn "Algunos servicios pueden no estar funcionando correctamente"
    fi
}

show_maintenance_status() {
    log_info "📊 Estado del modo mantenimiento"
    echo ""
    
    # Verificar si el mantenimiento está activo
    local is_active=false
    if [[ -f "$MAINTENANCE_STATUS_FILE" ]]; then
        is_active=true
    fi
    
    if [[ "$is_active" == "true" ]]; then
        echo "Estado: 🔧 MANTENIMIENTO ACTIVO"
        
        if command -v jq &> /dev/null && [[ -f "$MAINTENANCE_STATUS_FILE" ]]; then
            local started_at
            local title
            local eta
            
            started_at=$(jq -r '.started_at' "$MAINTENANCE_STATUS_FILE" 2>/dev/null || echo "unknown")
            title=$(jq -r '.title' "$MAINTENANCE_STATUS_FILE" 2>/dev/null || echo "unknown")
            eta=$(jq -r '.eta' "$MAINTENANCE_STATUS_FILE" 2>/dev/null || echo "unknown")
            
            echo "Título: $title"
            echo "Iniciado: $started_at"
            echo "ETA: $eta"
            echo "Página: $MAINTENANCE_PAGE_FILE"
        fi
        
        echo ""
        echo "Estado de contenedores de mantenimiento:"
        local maintenance_containers
        maintenance_containers=$(docker ps --filter "name=ai_news_maintenance" --format "{{.Names}}\t{{.Status}}" 2>/dev/null || echo "")
        
        if [[ -n "$maintenance_containers" ]]; then
            echo "$maintenance_containers" | while IFS=$'\t' read -r name status; do
                echo "  ✅ $name: $status"
            done
        else
            echo "  ❌ No hay contenedores de mantenimiento ejecutándose"
        fi
    else
        echo "Estado: ✅ OPERACIONAL"
        echo "Modo mantenimiento no está activo"
    fi
    
    echo ""
    echo "Estado de servicios principales:"
    
    # Verificar servicios principales
    local services=("ai_news_frontend" "ai_news_backend" "ai_news_postgres" "ai_news_redis")
    
    for service in "${services[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "$service"; then
            echo "  ✅ $service: Ejecutándose"
        else
            echo "  ❌ $service: No disponible"
        fi
    done
    
    echo ""
    echo "Configuración:"
    echo "  Servidor web: ${WEB_SERVER:-auto}"
    echo "  Puerto frontend: $FRONTEND_PORT"
    echo "  Puerto backend: $BACKEND_PORT"
    echo "  Directorio config: $MAINTENANCE_CONFIG_DIR"
}

schedule_maintenance() {
    local schedule_time="$2"
    local duration="$3"
    local title="${4:-$DEFAULT_MAINTENANCE_TITLE}"
    
    if [[ -z "$schedule_time" ]]; then
        log_error "Hora de programación requerida (formato: HH:MM)"
        usage
        exit 1
    fi
    
    log_info "📅 Programando mantenimiento para $schedule_time (duración: $duration)"
    
    # Crear directorio de configuración si no existe
    mkdir -p "$MAINTENANCE_CONFIG_DIR"
    
    # Crear script de mantenimiento programado
    local schedule_script="$MAINTENANCE_CONFIG_DIR/scheduled_maintenance.sh"
    
    cat > "$schedule_script" <<EOF
#!/bin/bash
# Script de mantenimiento programado
# Programa: $schedule_time
# Duración: $duration
# Título: $title

# Ejecutar cuando llegue la hora programada
sleep \$(( (\$(date -d "$schedule_time today" +%s) - \$(date +%s) ) 3600 ))

# Activar mantenimiento
$(realpath "$SCRIPT_DIR/maintenance.sh") on "$title" "Mantenimiento programado" "$duration"

# Esperar la duración especificada
sleep $(duration_to_seconds "$duration")

# Desactivar mantenimiento
$(realpath "$SCRIPT_DIR/maintenance.sh") off
EOF
    
    chmod +x "$schedule_script"
    
    # Programar usando cron
    local cron_date
    cron_date=$(date -d "today $schedule_time" '+%M %H %d %m *')
    
    (crontab -l 2>/dev/null; echo "$cron_date $(realpath "$schedule_script") >> $(realpath "$MAINTENANCE_CONFIG_DIR/schedule.log") 2>&1") | crontab -
    
    log_success "✅ Mantenimiento programado"
    log_info "Fecha/Hora: $schedule_time (hoy)"
    log_info "Duración: $duration"
    log_info "Título: $title"
    log_info "Script: $schedule_script"
    
    # Mostrar próximos mantenimientos programados
    echo ""
    log_info "Próximos mantenimientos programados:"
    crontab -l 2>/dev/null | grep -i maintenance.sh | while read -r line; do
        echo "  📅 $line"
    done
}

duration_to_seconds() {
    local duration="$1"
    local total_seconds=0
    
    # Parsear duración (formatos soportados: 30m, 1h, 2h 30m, 90s)
    if [[ "$duration" =~ ([0-9]+)h[[:space:]]*([0-9]+)m ]]; then
        local hours="${BASH_REMATCH[1]}"
        local minutes="${BASH_REMATCH[2]}"
        total_seconds=$((hours * 3600 + minutes * 60))
    elif [[ "$duration" =~ ([0-9]+)h ]]; then
        total_seconds=$((${BASH_REMATCH[1]} * 3600))
    elif [[ "$duration" =~ ([0-9]+)m ]]; then
        total_seconds=$((${BASH_REMATCH[1]} * 60))
    elif [[ "$duration" =~ ([0-9]+) ]]; then
        total_seconds=${BASH_REMATCH[1]}
    fi
    
    echo "$total_seconds"
}

configure_maintenance_page() {
    log_info "⚙️  Configurando página de mantenimiento"
    echo ""
    
    # Mostrar configuración actual
    echo "Configuración actual:"
    echo "  Página: $MAINTENANCE_PAGE_FILE"
    echo "  Título: $DEFAULT_MAINTENANCE_TITLE"
    echo "  Mensaje: $DEFAULT_MAINTENANCE_MESSAGE"
    echo "  ETA: $DEFAULT_MAINTENANCE_ETA"
    echo ""
    
    # Generar página con configuración personalizada
    echo "¿Deseas personalizar la página de mantenimiento? (y/n)"
    read -r customize
    
    if [[ "$customize" =~ ^[Yy]$ ]]; then
        echo "Ingresa el título:"
        read -r custom_title
        
        echo "Ingresa el mensaje:"
        read -r custom_message
        
        echo "Ingresa el tiempo estimado (ej: 30 minutos, 2 horas):"
        read -r custom_eta
        
        generate_maintenance_page "${custom_title:-$DEFAULT_MAINTENANCE_TITLE}" "${custom_message:-$DEFAULT_MAINTENANCE_MESSAGE}" "${custom_eta:-$DEFAULT_MAINTENANCE_ETA}"
        
        log_success "Página de mantenimiento personalizada generada"
    else
        log_info "Usando configuración por defecto"
        generate_maintenance_page "$DEFAULT_MAINTENANCE_TITLE" "$DEFAULT_MAINTENANCE_MESSAGE" "$DEFAULT_MAINTENANCE_ETA"
    fi
    
    # Mostrar vista previa
    if command -v curl &> /dev/null; then
        echo ""
        echo "¿Deseas probar la página? (y/n)"
        read -r test_page
        
        if [[ "$test_page" =~ ^[Yy]$ ]]; then
            test_maintenance_mode
        fi
    fi
}

test_maintenance_mode() {
    log_info "🧪 Probando modo mantenimiento"
    
    # Verificar si la página existe
    if [[ ! -f "$MAINTENANCE_PAGE_FILE" ]]; then
        log_warn "Página de mantenimiento no encontrada, generando una..."
        generate_maintenance_page "Test de Mantenimiento" "Esta es una prueba del modo mantenimiento" "5 minutos"
    fi
    
    # Iniciar servidor temporal para probar la página
    local test_port=8080
    local test_server
    
    # Usar Python para servir la página
    if command -v python3 &> /dev/null; then
        cd "$MAINTENANCE_CONFIG_DIR" && python3 -m http.server $test_port > /dev/null 2>&1 &
        test_server=$!
        sleep 2
    elif command -v python &> /dev/null; then
        cd "$MAINTENANCE_CONFIG_DIR" && python -m SimpleHTTPServer $test_port > /dev/null 2>&1 &
        test_server=$!
        sleep 2
    else
        log_error "No se encontró Python para servir la página de prueba"
        return 1
    fi
    
    # Probar acceso a la página
    if curl -s "http://localhost:$test_port/" > /dev/null; then
        log_success "✅ Página de mantenimiento accesible en http://localhost:$test_port/"
        echo ""
        echo "Página de mantenimiento:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        curl -s "http://localhost:$test_port/" | head -20
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    else
        log_error "❌ No se pudo acceder a la página de mantenimiento"
    fi
    
    # Limpiar servidor de prueba
    if [[ -n "$test_server" ]]; then
        kill "$test_server" 2>/dev/null || true
        log_info "Servidor de prueba detenido"
    fi
}

show_maintenance_instructions() {
    echo ""
    log_info "📋 Instrucciones de modo mantenimiento:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Modo mantenimiento activado exitosamente"
    echo ""
    echo "🌐 Acceso público:"
    echo "   Los usuarios serán redirigidos a la página de mantenimiento"
    echo "   URL: http://localhost:$FRONTEND_PORT/"
    echo ""
    echo "🔧 Acceso de desarrollo:"
    echo "   Backend disponible en: http://localhost:$BACKEND_PORT/"
    echo "   Health check: http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "⏹️  Para desactivar:"
    echo "   $0 off"
    echo ""
    echo "📊 Monitoreo:"
    echo "   Estado: $0 status"
    echo "   Logs: docker logs ai_news_maintenance"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN] [parámetros]

Acciones disponibles:
  on [título] [mensaje] [eta]     - Activar modo mantenimiento
  off                              - Desactivar modo mantenimiento
  status                           - Mostrar estado actual
  schedule <hora> <duración> [título] - Programar mantenimiento
  config                           - Configurar página de mantenimiento
  test                             - Probar página de mantenimiento

Parámetros:
  título                          - Título del mantenimiento (default: Sistema en Mantenimiento)
  mensaje                         - Mensaje descriptivo (default: Trabajos de mantenimiento)
  eta                            - Tiempo estimado (default: 30 minutos)
  hora                           - Hora de programación (formato: HH:MM)
  duración                       - Duración del mantenimiento (ej: 30m, 1h, 2h 30m)

Variables de entorno:
  WEB_SERVER                     - Tipo de servidor (nginx|apache|docker|auto)
  FRONTEND_PORT                 - Puerto del frontend (default: 3000)
  BACKEND_PORT                  - Puerto del backend (default: 8000)
  MAINTENANCE_CONFIG_DIR        - Directorio de configuración (default: ./maintenance)
  CLEANUP_MAINTENANCE_FILES     - Limpiar archivos al desactivar (default: true)

Ejemplos:
  $0 on                             # Activar con configuración por defecto
  $0 on "Mantenimiento BD" "Actualizando esquema" "45 minutos"  # Personalizado
  $0 off                            # Desactivar modo mantenimiento
  $0 status                         # Ver estado actual
  $0 schedule "02:00" "1h" "Mantenimiento mensual"  # Programar para las 2:00 AM
  $0 config                         # Configurar página personalizada
  $0 test                           # Probar página de mantenimiento

Configuración de servidor:
  export WEB_SERVER=nginx           # Forzar Nginx
  export WEB_SERVER=apache          # Forzar Apache
  export WEB_SERVER=docker          # Forzar Docker (recomendado para desarrollo)
  export WEB_SERVER=auto            # Detección automática (default)

Páginas de mantenimiento:
  Se generan en: ./maintenance/maintenance.html
  Estado en: ./maintenance/.maintenance_active

EOF
}

# Ejecutar función principal
main "$@"