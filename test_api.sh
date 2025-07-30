#!/bin/bash
# Test script for IBAN Calculator API
# Deployed at: https://iban-scraper-fast-z5cmh.ondigitalocean.app/

API_URL="https://iban-scraper-fast-z5cmh.ondigitalocean.app"

echo "🧪 Testing IBAN Calculator API"
echo "================================"

# Test 1: Health Check
echo "1. Health Check:"
curl -s "$API_URL/health" | jq '.' || curl -s "$API_URL/health"
echo -e "\n"

# Test 2: API Info
echo "2. API Information:"
curl -s "$API_URL/" | jq '.' || curl -s "$API_URL/"
echo -e "\n"

# Test 3: German IBAN Calculation
echo "3. German IBAN (Deutsche Bank):"
curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "37040044",
    "account_number": "532013000"
  }' | jq '.' || curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "37040044",
    "account_number": "532013000"
  }'
echo -e "\n"

# Test 4: UK IBAN Calculation
echo "4. UK IBAN (Barclays):"
curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "ABNA",
    "account_number": "0400000007"
  }' | jq '.' || curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "ABNA",
    "account_number": "0400000007"
  }'
echo -e "\n"

# Test 5: French IBAN Calculation
echo "5. French IBAN (BNP Paribas):"
curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "FR",
    "bank_code": "20041",
    "account_number": "01005027637"
  }' | jq '.' || curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "FR",
    "bank_code": "20041",
    "account_number": "01005027637"
  }'
echo -e "\n"

# Test 6: Invalid Input Test
echo "6. Invalid Input Test:"
curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "XX",
    "bank_code": "",
    "account_number": ""
  }' | jq '.' || curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "XX",
    "bank_code": "",
    "account_number": ""
  }'
echo -e "\n"

echo "✅ API Testing Complete!"