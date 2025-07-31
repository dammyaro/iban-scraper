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
                    '--no-zygote'
                ]
            )
            
            page = await browser.new_page()
            
            try:
                # Navigate to Wise
                await page.goto("https://wise.com/ca/iban/calculator", timeout=30000)
                await page.wait_for_timeout(2000)  # Simple wait instead of networkidle
                logger.info("Page loaded")
                
                # Try multiple approaches for country selection
                logger.info("Attempting country selection...")
                
                # Method 1: Try button click
                try:
                    await page.click('button:has-text("Select a Country")', timeout=30000)
                    await page.wait_for_timeout(2000)
                    logger.info("Country dropdown opened")
                except Exception as e:
                    logger.warning(f"Button click failed: {e}")
                    # Try alternative selector
                    await page.click('[data-testid="country-selector"]', timeout=30000)
                    await page.wait_for_timeout(2000)
                
                # Method 2: Select country with multiple attempts
                logger.info(f"Selecting country: {country_code}")
                country_selected = False
                
                for attempt in range(3):
                    try:
                        if country_code.upper() == 'GB':
                            await page.click('text=United Kingdom', timeout=30000)
                        elif country_code.upper() == 'DE':
                            await page.click('text=Germany', timeout=30000)
                        elif country_code.upper() == 'FR':
                            await page.click('text=France', timeout=30000)
                        else:
                            await page.click(f'text={country_code.upper()}', timeout=30000)
                        
                        country_selected = True
                        break
                    except Exception as e:
                        logger.warning(f"Country selection attempt {attempt + 1} failed: {e}")
                        await page.wait_for_timeout(2000)
                
                if not country_selected:
                    raise Exception("Failed to select country after 3 attempts")
                
                await page.wait_for_timeout(5000)
                logger.info(f"Selected country: {country_code}")
                
                # Fill form with retry logic
                logger.info("Filling form fields...")
                for attempt in range(3):
                    try:
                        await page.fill('input[name="branch_code"]', bank_code, timeout=20000)
                        await page.fill('input[name="account_number"]', account_number, timeout=20000)
                        logger.info("Form filled successfully")
                        break
                    except Exception as e:
                        logger.warning(f"Form fill attempt {attempt + 1} failed: {e}")
                        await page.wait_for_timeout(2000)
                
                # Click calculate with retry
                logger.info("Clicking calculate button...")
                for attempt in range(3):
                    try:
                        await page.click('button:has-text("Calculate IBAN")', timeout=30000)
                        logger.info("Calculate button clicked")
                        break
                    except Exception as e:
                        logger.warning(f"Calculate click attempt {attempt + 1} failed: {e}")
                        await page.wait_for_timeout(2000)
                
                await page.wait_for_timeout(10000)
                logger.info("Waiting for result...")
                
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