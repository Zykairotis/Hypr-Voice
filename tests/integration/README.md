# Integration Tests

This directory contains integration tests that validate the interaction between different components of the Hypr-Voice system.

## 📁 Test Files

- **[test_ws.py](test_ws.py)** - WebSocket integration test for real-time communication testing

## 🧪 Running Tests

```bash
# Run individual test
cd tests/integration
python test_ws.py

# Run all tests (from project root)
python -m pytest tests/integration/
```

## 📅 Organization Date

**Organized on:** 2025-11-25
**Purpose:** Move test files from root directory to proper test structure for better maintainability.