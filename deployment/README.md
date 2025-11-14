# Configuración de Dominio, SSL y CDN - AI News Aggregator

Este directorio contiene la configuración completa para el deployment seguro de AI News Aggregator con dominio, SSL, CDN, y todas las medidas de seguridad necesarias.

## 🏗️ Estructura del Directorio

```
deployment/
├── nginx/                    # Configuración de Nginx
│   ├── nginx.conf           # Configuración principal
│   ├── sites-enabled/       # Sitios virtuales
│   └── conf.d/             # Configuraciones comunes
├── certbot/                 # Let's Encrypt automation
│   ├── certbot.ini         # Configuración de Certbot
│   └── renew-certs.sh      # Script de renovación
├── cloudflare/              # CDN y Workers
│   ├── cloudflare-config.json # Configuración de Cloudflare
│   ├── worker.js           # Worker para API
│   └── cache-worker.js     # Worker para cache
├── dns/                    # Gestión de DNS
│   └── dns-manager.sh      # Script de gestión DNS
├── security/               # Headers y protección
│   ├── security-headers.conf # Headers de seguridad
│   └── ddos-protection.conf # Protección DDoS
├── firewall/               # Configuración de firewall
│   └── firewall.sh         # Script de configuración
├── load-balancer/          # HAProxy
│   └── haproxy.cfg         # Configuración de Load Balancer
├── docker-compose.deployment.yml # Compose para deployment
└── scripts/               # Scripts de configuración
    ├── setup.sh           # Setup automático
    ├── health-check.sh    # Health checks
    └── deploy.sh          # Deployment script
```

## 🚀 Configuración Rápida

### 1. Configuración Inicial

```bash
# Clonar el proyecto
git clone <repository>
cd ai-news-aggregator/deployment

# Hacer ejecutables los scripts
chmod +x scripts/*.sh certbot/renew-certs.sh dns/dns-manager.sh firewall/firewall.sh

# Configurar variables de entorno
cp .env.example .env
# Editar .env con las configuraciones específicas
```

### 2. Variables de Entorno Requeridas

```bash
# .env file
POSTGRES_PASSWORD=your_secure_password_here
GRAFANA_PASSWORD=admin_password_here
CLOUDFLARE_API_TOKEN=your_cloudflare_token
CLOUDFLARE_EMAIL=your_email@domain.com
DOMAIN_PRODUCTION=ainews.production.ai
DOMAIN_STAGING=ainews.staging.ai
SSL_EMAIL=admin@ainews.production.ai
```

### 3. Setup Automático

```bash
# Ejecutar setup completo
./scripts/setup.sh

# O configuración paso a paso
./scripts/setup.sh --step 1  # DNS
./scripts/setup.sh --step 2  # SSL
./scripts/setup.sh --step 3  # Seguridad
./scripts/setup.sh --step 4  # Deploy
```

## 🔧 Configuraciones Incluidas

### 1. Nginx con SSL y Seguridad

- **SSL/HTTPS**: Configuración moderna con TLS 1.2/1.3
- **Rate Limiting**: Por IP, usuario y endpoint
- **Compresión**: Gzip y Brotli
- **Headers de Seguridad**: CSP, HSTS, X-Frame-Options, etc.
- **Cache**: Configuración de cache para recursos estáticos
- **Proxy**: Configuración de proxy reverso para servicios

### 2. Certbot para Let's Encrypt

- **Renovación Automática**: Script de renovación cada 12 horas
- **Múltiples Dominios**: Soporte para dominios y wildcards
- **Verificación Webroot**: Para validación sin downtime
- **Configuración Robusta**: Manejo de errores y logging

### 3. Cloudflare CDN

- **Caching Inteligente**: Por tipo de contenido
- **Workers Personalizados**: Procesamiento de API y cache
- **Seguridad**: DDoS protection, WAF, rate limiting
- **SSL**: Full (Strict) SSL mode
- **Optimización**: Minificación, compresión, HTTP/2/3

### 4. Gestión de DNS

- **Script Automatizado**: Gestión completa de registros DNS
- **Cloudflare API**: Integración nativa con Cloudflare
- **Múltiples Ambientes**: Producción, staging, desarrollo
- **Verificación**: Health checks de configuración DNS

### 5. Seguridad Avanzada

- **Headers de Seguridad**: CSP, HSTS, XSS Protection, etc.
- **Protección DDoS**: Rate limiting, geoblocking, pattern matching
- **Firewall**: iptables/ufw con reglas específicas
- **Headers de Cache**: Configuración por tipo de contenido

### 6. Load Balancing

- **HAProxy**: Load balancer profesional
- **Algoritmos**: Round-robin, least connections, IP hash
- **Health Checks**: Verificación de salud de backends
- **SSL Termination**: Termina SSL en el load balancer
- **Sticky Sessions**: Para WebSocket y sesiones

