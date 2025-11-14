#!/bin/bash

# AI News Aggregator - Setup Docker Production Scripts
# Make all Docker production scripts executable

echo "🔧 Making Docker production scripts executable..."

# Make scripts executable
chmod +x init-docker-prod.sh 2>/dev/null || echo "Note: init-docker-prod.sh permissions - may need manual chmod +x"
chmod +x deploy-prod.sh 2>/dev/null || echo "Note: deploy-prod.sh permissions - may need manual chmod +x"

echo "✅ Script permissions setup completed!"
echo ""
echo "🚀 Quick Start Commands:"
echo "  ./init-docker-prod.sh          - Initialize production environment"
echo "  ./deploy-prod.sh deploy        - Full production deployment"
echo "  make prod-deploy               - Using Makefile"
echo ""
echo "📖 See DOCKER_PRODUCTION.md for detailed documentation"