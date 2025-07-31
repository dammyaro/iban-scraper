#!/bin/bash
# Fixed curl commands for local testing

echo "Testing IBAN API on localhost:8000"
echo "=================================="

# 1. Health Check
echo "1. Health Check:"
curl http://localhost:8000/health
echo -e "\n"

# 2. API Info
echo "2. API Information:"
curl http://localhost:8000/
echo -e "\n"

# 3. German IBAN (single line, properly formatted)
echo "3. German IBAN Test:"
curl -X POST http://localhost:8000/calculate-iban -H "Content-Type: application/json" -d '{"country_code": "DE", "bank_code": "37040044", "account_number": "532013000"}'
echo -e "\n"

# 4. UK IBAN (single line)
echo "4. UK IBAN Test:"
curl -X POST http://localhost:8000/calculate-iban -H "Content-Type: application/json" -d '{"country_code": "GB", "bank_code": "200000", "account_number": "55779911"}'
echo -e "\n"

# 5. French IBAN (single line)
echo "5. French IBAN Test:"
curl -X POST http://localhost:8000/calculate-iban -H "Content-Type: application/json" -d '{"country_code": "FR", "bank_code": "20041", "account_number": "01005027637"}'
echo -e "\n"

echo "✅ Testing completed!"