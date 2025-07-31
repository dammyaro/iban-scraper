#!/bin/bash
# Production deployment script for IBAN Calculator API

set -e

echo "🚀 Setting up IBAN Calculator API for Production"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

VPS_IP="142.93.113.224"

echo "📋 Step 1: Creating systemd service..."
cat > /etc/systemd/system/iban-api.service << EOF
[Unit]
Description=IBAN Calculator API
After=network.target

[Service]
Type=simple
User=ibanapp
Group=ibanapp
WorkingDirectory=/home/ibanapp/iban-scraper
Environment=PATH=/home/ibanapp/iban-scraper/venv/bin
Environment=PYTHONPATH=/home/ibanapp/iban-scraper
Environment=PLAYWRIGHT_HEADLESS=true
Environment=PLAYWRIGHT_TIMEOUT=60000
Environment=HOST=0.0.0.0
Environment=PORT=8000
ExecStart=/home/ibanapp/iban-scraper/venv/bin/python main_fixed.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "🔧 Step 2: Enabling and starting service..."
systemctl daemon-reload
systemctl enable iban-api
systemctl start iban-api

echo "📊 Service status:"
systemctl status iban-api --no-pager -l

echo "🌐 Step 3: Setting up Nginx reverse proxy..."
cat > /etc/nginx/sites-available/iban-api << EOF
server {
    listen 80;
    server_name $VPS_IP _;

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

    # Health check endpoint (faster response)
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

echo "🔗 Step 4: Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/iban-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "✅ Testing Nginx configuration..."
nginx -t

echo "🔄 Restarting Nginx..."
systemctl restart nginx

echo "🔒 Step 5: Setting up firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

echo "⏳ Waiting for services to start..."
sleep 5

echo "🧪 Step 6: Testing deployment..."
echo "Health check:"
curl -s http://$VPS_IP/health | jq '.' || curl -s http://$VPS_IP/health

echo ""
echo "API info:"
curl -s http://$VPS_IP/ | jq '.version' || curl -s http://$VPS_IP/ | grep version

echo ""
echo "🎉 Production Deployment Complete!"
echo "================================="
echo "✅ Your API is now running permanently at:"
echo "   🌐 http://$VPS_IP/"
echo "   📊 http://$VPS_IP/health"
echo "   📚 http://$VPS_IP/docs"
echo ""
echo "🔧 Management Commands:"
echo "   sudo systemctl status iban-api"
echo "   sudo systemctl restart iban-api"
echo "   sudo journalctl -u iban-api -f"
echo ""
echo "🧪 Test IBAN Calculation:"
echo "   curl -X POST http://$VPS_IP/calculate-iban \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"country_code\": \"GB\", \"bank_code\": \"200000\", \"account_number\": \"55779911\"}'"
echo ""
echo "🔄 Auto-restart: Service will automatically restart on failure or reboot"
echo "🔒 Security: Firewall configured, security headers added"
echo "📊 Monitoring: Logs available via journalctl"