terraform {
  required_version = ">= 1.0"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
  
  backend "remote" {
    organization = "ai-news-aggregator"
    workspaces {
      name = "ai-news-aggregator"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# Variables
variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ai-news-aggregator"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "domain" {
  description = "Domain name for the application"
  type        = string
}

variable "subdomain" {
  description = "Subdomain for the application"
  type        = string
  default     = ""
}

variable "droplet_size" {
  description = "Size of droplets"
  type        = string
  default     = "s-2vcpu-4gb"
}

variable "web_droplets_count" {
  description = "Number of web application droplets"
  type        = number
  default     = 2
}

variable "worker_droplets_count" {
  description = "Number of worker droplets"
  type        = number
  default     = 1
}

variable "database_size" {
  description = "Database size"
  type        = string
  default     = "db-s-2vcpu-4gb"
}

variable "ssh_keys" {
  description = "List of SSH key IDs"
  type        = list(string)
  default     = []
}

# Outputs
output "load_balancer_ip" {
  description = "Public IP of the load balancer"
  value       = digitalocean_load_balancer.public_ip
}

output "database_host" {
  description = "Database connection host"
  value       = digitalocean_database_cluster.main.host
}

output "web_droplet_ips" {
  description = "List of web droplet IPs"
  value       = digitalocean_droplet.web[*].ipv4_address
}

output "worker_droplet_ips" {
  description = "List of worker droplet IPs"
  value       = digitalocean_droplet.worker[*].ipv4_address
}