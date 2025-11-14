# Domain Records
resource "digitalocean_domain" "main" {
  name = var.domain
}

# A Records for Load Balancer
resource "digitalocean_record" "www" {
  domain = digitalocean_domain.main.name
  type   = "A"
  name   = "www"
  value  = digitalocean_load_balancer.public_ip
  ttl    = 300
}

resource "digitalocean_record" "root" {
  domain = digitalocean_domain.main.name
  type   = "A"
  name   = "@"
  value  = digitalocean_load_balancer.public_ip
  ttl    = 300
}

# A Records for individual droplets (optional)
resource "digitalocean_record" "web_droplet" {
  count  = var.web_droplets_count
  domain = digitalocean_domain.main.name
  type   = "A"
  name   = "web-${count.index + 1}"
  value  = digitalocean_droplet.web[count.index].ipv4_address
  ttl    = 300
}

resource "digitalocean_record" "worker_droplet" {
  count  = var.worker_droplets_count
  domain = digitalocean_domain.main.name
  type   = "A"
  name   = "worker-${count.index + 1}"
  value  = digitalocean_droplet.worker[count.index].ipv4_address
  ttl    = 300
}

# CNAME Records for subdomains
resource "digitalocean_record" "api" {
  domain = digitalocean_domain.main.name
  type   = "CNAME"
  name   = "api"
  value  = "www.${var.domain}."
  ttl    = 300
}

resource "digitalocean_record" "admin" {
  domain = digitalocean_domain.main.name
  type   = "CNAME"
  name   = "admin"
  value  = "www.${var.domain}."
  ttl    = 300
}

# TXT Records for DNS verification
resource "digitalocean_record" "google_site_verification" {
  domain = digitalocean_domain.main.name
  type   = "TXT"
  name   = "google-site-verification"
  value  = "google-verification-token"
  ttl    = 3600
}

resource "digitalocean_record" "letsencrypt_verification" {
  domain = digitalocean_domain.main.name
  type   = "TXT"
  name   = "_acme-challenge"
  value  = "letsencrypt-verification-token"
  ttl    = 300
}

# MX Records for email (if needed)
resource "digitalocean_record" "mail" {
  domain = digitalocean_domain.main.name
  type   = "MX"
  name   = "@"
  value  = "mail.${var.domain}."
  priority = 10
  ttl    = 300
}

# SPF Record
resource "digitalocean_record" "spf" {
  domain = digitalocean_domain.main.name
  type   = "TXT"
  name   = "@"
  value  = "v=spf1 mx ~all"
  ttl    = 300
}

# CAA Records
resource "digitalocean_record" "caa" {
  domain = digitalocean_domain.main.name
  type   = "CAA"
  name   = "@"
  value  = "letsencrypt.org"
  flags  = 0
  tag    = "issue"
  ttl    = 300
}

resource "digitalocean_record" "caa_wildcard" {
  domain = digitalocean_domain.main.name
  type   = "CAA"
  name   = "@"
  value  = "letsencrypt.org"
  flags  = 0
  tag    = "issuewild"
  ttl    = 300
}