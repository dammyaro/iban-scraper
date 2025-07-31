#!/bin/bash
# Quick VPS deployment script for IBAN Calculator

set -e

echo "🚀 IBAN Calculator VPS Deployment Script"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "📦 Installing system packages..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx supervisor curl htop

# Install Node.js for Playwright
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Install Playwright system dependencies
echo "📦 Installing Playwright dependencies..."
apt install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils

# Create application user
echo "👤 Creating application user..."
if ! id "ibanapp" &>/dev/null; then
    useradd -m -s /bin/bash ibanapp
fi

# Setup application
echo "📁 Setting up application..."
sudo -u ibanapp bash << 'EOF'
cd /home/ibanapp

# Clone or update repository
if [ -d "iban-scraper" ]; then
    cd iban-scraper
    git pull
else
    git clone https://github.com/dammyaro/iban-scraper.git
    cd iban-scraper
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium

echo "✅ Application setup complete"
EOF

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/iban-api.service << 'EOF'
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

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable iban-api
systemctl start iban-api

# Setup Nginx
echo "🌐 Setting up Nginx..."
cat > /etc/nginx/sites-available/iban-api << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/iban-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Setup firewall
echo "🔒 Setting up firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "✅ Service Status:"
systemctl status iban-api --no-pager -l
echo ""
echo "🌐 Your API is available at:"
echo "   http://$SERVER_IP/"
echo "   http://$SERVER_IP/docs"
echo ""
echo "🧪 Test with:"
echo "   curl http://$SERVER_IP/health"
echo ""
echo "📊 Monitor with:"
echo "   systemctl status iban-api"
echo "   journalctl -u iban-api -f"
echo ""
echo "🔄 Update with:"
echo "   sudo systemctl restart iban-api"