#!/bin/bash
# Remove SSL and restore HTTP-only configuration
# Run this on your VPS as root: ssh root@142.93.113.224

set -e

echo "🔄 Removing SSL and Restoring HTTP Configuration"
echo "==============================================="
echo ""

# Get the server's public IP
SERVER_IP=$(curl -s ifconfig.me)
echo "Server IP: $SERVER_IP"
echo ""

echo "1. Stopping Nginx..."
systemctl stop nginx

echo "2. Removing SSL certificates and directories..."
rm -rf /etc/nginx/ssl/
rm -f /etc/letsencrypt/live/*/
rm -f /etc/letsencrypt/archive/*/
rm -f /etc/letsencrypt/renewal/*/

echo "3. Removing Certbot if installed..."
apt remove --purge -y certbot python3-certbot-nginx 2>/dev/null || echo "Certbot not installed"

echo "4. Removing SSL cron jobs..."
crontab -l 2>/dev/null | grep -v certbot | crontab - 2>/dev/null || echo "No certbot cron jobs found"

echo "5. Restoring original HTTP-only Nginx configuration..."
cat > /etc/nginx/sites-available/iban-api << 'EOF'
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        client_max_body_size 10M;
    }

    # Health check endpoint (faster response)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Alternative API documentation
    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "6. Testing Nginx configuration..."
nginx -t

echo "7. Starting Nginx..."
systemctl start nginx

echo "8. Checking Nginx status..."
systemctl status nginx --no-pager -l

echo ""
echo "9. Testing HTTP endpoints..."
echo "Health check:"
curl -s http://$SERVER_IP/health | jq '.' 2>/dev/null || curl -s http://$SERVER_IP/health

echo ""
echo "API info:"
curl -s http://$SERVER_IP/ | jq '.version' 2>/dev/null || curl -s http://$SERVER_IP/ | grep version

echo ""
echo "✅ SSL Removal Complete!"
echo "======================="
echo "🌐 Your API is now available at:"
echo "   📡 http://$SERVER_IP/"
echo "   📊 http://$SERVER_IP/health"
echo "   📚 http://$SERVER_IP/docs"
echo "   📖 http://$SERVER_IP/redoc"
echo ""
echo "🧪 Test IBAN calculation:"
echo "curl -X POST http://$SERVER_IP/calculate-iban \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"country_code\": \"GB\", \"bank_code\": \"200000\", \"account_number\": \"55779911\"}'"
echo ""
echo "🔧 Configuration restored to HTTP-only"
echo "🔒 SSL certificates and configurations removed"
echo "⚡ Ready for normal HTTP usage"