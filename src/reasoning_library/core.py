"""Core utilities for the reasoning library.

Facade module providing backward compatibility by re-exporting all public APIs
from the focused modules that implement single responsibilities.
"""

# Re-export decorators
from .decorators import curry, tool_spec

# Re-export mathematical detection components
from .mathematical_detection import (
    CLEAN_FACTOR_PATTERN,
    COMBINATION_PATTERN,
    COMMENT_PATTERN,
    EVIDENCE_PATTERN,
    FACTOR_PATTERN,
    MAX_SOURCE_CODE_SIZE,
    _detect_mathematical_reasoning,
)

# Re-export reasoning chain data structures
from .reasoning_chain import ReasoningChain, ReasoningStep

# Re-export tool registry and metadata
from .tool_registry import (
    ENHANCED_TOOL_REGISTRY,
    TOOL_REGISTRY,
    ToolMetadata,
    _bedrock_format,
    _openai_format,
    _safe_copy_spec,
    get_bedrock_tools,
    get_enhanced_tool_registry,
    get_openai_tools,
    get_tool_specs,
)

# Re-export type utilities
from .type_utils import TYPE_MAP, get_json_schema_type

# Public API - all imports that should be available for backward compatibility
__all__ = [
    # Decorators
    "curry",
    "tool_spec",
    # Mathematical detection constants and functions
    "MAX_SOURCE_CODE_SIZE",
    "FACTOR_PATTERN",
    "COMMENT_PATTERN",
    "EVIDENCE_PATTERN",
    "COMBINATION_PATTERN",
    "CLEAN_FACTOR_PATTERN",
    "_detect_mathematical_reasoning",
    # Reasoning chain classes
    "ReasoningStep",
    "ReasoningChain",
    # Tool registry and metadata
    "ToolMetadata",
    "ENHANCED_TOOL_REGISTRY",
    "TOOL_REGISTRY",
    "_safe_copy_spec",
    "_openai_format",
    "_bedrock_format",
    "get_tool_specs",
    "get_openai_tools",
    "get_bedrock_tools",
    "get_enhanced_tool_registry",
    # Type utilities
    "TYPE_MAP",
    "get_json_schema_type",
]