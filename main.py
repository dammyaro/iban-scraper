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
    title="IBAN Calculator Scraper",
    description="A web scraper API that calculates IBAN numbers using Wise",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    """Calculate IBAN using Wise - simplified working version"""
    try:
        logger.info("Attempting IBAN calculation using Wise")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--single-process',
                    '--no-zygote',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            page = await browser.new_page()
            
            try:
                # Navigate to Wise with extended timeout for cloud environment
                timeout_ms = int(os.getenv("PLAYWRIGHT_TIMEOUT", "60000"))  # Even longer timeout
                logger.info(f"Navigating to Wise with {timeout_ms}ms timeout")
                await page.goto("https://wise.com/ca/iban/calculator", timeout=timeout_ms)
                await page.wait_for_timeout(5000)  # Longer wait for cloud environment
                logger.info("Page loaded successfully")
                
                # Select country
                await page.click('button:has-text("Select a Country")')
                await page.wait_for_timeout(1000)
                
                if country_code.upper() == 'GB':
                    await page.click('text=United Kingdom')
                elif country_code.upper() == 'DE':
                    await page.click('text=Germany')
                elif country_code.upper() == 'FR':
                    await page.click('text=France')
                else:
                    await page.click(f'text={country_code.upper()}')
                
                await page.wait_for_timeout(2000)
                logger.info(f"Selected country: {country_code}")
                
                # Fill form
                await page.fill('input[name="branch_code"]', bank_code)
                await page.fill('input[name="account_number"]', account_number)
                logger.info("Form filled")
                
                # Click calculate
                await page.click('button:has-text("Calculate IBAN")')
                await page.wait_for_timeout(3000)
                logger.info("Calculate clicked")
                
                # Get page content
                content = await page.content()
                logger.info(f"Content length: {len(content)}")
                
                # Look for IBAN and bank name
                iban = None
                bank_name = None
                
                # Method 1: Country-specific patterns
                if country_code.upper() == 'GB':
                    iban_match = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', content)
                elif country_code.upper() == 'DE':
                    iban_match = re.search(r'\b(DE[0-9]{2}[A-Z0-9]{18})\b', content)
                else:
                    iban_match = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\b', content)
                
                if iban_match:
                    iban = iban_match.group(1)
                    logger.info(f"Found IBAN: {iban}")
                
                # Method 2: Extract bank name from JavaScript dataLayer
                bank_name_js = re.search(r"'ibanBankName':\s*[\"']([^\"']+)[\"']", content)
                if bank_name_js:
                    bank_name = bank_name_js.group(1)
                    logger.info(f"Found bank name from JS: {bank_name}")
                
                # Method 3: Extract bank name from image alt text (fallback)
                if not bank_name:
                    soup = BeautifulSoup(content, 'html.parser')
                    bank_img = soup.find('img', {'class': 'bank-logo'})
                    if bank_img and bank_img.get('alt'):
                        bank_name = bank_img.get('alt')
                        logger.info(f"Found bank name from image alt: {bank_name}")
                
                # Method 4: Look for bank name patterns in text (fallback)
                if not bank_name:
                    uk_banks = [
                        'BANK OF SCOTLAND PLC', 'HALIFAX PLC', 'BARCLAYS BANK PLC',
                        'HSBC UK BANK PLC', 'LLOYDS BANK PLC', 'NATWEST BANK PLC',
                        'SANTANDER UK PLC', 'TSB BANK PLC', 'NATIONWIDE BUILDING SOCIETY'
                    ]
                    for bank in uk_banks:
                        if bank in content:
                            bank_name = bank
                            logger.info(f"Found bank name by pattern: {bank_name}")
                            break
                
                await browser.close()
                
                if not iban or len(iban) < 15:
                    raise Exception("Could not extract valid IBAN")
                
                check_digits = iban[2:4] if len(iban) >= 4 else ""
                is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
                
                return {
                    "iban": iban,
                    "country": country_code.upper(),
                    "bank_code": bank_code,
                    "account_number": account_number,
                    "check_digits": check_digits,
                    "is_valid": is_valid,
                    "bank_name": bank_name,
                    "message": "IBAN calculated successfully",
                    "method_used": "wise"
                }
                
            except Exception as e:
                await browser.close()
                raise e
                
    except Exception as e:
        logger.error(f"Wise method failed: {e}")
        raise Exception(f"Wise failed: {str(e)}")

class IBANScraper:
    def __init__(self):
        pass
    
    async def calculate_iban(self, country_code: str, bank_code: str, account_number: str) -> dict:
        """Calculate IBAN using Wise"""
        try:
            logger.info("Using Wise method")
            return await calculate_iban_wise(country_code, bank_code, account_number)
        except Exception as e:
            logger.error(f"Wise method failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"IBAN calculation failed. Wise error: {str(e)}"
            )

# Global scraper instance
scraper = IBANScraper()

@app.get("/")
async def root():
    return {
        "message": "IBAN Calculator Scraper API",
        "version": "3.1.0 (Wise Fixed)",
        "description": "Calculate IBAN numbers using Wise",
        "methods": ["wise"],
        "platform": platform.system(),
        "environment": "testing",
        "endpoints": {
            "calculate": "/calculate-iban",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IBAN Calculator Scraper",
        "platform": platform.system(),
        "version": "3.1.0"
    }

@app.post("/calculate-iban", response_model=IBANResponse)
async def calculate_iban_endpoint(request: IBANRequest):
    """Calculate IBAN using Wise"""
    try:
        # Validate input
        if not request.country_code or len(request.country_code) != 2:
            raise HTTPException(status_code=400, detail="Country code must be 2 characters")
        
        if not request.bank_code or not request.account_number:
            raise HTTPException(status_code=400, detail="Bank code and account number required")
        
        # Clean inputs
        country_code = request.country_code.strip().upper()
        bank_code = request.bank_code.strip()
        account_number = request.account_number.strip()
        
        logger.info(f"Calculating IBAN for {country_code}, {bank_code}, {account_number}")
        
        # Calculate IBAN
        result = await scraper.calculate_iban(country_code, bank_code, account_number)
        
        return IBANResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting IBAN Calculator API on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, reload=False)