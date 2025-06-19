# r4r Test Suite

Comprehensive test coverage for all r4r commands and functionality.

## Running Tests

### All Tests
```bash
make test
# or
python run_tests.py
```

### Unit Tests Only
```bash
make test-unit
# or
python run_tests.py --unit
```

### Integration Tests Only
```bash
make test-integration
# or
python run_tests.py --integration
```

### With Coverage Report
```bash
make test-coverage
# or
python run_tests.py --coverage
```

### Verbose Output
```bash
make test-verbose
# or
python run_tests.py -v
```

### Specific Test File
```bash
python run_tests.py tests/test_commands.py
```

## Test Structure

- `test_config.py` - Tests for configuration, HTTP client, and utilities
- `test_api.py` - Tests for Render API client and domain entities
- `test_display.py` - Tests for UI components and formatting
- `test_commands.py` - Tests for CLI command handlers
- `test_integration.py` - Integration tests for complete workflows

## Coverage

Each command is tested with:
- ✅ Success cases
- ❌ Error handling
- 🔄 Edge cases
- 🔗 Integration flows

## Writing Tests

Tests use pytest with mocking for external dependencies:

```python
def test_example(self, cli):
    # Arrange
    cli._find_service = Mock(return_value=sample_service)
    
    # Act
    cli.deploy_service("test-app")
    
    # Assert
    cli.render_service.api.trigger_deploy.assert_called_with("srv-123", False)
```