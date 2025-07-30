# IBAN Calculator Scraper API

A FastAPI-based web scraper that calculates IBAN numbers using the iban.com calculator.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `python main.py`
3. Visit: http://localhost:8000/docs

## Usage
POST /calculate-iban with:
```json
{
  "country_code": "DE",
  "bank_code": "37040044", 
  "account_number": "532013000"
}