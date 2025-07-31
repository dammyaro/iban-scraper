#!/bin/bash
# VPS Playwright Diagnostic Script

echo "🔍 VPS Playwright Diagnostic"
echo "============================"

# Check if we can SSH to the VPS
VPS_IP="142.93.113.224"

echo "1. Checking service status..."
ssh root@$VPS_IP "systemctl status iban-api --no-pager -l | head -20"

echo ""
echo "2. Checking recent logs..."
ssh root@$VPS_IP "journalctl -u iban-api --no-pager -n 50 | tail -20"

echo ""
echo "3. Checking Playwright installation..."
ssh root@$VPS_IP "sudo -u ibanapp bash -c 'cd /home/ibanapp/iban-scraper && source venv/bin/activate && playwright --version'"

echo ""
echo "4. Checking browser installation..."
ssh root@$VPS_IP "sudo -u ibanapp bash -c 'ls -la /home/ibanapp/.cache/ms-playwright/ 2>/dev/null || echo \"Browser cache not found\"'"

echo ""
echo "5. Checking system dependencies..."
ssh root@$VPS_IP "dpkg -l | grep -E '(chromium|libnss3|libgbm1)' | head -10"

echo ""
echo "6. Testing browser launch..."
ssh root@$VPS_IP "sudo -u ibanapp bash -c 'cd /home/ibanapp/iban-scraper && source venv/bin/activate && python3 -c \"
import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=[\"--no-sandbox\", \"--disable-dev-shm-usage\"])
            page = await browser.new_page()
            await page.goto(\"https://www.google.com\", timeout=10000)
            title = await page.title()
            await browser.close()
            print(f\"✅ Browser test successful: {title}\")
    except Exception as e:
        print(f\"❌ Browser test failed: {e}\")

asyncio.run(test_browser())
\"'"