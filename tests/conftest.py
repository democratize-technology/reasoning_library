"""
Pytest configuration and fixtures for test isolation.

This module provides fixtures to ensure proper test isolation by resetting
global state variables that persist between test runs.
"""

import threading
from collections import OrderedDict

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
    try:
        from reasoning_library.core import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY

        TOOL_REGISTRY.clear()
        ENHANCED_TOOL_REGISTRY.clear()
    except ImportError:
        # Handle case where import path differs
        from src.reasoning_library.core import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY

        TOOL_REGISTRY.clear()
        ENHANCED_TOOL_REGISTRY.clear()

    # Reset chain_of_thought module conversation storage
    try:
        from reasoning_library.chain_of_thought import (
            _conversations,
            _conversations_lock,
        )

        with _conversations_lock:
            _conversations.clear()
    except ImportError:
        # Handle case where import path differs
        from src.reasoning_library.chain_of_thought import (
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
    try:
        from reasoning_library.core import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY
    except ImportError:
        from src.reasoning_library.core import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY

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
    try:
        from reasoning_library.chain_of_thought import (
            _conversations,
            _conversations_lock,
        )
    except ImportError:
        from src.reasoning_library.chain_of_thought import (
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
    try:
        from reasoning_library.core import ReasoningChain
    except ImportError:
        from src.reasoning_library.core import ReasoningChain

    return ReasoningChain()


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add 'unit' marker to all tests by default
        if not any(
            marker.name in ["integration", "slow"] for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)
