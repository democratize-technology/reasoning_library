"""
Reasoning Library

Enhanced tool specification system supporting AWS Bedrock and OpenAI compatibility
with automatic confidence documentation for mathematical reasoning functions.
"""

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
TOOL_SPECS = get_tool_specs()           # Legacy format
OPENAI_TOOLS = get_openai_tools()       # OpenAI format
BEDROCK_TOOLS = get_bedrock_tools()     # Bedrock format