### 7. Múltiples Dominios

- **Dominios de Producción**: ainews.production.ai
- **Dominios de Staging**: ainews.staging.ai
- **Subdominios Dinámicos**: user[0-9]*, team[0-9]*, demo[0-9]*
- **Servicios Separados**: API, CDN, Admin, Docs
- **SSL por Dominio**: Certificados específicos por dominio

## 🛠️ Comandos Útiles

### Gestión de DNS

```bash
# Listar registros DNS
./dns/dns-manager.sh list-domain ainews.production.ai

# Configurar DNS para producción
./dns/dns-manager.sh setup-prod

# Configurar DNS para staging
./dns/dns-manager.sh setup-stage

# Verificar configuración
./dns/dns-manager.sh verify ainews.production.ai
```

### Gestión de SSL

```bash
# Renovar certificados
./certbot/renew-certs.sh

# Obtener nuevos certificados
./certbot/renew-certs.sh --new-certs

# Verificar estado de certificados
certbot certificates
```

### Gestión de Firewall

```bash
# Configurar firewall (requiere root)
sudo ./firewall/firewall.sh

# Solo mostrar reglas sin aplicar
./firewall/firewall.sh --preview
```

### Deploy con Docker Compose

```bash
# Deploy completo
docker-compose -f docker-compose.deployment.yml up -d

# Solo servicios específicos
docker-compose -f docker-compose.deployment.yml up -d nginx haproxy

# Con monitoreo
docker-compose -f docker-compose.deployment.yml --profile monitoring up -d

# Con backup
docker-compose -f docker-compose.deployment.yml --profile backup run postgres_backup
```

## 🔍 Monitoreo y Health Checks

### Endpoints de Health Check

- `https://ainews.production.ai/health` - Health check principal
- `http://localhost:8404/stats` - HAProxy stats (requiere auth)
- `http://localhost:3000` - Grafana dashboard (perfil monitoring)
- `http://localhost:9090` - Prometheus metrics

### Logs Importantes

```bash
# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Certbot logs
tail -f /var/log/certbot-renewal.log

# HAProxy logs
tail -f /var/log/haproxy.log

# Docker logs
docker-compose -f docker-compose.deployment.yml logs -f nginx
docker-compose -f docker-compose.deployment.yml logs -f haproxy
```

## 🚨 Seguridad

### Medidas Implementadas

1. **SSL/HTTPS**: Configuración moderna con Perfect Forward Secrecy
2. **Rate Limiting**: Múltiples niveles de limitación de velocidad
3. **Headers de Seguridad**: CSP, HSTS, XSS Protection, etc.
4. **DDoS Protection**: Geoblocking, pattern matching, connection limiting
5. **Firewall**: Reglas específicas por puerto y protocolo
6. **Certificados**: Renovación automática y verificación
7. **CORS**: Configuración restrictiva por dominio

### Auditoría de Seguridad

```bash
# Verificar configuración SSL
sslscan ainews.production.ai

# Verificar headers de seguridad
curl -I https://ainews.production.ai

# Verificar rate limiting
curl -H "User-Agent: test" https://ainews.production.ai/api/test

# Verificar configuración DNS
dig ainews.production.ai
```

## 🔧 Troubleshooting

### Problemas Comunes

1. **Certificados SSL no se renuevan**
   ```bash
   # Verificar logs
   tail -f /var/log/certbot-renewal.log
   # Forzar renovación
   ./certbot/renew-certs.sh --force-renewal
   ```

2. **Rate limiting muy restrictivo**
   ```bash
   # Verificar configuración
   grep "limit_req" nginx/sites-enabled/*
   # Ajustar límites en nginx.conf
   ```

3. **DNS no resuelve**
   ```bash
   # Verificar configuración DNS
   ./dns/dns-manager.sh verify ainews.production.ai
   # Verificar propagación
   dig @8.8.8.8 ainews.production.ai
   ```

4. **Load balancer no balancea**
   ```bash
   # Verificar stats de HAProxy
   curl http://localhost:8404/stats
   # Verificar logs
   tail -f /var/log/haproxy.log
   ```

## 📚 Referencias

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Cloudflare Documentation](https://developers.cloudflare.com/)
- [HAProxy Documentation](https://www.haproxy.org/#docs)
- [Docker Security](https://docs.docker.com/engine/security/)

## 🆘 Soporte

Para problemas específicos:

1. Verificar logs en `/var/log/`
2. Ejecutar health checks con `./scripts/health-check.sh`
3. Revisar configuración con `./scripts/verify-config.sh`
4. Consultar troubleshooting guide arriba

## 📝 Notas de Actualización

- **v1.0.0**: Configuración inicial completa
- Actualizaciones futuras en CHANGELOG.md

---

**Nota**: Esta configuración está diseñada para un entorno de producción. Para desarrollo, ajustar según sea necesario.