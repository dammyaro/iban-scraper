from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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

def setup_chrome_options():
    """Enhanced Chrome setup optimized for Digital Ocean App Platform"""
    chrome_options = Options()
    
    # Headless mode - required for server environments
    if os.getenv("CHROME_HEADLESS", "true").lower() == "true":
        chrome_options.add_argument("--headless=new")
    
    # Essential stability options for containerized environments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Memory optimization for limited resources
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=2048")
    chrome_options.add_argument("--aggressive-cache-discard")
    
    # Disable unnecessary features to save resources
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-default-apps")
    
    # Process optimization
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--disable-setuid-sandbox")
    
    # Window and display settings
    chrome_options.add_argument("--window-size=1024,768")
    chrome_options.add_argument("--virtual-time-budget=5000")
    
    # User agent for better compatibility
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Disable automation detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set Chrome binary location for Linux containers
    if platform.system() == "Linux":
        chrome_options.binary_location = "/usr/bin/google-chrome"
    elif platform.system() == "Darwin":
        # Keep macOS support for local development
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"
        ]
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
                logger.info(f"Using Chrome binary: {chrome_path}")
                break
    
    return chrome_options

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
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver optimized for Digital Ocean App Platform"""
        try:
            chrome_options = setup_chrome_options()
            
            # Get ChromeDriver with timeout handling
            chrome_driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver path: {chrome_driver_path}")
            
            # Fix permissions for both macOS and Linux
            try:
                if platform.system() == "Darwin":
                    subprocess.run(['xattr', '-d', 'com.apple.quarantine', chrome_driver_path], 
                                 check=False, capture_output=True)
                subprocess.run(['chmod', '+x', chrome_driver_path], 
                             check=False, capture_output=True)
                logger.info("Fixed ChromeDriver permissions")
            except Exception as e:
                logger.warning(f"Could not fix permissions: {e}")
            
            # Create service with optimized settings
            service = Service(
                chrome_driver_path,
                log_level='ERROR',  # Reduce Chrome logs
                service_args=['--verbose']
            )
            
            # Initialize driver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    break
                except Exception as e:
                    logger.warning(f"Driver initialization attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
            
            # Set optimized timeouts for Digital Ocean
            selenium_timeout = int(os.getenv("SELENIUM_TIMEOUT", "30"))
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(selenium_timeout)
            self.driver.set_script_timeout(15)
            
            logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            raise Exception(f"Chrome setup failed: {str(e)}")
    
    def close_driver(self):
        """Safely close the driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def calculate_iban_selenium(self, country_code: str, bank_code: str, account_number: str) -> dict:
        """Calculate IBAN using Selenium (primary method)"""
        try:
            self.setup_driver()
            
            url = "https://www.iban.com/calculate-iban"
            logger.info(f"Navigating to {url}")
            
            self.driver.get(url)
            
            # Wait and select country
            country_dropdown = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "country"))
            )
            
            select = Select(country_dropdown)
            select.select_by_value(country_code.upper())
            logger.info(f"Selected country: {country_code}")
            
            time.sleep(1)  # Wait for form update
            
            # Fill bank code
            bank_field = self.driver.find_element(By.ID, "bank")
            bank_field.clear()
            bank_field.send_keys(bank_code)
            
            # Fill account number
            account_field = self.driver.find_element(By.ID, "account")
            account_field.clear()
            account_field.send_keys(account_number)
            
            # Submit form
            calculate_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            calculate_btn.click()
            
            logger.info("Form submitted, waiting for result")
            
            # Wait for result
            WebDriverWait(self.driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "iban")),
                    EC.presence_of_element_located((By.CLASS_NAME, "result")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".alert"))
                )
            )
            
            # Extract IBAN
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
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
            
            if not iban or len(iban) < 15:
                raise Exception("Could not extract valid IBAN from Selenium result")
            
            check_digits = iban[2:4] if len(iban) >= 4 else ""
            is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
            
            logger.info(f"Successfully calculated IBAN using Selenium: {iban}")
            
            return {
                "iban": iban,
                "country": country_code.upper(),
                "bank_code": bank_code,
                "account_number": account_number,
                "check_digits": check_digits,
                "is_valid": is_valid,
                "message": "IBAN calculated successfully",
                "method_used": "selenium"
            }
            
        except Exception as e:
            logger.error(f"Selenium method failed: {e}")
            raise Exception(f"Selenium failed: {str(e)}")
        
        finally:
            self.close_driver()
    
    def calculate_iban(self, country_code: str, bank_code: str, account_number: str) -> dict:
        """Calculate IBAN with fallback methods"""
        
        # Method 1: Try requests-only first (more reliable on macOS)
        try:
            logger.info("Trying requests-only method first")
            return calculate_iban_requests_only(country_code, bank_code, account_number)
        except Exception as e:
            logger.warning(f"Requests-only method failed: {e}")
        
        # Method 2: Try Selenium as fallback
        try:
            logger.info("Trying Selenium method as fallback")
            return self.calculate_iban_selenium(country_code, bank_code, account_number)
        except Exception as e:
            logger.error(f"Selenium method also failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Both calculation methods failed. Requests: Failed, Selenium: {str(e)}"
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
        
        # Calculate IBAN using fallback methods
        result = scraper.calculate_iban(country_code, bank_code, account_number)
        
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