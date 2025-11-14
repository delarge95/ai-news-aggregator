# 🔧 CI/CD Pipeline Configuration Guide

## 📋 Overview

Este documento describe la configuración completa del pipeline CI/CD para el proyecto AI News Aggregator.

## 🗂️ Estructura del Pipeline

El pipeline incluye los siguientes workflows:

1. **ci.yml** - Testing automatizado (unit, integration, e2e)
2. **security-scan.yml** - Análisis de vulnerabilidades
3. **docker-build.yml** - Builds automatizados
4. **deploy-staging.yml** - Deploy a staging
5. **deploy-production.yml** - Deploy a producción
6. **notification.yml** - Sistema de alertas

## 🔐 Secrets Configuration

### GitHub Repository Secrets

Los siguientes secrets deben configurados en `Settings > Secrets and variables > Actions`:

#### Core Secrets
```bash
# Database connection strings
STAGING_KUBECONFIG=<base64-encoded-staging-kubeconfig>
PRODUCTION_KUBECONFIG=<base64-encoded-production-kubeconfig>

# Database URLs (used in deployments)
STAGING_DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/ai_news_db
PRODUCTION_DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/ai_news_db

# Redis URLs
STAGING_REDIS_URL=redis://staging-redis:6379
PRODUCTION_REDIS_URL=redis://prod-redis:6379

# Celery configuration
STAGING_CELERY_BROKER_URL=redis://staging-redis:6379
PRODUCTION_CELERY_BROKER_URL=redis://prod-redis:6379
STAGING_CELERY_RESULT_BACKEND=redis://staging-redis:6379
PRODUCTION_CELERY_RESULT_BACKEND=redis://prod-redis:6379

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
```

#### Notification Secrets
```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Microsoft Teams
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=123456789

# Email (SMTP)
EMAIL_FROM=noreply@ainews.example.com
EMAIL_TO=alerts@ainews.example.com,dev-team@ainews.example.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=username@gmail.com
EMAIL_PASSWORD=app-password

# PagerDuty (for production alerts)
PAGERDUTY_INTEGRATION_KEY=...
```

#### Optional Secrets
```bash
# Codecov token (for coverage reporting)
CODECOV_TOKEN=...

# SonarCloud token
SONAR_TOKEN=...

# Docker registry credentials (if not using GitHub Container Registry)
DOCKER_USERNAME=...
DOCKER_PASSWORD=...

# AWS credentials (if deploying to AWS EKS)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

## 🌐 Environment Variables

### GitHub Repository Variables

Configurar en `Settings > Secrets and variables > Actions > Variables`:

```bash
# Registry configuration
REGISTRY=ghcr.io
BACKEND_IMAGE_NAME=your-username/ai-news-aggregator-backend
FRONTEND_IMAGE_NAME=your-username/ai-news-aggregator-frontend

# Environment names
STAGING_NAMESPACE=ai-news-staging
PRODUCTION_NAMESPACE=ai-news-production

# Service names
BACKEND_SERVICE_NAME=ai-news-backend
FRONTEND_SERVICE_NAME=ai-news-frontend

# URLs
STAGING_URL=https://staging.ainews.example.com
PRODUCTION_URL=https://ainews.example.com
API_STAGING_URL=https://api-staging.ainews.example.com
API_PRODUCTION_URL=https://api.ainews.example.com

# Testing configuration
COVERAGE_THRESHOLD=80
PERFORMANCE_TEST_DURATION=300
LOAD_TEST_CONCURRENT_USERS=50
```

### Pipeline Environment Variables

#### CI Pipeline (ci.yml)
```bash
# Testing
TEST_TIMEOUT=300
PARALLEL_TEST_WORKERS=4
COVERAGE_THRESHOLD=80

# Database test configuration
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_news_db_test
TEST_REDIS_URL=redis://localhost:6379/1

