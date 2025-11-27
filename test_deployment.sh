#!/bin/bash

# Script to test the deployed quiz solver

# Configuration
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
EMAIL="${EMAIL:-23f3004233@ds.study.iitm.ac.in}"
SECRET="${SECRET:-your_secret_here}"

echo "Testing LLM Quiz Solver"
echo "Server: $SERVER_URL"
echo "Email: $EMAIL"
echo "========================"

# Test health endpoint
echo -e "\n1. Testing /health endpoint..."
curl -s "$SERVER_URL/health" | python -m json.tool
echo ""

# Test root endpoint
echo -e "\n2. Testing / endpoint..."
curl -s "$SERVER_URL/" | python -m json.tool
echo ""

# Test quiz endpoint with demo
echo -e "\n3. Testing /quiz endpoint with demo..."
curl -X POST "$SERVER_URL/quiz" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"secret\": \"$SECRET\",
    \"url\": \"https://tds-llm-analysis.s-anand.net/demo\"
  }" | python -m json.tool
echo ""

# Test with invalid secret
echo -e "\n4. Testing /quiz endpoint with invalid secret..."
curl -X POST "$SERVER_URL/quiz" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"secret\": \"wrong_secret\",
    \"url\": \"https://tds-llm-analysis.s-anand.net/demo\"
  }"
echo -e "\n"

echo "========================"
echo "Testing complete!"