# Configuración de Monitoreo y Observabilidad

## Tabla de Contenidos
- [Stack de Monitoreo](#stack-de-monitoreo)
- [Prometheus Setup](#prometheus-setup)
- [Grafana Configuration](#grafana-configuration)
- [APM con Sentry](#apm-con-sentry)
- [Logging Centralizado](#logging-centralizado)
- [Alertas y Notificaciones](#alertas-y-notificaciones)
- [Dashboards](#dashboards)
- [Métricas Personalizadas](#métricas-personalizadas)
- [Troubleshooting](#troubleshooting)

## Stack de Monitoreo

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoreo Stack                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Prometheus  │  │   Grafana   │  │    Sentry   │             │
│  │ (Metrics)   │  │  (Dashboards)│  │   (APM)     │             │
│  │  Port:9090  │  │ Port:3000   │  │ Integration │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│          │                │                │                   │
│          └────────────────┼────────────────┘                   │
│                           │                                    │
│  ┌─────────────┐  ┌───────▼───────┐  ┌─────────────┐          │
│  │ Node        │  │   Application │  │   Nginx     │          │
│  │ Exporter    │  │   Metrics     │  │  Exporter   │          │
│  │ Port:9100   │  │  (Custom)     │  │ Port:9113   │          │
│  └─────────────┘  └───────────────┘  └─────────────┘          │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ PostgreSQL  │  │    Redis    │  │   Celery    │          │
│  │ Exporter    │  │  Exporter   │  │  Exporter   │          │
│  │ Port:9187   │  │ Port:9121   │  │   Custom    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌─────────▼─────────┐
                    │ AlertManager      │
                    │ (Notifications)   │
                    └───────────────────┘
```

## Prometheus Setup

### 1. Instalación de Prometheus

```bash
# Crear usuario para Prometheus
sudo useradd --no-create-home --shell /bin/false prometheus

# Crear directorios
sudo mkdir -p /etc/prometheus/{rules,files_sd}
sudo mkdir -p /var/lib/prometheus

# Descargar Prometheus
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Instalar binarios
sudo cp prometheus promtool /usr/local/bin/
sudo chown prometheus:prometheus /usr/local/bin/prometheus
sudo chown prometheus:prometheus /usr/local/bin/promtool

# Instalar console templates
sudo cp -r consoles console_libraries /etc/prometheus/
sudo chown -R prometheus:prometheus /etc/prometheus/consoles
sudo chown -R prometheus:prometheus /etc/prometheus/console_libraries

# Crear systemd service
sudo cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file /etc/prometheus/prometheus.yml \
  --storage.tsdb.path /var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle \
  --storage.tsdb.retention.time=30d

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
```

### 2. Configuración de Prometheus

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ai-news-aggregator'
    replica: 'prometheus-1'

rule_files:
  - "/etc/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 5s

  # Node Exporter (system metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100', '10.116.0.11:9100', '10.116.0.12:9100']
    scrape_interval: 10s
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'web-server-1'

  # Nginx Exporter
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['localhost:9113']
    scrape_interval: 10s

  # Backend Application (FastAPI)
  - job_name: 'backend-app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # PostgreSQL Exporter
  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
    scrape_interval: 30s

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
    scrape_interval: 30s

  # Celery Exporter (custom)
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/celery-metrics'
    scrape_interval: 30s

  # Docker containers (cAdvisor)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['localhost:8080']
    scrape_interval: 30s
```

### 3. Reglas de Alertas

```yaml
# /etc/prometheus/rules/ai-news-rules.yml
groups:
  - name: ai-news-system
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High CPU usage detected on {{ $labels.instance }}"
          description: "CPU usage is above 80% for more than 5 minutes on {{ $labels.instance }}. Current value: {{ $value }}%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High memory usage detected on {{ $labels.instance }}"
          description: "Memory usage is above 85% for more than 5 minutes on {{ $labels.instance }}. Current value: {{ $value }}%"

      - alert: DiskSpaceLow
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 90
        for: 10m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Disk space is running low on {{ $labels.instance }}"
          description: "Disk usage is above 90% on {{ $labels.instance }}. Current value: {{ $value }}%"

  - name: ai-news-application
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="backend-app"}[5m])) > 0.5
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is above 500ms for more than 10 minutes. Current value: {{ $value }}s"

      - alert: HighErrorRate
        expr: rate(http_requests_total{job="backend-app",status=~"5.."}[5m]) / rate(http_requests_total{job="backend-app"}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 1% for more than 5 minutes. Current value: {{ $value | humanizePercentage }}"

      - alert: DatabaseConnectionPoolExhausted
        expr: postgresql_up == 0
        for: 2m
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection pool exhausted"
          description: "PostgreSQL database is not responding"

      - alert: RedisDown
        expr: redis_up == 0
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Redis cache is down"
          description: "Redis server is not responding"

  - name: ai-news-business
    rules:
      - alert: NoNewsArticles
        expr: rate(articles_processed_total[1h]) == 0
        for: 30m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "No news articles processed recently"
          description: "No articles have been processed in the last hour"

      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 1000
        for: 15m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "Celery queue backlog detected"
          description: "Celery queue has {{ $value }} pending tasks"
```

## Grafana Configuration

### 1. Instalación de Grafana

```bash
# Instalar dependencias
sudo apt-get install -y apt-transport-https software-properties-common

# Agregar repositorio
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# Instalar Grafana
sudo apt-get update
sudo apt-get install -y grafana

# Configurar systemd
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### 2. Configuración Inicial

```yaml
# /etc/grafana/grafana.ini
[server]
protocol = http
http_addr = 127.0.0.1
http_port = 3000
domain = localhost
root_url = %(protocol)s://%(domain)s:%(http_port)s/
serve_from_sub_path = false
router_logging = false
static_root_path = public
enable_gzip = false
cert_file =
cert_key =

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db
url =

[security]
admin_user = admin
admin_password = your-secure-grafana-password
secret_key = your-secret-key-here
cookie_secure = false
cookie_samesite = lax
allow_sign_up = true

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer

[alerting]
enabled = true
execute_alerts = true

[metrics]
enabled = true
interval_seconds = 10
disable_total_stats = false

[log]
mode = console
level = info
format = text
```

### 3. Data Sources Configuration

```bash
# Configurar Prometheus como data source
curl -X POST \
  http://admin:your-secure-grafana-password@localhost:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

### 4. Dashboard Import

```bash
# Crear dashboard para AI News Aggregator
curl -X POST \
  http://admin:your-secure-grafana-password@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @/path/to/ai-news-dashboard.json
```

## APM con Sentry

### 1. Instalación de Sentry

```bash
# Instalar Sentry CLI
curl -sL https://sentry.io/get-cli/ | bash

# O instalar via pip
pip install sentry-sdk[fastapi]
```

### 2. Configuración en Aplicación

```python
# backend/app/core/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import structlog

# Configuración de Sentry
sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR,
)

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN_HERE",
    integrations=[
        sentry_logging,
        CeleryIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment="production",
    release="ai-news-aggregator@1.0.0",
    before_send=before_send,
)

def before_send(event, hint):
    # Filtrar errores de bajo impacto
    if event.get('exception'):
        exception = event['exception']['values'][0]
        if 'Health check' in exception.get('value', ''):
            return None
    return event

# Configuración de logging estructurado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### 3. Métricas Personalizadas en Sentry

```python
# backend/app/core/metrics.py
from sentry_sdk import add_breadcrumb, set_extra, set_tag, set_user

class AppMetrics:
    @staticmethod
    def track_api_request(endpoint: str, method: str, status_code: int, duration: float):
        """Track API request metrics"""
        set_tag("api_endpoint", endpoint)
        set_tag("http_method", method)
        set_tag("status_code", status_code)
        set_extra("request_duration", duration)
        
        # Enviar a Sentry como breadcrumb
        add_breadcrumb(
            category="api.request",
            message=f"{method} {endpoint} - {status_code}",
            level="info",
            data={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration": duration
            }
        )

    @staticmethod
    def track_celery_task(task_name: str, success: bool, duration: float):
        """Track Celery task metrics"""
        set_tag("celery_task", task_name)
        set_tag("task_success", success)
        set_extra("task_duration", duration)
        
        if not success:
            set_tag("error", "celery_task_failed")

    @staticmethod
    def track_database_query(query_type: str, table: str, duration: float):
        """Track database query metrics"""
        set_tag("query_type", query_type)
        set_tag("db_table", table)
        set_extra("query_duration", duration)

    @staticmethod
    def track_external_api(api_name: str, endpoint: str, success: bool, duration: float):
        """Track external API calls"""
        set_tag("external_api", api_name)
        set_tag("api_endpoint", endpoint)
        set_tag("api_success", success)
        set_extra("api_duration", duration)
```

## Logging Centralizado

### 1. Configuración de ELK Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.2
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - monitoring

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.2
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - monitoring

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.2
    container_name: logstash
    volumes:
      - ./config/logstash/pipeline:/usr/share/logstash/pipeline
      - ./config/logstash/logstash.yml:/usr/share/logstash/config/logstash.yml
      - /var/log/nginx:/var/log/nginx:ro
      - /var/www/ai-news-aggregator/logs:/var/www/ai-news-aggregator/logs:ro
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    depends_on:
      - elasticsearch
    networks:
      - monitoring

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.10.2
    container_name: filebeat
    user: root
    volumes:
      - ./config/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/log/nginx:/var/log/nginx:ro
      - /var/www/ai-news-aggregator/logs:/var/www/ai-news-aggregator/logs:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - elasticsearch
    networks:
      - monitoring

volumes:
  elasticsearch_data:

networks:
  monitoring:
    driver: bridge
```

### 2. Configuración de Logstash

```ruby
# config/logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }
  
  tcp {
    port => 5000
    codec => json
  }
  
  udp {
    port => 5000
    codec => json
  }
}

filter {
  if [fields][service] == "ai-news-backend" {
    grok {
      match => { 
        "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:logger} - %{GREEDYDATA:message}" 
      }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    mutate {
      add_field => { "service" => "backend" }
    }
  }
  
  if [fields][service] == "nginx" {
    grok {
      match => { 
        "message" => "%{NGINXACCESS}" 
      }
    }
    
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
    }
  }
  
  if [level] == "ERROR" {
    mutate {
      add_tag => [ "error" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ai-news-%{+YYYY.MM.dd}"
  }
  
  if "error" in [tags] {
    email {
      to => "alerts@yourdomain.com"
      subject => "Error in AI News Aggregator"
      body => "Error message: %{message}"
    }
  }
}
```

### 3. Configuración de Filebeat

```yaml
# config/filebeat/filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/www/ai-news-aggregator/logs/*.log
  fields:
    service: ai-news-backend
  fields_under_root: true
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

- type: log
  enabled: true
  paths:
    - /var/log/nginx/access.log
  fields:
    service: nginx
  fields_under_root: true
  json.keys_under_root: true

output.logstash:
  hosts: ["logstash:5044"]

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644

processors:
- add_cloud_metadata: ~

monitoring.enabled: true
```

## Alertas y Notificaciones

### 1. AlertManager Setup

```yaml
# /etc/prometheus/alertmanager.yml
global:
  smtp_smarthost: 'smtp.sendgrid.net:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'apikey'
  smtp_auth_password: 'your_sendgrid_api_key'

route:
  group_by: ['alertname', 'instance']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'web.hook'
  routes:
  - match:
      team: infrastructure
    receiver: 'infrastructure-team'
  - match:
      team: backend
    receiver: 'backend-team'
  - match:
      team: database
    receiver: 'database-team'
  - match:
      severity: critical
    receiver: 'critical-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'

- name: 'infrastructure-team'
  email_configs:
  - to: 'infra@yourdomain.com'
    subject: 'Infrastructure Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Instance: {{ .Labels.instance }}
      Severity: {{ .Labels.severity }}
      {{ end }}
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#infrastructure'
    title: 'Infrastructure Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'backend-team'
  email_configs:
  - to: 'backend@yourdomain.com'
    subject: 'Backend Alert: {{ .GroupLabels.alertname }}'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#backend'

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@yourdomain.com'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#oncall'
  webhook_configs:
  - url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

### 2. Slack Integration

```python
# backend/app/core/slack_notifications.py
import requests
import json
from typing import Dict, Any

class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_alert(self, title: str, message: str, color: str = "warning", fields: Dict[str, Any] = None):
        """Send alert to Slack"""
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [
                        {"title": k, "value": str(v), "short": True} 
                        for k, v in (fields or {}).items()
                    ],
                    "ts": int(time.time())
                }
            ]
        }
        
        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        
        return response.status_code == 200

    def send_critical_alert(self, alert_data: Dict[str, Any]):
        """Send critical alert with high priority"""
        return self.send_alert(
            title=f"🚨 CRITICAL: {alert_data['alertname']}",
            message=alert_data['description'],
            color="danger",
            fields={
                "Instance": alert_data.get('instance', 'N/A'),
                "Severity": alert_data.get('severity', 'unknown'),
                "Started": alert_data.get('startsAt', 'N/A')
            }
        )
```

## Dashboards

### 1. System Overview Dashboard

```json
{
  "dashboard": {
    "title": "AI News Aggregator - System Overview",
    "tags": ["ai-news", "system"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "System CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ],
        "yAxes": [
          {
            "label": "CPU %",
            "min": 0,
            "max": 100
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Network Traffic",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m]) * 8",
            "legendFormat": "{{instance}} RX"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total[5m]) * 8",
            "legendFormat": "{{instance}} TX"
          }
        ]
      }
    ]
  }
}
```

### 2. Application Dashboard

```json
{
  "dashboard": {
    "title": "AI News Aggregator - Application",
    "panels": [
      {
        "title": "API Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100"
          }
        ],
        "valueName": "current"
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "postgresql_connections_active",
            "legendFormat": "Active"
          },
          {
            "expr": "postgresql_connections_max",
            "legendFormat": "Max"
          }
        ]
      }
    ]
  }
}
```

## Métricas Personalizadas

### 1. Métricas de Aplicación

```python
# backend/app/core/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
ARTICLES_PROCESSED = Counter(
    'articles_processed_total',
    'Total articles processed',
    ['source', 'category']
)

