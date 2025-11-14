# VPC Network
resource "digitalocean_vpc" "main" {
  name     = "${var.project_name}-${var.environment}"
  region   = var.region
  ip_range = "10.244.0.0/16"
}

# SSH Key (optional)
resource "digitalocean_ssh_key" "main" {
  name       = "${var.project_name}-${var.environment}-key"
  public_key = file(var.ssh_keys[0])
}

# Load Balancer
resource "digitalocean_load_balancer" "public" {
  name         = "${var.project_name}-lb"
  region       = var.region
  size         = "lb-small"
  vpc_uuid     = digitalocean_vpc.main.id
  
  # Health check configuration
  algorithm                        = "round_robin"
  http_check_healthy_interval      = 10
  http_check_unhealthy_interval    = 5
  http_check_unhealthy_times       = 3
  http_check_interval_seconds      = 10
  
  # Sticky sessions
  sticky_sessions {
    type             = "cookies"
    cookie_name      = "lb_cookie"
    cookie_ttl_seconds = 300
  }
  
  # Forwarding rules
  forwarding_rule {
    entry_port     = 80
    entry_protocol = "http"
    
    target_port     = 80
    target_protocol = "http"
  }
  
  forwarding_rule {
    entry_port     = 443
    entry_protocol = "https"
    
    target_port     = 443
    target_protocol = "http"
    tls_passthrough = true
  }
  
  # Droplet health status for load balancer
  droplet_ids = concat(
    digitalocean_droplet.web[*].id
  )
  
  # Health check rules
  healthcheck {
    protocol = "http"
    port     = 80
    path     = "/health"
  }
}

# Web Application Droplets
resource "digitalocean_droplet" "web" {
  count = var.web_droplets_count
  
  name   = "${var.project_name}-web-${count.index}"
  size   = var.droplet_size
  image  = "ubuntu-22-04-x64"
  region = var.region
  vpc_uuid = digitalocean_vpc.main.id
  
  # User data script
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
      - nginx
      - certbot
      - python3-certbot-nginx
      - htop
      - unzip
    
    write_files:
      - content: |
          [Unit]
          Description=Docker Application Container Engine
          Documentation=https://docs.docker.com
          After=network-online.target docker.socket firewalld.service containerd.service
          Wants=network-online.target
          Requires=docker.socket containerd.service

          [Service]
          Type=notify
          ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
          ExecReload=/bin/kill -s HUP \$MAINPID
          TimeoutSec=0
          RestartSec=2
          Restart=always
          StartLimitBurst=3
          StartLimitInterval=60s
          LimitNOFILE=infinity
          LimitNPROC=infinity
          LimitCORE=infinity
          TasksMax=infinity
          Delegate=yes
          KillMode=process
          OOMScoreAdjust=-500

          [Install]
          WantedBy=multi-user.target
        path: /etc/systemd/system/docker.service
        permissions: '0644'
    
    runcmd:
      - systemctl daemon-reload
      - systemctl enable docker
      - systemctl start docker
      - usermod -aG docker deploy
      - mkdir -p /opt/ai-news-aggregator
      - chown deploy:deploy /opt/ai-news-aggregator
      - echo "Droplet ${count.index} ready for deployment"
  EOF
  
  tags = [
    "${var.project_name}-web",
    var.environment,
    "web-server"
  ]
  
  connection {
    type        = "ssh"
    user        = "root"
    host        = self.ipv4_address
    private_key = file(var.ssh_keys[0])
  }
}

# Worker Droplets
resource "digitalocean_droplet" "worker" {
  count = var.worker_droplets_count
  
  name   = "${var.project_name}-worker-${count.index}"
  size   = var.droplet_size
  image  = "ubuntu-22-04-x64"
  region = var.region
  vpc_uuid = digitalocean_vpc.main.id
  
  # User data script
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
      - redis-tools
      - python3-pip
      - htop
      - unzip
    
    runcmd:
      - systemctl enable docker
      - systemctl start docker
      - usermod -aG docker deploy
      - mkdir -p /opt/ai-news-aggregator
      - chown deploy:deploy /opt/ai-news-aggregator
      - echo "Worker droplet ${count.index} ready"
  EOF
  
  tags = [
    "${var.project_name}-worker",
    var.environment,
    "worker"
  ]
  
  connection {
    type        = "ssh"
    user        = "root"
    host        = self.ipv4_address
    private_key = file(var.ssh_keys[0])
  }
}

# Database Cluster
resource "digitalocean_database_cluster" "main" {
  name       = "${var.project_name}-${var.environment}"
  engine     = "postgres"
  version    = "15"
  size       = var.database_size
  region     = var.region
  vpc_uuid   = digitalocean_vpc.main.id
  node_count = 2
  
  maintenance_window {
    day  = "sun"
    hour = "02:00"
  }
  
  tags = [
    "${var.project_name}-db",
    var.environment,
    "postgresql"
  ]
}

# Database User
resource "digitalocean_database_user" "main" {
  cluster_id = digitalocean_database_cluster.main.id
  name       = "app_user"
}

# Database DB
resource "digitalocean_database_db" "main" {
  cluster_id = digitalocean_database_cluster.main.id
  name       = "ai_news_aggregator"
}

# Firewall - Web tier
resource "digitalocean_firewall" "web" {
  name = "${var.project_name}-web-firewall"
  
  droplet_ids = concat(
    digitalocean_droplet.web[*].id,
    [digitalocean_load_balancer.public.id]
  )
  
  # Inbound rules
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Outbound rules
  outbound_rule {
    protocol              = "tcp"
    port_range           = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Firewall - Worker tier
resource "digitalocean_firewall" "worker" {
  name = "${var.project_name}-worker-firewall"
  
  droplet_ids = digitalocean_droplet.worker[*].id
  
  # Inbound rules
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "6379"
    source_addresses = [digitalocean_vpc.main.ip_range]
  }
  
  # Outbound rules
  outbound_rule {
    protocol              = "tcp"
    port_range           = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}