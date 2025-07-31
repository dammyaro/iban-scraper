#!/usr/bin/env python3
"""
Comprehensive IBAN checker tests for multiple countries and scenarios
"""
import asyncio
import json
import time
from playwright.async_api import async_playwright
import requests

# Test cases for different countries
TEST_CASES = [
    # German IBANs
    {
        "name": "German IBAN (Deutsche Bank)",
        "country_code": "DE",
        "bank_code": "37040044",
        "account_number": "532013000",
        "expected_iban": "DE89370400440532013000"
    },
    {
        "name": "German IBAN (Commerzbank)",
        "country_code": "DE", 
        "bank_code": "20040000",
        "account_number": "628901300"
    },
    
    # UK IBANs
    {
        "name": "UK IBAN (Barclays)",
        "country_code": "GB",
        "bank_code": "200000",
        "account_number": "55779911",
        "expected_iban": "GB60BARC20000055779911"
    },
    {
        "name": "UK IBAN (HSBC)",
        "country_code": "GB",
        "bank_code": "400500",
        "account_number": "12345678"
    },
    
    # French IBANs
    {
        "name": "French IBAN (BNP Paribas)",
        "country_code": "FR",
        "bank_code": "20041",
        "account_number": "01005027637"
    },
    {
        "name": "French IBAN (Credit Agricole)",
        "country_code": "FR",
        "bank_code": "14706",
        "account_number": "0001530101"
    },
    
    # Italian IBANs
    {
        "name": "Italian IBAN (UniCredit)",
        "country_code": "IT",
        "bank_code": "05428",
        "account_number": "11101000000012345"
    },
    
    # Spanish IBANs
    {
        "name": "Spanish IBAN (Santander)",
        "country_code": "ES",
        "bank_code": "0049",
        "account_number": "015000001234567891"
    },
    
    # Netherlands IBANs
    {
        "name": "Netherlands IBAN (ING)",
        "country_code": "NL",
        "bank_code": "ABNA",
        "account_number": "0417164300"
    },
    
    # Austrian IBANs
    {
        "name": "Austrian IBAN",
        "country_code": "AT",
        "bank_code": "19043",
        "account_number": "00234573201"
    },
    
    # Belgian IBANs
    {
        "name": "Belgian IBAN",
        "country_code": "BE",
        "bank_code": "539",
        "account_number": "0075470"
    }
]

# Error test cases
ERROR_TEST_CASES = [
    {
        "name": "Invalid Country Code",
        "country_code": "XX",
        "bank_code": "12345",
        "account_number": "67890",
        "should_fail": True
    },
    {
        "name": "Empty Bank Code",
        "country_code": "DE",
        "bank_code": "",
        "account_number": "532013000",
        "should_fail": True
    },
    {
        "name": "Empty Account Number",
        "country_code": "DE",
        "bank_code": "37040044",
        "account_number": "",
        "should_fail": True
    },
    {
        "name": "Invalid Country Code Length",
        "country_code": "DEU",
        "bank_code": "37040044",
        "account_number": "532013000",
        "should_fail": True
    }
]

