"""
Reasoning Library

Enhanced tool specification system supporting AWS Bedrock and OpenAI compatibility
with automatic confidence documentation for mathematical reasoning functions.
"""

from typing import List, Dict, Any
from .core import ReasoningChain, ReasoningStep
from .deductive import apply_modus_ponens
from .inductive import predict_next_in_sequence, find_pattern_description
from .chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
from .core import (
    get_tool_specs,           # Legacy format for backward compatibility
    get_openai_tools,         # OpenAI ChatCompletions API format
    get_bedrock_tools,        # AWS Bedrock Converse API format
    get_enhanced_tool_registry, # Complete enhanced registry with metadata
    ToolMetadata              # Metadata class for enhanced tools
)

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
