# 🚀 Digital Ocean VPS Deployment Guide

## 📋 **VPS Setup**

### **1. Create Digital Ocean Droplet**
- **Size**: Basic ($6/month) - 1 vCPU, 1GB RAM, 25GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Region**: Choose closest to your users
- **Authentication**: SSH keys recommended

### **2. Initial Server Setup**
```bash
# Connect to your VPS
ssh root@your_vps_ip

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git nginx supervisor curl

# Install Node.js (for Playwright)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs
```

### **3. Install Playwright System Dependencies**
```bash
# Install Playwright system dependencies
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
```

## 🔧 **Application Deployment**

### **4. Setup Application**
```bash
# Create app user
useradd -m -s /bin/bash ibanapp
su - ibanapp

# Clone repository
git clone https://github.com/dammyaro/iban-scraper.git
cd iban-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### **5. Test Application**
```bash
# Test locally on VPS
python main_fixed.py

# Test API (in another terminal)
curl http://localhost:8000/health
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{"country_code": "GB", "bank_code": "200000", "account_number": "55779911"}'
```

## 🌐 **Production Setup**

### **6. Create Systemd Service**
```bash
# Exit from ibanapp user
exit

# Create service file
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
systemctl status iban-api
```

### **7. Setup Nginx Reverse Proxy**
```bash
# Create Nginx config
cat > /etc/nginx/sites-available/iban-api << 'EOF'
server {
    listen 80;
    server_name your_domain.com;  # Replace with your domain or IP

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
ln -s /etc/nginx/sites-available/iban-api /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### **8. Setup Firewall**
```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

## 🔒 **SSL Setup (Optional)**

### **9. Install SSL Certificate**
```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
certbot --nginx -d your_domain.com

# Auto-renewal
systemctl enable certbot.timer
```

## 📊 **Monitoring & Maintenance**

### **10. Useful Commands**
```bash
# Check service status
systemctl status iban-api

# View logs
journalctl -u iban-api -f

# Restart service
systemctl restart iban-api

# Update application
su - ibanapp
cd iban-scraper
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
systemctl restart iban-api

# Check Nginx
systemctl status nginx
nginx -t

# Monitor resources
htop
df -h
free -h
```

### **11. Test Endpoints**
```bash
# Health check
curl http://your_vps_ip/health

# IBAN calculation
curl -X POST http://your_vps_ip/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{"country_code": "GB", "bank_code": "200000", "account_number": "55779911"}'

# API documentation
curl http://your_vps_ip/docs
```

## 🎯 **Expected Benefits**

- ✅ **Full Control**: Complete server access
- ✅ **Better Performance**: Dedicated resources
- ✅ **No Timeouts**: No platform limitations
- ✅ **Cost Effective**: $6/month vs App Platform costs
- ✅ **Easier Debugging**: Direct server access
- ✅ **Custom Configuration**: Optimize for Playwright

## 🚨 **Security Notes**

- Change default SSH port
- Use SSH keys instead of passwords
- Keep system updated
- Monitor logs regularly
- Consider fail2ban for SSH protection

## 📞 **Support**

If you need help with any step, the VPS approach gives us much more flexibility to debug and optimize the Playwright setup!