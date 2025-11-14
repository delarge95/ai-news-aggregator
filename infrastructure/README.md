# AI News Aggregator - Infraestructura DigitalOcean

Este directorio contiene toda la configuración de infraestructura para el proyecto AI News Aggregator desplegado en DigitalOcean.

## Estructura del Proyecto

```
infrastructure/
├── terraform/          # Provisioning de recursos con Terraform
├── ansible/            # Configuration management con Ansible
├── scripts/            # Scripts de automatización
├── monitoring/         # Configuración de Prometheus, Grafana y Alertmanager
├── ssl/               # Configuración SSL/TLS y Let's Encrypt
├── dns/               # Configuración de DNS y registros
└── README.md          # Esta documentación
```

## Características de la Infraestructura

### 🏗️ Provisioning (Terraform)
- **Load Balancer**: Balanceador de carga con health checks
- **Droplets**: Servidores web, workers y monitoreo
- **Database**: Cluster PostgreSQL con alta disponibilidad
- **Networking**: VPC personalizada con firewalls
- **DNS**: Configuración automática de registros
- **SSL**: Integración con Let's Encrypt

### ⚙️ Configuration Management (Ansible)
- **Docker**: Instalación y configuración de Docker/Compose
- **Nginx**: Proxy reverso con SSL y rate limiting
- **SSL**: Certificados automáticos con renovación
- **Seguridad**: Configuración de fail2ban y UFW
- **Monitoreo**: Setup de métricas y alertas

### 🔍 Monitoring Stack
- **Prometheus**: Recolección de métricas
- **Grafana**: Visualización y dashboards
- **Alertmanager**: Gestión de alertas
- **Node Exporter**: Métricas del sistema
- **cAdvisor**: Métricas de contenedores

### 🔐 SSL/TLS
- **Let's Encrypt**: Certificados automáticos
- **Traefik**: Proxy reverso con SSL automático
- **Auto-renovación**: Renovación automática
- **Múltiples dominios**: Soporte para subdominios

### 🌐 DNS
- **DigitalOcean**: Gestión automática de DNS
- **Múltiples registros**: A, CNAME, MX, TXT, CAA
- **Verificación**: Scripts de validación y propagación

### 💾 Backup Strategy
- **Base de datos**: Backups automáticos con retención
- **Archivos**: Código y configuraciones
- **SSL**: Respaldo de certificados
- **Monitoreo**: Configuración de sistemas
- **Cloud storage**: Subida automática a S3/Spaces

## Inicio Rápido

### Prerrequisitos

1. **DigitalOcean Account** con API token
2. **Terraform** >= 1.0
3. **Ansible** >= 2.9
4. **doctl** (DigitalOcean CLI)
5. **SSH keys** configuradas

### Variables de Entorno Requeridas

```bash
# Token de DigitalOcean
export DO_TOKEN="your_do_api_token"

# Dominio principal
export DOMAIN_NAME="your-domain.com"

# Entorno (dev, staging, prod)
export ENVIRONMENT="prod"

# Email para Let's Encrypt
export SSL_EMAIL="admin@your-domain.com"

# Credenciales de base de datos
export DATABASE_HOST="your-db-host"
export DATABASE_NAME="ai_news_aggregator"
export DATABASE_USER="app_user"
export DATABASE_PASSWORD="secure_password"
```

### Setup Automático

Ejecuta el script de setup principal:

```bash
./scripts/setup-digitalocean.sh
```

Este script:
1. ✅ Verifica dependencias
2. ✅ Valida configuración
3. ✅ Genera SSH keys
4. 🔧 Provisiona infraestructura con Terraform
5. ⚙️ Configura servidores con Ansible
6. 📊 Configura monitoreo
7. 🔐 Configura SSL automático
8. 🩺 Ejecuta health checks

### Setup Manual (Paso a Paso)

#### 1. Configurar Terraform

