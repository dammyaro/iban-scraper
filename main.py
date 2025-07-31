from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import httpx
import aiohttp
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
            # Launch browser with optimized settings
            browser = await p.chromium.launch(
                headless=True,
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
                    '--no-zygote'
                ]
            )
            
            page = await browser.new_page()
            
            # Set user agent
            await page.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Navigate to IBAN calculator
            url = "https://www.iban.com/calculate-iban"
            await page.goto(url, timeout=30000)
            
            # Fill the form
            await page.select_option('#country', country_code.upper())
            await page.wait_for_timeout(1000)  # Wait for form update
            
            await page.fill('#bank', bank_code)
            await page.fill('#account', account_number)
            
            # Submit form
            await page.click('button[type="submit"]')
            
            # Wait for result
            await page.wait_for_selector('#iban,div.result,.alert', timeout=15000)
            
            # Extract IBAN
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            iban = None
            
            # Method 1: Input field
            iban_input = soup.find('input', {'id': 'iban'})
            if iban_input and iban_input.get('value'):
                iban = iban_input.get('value').strip()
            
            # Method 2: Result text
            if not iban:
                result_div = soup.find('div', class_='result')
                if result_div:
                    iban_match = re.search(r'[A-Z]{2}[0-9]{2}[A-Z0-9]+', result_div.get_text())
                    if iban_match:
                        iban = iban_match.group()
            
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

async def calculate_iban_httpx(country_code: str, bank_code: str, account_number: str) -> dict:
    """Enhanced async requests method using httpx"""
    try:
        logger.info("Attempting IBAN calculation using async httpx")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0',
        }
        
        timeout = httpx.Timeout(20.0)
        
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # Get form page
            url = "https://www.iban.com/calculate-iban"
            response = await client.get(url)
            response.raise_for_status()
            
            # Parse form
            soup = BeautifulSoup(response.content, 'html.parser')
            form = soup.find('form')
            
            # Prepare form data
            form_data = {
                'country': country_code.upper(),
                'bank': bank_code,
                'account': account_number
            }
            
            # Add hidden fields
            if form:
                for hidden_input in form.find_all('input', type='hidden'):
                    name = hidden_input.get('name')
                    value = hidden_input.get('value', '')
                    if name:
                        form_data[name] = value
            
            # Submit form
            headers['Referer'] = url
            response = await client.post(url, data=form_data)
            response.raise_for_status()
            
            # Parse result
            soup = BeautifulSoup(response.content, 'html.parser')
            iban = None
            
            # Extract IBAN using multiple methods
            iban_input = soup.find('input', {'id': 'iban'})
            if iban_input and iban_input.get('value'):
                iban = iban_input.get('value').strip()
            
            if not iban:
                result_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'result|iban|output', re.I))
                for element in result_elements:
                    text = element.get_text()
                    iban_match = re.search(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4,32}\b', text)
                    if iban_match:
                        iban = iban_match.group()
                        break
            
            if not iban:
                page_text = soup.get_text()
                iban_pattern = re.search(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4,32}\b', page_text)
                if iban_pattern:
                    iban = iban_pattern.group()
            
            if not iban or len(iban) < 15:
                raise Exception("Could not extract valid IBAN from httpx response")
            
            check_digits = iban[2:4] if len(iban) >= 4 else ""
            is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
            
            logger.info(f"Successfully calculated IBAN using httpx: {iban}")
            
            return {
                "iban": iban,
                "country": country_code.upper(),
                "bank_code": bank_code,
                "account_number": account_number,
                "check_digits": check_digits,
                "is_valid": is_valid,
                "message": "IBAN calculated successfully",
                "method_used": "httpx_async"
            }
            
    except Exception as e:
        logger.error(f"Httpx method failed: {e}")
        raise Exception(f"Httpx method failed: {str(e)}")

