# Sample Curl Tests for IBAN Scraper API

## 🚀 Base URL: https://iban-scraper-fast-z5cmh.ondigitalocean.app

### 1. Health Check
```bash
curl https://iban-scraper-fast-z5cmh.ondigitalocean.app/health
```

### 2. API Information
```bash
curl https://iban-scraper-fast-z5cmh.ondigitalocean.app/
```

### 3. German IBAN (Deutsche Bank)
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "37040044",
    "account_number": "532013000"
  }'
```

### 4. UK IBAN (Barclays)
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "200000",
    "account_number": "55779911"
  }'
```

### 5. French IBAN (BNP Paribas)
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "FR",
    "bank_code": "20041",
    "account_number": "01005027637"
  }'
```

### 6. Italian IBAN (UniCredit)
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "IT",
    "bank_code": "05428",
    "account_number": "11101000000012345"
  }'
```

### 7. Spanish IBAN (Santander)
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "ES",
    "bank_code": "0049",
    "account_number": "015000001234567891"
  }'
```

### 8. Netherlands IBAN (ING)
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "NL",
    "bank_code": "ABNA",
    "account_number": "0417164300"
  }'
```

### 9. Austrian IBAN
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "AT",
    "bank_code": "19043",
    "account_number": "00234573201"
  }'
```

### 10. Belgian IBAN
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "BE",
    "bank_code": "539",
    "account_number": "0075470"
  }'
```

## 🔍 Expected Response Format
```json
{
  "iban": "DE89370400440532013000",
  "country": "DE",
  "bank_code": "37040044",
  "account_number": "532013000",
  "check_digits": "89",
  "is_valid": true,
  "message": "IBAN calculated successfully",
  "method_used": "requests_optimized"
}
```

## 🚨 Error Testing

### Invalid Country Code
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "XX",
    "bank_code": "12345",
    "account_number": "67890"
  }'
```

### Missing Fields
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE"
  }'
```

### Empty Values
```bash
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "",
    "account_number": ""
  }'
```

## 📊 Performance Testing

### Multiple Requests (Bash Loop)
```bash
for i in {1..5}; do
  echo "Request $i:"
  curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
    -H "Content-Type: application/json" \
    -d '{
      "country_code": "DE",
      "bank_code": "37040044",
      "account_number": "532013000"
    }' && echo
  sleep 1
done
```

## 🧪 Quick Test Script
```bash
#!/bin/bash
# Save as test_iban_api.sh and run: chmod +x test_iban_api.sh && ./test_iban_api.sh

API_URL="https://iban-scraper-fast-z5cmh.ondigitalocean.app"

echo "Testing IBAN API..."

# Health check
echo "1. Health Check:"
curl -s "$API_URL/health" | jq '.' 2>/dev/null || curl -s "$API_URL/health"
echo

# German IBAN test
echo "2. German IBAN Test:"
curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "37040044",
    "account_number": "532013000"
  }' | jq '.' 2>/dev/null || curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "37040044",
    "account_number": "532013000"
  }'

echo "✅ Test completed!"
```