```bash
cd infrastructure/terraform

# Copiar variables de ejemplo
cp terraform.tfvars.example terraform.tfvars

# Editar variables
nano terraform.tfvars

# Inicializar Terraform
terraform init

# Planificar despliegue
terraform plan

# Aplicar configuración
terraform apply
```

#### 2. Configurar Ansible

```bash
cd infrastructure/ansible

# Crear vault password
openssl rand -base64 32 > .vault-pass.txt

# Configurar inventario
nano inventory/inventory.yml

# Ejecutar configuración
ansible-playbook -i inventory/inventory.yml playbooks/site.yml
```

#### 3. Configurar DNS

```bash
cd infrastructure/dns

# Verificar configuración DNS
./manage-dns.sh check

# Crear dominio
./manage-dns.sh setup

# Listar registros
./manage-dns.sh list
```

#### 4. Configurar SSL

```bash
cd infrastructure/ssl

# Instalar certbot
./manage-ssl.sh install

# Obtener certificados
./manage-ssl.sh obtain

# Configurar auto-renovación
./manage-ssl.sh setup-auto-renewal
```

#### 5. Setup Monitoreo

```bash
cd infrastructure/monitoring

# Ejecutar stack de monitoreo
docker-compose up -d

# Verificar servicios
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health # Grafana
```

## Scripts Disponibles

### Scripts Principales

```bash
# Setup automático completo
./scripts/setup-digitalocean.sh

# Estrategia de backup
./scripts/backup-strategy.sh
```

### DNS Management

```bash
# Verificar DNS
./dns/manage-dns.sh check

# Listar registros
./dns/manage-dns.sh list

# Agregar registro A
./dns/manage-dns.sh add-a www 192.168.1.1

# Verificar propagación
./dns/manage-dns.sh propagation www

# Generar reporte
./dns/manage-dns.sh report
```

### SSL Management

```bash
# Verificar certificados
./ssl/manage-ssl.sh check

# Renovar certificados
./ssl/manage-ssl.sh renew

# Hacer backup de certificados
./ssl/manage-ssl.sh backup

# Revocar certificado
./ssl/manage-ssl.sh revoke
```

## Configuración por Entorno

### Desarrollo (dev)
- 1 web droplet (s-1vcpu-2gb)
- 1 worker droplet (s-1vcpu-2gb)
- Database pequeña (db-s-1vcpu-1gb)
- Sin load balancer
- Dominio: dev.your-domain.com

### Staging (staging)
- 1 web droplet (s-2vcpu-4gb)
- 1 worker droplet (s-2vcpu-4gb)
- Database mediana (db-s-2vcpu-4gb)
- Sin load balancer
- Dominio: staging.your-domain.com

### Producción (prod)
- 3 web droplets (s-4vcpu-8gb)
- 2 worker droplets (s-4vcpu-8gb)
- Database grande (db-s-4vcpu-8gb)
- Con load balancer
- Monitoring dedicado
- Dominio: your-domain.com

## Monitoreo y Alertas

### URLs de Monitoreo

- **Grafana**: https://monitoring.your-domain.com
- **Prometheus**: https://prometheus.your-domain.com
- **Alertmanager**: https://alertmanager.your-domain.com
- **Traefik Dashboard**: https://traefik.your-domain.com

### Dashboards Disponibles

1. **System Overview**: Métricas generales del sistema
2. **Application Metrics**: Métricas específicas de la aplicación
3. **Database Performance**: Métricas de PostgreSQL
4. **Infrastructure**: Métricas de red y disco
5. **Business Metrics**: Métricas de negocio

### Alertas Configuradas

- 🚨 **Críticas**: Servicios caídos, alta latencia, errores
- ⚠️ **Advertencias**: Uso de recursos, SSL próximo a vencer
- 📊 **Informativas**: Tendencias, optimizaciones

## Seguridad

### Medidas Implementadas

- 🔐 **SSL/TLS**: Certificados automáticos con Let's Encrypt
- 🛡️ **Firewalls**: Configuración restrictiva de puertos
- 🔑 **SSH**: Autenticación por key, deshabilitada por password
- 🚫 **Fail2ban**: Protección contra ataques de fuerza bruta
- 🔒 **Rate Limiting**: Protección contra DoS
- 📋 **Headers de Seguridad**: CSP, HSTS, X-Frame-Options

