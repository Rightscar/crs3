#!/bin/bash

# Test Execution Script for Character Interaction Engine
echo "🧪 Character Interaction Engine - Test Suite Execution"
echo "====================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Create test results directory
mkdir -p test_results

# Run unit tests
echo ""
echo -e "${GREEN}1. Running Unit Tests...${NC}"
echo "------------------------"
pytest tests/test_personality_service.py tests/test_relationship_service.py -v --tb=short -m "not integration" > test_results/unit_tests.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Unit tests passed!${NC}"
    grep -E "(passed|failed|error)" test_results/unit_tests.log | tail -5
else
    echo -e "${RED}❌ Unit tests failed!${NC}"
    tail -10 test_results/unit_tests.log
fi

# Run integration tests
echo ""
echo -e "${GREEN}2. Running Integration Tests...${NC}"
echo "-------------------------------"
pytest tests/test_character_interaction_engine.py -v --tb=short > test_results/integration_tests.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests passed!${NC}"
    grep -E "(passed|failed|error)" test_results/integration_tests.log | tail -5
else
    echo -e "${RED}❌ Integration tests failed!${NC}"
    tail -10 test_results/integration_tests.log
fi

# Run WebSocket tests
echo ""
echo -e "${GREEN}3. Running WebSocket Tests...${NC}"
echo "-----------------------------"
pytest tests/test_websocket.py -v --tb=short > test_results/websocket_tests.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ WebSocket tests passed!${NC}"
    grep -E "(passed|failed|error)" test_results/websocket_tests.log | tail -5
else
    echo -e "${RED}❌ WebSocket tests failed!${NC}"
    tail -10 test_results/websocket_tests.log
fi

# Run all tests with coverage
echo ""
echo -e "${GREEN}4. Running Full Test Suite with Coverage...${NC}"
echo "-------------------------------------------"
pytest --cov=services --cov=api --cov-report=term-missing --cov-report=html --cov-report=json -v > test_results/coverage_report.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Coverage Report:"
    echo "----------------"
    tail -20 test_results/coverage_report.log | grep -E "(TOTAL|services/|api/)" || tail -20 test_results/coverage_report.log
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    tail -20 test_results/coverage_report.log
fi

# Generate test summary
echo ""
echo -e "${GREEN}5. Test Summary${NC}"
echo "---------------"
python3 << EOF
import json
import os

# Read coverage data if exists
coverage_file = 'coverage.json'
if os.path.exists(coverage_file):
    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        print(f"Total Coverage: {total_coverage:.1f}%")

# Count test files
test_files = [f for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')]
print(f"Test Files: {len(test_files)}")

# Parse test results
for log_file in ['unit_tests.log', 'integration_tests.log', 'websocket_tests.log']:
    path = f'test_results/{log_file}'
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
            if 'passed' in content:
                # Extract test count
                import re
                match = re.search(r'(\d+) passed', content)
                if match:
                    print(f"{log_file.replace('_', ' ').replace('.log', '').title()}: {match.group(1)} passed")
EOF

echo ""
echo -e "${GREEN}📊 Performance Test Command:${NC}"
echo "locust -f tests/test_performance.py --host=http://localhost:8000 --users 10 --spawn-rate 1 --run-time 30s --headless"

echo ""
echo -e "${GREEN}📁 Test Results Location:${NC}"
echo "- Coverage HTML Report: htmlcov/index.html"
echo "- Test Logs: test_results/"
echo ""

# Deactivate virtual environment
deactivate

echo "✨ Test execution complete!"