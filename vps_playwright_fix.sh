#!/bin/bash
# VPS Playwright Fix Script
# Run this on your VPS as root: ssh root@142.93.113.224

set -e

echo "🔧 VPS Playwright Fix Script"
echo "============================"
echo ""

echo "1. Stopping the IBAN API service..."
systemctl stop iban-api

echo "2. Installing system dependencies for Playwright..."
apt update && apt install -y \
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm-dev \
    libxkbcommon-dev \
    libxcomposite-dev \
    libxdamage-dev \
    libxrandr-dev \
    libgbm-dev \
    libxss-dev \
    libasound2-dev \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-noto-cjk

echo "3. Reinstalling Playwright browsers with proper permissions..."
sudo -u ibanapp bash -c '
cd /home/ibanapp/iban-scraper
source venv/bin/activate
rm -rf ~/.cache/ms-playwright
pip install --upgrade playwright
playwright install chromium
playwright install-deps chromium
chmod -R 755 ~/.cache/ms-playwright
'

echo "4. Testing browser installation..."
sudo -u ibanapp bash -c '
cd /home/ibanapp/iban-scraper
source venv/bin/activate
python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=[\"--no-sandbox\", \"--disable-dev-shm-usage\"]
        )
        await browser.close()
        print(\"✅ Browser test successful\")

asyncio.run(test())
"
'

echo "5. Starting the IBAN API service..."
systemctl start iban-api

echo "6. Checking service status..."
systemctl status iban-api --no-pager -l

echo ""
echo "✅ VPS Playwright fix complete!"
echo ""
echo "🧪 Test your API with:"
echo "curl http://142.93.113.224/health"
echo ""
echo "curl -X POST http://142.93.113.224/calculate-iban \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"country_code\": \"GB\", \"bank_code\": \"200000\", \"account_number\": \"55779911\"}'"