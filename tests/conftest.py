"""
Pytest configuration and fixtures for test isolation.

This module provides fixtures to ensure proper test isolation by resetting
global state variables that persist between test runs.
"""


import pytest


@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Fixture to reset all global state before each test.

    This ensures test isolation by clearing module-level variables that
    can persist between test runs and cause test interference.

    The fixture uses autouse=True so it runs automatically before every test.
    """
    # Reset core module global registries
    from reasoning_library.core import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY

    TOOL_REGISTRY.clear()
    ENHANCED_TOOL_REGISTRY.clear()

    # Reset chain_of_thought module conversation storage
    from reasoning_library.chain_of_thought import (
        _conversations,
        _conversations_lock,
    )

    with _conversations_lock:
        _conversations.clear()

    yield  # Run the test

    # Optional: Clean up after test (usually not needed if we reset before each test)


@pytest.fixture
def clean_tool_registry():
    """
    Fixture specifically for tests that need a clean tool registry.

    Use this fixture explicitly in tests that specifically test tool registration.
    """
    from reasoning_library.core import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY

    # Clear registries
    TOOL_REGISTRY.clear()
    ENHANCED_TOOL_REGISTRY.clear()

    yield

    # Clean up after test
    TOOL_REGISTRY.clear()
    ENHANCED_TOOL_REGISTRY.clear()


@pytest.fixture
def clean_conversations():
    """
    Fixture specifically for tests that need clean conversation storage.

    Use this fixture explicitly in tests that test conversation management.
    """
    from reasoning_library.chain_of_thought import (
        _conversations,
        _conversations_lock,
    )

    # Clear conversations
    with _conversations_lock:
        _conversations.clear()

    yield

    # Clean up after test
    with _conversations_lock:
        _conversations.clear()


@pytest.fixture
def isolated_reasoning_chain():
    """
    Fixture that provides a fresh ReasoningChain instance.

    Use this when you need a guaranteed clean ReasoningChain for testing.
    """
    from reasoning_library.core import ReasoningChain

    return ReasoningChain()


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Legacy markers (moved to pyproject.toml but keeping for compatibility)
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically based on test names and paths.

    This function automatically categorizes tests into appropriate markers
    based on their file names, function names, and module paths.
    """
    import os
    import re

    for item in items:
        # Get test file path and name for analysis
        test_file = os.path.basename(str(item.fspath))
        test_name = item.name.lower()
        test_module = item.module.__name__ if hasattr(item, 'module') else ''

        # Security-related test markers
        security_keywords = [
            'security', 'vulnerability', 'attack', 'malicious', 'injection',
            'dos', 'denial', 'redos', 'regex', 'timing', 'race', 'concurrent',
            'thread', 'safety', 'validation', 'sanitization', 'escape', 'bypass'
        ]

        # Performance-related test markers
        performance_keywords = [
            'performance', 'perf', 'timing', 'speed', 'memory', 'scalability',
            'throughput', 'benchmark', 'load', 'stress', 'efficiency'
        ]

        # Integration test markers
        integration_keywords = [
            'integration', 'end_to_end', 'e2e', 'workflow', 'chain'
        ]

        # Slow test markers
        slow_keywords = [
            'slow', 'load', 'stress', 'benchmark', 'performance', 'timeout'
        ]

        # Add automatic markers based on test characteristics

        # Security markers
        if any(keyword in test_name or keyword in test_file for keyword in security_keywords):
            item.add_marker(pytest.mark.security)

            # Specific security sub-markers
            if any(keyword in test_name or keyword in test_file for keyword in ['redos', 'regex', 'catastrophic']):
                item.add_marker(pytest.mark.redos)
            if any(keyword in test_name or keyword in test_file for keyword in ['dos', 'denial', 'exhaustion']):
                item.add_marker(pytest.mark.dos)
            if any(keyword in test_name or keyword in test_file for keyword in ['injection', 'sanitization', 'escape']):
                item.add_marker(pytest.mark.injection)
            if any(keyword in test_name or keyword in test_file for keyword in ['timing', 'side_channel']):
                item.add_marker(pytest.mark.timing)
            if any(keyword in test_name or keyword in test_file for keyword in ['memory', 'leak', 'allocation']):
                item.add_marker(pytest.mark.memory)
            if any(keyword in test_name or keyword in test_file for keyword in ['thread', 'concurrent', 'race', 'lock']):
                item.add_marker(pytest.mark.concurrency)

        # Performance markers
        if any(keyword in test_name or keyword in test_file for keyword in performance_keywords):
            item.add_marker(pytest.mark.performance)

        # Integration markers
        if any(keyword in test_name or keyword in test_file for keyword in integration_keywords):
            item.add_marker(pytest.mark.integration)

        # Slow test markers
        if any(keyword in test_name or keyword in test_file for keyword in slow_keywords):
            item.add_marker(pytest.mark.slow)

        # File-based automatic marking
        if test_file.startswith('test_security') or 'vulnerability' in test_file:
            item.add_marker(pytest.mark.security)
        elif test_file.startswith('test_performance') or 'perf' in test_file:
            item.add_marker(pytest.mark.performance)
        elif test_file.startswith('test_integration'):
            item.add_marker(pytest.mark.integration)

        # Default to 'unit' if no other specific markers applied
        if not any(
            marker.name in ["security", "performance", "integration", "slow"]
            for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)


# Add custom test collection hooks for better organization
def pytest_report_header(config):
    """Add custom header to pytest report."""
    return """
Reasoning Library Test Suite
============================
Security Tests:     pytest -m security
Performance Tests:  pytest -m performance
Integration Tests:  pytest -m integration
Unit Tests:         pytest -m unit
Quick Tests Only:   pytest -m "not slow"
Coverage Report:    pytest --cov=src/reasoning_library
"""


def pytest_html_report_title(report):
    """Custom title for HTML reports."""
    report.title = "Reasoning Library Test Results"
