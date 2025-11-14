# Outputs file for deployment
data "digitalocean_database_cluster" "main" {
  name = digitalocean_database_cluster.main.name
}

# Database connection details
output "database_connection_info" {
  description = "Database connection information"
  value = {
    host     = digitalocean_database_cluster.main.host
    port     = digitalocean_database_cluster.main.port
    database = digitalocean_database_db.main.name
    user     = digitalocean_database_user.main.name
    ssl_mode = "require"
  }
}

output "database_password" {
  description = "Database user password (get from Terraform state)"
  value       = digitalocean_database_user.main.password
  sensitive   = true
}

# Load Balancer details
output "load_balancer_info" {
  description = "Load Balancer information"
  value = {
    id             = digitalocean_load_balancer.public.id
    ip             = digitalocean_load_balancer.public_ip
    status         = digitalocean_load_balancer.public.status
    algorithm      = digitalocean_load_balancer.public.algorithm
    sticky_sessions = digitalocean_load_balancer.public.sticky_sessions
  }
}

# Droplet information
output "web_droplets" {
  description = "Web application droplets"
  value = [for i in range(var.web_droplets_count) : {
    id           = digitalocean_droplet.web[i].id
    name         = digitalocean_droplet.web[i].name
    ip           = digitalocean_droplet.web[i].ipv4_address
    private_ip   = digitalocean_droplet.web[i].ipv4_address_private
    size         = digitalocean_droplet.web[i].size
    region       = digitalocean_droplet.web[i].region
    vpc          = digitalocean_droplet.web[i].vpc_uuid
    status       = digitalocean_droplet.web[i].status
    domain_record = digitalocean_record.web_droplet[i].fqdn
  }]
}

output "worker_droplets" {
  description = "Worker application droplets"
  value = [for i in range(var.worker_droplets_count) : {
    id           = digitalocean_droplet.worker[i].id
    name         = digitalocean_droplet.worker[i].name
    ip           = digitalocean_droplet.worker[i].ipv4_address
    private_ip   = digitalocean_droplet.worker[i].ipv4_address_private
    size         = digitalocean_droplet.worker[i].size
    region       = digitalocean_droplet.worker[i].region
    vpc          = digitalocean_droplet.worker[i].vpc_uuid
    status       = digitalocean_droplet.worker[i].status
    domain_record = digitalocean_record.worker_droplet[i].fqdn
  }]
}

output "monitoring_droplet" {
  description = "Monitoring droplet information"
  value = {
    id           = digitalocean_droplet.monitoring[0].id
    name         = digitalocean_droplet.monitoring[0].name
    ip           = digitalocean_droplet.monitoring[0].ipv4_address
    private_ip   = digitalocean_droplet.monitoring[0].ipv4_address_private
    size         = digitalocean_droplet.monitoring[0].size
    region       = digitalocean_droplet.monitoring[0].region
    prometheus_url = "http://${digitalocean_droplet.monitoring[0].ipv4_address}:9090"
    grafana_url    = "http://${digitalocean_droplet.monitoring[0].ipv4_address}:3000"
  }
}

# Domain information
output "domain_info" {
  description = "Domain configuration"
  value = {
    domain = digitalocean_domain.main.name
    records = {
      root        = digitalocean_record.root.fqdn
      www         = digitalocean_record.www.fqdn
      api         = digitalocean_record.api.fqdn
      admin       = digitalocean_record.admin.fqdn
      monitoring  = digitalocean_record.monitoring.fqdn
      prometheus  = digitalocean_record.prometheus.fqdn
      grafana     = digitalocean_record.grafana.fqdn
    }
  }
}

# Network information
output "network_info" {
  description = "Network configuration"
  value = {
    vpc_id      = digitalocean_vpc.main.id
    vpc_name    = digitalocean_vpc.main.name
    vpc_region  = digitalocean_vpc.main.region
    vpc_cidr    = digitalocean_vpc.main.ip_range
  }
}

# Firewall information
output "firewall_info" {
  description = "Firewall configuration"
  value = {
    web = {
      id      = digitalocean_firewall.web.id
      name    = digitalocean_firewall.web.name
      rules   = digitalocean_firewall.web.inbound_rule
    }
    worker = {
      id      = digitalocean_firewall.worker.id
      name    = digitalocean_firewall.worker.name
      rules   = digitalocean_firewall.worker.inbound_rule
    }
  }
}

# Environment summary
output "environment_summary" {
  description = "Complete environment configuration summary"
  value = {
    project      = var.project_name
    environment  = var.environment
    region       = var.region
    domain       = var.domain
    resources = {
      web_droplets    = var.web_droplets_count
      worker_droplets = var.worker_droplets_count
      database_size   = var.database_size
      droplet_size    = var.droplet_size
    }
    urls = {
      application = "https://${digitalocean_record.www.fqdn}"
      admin       = "https://${digitalocean_record.admin.fqdn}/admin"
      monitoring  = "http://${digitalocean_record.monitoring.fqdn}:3000"
      prometheus  = "http://${digitalocean_record.prometheus.fqdn}:9090"
    }
    ssl_enabled = true
    monitoring_enabled = true
  }
}