### DNS Security

- **CAA Records**: Restricción de emisores de certificados
- **SPF Records**: Protección contra spoofing de email
- **DNSSEC**: Firma de zona DNS (opcional)

## Backup Strategy

### Componentes Respaldados

1. **Base de Datos**: Dump completo + schema
2. **Código Fuente**: Archivos de aplicación
3. **Configuraciones**: Terraform, Ansible, Nginx
4. **SSL Certificados**: Let's Encrypt
5. **Monitoreo**: Configuraciones de Grafana/Prometheus

### Retención

- **Diarios**: 7 días
- **Semanales**: 4 semanas
- **Mensuales**: 6 meses

### Storage

- **Local**: Directorio `/opt/backups`
- **Remoto**: DigitalOcean Spaces (opcional)
- **Encriptación**: GPG con clave personalizable

## Troubleshooting

### Problemas Comunes

#### Terraform Error: "Invalid credentials"
```bash
# Verificar token
export DO_TOKEN="your_token"
echo $DO_TOKEN | wc -c  # Debe ser > 10 caracteres
```

#### Ansible Connection Error
```bash
# Verificar SSH key
ssh -i ~/.ssh/ai-news-prod.key root@your-server-ip

# Verificar configuración de inventario
ansible all -i inventory/inventory.yml -m ping
```

#### SSL Certificate Error
```bash
# Verificar DNS
dig your-domain.com

# Renovar certificado
./ssl/manage-ssl.sh renew

# Verificar logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

#### Monitoreo No Funciona
```bash
# Verificar contenedores Docker
docker ps

# Verificar logs
docker logs ai-news-prometheus
docker logs ai-news-grafana

# Verificar configuración
docker exec ai-news-prometheus cat /etc/prometheus/prometheus.yml
```

### Logs Importantes

```bash
# Terraform
tail -f /tmp/ai-news-setup-*.log

# Nginx
sudo tail -f /var/log/nginx/error.log

# Docker
docker logs ai-news-web

# SSL
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Fail2ban
sudo tail -f /var/log/fail2ban.log
```

## Mantenimiento

### Tareas Regulares

#### Semanal
- [ ] Verificar health checks
- [ ] Revisar logs de errores
- [ ] Verificar uso de recursos
- [ ] Actualizar paquetes del sistema

#### Mensual
- [ ] Ejecutar backup manual
- [ ] Verificar SSL certificates
- [ ] Revisar métricas de performance
- [ ] Limpiar logs antiguos

#### Trimestral
- [ ] Actualizar Terraform/Ansable
- [ ] Revisar configuración de seguridad
- [ ] Auditar accesos SSH
- [ ] Planificar escalabilidad

### Comandos de Mantenimiento

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Limpiar logs
sudo journalctl --vacuum-time=7d

# Verificar espacio en disco
df -h

# Verificar servicios
sudo systemctl status nginx docker

# Ejecutar backup manual
./scripts/backup-strategy.sh

# Verificar SSL
./ssl/manage-ssl.sh check
```

## Escalabilidad

### Optimizaciones Disponibles

1. **Auto-scaling**: Configuración para scale automático
2. **CDN**: Integración con Cloudflare
3. **Caching**: Redis para session/data caching
4. **Database**: Read replicas para mejor performance
5. **Monitoring**: Alertas predictivas

### Plan de Escalado

#### Nivel 1: Web Servers
- Escalar horizontalmente web droplets
- Configurar session affinity en load balancer

#### Nivel 2: Database
- Agregar read replicas
- Implementar connection pooling

#### Nivel 3: Application
- Escalar workers Celery
- Implementar message queue clustering

## Contacto y Soporte

- **Email**: admin@ai-news-aggregator.com
- **Documentación**: https://docs.your-domain.com
- **Issues**: GitHub repository

## Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.