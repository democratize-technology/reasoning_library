# Error Handling Guidelines

This document outlines the standardized error handling patterns for the reasoning library.

## Overview

The reasoning library uses a hierarchical exception system to provide clear, specific error categorization while maintaining backward compatibility. All custom exceptions inherit from `ReasoningError`, which provides consistent error formatting and debugging capabilities.

## Exception Hierarchy

```
ReasoningError (base class)
├── ValidationError
├── ComputationError
│   └── PatternDetectionError
├── TimeoutError
├── CacheError
├── SecurityError
├── ImportWarning
├── ReasoningChainError
└── ToolSpecificationError
```

## Exception Types and Usage

### ValidationError
**Use Case**: Input validation failures
**Examples**: Invalid parameter types, out-of-range values, malformed input
```python
if not isinstance(value, (int, float)):
    raise ValidationError(f"Value '{value}' must be numeric, got {type(value).__name__}")
```

### ComputationError
**Use Case**: Mathematical or logical computation failures
**Examples**: Division by zero, overflow, numerical instability

### PatternDetectionError
**Use Case**: Pattern recognition algorithm failures
**Examples**: Invalid sequences, computational limits exceeded

### TimeoutError
**Use Case**: Operations exceeding time limits
**Examples**: Long-running computations, external service calls

### CacheError
**Use Case**: Caching operation failures
**Examples**: Cache corruption, memory limits, serialization errors

### SecurityError
**Use Case**: Security constraint violations
**Examples**: Input injection attempts, DoS attack detection

### ImportWarning
**Use Case**: Optional dependency import failures (non-fatal)
**Examples**: Optional libraries not available, graceful degradation

### ReasoningChainError
**Use Case**: Reasoning chain operation failures
**Examples**: Invalid chain states, step execution failures

### ToolSpecificationError
**Use Case**: Tool specification creation/validation failures
**Examples**: Invalid metadata, malformed specifications

## Error Handling Principles

### 1. Use Specific Exceptions
Avoid broad `except Exception` clauses. Use specific exception types that clearly indicate the error category.

**Before:**
```python
try:
    result = process_input(data)
except Exception:
    handle_error()
```

**After:**
```python
try:
    result = process_input(data)
except (ValueError, TypeError) as e:
    handle_validation_error(e)
except ComputationError as e:
    handle_computation_error(e)
```

### 2. Include Context in Error Messages
Error messages should include the problematic value and relevant context.

**Good:**
```python
raise ValidationError(f"Confidence value '{confidence}' must be between 0.0 and 1.0, got {confidence}")
```

**Poor:**
```python
raise ValidationError("Invalid confidence")
```

### 3. Propagate Errors Appropriately
Don't swallow exceptions unless you have a specific recovery strategy. Allow errors to propagate to levels where they can be properly handled.

### 4. Maintain Backward Compatibility
New exception types inherit from standard Python exceptions when appropriate, ensuring existing exception handling continues to work.

## Implementation Guidelines

### When Raising Exceptions

1. **Choose the right exception type** based on the error category
2. **Include specific context** with the error message
3. **Use descriptive error messages** that help with debugging
4. **Follow the established patterns** in the codebase

```python
def validate_confidence(confidence: float) -> float:
    """Validate and normalize confidence value."""
    if not isinstance(confidence, (int, float)):
        raise ValidationError(
            f"Confidence value '{confidence}' must be numeric, got {type(confidence).__name__}"
        )

    if not 0.0 <= confidence <= 1.0:
        raise ValidationError(
            f"Confidence value '{confidence}' must be between 0.0 and 1.0"
        )

    return float(confidence)
```

### When Handling Exceptions

1. **Catch specific exceptions** rather than broad ones
2. **Handle at the appropriate level** - where you can meaningfully recover
3. **Log errors with context** when appropriate
4. **Preserve the original error** when re-raising or wrapping

```python
def process_user_input(user_input: str) -> Dict[str, Any]:
    """Process user input with comprehensive error handling."""
    try:
        validated_input = validate_input(user_input)
        result = compute_result(validated_input)
        return format_result(result)
    except ValidationError as e:
        logger.warning(f"Input validation failed: {e}")
        return {"error": "Invalid input", "details": str(e)}
    except ComputationError as e:
        logger.error(f"Computation failed: {e}")
        return {"error": "Processing error", "details": str(e)}
```

### Pattern Detection Error Handling

For pattern detection algorithms that try multiple approaches:

```python
def detect_pattern(sequence: List[float]) -> Optional[Dict[str, Any]]:
    """Detect patterns with specific exception handling."""
    patterns = [
        ("arithmetic", detect_arithmetic),
        ("geometric", detect_geometric),
        ("fibonacci", detect_fibonacci),
    ]

    for pattern_name, detector in patterns:
        try:
            result = detector(sequence)
            if result:
                return result
        except (ValueError, TypeError, ZeroDivisionError, OverflowError, MemoryError):
            # Continue to next pattern if current one fails
            continue

    return None
```

## Testing Error Handling

### Test Exception Types
Verify that the correct exception types are raised:

```python
def test_confidence_validation():
    with pytest.raises(ValidationError) as exc_info:
        validate_confidence("invalid")
    assert "invalid" in str(exc_info.value)
    assert "must be numeric" in str(exc_info.value)
```

### Test Error Messages
Ensure error messages contain expected information:

```python
def test_error_message_content():
    try:
        validate_conversation_id("")
    except ValidationError as e:
        assert "Invalid conversation_id format" in str(e)
```

### Test Error Propagation
Verify that errors propagate correctly through call stacks:

```python
def test_error_propagation():
    with pytest.raises(ValidationError):
        outer_function_calling_invalid_code()
```

## Migration Guide

### Migrating from Broad Exception Handling

1. **Identify broad exception handling** using `except Exception:`
2. **Analyze what specific exceptions** can occur in the try block
3. **Replace with specific exception types**
4. **Update error handling logic** if needed
5. **Add tests** for the new exception handling

### Example Migration

**Before:**
```python
try:
    result = complex_computation(data)
except Exception:
    fallback_result = default_value
```

**After:**
```python
try:
    result = complex_computation(data)
except ValidationError as e:
    logger.warning(f"Input validation failed: {e}")
    fallback_result = default_value
except ComputationError as e:
    logger.error(f"Computation failed: {e}")
    fallback_result = default_value
except TimeoutError as e:
    logger.error(f"Computation timed out: {e}")
    fallback_result = default_value
```

## Best Practices

1. **Be specific** - Catch only the exceptions you can handle
2. **Fail fast** - Validate inputs early and fail with clear errors
3. **Provide context** - Include relevant information in error messages
4. **Log appropriately** - Log errors with sufficient context for debugging
5. **Document exceptions** - Document what exceptions your functions can raise
6. **Test error paths** - Write tests for error conditions and exception handling
7. **Maintain consistency** - Follow the established patterns throughout the codebase

## Security Considerations

1. **Avoid information disclosure** in error messages to users
2. **Log detailed errors** for debugging without exposing sensitive information
3. **Handle malicious inputs** gracefully without exposing system details
4. **Rate limit error responses** to prevent information gathering attacks

By following these guidelines, we ensure consistent, maintainable, and secure error handling throughout the reasoning library.