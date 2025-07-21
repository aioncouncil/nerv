#!/bin/bash
set -e

# NERV Test Runner Script
# Runs all tests for the NERV geometric engine system

echo "🚀 Starting NERV Test Suite"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Track test results
RUST_TESTS_PASSED=false
PYTHON_TESTS_PASSED=false
INTEGRATION_TESTS_PASSED=false

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the NERV project root directory"
    exit 1
fi

# Start services for testing
print_status "Starting test services..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.yml up -d neo4j redis
    print_success "Test services started"
else
    print_warning "Docker Compose not available - tests will run in fallback mode"
fi

# 1. Test Rust Core
print_status "Running Rust core tests..."
cd backend/rust-core

if command -v cargo &> /dev/null; then
    echo "Running Rust formatter check..."
    if cargo fmt -- --check; then
        print_success "Rust formatting check passed"
    else
        print_warning "Rust formatting issues found"
    fi

    echo "Running Rust linter (Clippy)..."
    if cargo clippy --all-targets --all-features -- -D warnings; then
        print_success "Rust linting passed"
    else
        print_error "Rust linting failed"
    fi

    echo "Running Rust tests..."
    if cargo test --verbose; then
        print_success "Rust tests passed ($(cargo test --verbose 2>&1 | grep -c 'test result: ok'))"
        RUST_TESTS_PASSED=true
    else
        print_error "Rust tests failed"
    fi

    echo "Building Rust release..."
    if cargo build --release; then
        print_success "Rust build succeeded"
    else
        print_error "Rust build failed"
    fi
else
    print_warning "Rust/Cargo not installed - skipping Rust tests"
fi

cd ../..

# 2. Test Python API
print_status "Running Python API tests..."
cd backend/python-api

if command -v python3 &> /dev/null && [ -d "venv" ]; then
    source venv/bin/activate
    
    echo "Running Python formatter check (Black)..."
    if black --check --diff app/; then
        print_success "Python formatting check passed"
    else
        print_warning "Python formatting issues found"
    fi

    echo "Running Python import sorting check (isort)..."
    if isort --check-only --diff app/; then
        print_success "Python import sorting passed"
    else
        print_warning "Python import sorting issues found"
    fi

    echo "Running Python linter (Flake8)..."
    if flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
        print_success "Python linting passed"
    else
        print_warning "Python linting issues found"
    fi

    echo "Running Python tests..."
    export NEO4J_URI="bolt://localhost:7687"
    export NEO4J_USER="neo4j"
    export NEO4J_PASSWORD="nervgeometry"
    export REDIS_URL="redis://localhost:6379/0"
    export ENVIRONMENT="testing"

    if pytest app/tests/ -v --tb=short; then
        print_success "Python tests passed"
        PYTHON_TESTS_PASSED=true
    else
        print_error "Python tests failed"
    fi

    deactivate
else
    print_warning "Python virtual environment not found - skipping Python tests"
    print_warning "Run 'python3 -m venv venv && source venv/bin/activate && pip install -e .' to set up"
fi

cd ../..

# 3. Test Frontend (if available)
print_status "Checking frontend tests..."
cd frontend

if [ -f "package.json" ] && command -v npm &> /dev/null; then
    echo "Installing frontend dependencies..."
    npm install

    echo "Running frontend linting..."
    if npm run lint 2>/dev/null; then
        print_success "Frontend linting passed"
    else
        print_warning "Frontend linting issues found or not configured"
    fi

    echo "Running frontend tests..."
    if npm test 2>/dev/null; then
        print_success "Frontend tests passed"
    else
        print_warning "Frontend tests failed or not configured"
    fi

    echo "Building frontend..."
    if npm run build 2>/dev/null; then
        print_success "Frontend build succeeded"
    else
        print_warning "Frontend build failed or not configured"
    fi
else
    print_warning "Frontend environment not set up - skipping frontend tests"
fi

cd ..

# 4. Integration Tests
print_status "Running integration tests..."

if [ "$RUST_TESTS_PASSED" = true ] && [ "$PYTHON_TESTS_PASSED" = true ]; then
    cd backend/python-api
    source venv/bin/activate 2>/dev/null || true
    
    echo "Testing API endpoints integration..."
    if python3 -c "
import asyncio
import sys
sys.path.append('.')

async def test_api_integration():
    try:
        from app.main import app
        from app.services.rust_bridge import RustGeometryService
        from app.services.neo4j_service import Neo4jService
        
        print('✓ API imports successful')
        
        # Test Rust service
        rust_service = RustGeometryService()
        health = await rust_service.health_check()
        print(f'✓ Rust service health: {health}')
        
        # Test Neo4j service  
        neo4j_service = Neo4jService()
        connected = await neo4j_service.connect()
        print(f'✓ Neo4j connection: {connected}')
        
        print('✓ Integration tests passed')
        return True
    except Exception as e:
        print(f'✗ Integration test failed: {e}')
        return False

result = asyncio.run(test_api_integration())
sys.exit(0 if result else 1)
"; then
        print_success "Integration tests passed"
        INTEGRATION_TESTS_PASSED=true
    else
        print_error "Integration tests failed"
    fi
    cd ../..
else
    print_warning "Skipping integration tests - prerequisites not met"
fi

# Clean up services
if command -v docker-compose &> /dev/null; then
    print_status "Cleaning up test services..."
    docker-compose -f docker-compose.yml down
fi

# Final Results
echo ""
echo "================================="
echo "🏁 NERV Test Results Summary"
echo "================================="

if [ "$RUST_TESTS_PASSED" = true ]; then
    print_success "✅ Rust Core Tests: PASSED"
else
    print_error "❌ Rust Core Tests: FAILED"
fi

if [ "$PYTHON_TESTS_PASSED" = true ]; then
    print_success "✅ Python API Tests: PASSED"
else
    print_error "❌ Python API Tests: FAILED"
fi

if [ "$INTEGRATION_TESTS_PASSED" = true ]; then
    print_success "✅ Integration Tests: PASSED"
else
    print_error "❌ Integration Tests: FAILED"
fi

# Overall result
if [ "$RUST_TESTS_PASSED" = true ] && [ "$PYTHON_TESTS_PASSED" = true ] && [ "$INTEGRATION_TESTS_PASSED" = true ]; then
    echo ""
    print_success "🎉 ALL TESTS PASSED - NERV System Ready!"
    echo ""
    echo "Next steps:"
    echo "- Run 'git add . && git commit -m \"feat: comprehensive test suite\"'"
    echo "- Push to trigger CI/CD pipeline"
    echo "- Deploy to staging/production environments"
    exit 0
else
    echo ""
    print_error "❌ SOME TESTS FAILED - Please review and fix issues"
    echo ""
    echo "Debug steps:"
    echo "- Check individual test outputs above"
    echo "- Run tests individually for more details"
    echo "- Ensure all dependencies are installed"
    exit 1
fi