# 🚀 IBAN Calculator - Single Service Deployment

## 📋 **Service Configuration**

### **Service Name**: `iban-wise-calculator`
- **Clean, single-service deployment**
- **Latest Wise integration with bank name extraction**
- **Version 3.1.0 - Production Ready**

## ✅ **Features**

- ✅ **IBAN Calculation**: Accurate UK IBAN generation
- ✅ **Bank Name Extraction**: Full bank names (e.g., "BARCLAYS BANK PLC")
- ✅ **Wise Integration**: Reliable, no query limits
- ✅ **Playwright Automation**: Modern browser automation
- ✅ **Cost Optimized**: Efficient resource usage

## 🔧 **Technical Specs**

- **Runtime**: Python 3.11
- **Framework**: FastAPI + Playwright
- **Instance**: basic-s (1 vCPU, 512MB RAM)
- **Auto-scaling**: 1-2 instances
- **Health Check**: 120s initial delay for browser setup

## 📊 **API Response Example**

```json
{
  "iban": "GB60BARC20000055779911",
  "country": "GB",
  "bank_code": "200000",
  "account_number": "55779911", 
  "check_digits": "60",
  "is_valid": true,
  "bank_name": "BARCLAYS BANK PLC",
  "message": "IBAN calculated successfully",
  "method_used": "wise"
}
```

## 🚀 **Deployment Steps**

1. **Delete old services** (iban-calculator-scraper, ibanscraper2)
2. **Deploy new service** using this configuration
3. **Test the API** with provided curl commands
4. **Monitor logs** for successful Playwright browser installation

## 🧪 **Test Commands**

```bash
# Health Check
curl https://your-new-url/health

# IBAN Calculation
curl -X POST https://your-new-url/calculate-iban \
  -H "Content-Type: application/json" \
  -d '{"country_code": "GB", "bank_code": "200000", "account_number": "55779911"}'
```

## 🎯 **Expected Results**

- **Response Time**: 5-8 seconds
- **Success Rate**: 95%+ for UK banks
- **Memory Usage**: ~300-400MB per request
- **Bank Names**: Extracted for all major UK banks

## 🔗 **Endpoints**

- `/` - API information
- `/health` - Health check
- `/calculate-iban` - IBAN calculation
- `/docs` - Interactive API documentation
- `/redoc` - Alternative API documentation