def calculate_iban_requests_only(country_code: str, bank_code: str, account_number: str) -> dict:
    """Optimized requests-only approach - primary method for Digital Ocean"""
    try:
        logger.info("Attempting IBAN calculation using optimized requests-only method")
        
        session = requests.Session()
        
        # Optimized headers for better success rate
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0',
        }
        
        # Get timeout from environment
        request_timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))
        
        # Get the form page with retry logic
        url = "https://www.iban.com/calculate-iban"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching form page (attempt {attempt + 1})")
                response = session.get(url, headers=headers, timeout=request_timeout)
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Form fetch attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        
        # Parse form and extract any CSRF tokens or hidden fields
        soup = BeautifulSoup(response.content, 'html.parser')
        form = soup.find('form')
        
        # Prepare form data with any hidden fields
        form_data = {
            'country': country_code.upper(),
            'bank': bank_code,
            'account': account_number
        }
        
        # Add any hidden form fields
        if form:
            for hidden_input in form.find_all('input', type='hidden'):
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    form_data[name] = value
        
        # Submit form with retry logic
        for attempt in range(max_retries):
            try:
                logger.info(f"Submitting form (attempt {attempt + 1})")
                headers['Referer'] = url
                response = session.post(url, data=form_data, headers=headers, timeout=request_timeout)
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Form submission attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        
        # Parse result with multiple extraction methods
        soup = BeautifulSoup(response.content, 'html.parser')
        iban = None
        
        # Method 1: Look for IBAN input field
        iban_input = soup.find('input', {'id': 'iban'})
        if iban_input and iban_input.get('value'):
            iban = iban_input.get('value').strip()
            logger.info("IBAN found in input field")
        
        # Method 2: Look for result div or span
        if not iban:
            result_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'result|iban|output', re.I))
            for element in result_elements:
                text = element.get_text()
                iban_match = re.search(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4,32}\b', text)
                if iban_match:
                    iban = iban_match.group()
                    logger.info("IBAN found in result element")
                    break
        
        # Method 3: Look in entire page text as fallback
        if not iban:
            page_text = soup.get_text()
            iban_pattern = re.search(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4,32}\b', page_text)
            if iban_pattern:
                iban = iban_pattern.group()
                logger.info("IBAN found in page text")
        
        if not iban or len(iban) < 15:
            raise Exception("Could not extract valid IBAN from response")
        
        # Validate IBAN format
        check_digits = iban[2:4] if len(iban) >= 4 else ""
        is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
        
        logger.info(f"Successfully calculated IBAN using requests: {iban}")
        
        return {
            "iban": iban,
            "country": country_code.upper(),
            "bank_code": bank_code,
            "account_number": account_number,
            "check_digits": check_digits,
            "is_valid": is_valid,
            "message": "IBAN calculated successfully",
            "method_used": "requests_optimized"
        }
        
    except Exception as e:
        logger.error(f"Optimized requests method failed: {e}")
        raise Exception(f"Requests method failed: {str(e)}")

class IBANScraper:
    def __init__(self):
        pass
    
    async def calculate_iban(self, country_code: str, bank_code: str, account_number: str) -> dict:
        """Calculate IBAN with multiple fallback methods (no ChromeDriver needed!)"""
        
        # Method 1: Try sync requests first (fastest)
        try:
            logger.info("Trying optimized requests method")
            return calculate_iban_requests_only(country_code, bank_code, account_number)
        except Exception as e:
            logger.warning(f"Requests method failed: {e}")
        
        # Method 2: Try async httpx (better connection handling)
        try:
            logger.info("Trying async httpx method")
            return await calculate_iban_httpx(country_code, bank_code, account_number)
        except Exception as e:
            logger.warning(f"Httpx method failed: {e}")
        
        # Method 3: Try Playwright as last resort (if enabled)
        if os.getenv("DISABLE_PLAYWRIGHT", "false").lower() != "true":
            try:
                logger.info("Trying Playwright method as fallback")
                return await calculate_iban_playwright(country_code, bank_code, account_number)
            except Exception as e:
                logger.error(f"Playwright method also failed: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"All calculation methods failed. Requests: failed, Httpx: failed, Playwright: {str(e)}"
                )
        else:
            logger.info("Playwright disabled, only using HTTP methods")
            raise HTTPException(
                status_code=500, 
                detail="IBAN calculation failed. All HTTP methods failed and Playwright is disabled."
            )

# Global scraper instance
scraper = IBANScraper()

@app.get("/")
async def root():
    return {
        "message": "IBAN Calculator Scraper API",
        "version": "2.0.0 (Digital Ocean Optimized)",
        "description": "Calculate IBAN numbers with optimized fallback methods",
        "methods": ["requests_optimized", "selenium_fallback"],
        "platform": platform.system(),
        "environment": "production" if os.getenv("CHROME_HEADLESS", "true").lower() == "true" else "development",
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