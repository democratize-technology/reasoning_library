"""
Reasoning Library

Enhanced tool specification system supporting AWS Bedrock and OpenAI compatibility
with automatic confidence documentation for mathematical reasoning functions.
"""

__version__ = "0.2.1"

from typing import Any, Dict, List

from .core import get_bedrock_tools  # AWS Bedrock Converse API format
from .core import get_openai_tools  # OpenAI ChatCompletions API format
from .core import get_tool_specs  # Legacy format for backward compatibility


# Pre - populated lists for easy integration
# Note: These are populated dynamically when modules are imported

def get_all_tool_specs() -> List[Dict[str, Any]]:
    """Get all tool specifications - call after importing tool modules."""
    return get_tool_specs()


def get_all_openai_tools() -> List[Dict[str, Any]]:
    """Get all OpenAI tool specifications - call after importing tool modules."""
    return get_openai_tools()


def get_all_bedrock_tools() -> List[Dict[str, Any]]:
    """Get all Bedrock tool specifications - call after importing tool modules."""
    return get_bedrock_tools()
