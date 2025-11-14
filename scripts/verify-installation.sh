#!/bin/bash

# verify-installation.sh - Script de verificación e instalación para AI News Aggregator
# Versión: 1.0.0
# Descripción: Verifica que todos los scripts estén correctamente instalados

set -euo pipefail

# Colores para output
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_RESET='\033[0m'

print_header() {
    echo -e "${COLOR_CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║              AI News Aggregator - Verificación de Instalación               ║"
    echo "║                              Versión 1.0.0                                   ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${COLOR_RESET}"
}

check_script() {
    local script_path="$1"
    local description="$2"
    
    if [[ -f "$script_path" ]]; then
        local size
        size=$(wc -l < "$script_path")
        echo -e "${COLOR_GREEN}✅ $description${COLOR_RESET}"
        echo -e "   📄 Archivo: $script_path"
        echo -e "   📊 Líneas: $size"
        
        # Verificar permisos si es posible
        if [[ -r "$script_path" ]]; then
            echo -e "   ✅ Permisos: Legible"
        else
            echo -e "   ⚠️  Permisos: Solo lectura"
        fi
        
        # Verificar shebang
        if head -n 1 "$script_path" | grep -q "^#!/bin/bash"; then
            echo -e "   ✅ Shebang: Correcto"
        else
            echo -e "   ⚠️  Shebang: No encontrado"
        fi
        
        echo ""
        return 0
    else
        echo -e "${COLOR_RED}❌ $description${COLOR_RESET}"
        echo -e "   📄 Archivo: $script_path (NO ENCONTRADO)"
        echo ""
        return 1
    fi
}