# Frontend testing
E2E_TEST_TIMEOUT=600
PLAYWRIGHT_BROWSERS=chromium,firefox,webkit
```

#### Security Scan (security-scan.yml)
```bash
# Security scan configuration
SAST_TOOLS=bandit,semgrep,codeql
DAST_ENABLED=true
DEPENDENCY_SCAN_ENABLED=true
CONTAINER_SCAN_ENABLED=true
INFRASTRUCTURE_SCAN_ENABLED=true

# Vulnerability thresholds
CRITICAL_VULNERABILITIES_THRESHOLD=0
HIGH_VULNERABILITIES_THRESHOLD=5
```

#### Docker Build (docker-build.yml)
```bash
# Build configuration
BUILD_CACHE_ENABLED=true
MULTI_PLATFORM_BUILD=true
PLATFORMS=linux/amd64,linux/arm64
BUILD_TIMEOUT=3600

# Registry configuration
PUSH_REGISTRY=true
REGISTRY_CACHE=true
```

#### Deployment Pipelines

##### Staging Deployment (deploy-staging.yml)
```bash
# Deployment strategy
DEFAULT_DEPLOYMENT_STRATEGY=blue-green
ROLLBACK_ENABLED=true
HEALTH_CHECK_TIMEOUT=300
DEPLOYMENT_TIMEOUT=600

# Monitoring
MONITORING_ENABLED=true
ALERTING_ENABLED=true
METRICS_ENABLED=true
```

##### Production Deployment (deploy-production.yml)
```bash
# Production deployment
DEFAULT_DEPLOYMENT_STRATEGY=blue-green
CANARY_ENABLED=true
AUTO_ROLLBACK_ENABLED=true
BLUE_GREEN_ENABLED=true

# Safety checks
PRODUCTION_CHECKS_ENABLED=true
DATABASE_MIGRATION_TIMEOUT=300
PRODUCTION_HEALTH_CHECK_TIMEOUT=600

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
ALERT_MANAGER_ENABLED=true
```

#### Notification Pipeline (notification.yml)
```bash
# Notification configuration
NOTIFICATION_CHANNELS=slack,teams,email,discord,telegram
NOTIFICATION_SUMMARY_ENABLED=true
ALERT_SEVERITY_PRODUCTION=critical
ALERT_SEVERITY_STAGING=warning
ALERT_SEVERITY_CI=info
```

## 🏗️ Infrastructure Configuration

### Kubernetes Configuration

#### Namespace Configuration
```yaml
# staging namespace
apiVersion: v1
kind: Namespace
metadata:
  name: ai-news-staging
  labels:
    environment: staging
    monitoring: enabled
---
# production namespace
apiVersion: v1
kind: Namespace
metadata:
  name: ai-news-production
  labels:
    environment: production
    monitoring: enabled
```

#### Secrets Management
```yaml
# staging-secrets
apiVersion: v1
kind: Secret
metadata:
  name: staging-secrets
  namespace: ai-news-staging
type: Opaque
data:
  database-url: <base64-encoded-db-url>
  redis-url: <base64-encoded-redis-url>
  celery-broker-url: <base64-encoded-celery-broker>
  celery-result-backend: <base64-encoded-celery-backend>
  openai-api-key: <base64-encoded-openai-key>

---
# production-secrets
apiVersion: v1
kind: Secret
metadata:
  name: production-secrets
  namespace: ai-news-production
type: Opaque
data:
  database-url: <base64-encoded-db-url>
  redis-url: <base64-encoded-redis-url>
  celery-broker-url: <base64-encoded-celery-broker>
  celery-result-backend: <base64-encoded-celery-backend>
  openai-api-key: <base64-encoded-openai-key>
```

#### RBAC Configuration
```yaml
# GitHub Actions service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: github-actions
  namespace: ai-news-staging
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: github-actions
  namespace: ai-news-production
```

#### Network Policies
```yaml
# Network policy for staging
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: staging-network-policy
  namespace: ai-news-staging
