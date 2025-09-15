"""
Reasoning Library

Enhanced tool specification system supporting AWS Bedrock and OpenAI compatibility
with automatic confidence documentation for mathematical reasoning functions.
"""

__version__ = "0.1.0"

from typing import Any, Dict, List

from .chain_of_thought import chain_of_thought_step, clear_chain, get_chain_summary
from .core import ToolMetadata  # Metadata class for enhanced tools
from .core import get_bedrock_tools  # AWS Bedrock Converse API format
from .core import get_enhanced_tool_registry  # Complete enhanced registry with metadata
from .core import get_openai_tools  # OpenAI ChatCompletions API format
from .core import get_tool_specs  # Legacy format for backward compatibility
from .core import ReasoningChain, ReasoningStep
from .deductive import apply_modus_ponens
from .inductive import find_pattern_description, predict_next_in_sequence


# Pre-populated lists for easy integration
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
