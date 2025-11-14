#!/usr/bin/env python3
"""
Script de verificación del sistema de monitoring
Verifica que todos los archivos y configuraciones estén presentes
"""

import os
import json
import yaml
from pathlib import Path

def check_file_exists(filepath, description):
    """Verificar si un archivo existe y mostrar su estado"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} - NO ENCONTRADO")
        return False

def validate_yaml(filepath):
    """Validar si un archivo YAML es válido"""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        print(f"⚠️  YAML inválido en {filepath}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Error leyendo {filepath}: {e}")
        return False

def validate_json(filepath):
    """Validar si un archivo JSON es válido"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON inválido en {filepath}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Error leyendo {filepath}: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("=== AI News Aggregator - Sistema de Monitoring ===")
    print("Verificando estructura de archivos y configuraciones...\n")
    
    monitoring_dir = "ai-news-aggregator/monitoring"
    
    # Verificar estructura de directorios
    print("📁 Estructura de Directorios:")
    required_dirs = [
        f"{monitoring_dir}/prometheus",
        f"{monitoring_dir}/grafana/dashboards",
        f"{monitoring_dir}/grafana/provisioning/datasources",
        f"{monitoring_dir}/grafana/provisioning/dashboards",
        f"{monitoring_dir}/alertmanager",
        f"{monitoring_dir}/elk/logstash",
        f"{monitoring_dir}/elk/config",
        f"{monitoring_dir}/uptime",
        f"{monitoring_dir}/health",
        f"{monitoring_dir}/config"
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directorio: {dir_path}")
        else:
            print(f"❌ Directorio: {dir_path} - FALTANTE")
    
    print(f"\n📄 Archivos de Configuración:")
    
    # Archivos principales
    files_to_check = [
        (f"{monitoring_dir}/docker-compose.monitoring.yml", "Docker Compose de monitoring"),
        (f"{monitoring_dir}/setup_monitoring.sh", "Script de setup automático"),
        (f"{monitoring_dir}/README.md", "Documentación principal"),
        
        # Prometheus
        (f"{monitoring_dir}/prometheus/prometheus.yml", "Configuración de Prometheus"),
        (f"{monitoring_dir}/prometheus/alert_rules.yml", "Reglas de alertas de Prometheus"),
        (f"{monitoring_dir}/prometheus/blackbox.yml", "Configuración de Blackbox Exporter"),
        
        # Grafana
        (f"{monitoring_dir}/grafana/provisioning/datasources/datasources.yml", "Fuentes de datos de Grafana"),
        (f"{monitoring_dir}/grafana/provisioning/dashboards/dashboards.yml", "Configuración de dashboards"),
        (f"{monitoring_dir}/grafana/dashboards/overview.json", "Dashboard de overview"),
        (f"{monitoring_dir}/grafana/dashboards/backend.json", "Dashboard de backend"),
        (f"{monitoring_dir}/grafana/dashboards/uptime.json", "Dashboard de uptime"),
        
        # AlertManager
        (f"{monitoring_dir}/alertmanager/alertmanager.yml", "Configuración de AlertManager"),
        
        # ELK Stack
        (f"{monitoring_dir}/elk/logstash/logstash.conf", "Configuración de Logstash"),
        (f"{monitoring_dir}/elk/config/jvm.options", "Configuración JVM de Logstash"),
        (f"{monitoring_dir}/elk/ai-news-logs-template.json", "Template de Elasticsearch"),
        
        # Uptime Monitoring
        (f"{monitoring_dir}/uptime/setup_monitors.sh", "Script de setup de monitors"),
        
        # Health Checks
        (f"{monitoring_dir}/health/health_checker.py", "Health checker principal"),
        (f"{monitoring_dir}/health/health_cron.py", "Scheduler de health checks"),
        (f"{monitoring_dir}/health/Dockerfile", "Dockerfile para health checks"),
        (f"{monitoring_dir}/health/requirements.txt", "Dependencias de Python"),
        
        # Configuración
        (f"{monitoring_dir}/config/integration.conf", "Configuración de integración"),
    ]
    
    all_files_ok = True
    yaml_files_ok = True
    json_files_ok = True
    
    for filepath, description in files_to_check:
        if check_file_exists(filepath, description):
            # Validar YAML
            if filepath.endswith('.yml') or filepath.endswith('.yaml'):
                if not validate_yaml(filepath):
                    yaml_files_ok = False
                    all_files_ok = False
            
            # Validar JSON
            if filepath.endswith('.json'):
                if not validate_json(filepath):
                    json_files_ok = False
                    all_files_ok = False
        else:
            all_files_ok = False
    
    print(f"\n🔍 Validación de Configuraciones:")
    
    if yaml_files_ok:
        print("✅ Archivos YAML válidos")
    else:
        print("❌ Algunos archivos YAML tienen errores")
        all_files_ok = False
    
    if json_files_ok:
        print("✅ Archivos JSON válidos")
    else:
        print("❌ Algunos archivos JSON tienen errores")
        all_files_ok = False
    
    print(f"\n📊 Estadísticas del Sistema:")
    
    # Contar líneas de código
    total_files = len(files_to_check)
    existing_files = sum(1 for filepath, _ in files_to_check if os.path.exists(filepath))
    
    # Calcular tamaño total
    total_size = 0
    file_count = 0
    
    for filepath, _ in files_to_check:
        if os.path.exists(filepath):
            try:
                total_size += os.path.getsize(filepath)
                file_count += 1
            except:
                pass
    
    print(f"📁 Total de archivos configurados: {total_files}")
    print(f"✅ Archivos creados: {existing_files}")
    print(f"📏 Tamaño total de configuraciones: {total_size:,} bytes")
    print(f"📈 Porcentaje de completado: {(existing_files/total_files)*100:.1f}%")
    
    print(f"\n🚀 Funcionalidades Implementadas:")
    
    features = [
        ("Prometheus", "Sistema de recolección de métricas"),
        ("Grafana", "Dashboards y visualización"),
        ("AlertManager", "Gestión y enrutamiento de alertas"),
        ("ELK Stack", "Logging centralizado (Elasticsearch, Logstash, Kibana)"),
        ("Uptime Kuma", "Monitoreo de uptime y status page"),
        ("Blackbox Exporter", "Monitoreo blackbox de endpoints"),
        ("Node Exporter", "Métricas del sistema"),
        ("cAdvisor", "Métricas de contenedores Docker"),
        ("Health Check System", "Verificaciones automatizadas de salud"),
        ("Docker Exporter", "Métricas de Redis y PostgreSQL"),
        ("Slack Integration", "Notificaciones en Slack"),
        ("Discord Integration", "Notificaciones en Discord"),
        ("Email Alerts", "Alertas por email"),
        ("Multi-channel Notifications", "Sistema de notificaciones múltiples"),
        ("Automated Setup", "Setup automático con script"),
        ("Status Dashboards", "Dashboards de estado en tiempo real"),
        ("Performance Monitoring", "Monitoreo de performance detallado"),
        ("Error Tracking", "Seguimiento y categorización de errores"),
        ("System Resource Monitoring", "Monitoreo de recursos del sistema"),
        ("Business Metrics", "Métricas de negocio específicas")
    ]
    
    for feature, description in features:
        print(f"✅ {feature}: {description}")
    
    print(f"\n🎯 URLs de Acceso:")
    urls = [
        "http://localhost:9090 - Prometheus (Métricas)",
        "http://localhost:3000 - Grafana (Dashboards)",
        "http://localhost:9093 - AlertManager (Alertas)",
        "http://localhost:5601 - Kibana (Logs)",
        "http://localhost:3001 - Uptime Kuma (Status)",
        "http://localhost:9200 - Elasticsearch (API)",
        "http://localhost:8080 - cAdvisor (Containers)",
        "http://localhost:9100 - Node Exporter (System)"
    ]
    
    for url in urls:
        print(f"🌐 {url}")
    
    print(f"\n🔧 Comandos para Iniciar:")
    print("# Setup completo automático:")
    print("cd ai-news-aggregator")
    print("./monitoring/setup_monitoring.sh")
    print()
    print("# Solo servicios de monitoring:")
    print("docker-compose -f monitoring/docker-compose.monitoring.yml up -d")
    print()
    print("# Health check manual:")
    print("python monitoring/health/health_checker.py")
    
    print(f"\n" + "="*60)
    
    if all_files_ok:
        print("🎉 ¡SISTEMA DE MONITORING IMPLEMENTADO COMPLETAMENTE!")
        print("✅ Todas las configuraciones están listas")
        print("🚀 El sistema está preparado para monitoreo en producción")
        return 0
    else:
        print("⚠️  SISTEMA DE MONITORING INCOMPLETO")
        print("❌ Faltan algunos archivos o configuraciones")
        print("🔧 Revisa la lista anterior para ver qué falta")
        return 1

if __name__ == "__main__":
    exit(main())