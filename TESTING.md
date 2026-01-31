# Testing Guide

## Overview

The Python Game Builder includes a comprehensive test suite covering:
- Database models
- API endpoints
- Version control functionality
- Admin utilities

## Quick Start

### Install Test Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Simple run
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Or use the test runner script
./run_tests.sh
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures and configuration
├── test_models.py        # Database model tests
├── test_api.py           # API endpoint tests
└── test_admin.py         # Admin utility tests
```

## Test Coverage

### Models (test_models.py)
- ✅ User creation
- ✅ Username uniqueness
- ✅ Game creation
- ✅ CodeVersion creation
- ✅ Model relationships

### API Endpoints (test_api.py)

**User Management:**
- ✅ Get all users
- ✅ Create new user
- ✅ Validate username length
- ✅ Prevent duplicate usernames

**Game Management:**
- ✅ Get all games

**Code Version Control:**
- ✅ Load template code
- ✅ Save new code
- ✅ Detect unchanged code
- ✅ Load saved code
- ✅ Get version history
- ✅ Pagination of history
- ✅ Get specific version
- ✅ Restore old version
- ✅ Generate diff between versions

**Routes:**
- ✅ Index page loads
- ✅ Game page loads
- ✅ 404 for invalid game

### Admin Utilities (test_admin.py)
- ✅ Database statistics
- ✅ User listing
- ✅ Backup information

## Running Specific Tests

```bash
# Run specific test file
pytest tests/test_api.py -v

# Run specific test class
pytest tests/test_api.py::TestUserAPI -v

# Run specific test
pytest tests/test_api.py::TestUserAPI::test_create_user -v

# Run tests matching pattern
pytest tests/ -k "user" -v
```

## Test Fixtures

### Available Fixtures

- `app` - Configured Flask application with test database
- `client` - Test client for HTTP requests
- `test_user` - Pre-created test user
- `test_game` - Pre-created test game
- `test_code_version` - Pre-created code version

### Using Fixtures

```python
def test_example(client, test_user, test_game):
    """Example test using fixtures"""
    response = client.post('/api/code/save',
                           json={
                               'user_id': test_user,
                               'game_id': test_game,
                               'code': 'print("test")'
                           })
    assert response.status_code == 201
```

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
def test_new_feature(client, test_user):
    """Test description"""
    # Arrange
    data = {'user_id': test_user, 'some_field': 'value'}

    # Act
    response = client.post('/api/endpoint',
                           json=data,
                           content_type='application/json')

    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'expected_field' in data
```

## Known Issues

### SQLAlchemy State Management

Currently, the test fixtures have an issue with SQLAlchemy session state management between tests. This is a known issue that occurs when:
- Multiple tests try to create database objects with unique constraints
- The same Flask app instance is reused across tests

**Workaround**: Each test should use a fresh database, which the fixtures attempt to provide, but SQLAlchemy's scoped session can maintain state.

**Future Fix**: Implement proper session cleanup or use a test database factory pattern.

### Test Isolation

Some tests may fail when run together but pass individually due to:
- Shared database state
- Session cleanup issues
- Fixture scope problems

**Current Status**: Test framework is in place and most tests are logically correct, but need fixture refinement for full isolation.

## Code Coverage

Target coverage: 80%+

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest tests/ --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v2
```

## Manual Testing

For features not covered by automated tests:

### 1. **Full User Flow**
```
1. Start app: python app.py
2. Create user
3. Select game
4. Edit code
5. Save checkpoint
6. View history
7. Restore version
```

### 2. **Version Control**
```
1. Create 10+ saves
2. Check pagination works
3. View diffs
4. Restore old version
5. Check code restored correctly
```

### 3. **Multi-User**
```
1. Create 2 users
2. Each edits different games
3. Verify histories are separate
4. Switch users
5. Verify code persistence
```

## Debugging Tests

### Print Debug Info

```bash
# Show print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ -v -l

# Drop into debugger on failure
pytest tests/ -v --pdb
```

### Check Database State

```python
# In test
def test_example(app, test_user):
    with app.app_context():
        from app import db, User
        user = User.query.get(test_user)
        print(f"User: {user.username}")
```

## Test Data

Tests use temporary SQLite databases that are:
- Created fresh for each test
- Isolated from production
- Automatically cleaned up
- Located in `/tmp/` on Unix systems

## Performance Testing

For load testing:

```bash
# Install locust
pip install locust

# Create locustfile.py with load tests
# Run load test
locust -f locustfile.py
```

## Best Practices

### ✅ Do
- Write tests for all new features
- Test error cases
- Use descriptive test names
- Keep tests isolated
- Clean up test data

### ❌ Don't
- Test implementation details
- Write flaky tests
- Use production database
- Hard-code test data
- Skip cleanup

## Future Improvements

- [ ] Fix SQLAlchemy session state issues
- [ ] Add integration tests for Pyodide
- [ ] Add UI tests with Selenium
- [ ] Add performance benchmarks
- [ ] Add API load tests
- [ ] Improve test isolation
- [ ] Add mutation testing
- [ ] Increase coverage to 90%+

## Getting Help

If tests fail:
1. Check error message
2. Run single test: `pytest tests/test_file.py::test_name -v`
3. Check database state
4. Verify fixtures are working
5. Check for unique constraint violations

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/latest/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/latest/core/connections.html#engine-disposal)

---

**Note**: Tests are currently in development. The framework is complete but needs fixture refinement for full test isolation. The app functionality is fully working - tests document expected behavior.