CELERY_TASKS = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

# Gauge metrics
DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections'
)

REDIS_CONNECTIONS = Gauge(
    'redis_connections_active',
    'Active Redis connections'
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_name']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_name']
)

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Increment request count
            method = scope["method"]
            path = scope["path"]
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics (assuming we can get status from send)
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
            
        else:
            await self.app(scope, receive, send)

def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
```

### 2. Exporters Personalizados

```python
# backend/app/core/custom_exporter.py
import psutil
import redis
import psycopg2
from prometheus_client import start_http_server, Gauge
import time

class CustomExporter:
    def __init__(self):
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
        self.redis_info = Gauge('redis_info', 'Redis info', ['key'])
        self.db_connections = Gauge('postgresql_connection_count', 'Database connections', ['state'])

    def collect_system_metrics(self):
        """Collect system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.percent)

        # Disk usage
        disk = psutil.disk_usage('/')
        self.disk_usage.set((disk.used / disk.total) * 100)

    def collect_redis_metrics(self):
        """Collect Redis metrics"""
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            info = r.info()
            
            self.redis_info.labels(key='connected_clients').set(info['connected_clients'])
            self.redis_info.labels(key='used_memory').set(info['used_memory'])
            self.redis_info.labels(key='used_memory_peak').set(info['used_memory_peak'])
            
        except Exception as e:
            print(f"Error collecting Redis metrics: {e}")

    def collect_database_metrics(self):
        """Collect PostgreSQL metrics"""
        try:
            # This would need proper connection string
            conn = psycopg2.connect("postgresql://user:pass@localhost/db")
            cur = conn.cursor()
            
            # Active connections
            cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
            active = cur.fetchone()[0]
            self.db_connections.labels(state='active').set(active)
            
            # Idle connections
            cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';")
            idle = cur.fetchone()[0]
            self.db_connections.labels(state='idle').set(idle)
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Error collecting database metrics: {e}")

    def start(self, port=8001):
        """Start the exporter"""
        start_http_server(port)
        
        while True:
            self.collect_system_metrics()
            self.collect_redis_metrics()
            self.collect_database_metrics()
            time.sleep(15)  # Collect every 15 seconds

if __name__ == '__main__':
    exporter = CustomExporter()
    exporter.start()
```

## Troubleshooting

### Common Issues

1. **Prometheus not scraping targets**
   ```bash
   # Verificar configuración
   curl http://localhost:9090/api/v1/targets
   
   # Verificar conectividad
   curl http://localhost:8000/metrics
   ```

2. **Grafana cannot connect to Prometheus**
   ```bash
   # Verificar configuración de data source
   curl -X GET http://admin:password@localhost:3000/api/datasources
   
   # Verificar logs
   journalctl -u grafana-server -f
   ```

3. **High memory usage in monitoring stack**
   ```yaml
   # Reducir retention en Prometheus
   storage.tsdb.retention.time=7d
   
   # Limitar recursos en Docker
   memory: 1g
   cpu_limit: 0.5
   ```

### Performance Tuning

1. **Optimizar Prometheus**
   ```yaml
   # Incrementar scrape interval para métricas de baja prioridad
   scrape_interval: 30s
   
   # Configurar remote storage para long-term retention
   remote_write:
     - url: "http://remote-storage:9201/write"
   ```

2. **Optimizar Grafana**
   ```ini
   # Cache dashboard queries
   cache_mode = aggressive
   
   # Disable live updates para dashboards públicos
   live_settings = disabled
   ```

## Comandos Útiles

```bash
# Verificar estado de servicios de monitoreo
systemctl status prometheus
systemctl status grafana-server

# Verificar targets en Prometheus
curl http://localhost:9090/api/v1/targets | jq

# Verificar métricas
curl http://localhost:9090/metrics | grep ai_news

# Verificar Grafana dashboards
curl http://admin:password@localhost:3000/api/dashboards

# Verificar logs
tail -f /var/log/prometheus/prometheus.log
tail -f /var/log/grafana/grafana.log

# Verificar connectivity
telnet localhost 9090
telnet localhost 3000
```

## Próximos Pasos

1. **Configurar alertas avanzadas**: Implementar machine learning para detectar anomalías
2. **Dashboard personalizables**: Permitir a usuarios crear dashboards personalizados
3. **Monitoreo de costos**: Trackear costos de infraestructura
4. **Synthetic monitoring**: Implementar checks sintéticos externos
5. **APM avanzado**: Implementar distributed tracing con Jaeger

---

**Nota**: Este setup asume monitoreo interno. Para monitoreo externo, considerar servicios como DataDog, New Relic, o Dynatrace.