#!/bin/bash
# Fix VPS Playwright Setup

set -e

VPS_IP="142.93.113.224"

echo "🔧 Fixing VPS Playwright Setup"
echo "==============================="

echo "1. Stopping the service..."
ssh root@$VPS_IP "systemctl stop iban-api"

echo "2. Installing additional system dependencies..."
ssh root@$VPS_IP "
apt update
apt install -y \
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
"

echo "3. Reinstalling Playwright browsers with proper permissions..."
ssh root@$VPS_IP "
sudo -u ibanapp bash -c '
cd /home/ibanapp/iban-scraper
source venv/bin/activate

# Remove old browser cache
rm -rf ~/.cache/ms-playwright

# Reinstall Playwright
pip install --upgrade playwright

# Install browsers with dependencies
PLAYWRIGHT_BROWSERS_PATH=/home/ibanapp/.cache/ms-playwright playwright install chromium
playwright install-deps chromium

# Set proper permissions
chmod -R 755 ~/.cache/ms-playwright
'
"

echo "4. Updating the main application with better browser args..."
ssh root@$VPS_IP "
cd /home/ibanapp/iban-scraper
cat > main_fixed_vps.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import logging
import os
import platform
import re
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title=\"IBAN Calculator Scraper\",
    description=\"A web scraper API that calculates IBAN numbers using Wise\",
    version=\"3.1.1\",
    docs_url=\"/docs\",
    redoc_url=\"/redoc\"
)

# Pydantic models
class IBANRequest(BaseModel):
    country_code: str
    bank_code: str
    account_number: str

class IBANResponse(BaseModel):
    iban: str
    country: str
    bank_code: str
    account_number: str
    check_digits: str
    is_valid: bool
    bank_name: Optional[str] = None
    message: Optional[str] = None
    method_used: Optional[str] = None

