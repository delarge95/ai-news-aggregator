# Monitoring Droplet (Prometheus + Grafana)
resource "digitalocean_droplet" "monitoring" {
  count = 1
  
  name   = "${var.project_name}-monitoring"
  size   = "s-2vcpu-4gb"
  image  = "ubuntu-22-04-x64"
  region = var.region
  vpc_uuid = digitalocean_vpc.main.id
  
  # User data script for monitoring setup
  user_data = <<-EOF
    #cloud-config
    users:
      - name: deploy
        groups: sudo
        shell: /bin/bash
        ssh_authorized_keys:
          ${length(var.ssh_keys) > 0 ? "- ${file(var.ssh_keys[0])}" : ""}
    
    packages:
      - docker.io
      - docker-compose
      - prometheus
      - node-exporter
      - grafana
      - htop
      - unzip
    
    write_files:
      - content: |
          version: '3.8'
          
          services:
            prometheus:
              image: prom/prometheus:latest
              container_name: prometheus
              restart: unless-stopped
              ports:
                - "9090:9090"
              volumes:
                - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
                - ./prometheus/rules:/etc/prometheus/rules
                - prometheus_data:/prometheus
              command:
                - '--config.file=/etc/prometheus/prometheus.yml'
                - '--storage.tsdb.path=/prometheus'
                - '--web.console.libraries=/etc/prometheus/console_libraries'
                - '--web.console.templates=/etc/prometheus/consoles'
                - '--storage.tsdb.retention.time=200h'
                - '--web.enable-lifecycle'
              networks:
                - monitoring
            
            grafana:
              image: grafana/grafana:latest
              container_name: grafana
              restart: unless-stopped
              ports:
                - "3000:3000"
              environment:
                - GF_SECURITY_ADMIN_USER=admin
                - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
                - GF_USERS_ALLOW_SIGN_UP=false
              volumes:
                - grafana_data:/var/lib/grafana
                - ./grafana/provisioning:/etc/grafana/provisioning
                - ./grafana/dashboards:/var/lib/grafana/dashboards
              depends_on:
                - prometheus
              networks:
                - monitoring
            
            node-exporter:
              image: prom/node-exporter:latest
              container_name: node-exporter
              restart: unless-stopped
              ports:
                - "9100:9100"
              volumes:
                - /proc:/host/proc:ro
                - /sys:/host/sys:ro
                - /:/rootfs:ro
              command:
                - '--path.procfs=/host/proc'
                - '--path.rootfs=/rootfs'
                - '--path.sysfs=/host/sys'
                - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
              networks:
                - monitoring
            
            alertmanager:
              image: prom/alertmanager:latest
              container_name: alertmanager
              restart: unless-stopped
              ports:
                - "9093:9093"
              volumes:
                - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
              networks:
                - monitoring
          
          volumes:
            prometheus_data:
            grafana_data:
          
          networks:
            monitoring:
              driver: bridge
        path: /opt/ai-news-aggregator/monitoring/docker-compose.yml
        permissions: '0644'
      
      - content: |
          global:
            scrape_interval: 15s
            evaluation_interval: 15s
          
          rule_files:
            - "rules/*.yml"
          
          alerting:
            alertmanagers:
              - static_configs:
                  - targets:
                    - alertmanager:9093
          
          scrape_configs:
            - job_name: 'prometheus'
              static_configs:
                - targets: ['localhost:9090']
            
            - job_name: 'node-exporter'
              static_configs:
                - targets: ['node-exporter:9100']
              scrape_interval: 5s
              metrics_path: /metrics
            
            - job_name: 'ai-news-web'
              static_configs:
                - targets: [${join(",", formatlist("%s:80", digitalocean_droplet.web[*].ipv4_address))}]
              scrape_interval: 30s
              metrics_path: /metrics
            
            - job_name: 'ai-news-worker'
              static_configs:
                - targets: [${join(",", formatlist("%s:8001", digitalocean_droplet.worker[*].ipv4_address))}]
              scrape_interval: 30s
              metrics_path: /metrics
        path: /opt/ai-news-aggregator/monitoring/prometheus/prometheus.yml
        permissions: '0644'
      
      - content: |
          version: '1.0'
          datasources:
            - name: Prometheus
              type: prometheus
              access: proxy
              url: http://prometheus:9090
              isDefault: true
          
          dashboards:
            - name: 'Default'
              dashboard: {}
        path: /opt/ai-news-aggregator/monitoring/grafana/provisioning/datasources/datasource.yml
        permissions: '0644'
    
    runcmd:
      - mkdir -p /opt/ai-news-aggregator/monitoring
      - mkdir -p /opt/ai-news-aggregator/monitoring/{prometheus/{rules},grafana/{provisioning/dashboards,dashboards},alertmanager}
      - chown -R deploy:deploy /opt/ai-news-aggregator/monitoring
      - systemctl enable docker
      - systemctl start docker
      - usermod -aG docker deploy
      - echo "Monitoring infrastructure ready"
  EOF
  
  tags = [
    "${var.project_name}-monitoring",
    var.environment,
    "monitoring"
  ]
  
  connection {
    type        = "ssh"
    user        = "root"
    host        = self.ipv4_address
    private_key = file(var.ssh_keys[0])
  }
}

# Monitoring DNS records
resource "digitalocean_record" "monitoring" {
  domain = digitalocean_domain.main.name
  type   = "CNAME"
  name   = "monitoring"
  value  = "${digitalocean_droplet.monitoring[0].ipv4_address}."
  ttl    = 300
}

resource "digitalocean_record" "prometheus" {
  domain = digitalocean_domain.main.name
  type   = "CNAME"
  name   = "prometheus"
  value  = "monitoring.${var.domain}."
  ttl    = 300
}

resource "digitalocean_record" "grafana" {
  domain = digitalocean_domain.main.name
  type   = "CNAME"
  name   = "grafana"
  value  = "monitoring.${var.domain}."
  ttl    = 300
}