async def test_iban_with_playwright(test_case):
    """Test IBAN calculation using Playwright directly"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            
            # Navigate to IBAN calculator
            await page.goto("https://www.iban.com/calculate-iban", timeout=30000)
            
            # Fill form
            await page.select_option('select[name="country"]', test_case["country_code"])
            await page.wait_for_timeout(1000)
            
            await page.fill('input[name="bankcode"]', test_case["bank_code"])
            await page.fill('input[name="account"]', test_case["account_number"])
            
            # Submit form
            await page.click('input[type="submit"]')
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Extract IBAN
            page_content = await page.content()
            
            # Look for IBAN in hidden input
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(page_content, 'html.parser')
            iban_inputs = soup.find_all('input', {'name': 'iban'})
            
            for iban_input in iban_inputs:
                value = iban_input.get('value', '').strip()
                if value and len(value) >= 15 and re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', value):
                    await browser.close()
                    return {
                        "success": True,
                        "iban": value,
                        "method": "playwright_direct"
                    }
            
            await browser.close()
            return {
                "success": False,
                "error": "Could not extract IBAN",
                "method": "playwright_direct"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "playwright_direct"
        }

def test_iban_with_api(test_case, api_url="http://localhost:8000"):
    """Test IBAN calculation using our API"""
    try:
        response = requests.post(
            f"{api_url}/calculate-iban",
            json={
                "country_code": test_case["country_code"],
                "bank_code": test_case["bank_code"],
                "account_number": test_case["account_number"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "iban": data.get("iban"),
                "method": data.get("method_used", "api"),
                "response": data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "method": "api"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "api"
        }

async def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("🧪 Starting Comprehensive IBAN Tests")
    print("=" * 60)
    
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    # Test valid IBANs
    print("\n📋 Testing Valid IBAN Cases:")
    print("-" * 40)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: {test_case['country_code']}, {test_case['bank_code']}, {test_case['account_number']}")
        
        results["total_tests"] += 1
        
        # Test with API
        start_time = time.time()
        api_result = test_iban_with_api(test_case)
        api_time = time.time() - start_time
        
        if api_result["success"]:
            iban = api_result["iban"]
            print(f"   ✅ API Result: {iban} ({api_time:.2f}s)")
            
            # Validate expected IBAN if provided
            if "expected_iban" in test_case:
                if iban == test_case["expected_iban"]:
                    print(f"   ✅ Expected IBAN matches!")
                    results["passed"] += 1
                else:
                    print(f"   ❌ Expected: {test_case['expected_iban']}, Got: {iban}")
                    results["failed"] += 1
            else:
                print(f"   ✅ IBAN generated successfully")
                results["passed"] += 1
                
        else:
            print(f"   ❌ API Failed: {api_result['error']}")
            results["failed"] += 1
        
        results["details"].append({
            "test_case": test_case["name"],
            "api_result": api_result,
            "api_time": api_time
        })
    
    # Test error cases
    print("\n\n🚨 Testing Error Cases:")
    print("-" * 40)
    
    for i, test_case in enumerate(ERROR_TEST_CASES, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: {test_case['country_code']}, {test_case['bank_code']}, {test_case['account_number']}")
        
        results["total_tests"] += 1
        
        api_result = test_iban_with_api(test_case)
        
        if test_case.get("should_fail", False):
            if not api_result["success"]:
                print(f"   ✅ Correctly failed: {api_result['error']}")
                results["passed"] += 1
            else:
                print(f"   ❌ Should have failed but got: {api_result['iban']}")
                results["failed"] += 1
        else:
            if api_result["success"]:
                print(f"   ✅ Succeeded: {api_result['iban']}")
                results["passed"] += 1
            else:
                print(f"   ❌ Failed: {api_result['error']}")
                results["failed"] += 1
    
    # Performance test
    print("\n\n⚡ Performance Test:")
    print("-" * 40)
    
    performance_test = TEST_CASES[0]  # Use German IBAN
    times = []
    
    for i in range(5):
        start_time = time.time()
        result = test_iban_with_api(performance_test)
        end_time = time.time()
        
        if result["success"]:
            times.append(end_time - start_time)
            print(f"   Run {i+1}: {end_time - start_time:.2f}s ✅")
        else:
            print(f"   Run {i+1}: Failed ❌")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"\n   📊 Performance Summary:")
        print(f"      Average: {avg_time:.2f}s")
        print(f"      Min: {min_time:.2f}s")
        print(f"      Max: {max_time:.2f}s")
    
    # Final report
    print("\n\n📊 Test Summary:")
    print("=" * 60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed']/results['total_tests']*100):.1f}%")
    
    if results['failed'] == 0:
        print("\n🎉 All tests passed! Ready for production deployment.")
    else:
        print(f"\n⚠️  {results['failed']} tests failed. Review before deployment.")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())