async def calculate_iban_wise(country_code: str, bank_code: str, account_number: str) -> dict:
    \"\"\"Calculate IBAN using Wise - VPS optimized version\"\"\"
    try:
        logger.info(\"Attempting IBAN calculation using Wise (VPS optimized)\")
        
        async with async_playwright() as p:
            # Enhanced browser args for VPS environment
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--memory-pressure-off',
                    '--max_old_space_size=4096',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-javascript',
                    '--disable-default-apps',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-background-networking'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to Wise with extended timeout
                timeout_ms = 90000  # 90 seconds for VPS
                logger.info(f\"Navigating to Wise with {timeout_ms}ms timeout\")
                
                await page.goto(\"https://wise.com/ca/iban/calculator\", 
                              timeout=timeout_ms, 
                              wait_until='networkidle')
                
                await page.wait_for_timeout(3000)
                logger.info(\"Page loaded successfully\")
                
                # Select country with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await page.click('button:has-text(\"Select a Country\")', timeout=10000)
                        await page.wait_for_timeout(2000)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f\"Country selection attempt {attempt + 1} failed, retrying...\")
                        await page.wait_for_timeout(2000)
                
                # Select specific country
                if country_code.upper() == 'GB':
                    await page.click('text=United Kingdom')
                elif country_code.upper() == 'DE':
                    await page.click('text=Germany')
                elif country_code.upper() == 'FR':
                    await page.click('text=France')
                else:
                    await page.click(f'text={country_code.upper()}')
                
                await page.wait_for_timeout(3000)
                logger.info(f\"Selected country: {country_code}\")
                
                # Fill form with retry logic
                await page.fill('input[name=\"branch_code\"]', bank_code)
                await page.wait_for_timeout(1000)
                await page.fill('input[name=\"account_number\"]', account_number)
                await page.wait_for_timeout(1000)
                logger.info(\"Form filled\")
                
                # Click calculate
                await page.click('button:has-text(\"Calculate IBAN\")')
                await page.wait_for_timeout(5000)
                logger.info(\"Calculate clicked\")
                
                # Get page content
                content = await page.content()
                logger.info(f\"Content length: {len(content)}\")
                
                # Look for IBAN and bank name
                iban = None
                bank_name = None
                
                # Country-specific IBAN patterns
                if country_code.upper() == 'GB':
                    iban_match = re.search(r'\\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\\b', content)
                elif country_code.upper() == 'DE':
                    iban_match = re.search(r'\\b(DE[0-9]{2}[A-Z0-9]{18})\\b', content)
                else:
                    iban_match = re.search(r'\\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\\b', content)
                
                if iban_match:
                    iban = iban_match.group(1)
                    logger.info(f\"Found IBAN: {iban}\")
                
                # Extract bank name
                bank_name_js = re.search(r\"'ibanBankName':\\s*[\\\"']([^\\\"']+)[\\\"']\", content)
                if bank_name_js:
                    bank_name = bank_name_js.group(1)
                    logger.info(f\"Found bank name: {bank_name}\")
                
                await browser.close()
                
                if not iban or len(iban) < 15:
                    raise Exception(\"Could not extract valid IBAN from page\")
                
                check_digits = iban[2:4] if len(iban) >= 4 else \"\"
                is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
                
                return {
                    \"iban\": iban,
                    \"country\": country_code.upper(),
                    \"bank_code\": bank_code,
                    \"account_number\": account_number,
                    \"check_digits\": check_digits,
                    \"is_valid\": is_valid,
                    \"bank_name\": bank_name,
                    \"message\": \"IBAN calculated successfully\",
                    \"method_used\": \"wise_vps_optimized\"
                }
                
            except Exception as e:
                await browser.close()
                raise e
                
    except Exception as e:
        logger.error(f\"Wise method failed: {e}\")
        raise Exception(f\"Wise failed: {str(e)}\")

class IBANScraper:
    def __init__(self):
        pass
    
    async def calculate_iban(self, country_code: str, bank_code: str, account_number: str) -> dict:
        \"\"\"Calculate IBAN using Wise\"\"\"
        try:
            logger.info(\"Using Wise method (VPS optimized)\")
            return await calculate_iban_wise(country_code, bank_code, account_number)
        except Exception as e:
            logger.error(f\"Wise method failed: {e}\")
            raise HTTPException(
                status_code=500, 
                detail=f\"IBAN calculation failed. Wise error: {str(e)}\"
            )

# Global scraper instance
scraper = IBANScraper()

@app.get(\"/\")
async def root():
    return {
        \"message\": \"IBAN Calculator Scraper API\",
        \"version\": \"3.1.1 (VPS Optimized)\",
        \"description\": \"Calculate IBAN numbers using Wise\",
        \"methods\": [\"wise_vps_optimized\"],
        \"platform\": platform.system(),
        \"environment\": \"production_vps\",
        \"endpoints\": {
            \"calculate\": \"/calculate-iban\",
            \"health\": \"/health\",
            \"docs\": \"/docs\",
            \"redoc\": \"/redoc\"
        }
    }

@app.get(\"/health\")
async def health_check():
    return {
        \"status\": \"healthy\",
        \"service\": \"IBAN Calculator Scraper\",
        \"platform\": platform.system(),
        \"version\": \"3.1.1\"
    }

@app.post(\"/calculate-iban\", response_model=IBANResponse)
async def calculate_iban_endpoint(request: IBANRequest):
    \"\"\"Calculate IBAN using Wise\"\"\"
    try:
        # Validate input
        if not request.country_code or len(request.country_code) != 2:
            raise HTTPException(status_code=400, detail=\"Country code must be 2 characters\")
        
        if not request.bank_code or not request.account_number:
            raise HTTPException(status_code=400, detail=\"Bank code and account number required\")
        
        # Clean inputs
        country_code = request.country_code.strip().upper()
        bank_code = request.bank_code.strip()
        account_number = request.account_number.strip()
        
        logger.info(f\"Calculating IBAN for {country_code}, {bank_code}, {account_number}\")
        
        # Calculate IBAN
        result = await scraper.calculate_iban(country_code, bank_code, account_number)
        
        return IBANResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"Unexpected error: {e}\")
        raise HTTPException(status_code=500, detail=\"Internal server error\")

if __name__ == \"__main__\":
    import uvicorn
    
    host = os.getenv(\"HOST\", \"0.0.0.0\")
    port = int(os.getenv(\"PORT\", 8000))
    
    logger.info(f\"Starting IBAN Calculator API on {host}:{port}\")
    
    uvicorn.run(app, host=host, port=port, reload=False)
EOF
"

echo "5. Updating systemd service to use the new file..."
ssh root@$VPS_IP "
sed -i 's/main_fixed.py/main_fixed_vps.py/g' /etc/systemd/system/iban-api.service
systemctl daemon-reload
"

echo "6. Starting the service..."
ssh root@$VPS_IP "systemctl start iban-api"

echo "7. Waiting for service to start..."
sleep 10

echo "8. Testing the fixed deployment..."
curl -s http://$VPS_IP/health | jq '.' || curl -s http://$VPS_IP/health

echo ""
echo "9. Testing IBAN calculation..."
curl -s -X POST http://$VPS_IP/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "200000",
    "account_number": "55779911"
  }' | jq '.' || curl -s -X POST http://$VPS_IP/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "200000",
    "account_number": "55779911"
  }'

echo ""
echo "✅ VPS Playwright fix complete!"