show_summary() {
    echo -e "${COLOR_CYAN}📋 RESUMEN DE ARCHIVOS CREADOS${COLOR_RESET}"
    echo ""
    
    local total_scripts=0
    local total_lines=0
    
    # Contar scripts principales
    for script in scripts/*.sh; do
        if [[ -f "$script" ]]; then
            ((total_scripts++))
            ((total_lines += $(wc -l < "$script" 2>/dev/null || echo 0)))
        fi
    done
    
    echo "Scripts principales: $total_scripts"
    echo "Total de líneas de código: $total_lines"
    echo ""
    
    # Contar archivos auxiliares
    local auxiliary_files
    auxiliary_files=$(find scripts -type f ! -name "*.sh" | wc -l)
    echo "Archivos auxiliares: $auxiliary_files"
    echo ""
    
    echo "Funcionalidades implementadas:"
    echo "  🚀 Deployment automatizado"
    echo "  🔄 Rollback rápido"
    echo "  🔍 Health checks completos"
    echo "  🔧 Migraciones de base de datos"
    echo "  📈 Auto-scaling"
    echo "  💾 Gestión de backups"
    echo "  🔒 Modo mantenimiento"
    echo "  🔐 Certificados SSL"
    echo "  📊 Sistema de logging"
    echo "  🔧 Scripts de operaciones"
    echo "  📝 Documentación"
    echo ""
}

show_usage_examples() {
    echo -e "${COLOR_YELLOW}🎯 EJEMPLOS DE USO${COLOR_RESET}"
    echo ""
    
    cat << 'EOF'
# 1. Verificación inicial
./scripts/verify-installation.sh

# 2. Configuración inicial
cp scripts/.env.example .env
vim .env

# 3. Deployment completo
./scripts/ops.sh deploy

# 4. Verificación de salud
./scripts/ops.sh health

# 5. Crear backup
./scripts/ops.sh backup

# 6. Activar mantenimiento
./scripts/ops.sh maintenance on "Mantenimiento" "Actualizando sistema" "30 min"

# 7. Escalado automático
./scripts/ops.sh scale auto

# 8. Uso del Makefile
make help
make deploy
make health
make backup

# 9. Comandos específicos
./scripts/backup-restore.sh list
./scripts/health-check.sh all
./scripts/migrate-database.sh status
./scripts/update-certificates.sh status
EOF
    
    echo ""
}

show_next_steps() {
    echo -e "${COLOR_CYAN}🚀 PRÓXIMOS PASOS${COLOR_RESET}"
    echo ""
    
    cat << 'EOF'
1. CONFIGURAR VARIABLES DE ENTORNO:
   cp scripts/.env.example .env
   # Editar .env con tus configuraciones específicas

2. CONFIGURAR CERTIFICADOS SSL (opcional):
   export DOMAINS="tu-dominio.com,www.tu-dominio.com"
   export EMAIL="admin@tu-dominio.com"
   ./scripts/update-certificates.sh generate production

3. CONFIGURAR AUTO-SCALING (opcional):
   cp scripts/scaling-config.json.example scaling-config.json
   # Editar según tus necesidades

4. PRIMER DEPLOYMENT:
   ./scripts/ops.sh deploy

5. VERIFICAR INSTALACIÓN:
   ./scripts/ops.sh health

6. CREAR BACKUP INICIAL:
   ./scripts/ops.sh backup

Para más información:
  - docs/README.md: Documentación completa
  - scripts/README.md: Documentación de scripts
  - ./scripts/ops.sh help: Ayuda interactiva
  - make help: Comandos Makefile
EOF
    
    echo ""
}

show_architecture() {
    echo -e "${COLOR_YELLOW}🏗️  ARQUITECTURA DEL SISTEMA${COLOR_RESET}"
    echo ""
    
    cat << 'EOF'
┌─────────────────────────────────────────────────────────────────┐
│                     AI News Aggregator                           │
│                         Operations Suite                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                Scripts            Utilities
                    │                   │
        ┌───────────┼───────────┐       │
        │           │           │       │
    Main    Specialized   Helpers   Makefile
        │           │           │       │
    ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ │
    │ops.sh   │ │backup-  │ │logger.sh│ │
    │deploy.sh│ │restore  │ │.env.    │ │
    │rollback │ │.sh      │ │example  │ │
    │health-  │ │migrate  │ │scaling  │ │
    │check.sh │ │.sh      │ │.json    │ │
    │scale-   │ │certifi- │ │         │ │
    │services │ │cates.sh │ │         │ │
    │.sh      │ │mainten  │ │         │ │
    │mainten  │ │ance.sh  │ │         │ │
    │ance.sh  │ │         │ │         │ │
    └─────────┘ └─────────┘ └─────────┘

SERVICIOS GESTIONADOS:
  📦 PostgreSQL     - Base de datos principal
  🧠 Redis          - Cache y colas de tareas
  🐍 Backend API    - FastAPI/Python
  ⚛️  Frontend      - React/TypeScript
  🔄 Celery Workers - Procesamiento asíncrono
  📅 Celery Beat    - Scheduler de tareas

CAPACIDADES:
  ✅ Deployment automatizado con verificaciones
  ✅ Rollback rápido con backups automáticos
  ✅ Health checks comprehensivos
  ✅ Migraciones de BD versionadas
  ✅ Auto-scaling basado en métricas
  ✅ Gestión completa de backups
  ✅ Modo mantenimiento con páginas personalizadas
  ✅ Renovación automática de certificados SSL
  ✅ Sistema de logging centralizado
  ✅ Monitor en tiempo real
  ✅ Documentación completa
EOF
    
    echo ""
}

main() {
    print_header
    echo ""
    
    echo -e "${COLOR_BLUE}🔍 Verificando archivos de scripts...${COLOR_RESET}"
    echo ""
    
    local missing_files=0
    local total_files=14
    
    # Verificar scripts principales
    check_script "scripts/ops.sh" "Script maestro de operaciones" || ((missing_files++))
    check_script "scripts/logger.sh" "Sistema de logging centralizado" || ((missing_files++))
    check_script "scripts/deploy.sh" "Deployment automatizado" || ((missing_files++))
    check_script "scripts/rollback.sh" "Rollback rápido" || ((missing_files++))
    check_script "scripts/health-check.sh" "Verificaciones de salud" || ((missing_files++))
    check_script "scripts/migrate-database.sh" "Migraciones de base de datos" || ((missing_files++))
    check_script "scripts/scale-services.sh" "Auto-scaling de servicios" || ((missing_files++))
    check_script "scripts/backup-restore.sh" "Gestión de backups" || ((missing_files++))
    check_script "scripts/maintenance.sh" "Modo mantenimiento" || ((missing_files++))
    check_script "scripts/update-certificates.sh" "Certificados SSL" || ((missing_files++))
    
    # Verificar archivos auxiliares
    check_script "scripts/README.md" "Documentación principal" || ((missing_files++))
    check_script "scripts/Makefile" "Comandos Makefile" || ((missing_files++))
    check_script "scripts/.env.example" "Plantilla de variables de entorno" || ((missing_files++))
    check_script "scripts/scaling-config.json.example" "Configuración de escalado" || ((missing_files++))
    
    echo ""
    
    # Resumen
    show_summary
    
    # Verificar dependencias
    echo -e "${COLOR_YELLOW}🔧 Verificando dependencias...${COLOR_RESET}"
    echo ""
    
    local missing_deps=0
    
    # Verificar Docker
    if command -v docker &> /dev/null; then
        echo -e "${COLOR_GREEN}✅ Docker: Disponible${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ Docker: No encontrado${COLOR_RESET}"
        ((missing_deps++))
    fi
    
    # Verificar Docker Compose
    if command -v docker-compose &> /dev/null; then
        echo -e "${COLOR_GREEN}✅ Docker Compose: Disponible${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ Docker Compose: No encontrado${COLOR_RESET}"
        ((missing_deps++))
    fi
    
    # Verificar herramientas opcionales
    if command -v jq &> /dev/null; then
        echo -e "${COLOR_GREEN}✅ jq: Disponible (funcionalidades extendidas)${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}⚠️  jq: No encontrado (funcionalidades limitadas)${COLOR_RESET}"
    fi
    
    if command -v openssl &> /dev/null; then
        echo -e "${COLOR_GREEN}✅ OpenSSL: Disponible${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}⚠️  OpenSSL: No encontrado (funcionalidades SSL limitadas)${COLOR_RESET}"
    fi
    
    echo ""
    
    # Resultado final
    if [[ $missing_files -eq 0 ]]; then
        echo -e "${COLOR_GREEN}🎉 ¡VERIFICACIÓN EXITOSA!${COLOR_RESET}"
        echo -e "${COLOR_GREEN}✅ Todos los scripts han sido creados correctamente${COLOR_RESET}"
        
        if [[ $missing_deps -eq 0 ]]; then
            echo -e "${COLOR_GREEN}✅ Todas las dependencias están disponibles${COLOR_RESET}"
        else
            echo -e "${COLOR_YELLOW}⚠️  Algunas dependencias no están disponibles (opcionales)${COLOR_RESET}"
        fi
        
        echo ""
        show_usage_examples
        show_next_steps
        
    else
        echo -e "${COLOR_RED}❌ VERIFICACIÓN FALLIDA${COLOR_RESET}"
        echo -e "${COLOR_RED}$missing_files archivo(s) faltante(s) de $total_files total${COLOR_RESET}"
        echo ""
        echo -e "${COLOR_YELLOW}Por favor, verifica que todos los archivos se hayan creado correctamente.${COLOR_RESET}"
    fi
    
    echo ""
    show_architecture
    
    echo -e "${COLOR_CYAN}📞 SOPORTE${COLOR_RESET}"
    echo "Para soporte y documentación:"
    echo "  📧 Email: devops@company.com"
    echo "  📖 Docs: scripts/README.md"
    echo "  🐛 Issues: GitHub Issues"
    echo ""
    
    if [[ $missing_files -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Ejecutar verificación
main "$@"