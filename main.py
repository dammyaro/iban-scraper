from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import logging
import os
import platform
import subprocess
import requests
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
    description="A web scraper API that calculates IBAN numbers using iban.com",
    version="1.0.0",
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
    message: Optional[str] = None
    method_used: Optional[str] = None

async def calculate_iban_playwright(country_code: str, bank_code: str, account_number: str) -> dict:
    """Calculate IBAN using Playwright (more reliable than Selenium)"""
    try:
        logger.info("Attempting IBAN calculation using Playwright")
        
        async with async_playwright() as p:
            # Launch browser with optimized settings for Digital Ocean
            headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--disable-translate',
                    '--disable-default-apps',
                    '--single-process',
                    '--no-zygote',
                    '--disable-setuid-sandbox',
                    '--disable-extensions',
                    '--disable-plugins'
                ]
            )
            
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Navigate to Wise IBAN calculator
            url = "https://wise.com/ca/iban/calculator"
            timeout = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))
            await page.goto(url, timeout=timeout)
            
            # Wait for page to load completely
            await page.wait_for_load_state('networkidle')
            
            # Step 1: Click on country dropdown to open it
            await page.click('button:has-text("Select a Country")')
            await page.wait_for_timeout(1000)
            
            # Step 2: Select the country (United Kingdom for GB)
            if country_code.upper() == 'GB':
                await page.click('text=United Kingdom')
            elif country_code.upper() == 'DE':
                await page.click('text=Germany')
            elif country_code.upper() == 'FR':
                await page.click('text=France')
            else:
                # Try to find the country by code or name
                await page.click(f'text={country_code.upper()}')
            
            await page.wait_for_timeout(2000)  # Wait for form to transform
            
            # Step 3: Fill bank code (sort code for UK)
            # The form should now show bank details inputs with specific names
            await page.fill('input[name="branch_code"]', bank_code)
            logger.info(f"Filled sort code: {bank_code}")
            
            # Step 4: Fill account number
            await page.fill('input[name="account_number"]', account_number)
            logger.info(f"Filled account number: {account_number}")
            
            # Step 5: Click calculate IBAN button
            await page.click('button:has-text("Calculate IBAN")')
            
            # Wait for result - look for the result page or any indication of completion
            result_timeout = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")) // 2
            await page.wait_for_load_state('networkidle', timeout=result_timeout)
            
            # Extract IBAN from Wise interface
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            iban = None
            
            # Method 1: Look for IBAN in result display area
            result_elements = await page.query_selector_all('.result, .iban-result, [class*="result"], [class*="iban"]')
            for element in result_elements:
                text = await element.text_content()
                if text:
                    text = text.strip()
                    if len(text) >= 15 and re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', text):
                        iban = text
                        logger.info(f"Found IBAN in result element: {iban}")
                        break
            
            # Method 2: Look for IBAN in any visible text on page
            if not iban:
                all_elements = await page.query_selector_all('*')
                for element in all_elements:
                    try:
                        text = await element.text_content()
                        if text and len(text.strip()) >= 15:
                            text = text.strip()
                            # Look for IBAN pattern in the text
                            iban_match = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\b', text)
                            if iban_match:
                                potential_iban = iban_match.group(1)
                                # Validate it starts with the correct country code
                                if potential_iban.startswith(country_code.upper()):
                                    iban = potential_iban
                                    logger.info(f"Found IBAN in page element: {iban}")
                                    break
                    except:
                        continue
            
            # Method 3: Look for country-specific IBAN patterns
            if not iban:
                if country_code.upper() == 'GB':
                    # UK IBAN pattern: GB + 2 digits + 4 letters + 6 digits + 8 digits
                    iban_pattern = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', page_content)
                elif country_code.upper() == 'DE':
                    # German IBAN pattern
                    iban_pattern = re.search(r'\b(DE[0-9]{2}[A-Z0-9]{16,18})\b', page_content)
                else:
                    # General IBAN pattern
                    iban_pattern = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', page_content)
                
                if iban_pattern:
                    iban = iban_pattern.group(1)
                    logger.info(f"Found IBAN by pattern matching: {iban}")
            
            # Method 4: Look in any text content for IBAN
            if not iban:
                # Remove spaces and look for IBAN pattern
                clean_content = re.sub(r'\s+', '', page_content)
                iban_pattern = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', clean_content)
                if iban_pattern:
                    iban = iban_pattern.group(1)
                    logger.info(f"Found IBAN in cleaned content: {iban}")
            
            # Method 5: Look in all text elements
            if not iban:
                all_text_elements = soup.find_all(text=True)
                for text_element in all_text_elements:
                    text = str(text_element).strip()
                    if len(text) >= 15:
                        iban_match = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', text)
                        if iban_match:
                            iban = iban_match.group(1)
                            logger.info(f"Found IBAN in text element: {iban}")
                            break
            
            await browser.close()
            
            if not iban or len(iban) < 15:
                raise Exception("Could not extract valid IBAN from Playwright result")
            
            check_digits = iban[2:4] if len(iban) >= 4 else ""
            is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
            
            logger.info(f"Successfully calculated IBAN using Playwright: {iban}")
            
            return {
                "iban": iban,
                "country": country_code.upper(),
                "bank_code": bank_code,
                "account_number": account_number,
                "check_digits": check_digits,
                "is_valid": is_valid,
                "message": "IBAN calculated successfully",
                "method_used": "playwright"
            }
            
    except Exception as e:
        logger.error(f"Playwright method failed: {e}")
        raise Exception(f"Playwright failed: {str(e)}")

# Removed other methods - focusing only on Playwright

class IBANScraper:
    def __init__(self):
        pass
    
    async def calculate_iban(self, country_code: str, bank_code: str, account_number: str) -> dict:
        """Calculate IBAN using only Playwright for testing"""
        
        try:
            logger.info("Using Playwright method only")
            return await calculate_iban_playwright(country_code, bank_code, account_number)
        except Exception as e:
            logger.error(f"Playwright method failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"IBAN calculation failed. Playwright error: {str(e)}"
            )

# Global scraper instance
scraper = IBANScraper()

@app.get("/")
async def root():
    return {
        "message": "IBAN Calculator Scraper API",
        "version": "3.0.0 (Playwright Only - Testing)",
        "description": "Calculate IBAN numbers using Playwright browser automation",
        "methods": ["playwright_only"],
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
        "version": "1.0.0"
    }

@app.post("/calculate-iban", response_model=IBANResponse)
async def calculate_iban_endpoint(request: IBANRequest):
    """Calculate IBAN with multiple fallback methods"""
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
        
        # Calculate IBAN using async fallback methods
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
    
    logger.info(f"Starting IBAN Calculator API on {host}:{port} (macOS optimized)")
    
    uvicorn.run(app, host=host, port=port, reload=False)  # Disable reload for stability