#!/bin/bash
# SSL Setup Script for Digital Ocean VPS
# Run this on your VPS as root: ssh root@142.93.113.224

set -e

echo "🔒 SSL Setup for IBAN Calculator API"
echo "===================================="
echo ""

# Get the server's public IP
SERVER_IP=$(curl -s ifconfig.me)
echo "Server IP: $SERVER_IP"
echo ""

echo "📋 SSL Setup Options:"
echo "1. Let's Encrypt with domain name (recommended)"
echo "2. Self-signed certificate (for testing)"
echo "3. Cloudflare SSL (if using Cloudflare)"
echo ""

read -p "Do you have a domain name pointing to $SERVER_IP? (y/n): " HAS_DOMAIN

if [ "$HAS_DOMAIN" = "y" ] || [ "$HAS_DOMAIN" = "Y" ]; then
    echo ""
    read -p "Enter your domain name (e.g., api.yourdomain.com): " DOMAIN_NAME
    
    echo "🔧 Setting up Let's Encrypt SSL for $DOMAIN_NAME..."
    
    # Install Certbot
    echo "📦 Installing Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
    
    # Update Nginx configuration for the domain
    echo "🌐 Updating Nginx configuration..."
    cat > /etc/nginx/sites-available/iban-api << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        client_max_body_size 10M;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Test Nginx configuration
    echo "✅ Testing Nginx configuration..."
    nginx -t
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    systemctl reload nginx
    
    # Get SSL certificate
    echo "🔒 Obtaining SSL certificate..."
    certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME --redirect
    
    # Setup auto-renewal
    echo "⏰ Setting up auto-renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    echo ""
    echo "🎉 SSL Setup Complete!"
    echo "====================="
    echo "✅ Your API is now available at:"
    echo "   🔒 https://$DOMAIN_NAME/"
    echo "   🔒 https://$DOMAIN_NAME/health"
    echo "   🔒 https://$DOMAIN_NAME/docs"
    echo ""
    echo "🧪 Test with:"
    echo "   curl https://$DOMAIN_NAME/health"
    echo ""
    echo "🔄 Certificate auto-renewal is set up"
    echo "📅 Certificate expires in 90 days and will auto-renew"

else
    echo ""
    echo "🔧 Setting up Self-Signed SSL Certificate..."
    echo "⚠️  Note: This will show security warnings in browsers"
    echo ""
    
    # Create SSL directory
    mkdir -p /etc/nginx/ssl
    
    # Generate self-signed certificate
    echo "🔑 Generating self-signed certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/iban-api.key \
        -out /etc/nginx/ssl/iban-api.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$SERVER_IP"
    
    # Update Nginx configuration for SSL
    echo "🌐 Updating Nginx configuration for SSL..."
    cat > /etc/nginx/sites-available/iban-api << EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $SERVER_IP _;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name $SERVER_IP _;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/iban-api.crt;
    ssl_certificate_key /etc/nginx/ssl/iban-api.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        client_max_body_size 10M;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOF

    # Test Nginx configuration
    echo "✅ Testing Nginx configuration..."
    nginx -t
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    systemctl reload nginx
    
    echo ""
    echo "🎉 Self-Signed SSL Setup Complete!"
    echo "=================================="
    echo "✅ Your API is now available at:"
    echo "   🔒 https://$SERVER_IP/ (will show security warning)"
    echo "   🔒 https://$SERVER_IP/health"
    echo "   🔒 https://$SERVER_IP/docs"
    echo ""
    echo "⚠️  Browser Security Warning:"
    echo "   - Click 'Advanced' then 'Proceed to $SERVER_IP'"
    echo "   - Or use curl with -k flag: curl -k https://$SERVER_IP/health"
    echo ""
    echo "🧪 Test with:"
    echo "   curl -k https://$SERVER_IP/health"
fi

echo ""
echo "🔒 SSL Security Features Added:"
echo "   ✅ HTTPS encryption"
echo "   ✅ HTTP to HTTPS redirect"
echo "   ✅ Security headers"
echo "   ✅ Modern TLS protocols"
echo ""
echo "🔧 Firewall already allows HTTPS (port 443)"