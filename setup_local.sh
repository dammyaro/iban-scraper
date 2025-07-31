#!/bin/bash
# Setup script for local Playwright testing

echo "🚀 Setting up Playwright for local testing..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Install system dependencies (if needed)
echo "🔧 Installing system dependencies..."
playwright install-deps chromium

echo "✅ Setup complete!"
echo ""
echo "🧪 Run tests:"
echo "  python test_playwright_local.py"
echo ""
echo "🚀 Start API server:"
echo "  python main.py"
echo ""
echo "🔗 Test API:"
echo "  curl -X POST http://localhost:8000/calculate-iban -H 'Content-Type: application/json' -d '{\"country_code\": \"DE\", \"bank_code\": \"37040044\", \"account_number\": \"532013000\"}'"