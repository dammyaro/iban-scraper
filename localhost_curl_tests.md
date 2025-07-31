# Local IBAN API Test Samples

## 🏠 Base URL: http://localhost:8000

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. API Information
```bash
curl http://localhost:8000/
```

### 3. German IBAN (Deutsche Bank)
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE",
    "bank_code": "37040044",
    "account_number": "532013000"
  }'
```

### 4. UK IBAN (Barclays)
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "200000",
    "account_number": "55779911"
  }'
```

### 5. French IBAN (BNP Paribas)
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "FR",
    "bank_code": "20041",
    "account_number": "01005027637"
  }'
```

### 6. Italian IBAN (UniCredit)
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "IT",
    "bank_code": "05428",
    "account_number": "11101000000012345"
  }'
```

### 7. Spanish IBAN (Santander)
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "ES",
    "bank_code": "0049",
    "account_number": "015000001234567891"
  }'
```

### 8. Netherlands IBAN (ING)
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "NL",
    "bank_code": "ABNA",
    "account_number": "0417164300"
  }'
```

### 9. Austrian IBAN
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "AT",
    "bank_code": "19043",
    "account_number": "00234573201"
  }'
```

### 10. Belgian IBAN
```bash
curl -X POST http://localhost:8000/calculate-iban \
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
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "XX",
    "bank_code": "12345",
    "account_number": "67890"
  }'
```

### Missing Fields
```bash
curl -X POST http://localhost:8000/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE"
  }'
```

### Empty Values
```bash
curl -X POST http://localhost:8000/calculate-iban \
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
  curl -X POST http://localhost:8000/calculate-iban \
    -H "Content-Type: application/json" \
    -d '{
      "country_code": "DE",
      "bank_code": "37040044",
      "account_number": "532013000"
    }' && echo
  sleep 1
done
```

## 🧪 Quick Test Script for Local Development
```bash
#!/bin/bash
# Save as test_local_iban.sh and run: chmod +x test_local_iban.sh && ./test_local_iban.sh

API_URL="http://localhost:8000"

echo "Testing Local IBAN API..."

# Health check
echo "1. Health Check:"
curl -s "$API_URL/health" | jq '.' 2>/dev/null || curl -s "$API_URL/health"
echo

# API info
echo "2. API Info:"
curl -s "$API_URL/" | jq '.' 2>/dev/null || curl -s "$API_URL/"
echo

# German IBAN test
echo "3. German IBAN Test:"
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
echo

# UK IBAN test
echo "4. UK IBAN Test:"
curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "200000",
    "account_number": "55779911"
  }' | jq '.' 2>/dev/null || curl -s -X POST "$API_URL/calculate-iban" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "GB",
    "bank_code": "200000",
    "account_number": "55779911"
  }'

echo "✅ Local testing completed!"
```

## 🚀 Start Local Server First
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (if using Playwright fallback)
playwright install chromium

# Start the server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📱 Access Local Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health