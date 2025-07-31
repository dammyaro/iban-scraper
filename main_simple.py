from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import time
import logging
import os
import platform
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
    description="A simple IBAN calculator using requests (no browser automation)",
    version="3.2.0",
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

def calculate_iban_simple(country_code: str, bank_code: str, account_number: str) -> dict:
    """Simple IBAN calculation using requests only - much faster for cloud"""
    try:
        logger.info("Attempting IBAN calculation using simple requests method")
        
        session = requests.Session()
        
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Try multiple IBAN calculator services
        services = [
            {
                "name": "iban.com",
                "url": "https://www.iban.com/calculate-iban",
                "method": "post",
                "data": {
                    'country': country_code.upper(),
                    'bank': bank_code,
                    'account': account_number
                }
            },
            {
                "name": "ibancalculator.com", 
                "url": "https://www.ibancalculator.com/",
                "method": "post",
                "data": {
                    'country': country_code.upper(),
                    'bankcode': bank_code,
                    'accountnumber': account_number
                }
            }
        ]
        
        for service in services:
            try:
                logger.info(f"Trying {service['name']}...")
                
                if service['method'] == 'post':
                    response = session.post(
                        service['url'], 
                        data=service['data'], 
                        headers=headers, 
                        timeout=15
                    )
                else:
                    response = session.get(service['url'], headers=headers, timeout=15)
                
                response.raise_for_status()
                
                # Parse response
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for IBAN patterns
                iban = None
                bank_name = None
                
                # Method 1: Look for IBAN input field
                iban_input = soup.find('input', {'name': 'iban'})
                if iban_input and iban_input.get('value'):
                    iban = iban_input.get('value').strip()
                
                # Method 2: Look for IBAN in page text
                if not iban:
                    page_text = response.text
                    if country_code.upper() == 'GB':
                        iban_match = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', page_text)
                    elif country_code.upper() == 'DE':
                        iban_match = re.search(r'\b(DE[0-9]{2}[A-Z0-9]{18})\b', page_text)
                    else:
                        iban_match = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\b', page_text)
                    
                    if iban_match:
                        iban = iban_match.group(1)
                
                # Look for bank name in common patterns
                if iban and country_code.upper() == 'GB':
                    bank_names = {
                        'BARC': 'BARCLAYS BANK PLC',
                        'HLFX': 'BANK OF SCOTLAND PLC', 
                        'HSBC': 'HSBC UK BANK PLC',
                        'LOYD': 'LLOYDS BANK PLC',
                        'NWBK': 'NATWEST BANK PLC',
                        'ABBY': 'SANTANDER UK PLC',
                        'TSBS': 'TSB BANK PLC',
                        'NAIA': 'NATIONWIDE BUILDING SOCIETY'
                    }
                    
                    if len(iban) >= 8:
                        bank_code_from_iban = iban[4:8]
                        bank_name = bank_names.get(bank_code_from_iban, f"UK BANK ({bank_code_from_iban})")
                
                if iban and len(iban) >= 15:
                    check_digits = iban[2:4] if len(iban) >= 4 else ""
                    is_valid = bool(iban and len(iban) >= 15 and iban[:2].isalpha() and iban[2:4].isdigit())
                    
                    logger.info(f"Successfully calculated IBAN using {service['name']}: {iban}")
                    
                    return {
                        "iban": iban,
                        "country": country_code.upper(),
                        "bank_code": bank_code,
                        "account_number": account_number,
                        "check_digits": check_digits,
                        "is_valid": is_valid,
                        "bank_name": bank_name,
                        "message": "IBAN calculated successfully",
                        "method_used": f"requests_{service['name']}"
                    }
                
            except Exception as e:
                logger.warning(f"{service['name']} failed: {e}")
                continue
        
        raise Exception("All IBAN calculation services failed")
        
    except Exception as e:
        logger.error(f"Simple requests method failed: {e}")
        raise Exception(f"Simple calculation failed: {str(e)}")

class IBANScraper:
    def __init__(self):
        pass
    
    async def calculate_iban(self, country_code: str, bank_code: str, account_number: str) -> dict:
        """Calculate IBAN using simple requests method"""
        try:
            logger.info("Using simple requests method")
            return calculate_iban_simple(country_code, bank_code, account_number)
        except Exception as e:
            logger.error(f"Simple method failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"IBAN calculation failed: {str(e)}"
            )

# Global scraper instance
scraper = IBANScraper()

@app.get("/")
async def root():
    return {
        "message": "IBAN Calculator Scraper API",
        "version": "3.2.0 (Simple & Fast)",
        "description": "Calculate IBAN numbers using simple requests (no browser)",
        "methods": ["requests_only"],
        "platform": platform.system(),
        "environment": "production",
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
        "version": "3.2.0"
    }

@app.post("/calculate-iban", response_model=IBANResponse)
async def calculate_iban_endpoint(request: IBANRequest):
    """Calculate IBAN using simple requests"""
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
    
    logger.info(f"Starting Simple IBAN Calculator API on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, reload=False)