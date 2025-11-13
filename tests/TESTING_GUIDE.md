# Testing Guide for Reasoning Library

This guide explains how to use the standardized testing framework, markers, and templates in the Reasoning Library test suite.

## Test Markers

The test suite uses comprehensive markers to categorize different types of tests:

### Primary Markers

- **`@pytest.mark.security`** - Security-focused tests (vulnerability testing, input validation, DoS protection)
- **`@pytest.mark.performance`** - Performance-focused tests (execution time, memory usage, scalability)
- **`@pytest.mark.integration`** - Integration tests (cross-module interaction, external dependencies)
- **`@pytest.mark.unit`** - Unit tests (isolated functionality testing)
- **`@pytest.mark.slow`** - Slow-running tests (deselect with `-m "not slow"`)

### Specialized Security Markers

- **`@pytest.mark.redos`** - ReDoS (Regular Expression DoS) vulnerability testing
- **`@pytest.mark.dos`** - Denial of Service resistance testing
- **`@pytest.mark.injection`** - Injection attack prevention testing
- **`@pytest.mark.timing`** - Timing attack prevention testing
- **`@pytest.mark.memory`** - Memory safety and leak detection
- **`@pytest.mark.concurrency`** - Thread safety and concurrent access testing

## Running Tests by Category

### Run All Tests
```bash
uv run pytest
```

### Run Only Security Tests
```bash
uv run pytest -m security
```

### Run Only Performance Tests
```bash
uv run pytest -m performance
```

### Run Only Integration Tests
```bash
uv run pytest -m integration
```

### Run Only Unit Tests
```bash
uv run pytest -m unit
```

### Run Fast Tests (Exclude Slow Tests)
```bash
uv run pytest -m "not slow"
```

### Run Specific Security Sub-categories
```bash
# ReDoS tests only
uv run pytest -m redos

# DoS resistance tests only
uv run pytest -m dos

# Memory safety tests only
uv run pytest -m memory
```

## Coverage Reporting

### Generate Coverage Report
```bash
uv run pytest --cov=src/reasoning_library --cov-report=term-missing
```

### Generate HTML Coverage Report
```bash
uv run pytest --cov=src/reasoning_library --cov-report=html
open htmlcov/index.html
```

### Coverage with Minimum Threshold (Currently set to 85%)
```bash
uv run pytest --cov=src/reasoning_library --cov-fail-under=85
```

## Test Templates

### Security Testing Template

Use the `SecurityTestBase` class for standardized security testing:

```python
from tests._templates.security_test_base import SecurityTestBase

class TestMyFunctionSecurity(SecurityTestBase):

    @pytest.mark.security
    def test_timing_attack_protection(self):
        # Test that execution time is consistent
        self.test_timing_attack_protection(
            my_function,
            ["input1", "input2", "malicious_input"],
            max_time=0.1
        )

    @pytest.mark.security
    def test_redos_vulnerability(self):
        # Test for ReDoS vulnerabilities
        self.test_redos_vulnerability(
            my_function_with_regex,
            [".*.*.*", "(a+)+b", "(a|a)+b"]
        )

    @pytest.mark.security
    def test_dos_attack_resistance(self):
        # Test resistance to DoS attacks
        self.test_dos_attack_resistance(
            my_function,
            ["x" * 10000, ["large" * 1000], {"big": "data"}]
        )
```

### Performance Testing Template

Use the `PerformanceTestTemplate` class for standardized performance testing:

```python
from tests._templates.performance_test_template import PerformanceTestTemplate

class TestMyFunctionPerformance(PerformanceTestTemplate):

    @pytest.mark.performance
    def test_execution_time_scalability(self):
        # Test performance scaling with input size
        self.test_execution_time_scalability(
            my_function,
            input_sizes=[10, 100, 1000],
            input_generator=lambda n: list(range(n)),
            max_complexity="linear"
        )

    @pytest.mark.performance
    def test_memory_usage_efficiency(self):
        # Test memory usage efficiency
        self.test_memory_usage_efficiency(
            my_function,
            input_sizes=[10, 100, 1000],
            input_generator=lambda n: list(range(n))
        )
```

