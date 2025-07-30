# Quick IBAN API Test Samples

## 🚀 Your API: https://iban-scraper-fast-z5cmh.ondigitalocean.app/

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

### 4. UK IBAN (Sort Code Format)
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

## 🧪 Run All Tests
```bash
# Make the test script executable and run it
chmod +x test_api.sh
./test_api.sh
```

## 📊 API Documentation
- **Swagger UI**: https://iban-scraper-fast-z5cmh.ondigitalocean.app/docs
- **ReDoc**: https://iban-scraper-fast-z5cmh.ondigitalocean.app/redoc

## 🚨 Error Testing
```bash
# Test with invalid country code
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "XX",
    "bank_code": "12345",
    "account_number": "67890"
  }'

# Test with missing fields
curl -X POST https://iban-scraper-fast-z5cmh.ondigitalocean.app/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "DE"
  }'
```