spec:
  podSelector:
    matchLabels:
      app: ai-news-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ai-news-staging
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
```

## 📊 Monitoring Configuration

### Prometheus Configuration
```yaml
# prometheus-config
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'ai-news-backend-staging'
      static_configs:
      - targets: ['ai-news-backend-staging.ai-news-staging:80']
    - job_name: 'ai-news-backend-production'
      static_configs:
      - targets: ['ai-news-backend.ai-news-production:80']
```

### Grafana Dashboards
```yaml
# Grafana dashboard configmap
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-news-dashboard
  namespace: monitoring
data:
  ai-news-dashboard.json: |
    {
      "dashboard": {
        "title": "AI News Aggregator",
        "panels": [...]
      }
    }
```

### Alert Manager Configuration
```yaml
# alert-manager-config
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'alerts@ainews.example.com'
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://alertmanager-webhook:5000/'
```

## 🔄 Rollback Strategy

### Automated Rollback Triggers
```yaml
# Rollback conditions:
# 1. Health check failures
# 2. Response time > 5 seconds
# 3. Error rate > 10%
# 4. Database migration failures
# 5. Manual trigger
```

### Rollback Commands
```bash
# Rollback staging
kubectl rollout undo deployment/ai-news-backend-staging -n ai-news-staging

# Rollback production
kubectl rollout undo deployment/ai-news-backend -n ai-news-production

# Rollback to specific version
kubectl rollout undo deployment/ai-news-backend --to-revision=2 -n ai-news-production
```

## 🧪 Testing Strategy

### Test Categories
1. **Unit Tests** - Fast, isolated tests
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Full user journey testing
4. **Performance Tests** - Load and stress testing
5. **Security Tests** - Vulnerability scanning

### Coverage Requirements
```bash
# Minimum coverage thresholds
Backend: 80%
Frontend: 75%
Overall: 80%

# Performance benchmarks
Response time: < 500ms (95th percentile)
Throughput: > 1000 requests/second
Error rate: < 0.1%
```

## 🚀 Deployment Strategies

### Blue-Green Deployment
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### Canary Deployment
```yaml
strategy:
  canary:
    steps:
    - setWeight: 10
    - pause: {duration: 30s}
    - setWeight: 50
    - pause: {duration: 60s}
    - setWeight: 100
```

## 📋 Configuration Checklist

### Pre-deployment Checklist
- [ ] Secrets configured in GitHub
- [ ] Environment variables set
- [ ] Kubernetes cluster configured
- [ ] Database migrations tested
- [ ] Monitoring configured
- [ ] Alert channels configured
- [ ] Rollback plan tested

### Staging Deployment Checklist
- [ ] CI pipeline passed
- [ ] Security scans completed
- [ ] Staging environment healthy
- [ ] Database migrations applied
- [ ] Smoke tests passed
- [ ] Performance benchmarks met

### Production Deployment Checklist
- [ ] Staging deployment successful
- [ ] All checks passed
- [ ] On-call team notified
- [ ] Rollback plan ready
- [ ] Monitoring active
- [ ] Alerts configured

## 🔧 Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Check RBAC permissions
kubectl auth can-i create deployments --as=system:serviceaccount:ai-news-staging:github-actions
```

#### Image Pull Failures
```bash
# Check image availability
docker pull ghcr.io/username/ai-news-aggregator-backend:latest
```

#### Health Check Failures
```bash
# Check pod status
kubectl get pods -n ai-news-staging
kubectl describe pod <pod-name> -n ai-news-staging
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it <pod-name> -n ai-news-staging -- python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql+asyncpg://user:pass@host:5432/db')
    await conn.execute('SELECT 1')
asyncio.run(test())
"
```

## 📞 Support

### Contact Information
- **On-call**: Available via PagerDuty
- **Slack**: #devops-support
- **Email**: devops@ainews.example.com

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

📝 **Note**: Actualizar este documento cuando se modifique la configuración del pipeline.