## Automatic Test Classification

Tests are automatically classified based on their names and file names:

### Security Tests (Auto-classified)
- Files containing: `security`, `vulnerability`, `attack`, `malicious`, `injection`
- Test names containing: `dos`, `redos`, `regex`, `timing`, `race`, `concurrent`, `thread`
- Example: `test_redos_vulnerability.py` → automatically marked as `security` and `redos`

### Performance Tests (Auto-classified)
- Files containing: `performance`, `perf`, `timing`, `speed`, `memory`, `scalability`
- Test names containing: `benchmark`, `load`, `stress`, `efficiency`
- Example: `test_memory_exhaustion.py` → automatically marked as `performance` and `memory`

### Integration Tests (Auto-classified)
- Files containing: `integration`, `end_to_end`, `e2e`, `workflow`, `chain`
- Test names containing: `integration`, `workflow`, `chain`
- Example: `test_chain_of_thought.py` → automatically marked as `integration`

## Writing New Tests

### 1. Unit Test Example
```python
import pytest
from reasoning_library import my_function

@pytest.mark.unit
def test_my_function_basic():
    """Test basic functionality of my_function."""
    result = my_function("test_input")
    assert result is not None
    assert isinstance(result, expected_type)
```

### 2. Security Test Example
```python
import pytest
from tests._templates.security_test_base import SecurityTestBase

class TestMyFunctionSecurity(SecurityTestBase):

    @pytest.mark.security
    @pytest.mark.injection
    def test_injection_attack_prevention(self):
        """Test that my_function prevents injection attacks."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "$(rm -rf /)",
            "../../etc/passwd"
        ]

        self.test_rejection_of_malicious_inputs(
            my_function,
            malicious_inputs,
            expected_exception=ValidationError
        )
```

### 3. Performance Test Example
```python
import pytest
from tests._templates.performance_test_template import PerformanceTestTemplate

class TestMyFunctionPerformance(PerformanceTestTemplate):

    @pytest.mark.performance
    def test_scalability(self):
        """Test that my_function scales linearly with input size."""
        self.test_execution_time_scalability(
            my_function,
            input_sizes=[100, 1000, 10000],
            input_generator=lambda n: list(range(n)),
            max_complexity="linear"
        )
```

## Test Best Practices

### 1. Use Appropriate Markers
- Always mark tests with appropriate `@pytest.mark.*` decorators
- Use specific security markers for vulnerability tests
- Use `@pytest.mark.slow` for tests that take more than 1 second

### 2. Follow Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Use descriptive names: `test_redos_vulnerability_in_keyword_extraction`

### 3. Use Templates
- Inherit from `SecurityTestBase` for security tests
- Inherit from `PerformanceTestTemplate` for performance tests
- Use provided fixtures for clean state management

### 4. Test Coverage
- Aim for high coverage but focus on critical paths
- Test both happy paths and error conditions
- Include edge cases and boundary conditions

### 5. Security Testing
- Test with malicious inputs
- Verify input sanitization
- Test for timing attacks and DoS resistance
- Test concurrent access and thread safety

## Continuous Integration

The test suite is designed to run efficiently in CI environments:

```bash
# Quick CI test run (no slow tests, no coverage)
uv run pytest -m "not slow" --tb=short

# Full CI test run with coverage
uv run pytest --cov=src/reasoning_library --cov-report=xml --cov-fail-under=85
```

## Troubleshooting

### Test Collection Errors
```bash
# Verify dependencies are installed
uv sync --dev

# Check test collection
uv run pytest --collect-only
```

### Coverage Issues
```bash
# Check what's not covered
uv run pytest --cov=src/reasoning_library --cov-report=term-missing

# Generate detailed HTML report
uv run pytest --cov=src/reasoning_library --cov-report=html
```

### Slow Tests
```bash
# Find slow tests
uv run pytest --durations=10

# Run only fast tests
uv run pytest -m "not slow"
```