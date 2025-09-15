# Contributing to Reasoning Library

Thank you for your interest in contributing to the Reasoning Library! This document provides guidelines and information to help you contribute effectively.

## 🚀 Quick Start

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/reasoning_library.git
   cd reasoning_library
   ```

2. **Set Up Development Environment**
   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync

   # Install pre-commit hooks
   uv run pre-commit install
   ```

3. **Verify Setup**
   ```bash
   # Run tests
   uv run pytest

   # Check types
   uv run mypy src/reasoning_library

   # Check formatting
   uv run black --check src/ tests/
   uv run isort --check-only src/ tests/
   ```

## 📋 Development Workflow

### Before You Start
- Check existing [issues](https://github.com/reasoning_library/reasoning_library/issues) and [pull requests](https://github.com/reasoning_library/reasoning_library/pulls)
- For major changes, create an issue first to discuss the approach
- Ensure your contribution aligns with the project's goals

### Making Changes
1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write Code**
   - Follow the existing code style and patterns
   - Add type hints for all new code
   - Include docstrings for public functions and classes
   - Write tests for new functionality

3. **Test Your Changes**
   ```bash
   # Run the full test suite
   uv run pytest tests/ -v

   # Check test coverage
   uv run pytest tests/ --cov=reasoning_library --cov-report=html

   # Type checking
   uv run mypy src/reasoning_library

   # Code formatting
   uv run black src/ tests/
   uv run isort src/ tests/
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new reasoning capability"
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines
- **Title**: Use conventional commit format (feat, fix, docs, etc.)
- **Description**: Clearly explain what and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant documentation
- **Backward Compatibility**: Maintain API compatibility unless breaking changes are necessary

## 🧪 Testing Guidelines

### Test Structure
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Edge Cases**: Test boundary conditions and error handling

### Writing Tests
```python
def test_reasoning_functionality():
    """Test description following the pattern."""
    # Arrange
    reasoning_chain = ReasoningChain()

    # Act
    result = some_function(reasoning_chain)

    # Assert
    assert result is not None
    assert reasoning_chain.steps
```

### Test Requirements
- All new code must have tests
- Test coverage should be ≥85%
- Tests must pass on all supported Python versions (3.10, 3.11, 3.12)
- Tests should be deterministic and isolated

## 📝 Code Style Guidelines

### Python Code Style
- **Formatting**: Black with default settings
- **Imports**: isort with profile=black
- **Type Hints**: Required for all public APIs
- **Docstrings**: Google style for public functions

### Example Code Style
```python
from typing import List, Optional, Union

def predict_sequence(
    sequence: List[float],
    reasoning_chain: Optional[ReasoningChain] = None
) -> Union[float, None]:
    """Predict the next value in a numerical sequence.

    Args:
        sequence: The input numerical sequence.
        reasoning_chain: Optional reasoning chain for step recording.

    Returns:
        The predicted next value, or None if no pattern found.

    Raises:
        ValueError: If sequence is empty or invalid.
    """
    if not sequence:
        raise ValueError("Sequence cannot be empty")

    # Implementation here
    return predicted_value
```

### Commit Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**: feat, fix, docs, style, refactor, test, chore

## 🏗️ Architecture Guidelines

### Core Principles
- **Functional Programming**: Prefer pure functions and immutable data
- **Type Safety**: Comprehensive type hints and mypy compliance
- **Security**: Input validation and protection against common vulnerabilities
- **Performance**: Efficient algorithms with O(n) complexity where possible

### Module Structure
- **core.py**: Fundamental reasoning primitives and tool registration
- **deductive.py**: Formal logic and inference rules
- **inductive.py**: Pattern recognition and sequence analysis
- **chain_of_thought.py**: Conversation management and step tracking

### Adding New Features
1. **Design Phase**: Consider API design and backward compatibility
2. **Implementation**: Follow existing patterns and conventions
3. **Testing**: Comprehensive test coverage with edge cases
4. **Documentation**: Update relevant documentation and examples

## 🛡️ Security Guidelines

### Security Best Practices
- **Input Validation**: Validate all external inputs
- **ReDoS Protection**: Limit regex complexity and input size
- **Dependency Security**: Keep dependencies updated and scan for vulnerabilities
- **Secrets**: Never commit secrets or API keys

### Reporting Security Issues
Please see our [Security Policy](SECURITY.md) for information on reporting security vulnerabilities.

## 📚 Documentation Guidelines

### Types of Documentation
- **API Documentation**: Docstrings for all public functions
- **Examples**: Working code examples in docstrings
- **README**: High-level project overview and quick start
- **Architecture**: Design decisions and patterns

### Documentation Standards
- Clear, concise language
- Working code examples
- Up-to-date with current implementation
- Accessible to both beginners and experts

## 🐛 Issue Reporting

### Bug Reports
Include:
- **Description**: Clear description of the issue
- **Reproduction**: Minimal code to reproduce the problem
- **Environment**: Python version, OS, dependencies
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens

### Feature Requests
Include:
- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Implementation**: Any implementation thoughts

## 🤝 Code Review Process

### For Contributors
- Respond to feedback promptly
- Make requested changes in additional commits
- Squash commits before merge if requested

### For Reviewers
- Be constructive and specific
- Focus on code quality, security, and maintainability
- Approve when ready for merge

## 📋 Release Process

Releases are handled by maintainers following semantic versioning:
- **Patch**: Bug fixes and minor improvements
- **Minor**: New features with backward compatibility
- **Major**: Breaking changes

## 🙋‍♀️ Getting Help

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs and feature requests
- **Documentation**: Check existing documentation first

## 🎯 Areas for Contribution

We welcome contributions in these areas:
- **New Reasoning Patterns**: Additional logical or mathematical reasoning capabilities
- **Performance Improvements**: Optimization and efficiency enhancements
- **Documentation**: Examples, tutorials, and API documentation
- **Testing**: Additional test cases and edge case coverage
- **Integration**: Support for additional LLM providers

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Reasoning Library! 🎉