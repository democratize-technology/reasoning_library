"""
Tool registry and export format utilities.

This module manages the tool registries and provides functions for exporting
tool specifications in different API formats (OpenAI, Bedrock).
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Enhanced registry storing functions with rich metadata
ENHANCED_TOOL_REGISTRY: List[Dict[str, Any]] = []

# Legacy registry for backward compatibility
TOOL_REGISTRY: List[Callable[..., Any]] = []


@dataclass
class ToolMetadata:
    """Enhanced metadata for tool specifications."""

    confidence_documentation: Optional[str] = None
    mathematical_basis: Optional[str] = None
    platform_notes: Optional[Dict[str, str]] = field(default_factory=dict)
    is_mathematical_reasoning: bool = False
    confidence_formula: Optional[str] = None
    confidence_factors: Optional[List[str]] = field(default_factory=list)


def _safe_copy_spec(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely copy tool specification with input validation to prevent prototype pollution.

    Args:
        tool_spec: Tool specification to copy

    Returns:
        Validated and safely copied tool specification

    Raises:
        ValueError: If tool specification is invalid or missing required fields
    """
    if not isinstance(tool_spec, dict):
        raise ValueError("Tool specification must be a dictionary")

    if "function" not in tool_spec:
        raise ValueError("Tool specification must contain 'function' key")

    if not isinstance(tool_spec["function"], dict):
        raise ValueError("Tool specification 'function' value must be a dictionary")

    # Whitelist of allowed top-level keys to prevent prototype pollution
    allowed_top_level_keys = {"type", "function"}

    # Whitelist of allowed function keys
    allowed_function_keys = {"name", "description", "parameters"}

    # Create safe copy with only whitelisted keys
    safe_spec = {}
    for key, value in tool_spec.items():
        if key in allowed_top_level_keys:
            if key == "function":
                # Safely copy function object with whitelisted keys only
                safe_function = {}
                for func_key, func_value in value.items():
                    if func_key in allowed_function_keys:
                        safe_function[func_key] = func_value
                safe_spec[key] = safe_function
            else:
                safe_spec[key] = value

    return safe_spec


def _openai_format(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool specification to OpenAI ChatCompletions API format.

    Args:
        tool_spec: Standard tool specification

    Returns:
        OpenAI-compatible tool specification
    """
    # Use safe copy to prevent prototype pollution
    safe_spec = _safe_copy_spec(tool_spec)
    return {
        "type": "function",
        "function": {
            "name": safe_spec["function"]["name"],
            "description": safe_spec["function"]["description"],
            "parameters": safe_spec["function"]["parameters"],
        },
    }


def _bedrock_format(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool specification to AWS Bedrock Converse API format.

    Args:
        tool_spec: Standard tool specification

    Returns:
        Bedrock-compatible tool specification
    """
    # Use safe copy to prevent prototype pollution
    safe_spec = _safe_copy_spec(tool_spec)
    return {
        "toolSpec": {
            "name": safe_spec["function"]["name"],
            "description": safe_spec["function"]["description"],
            "inputSchema": {"json": safe_spec["function"]["parameters"]},
        }
    }


def _enhance_description_with_confidence_docs(
    description: str, metadata: ToolMetadata
) -> str:
    """
    Enhance tool description with confidence documentation for mathematical reasoning functions.

    Args:
        description: Original function description
        metadata: Tool metadata containing confidence information

    Returns:
        Enhanced description with confidence documentation
    """
    if not metadata.is_mathematical_reasoning:
        return description

    # Avoid duplicate enhancement by checking if already enhanced
    if "Mathematical Basis:" in description:
        return description

    enhanced_desc = description

    if metadata.mathematical_basis:
        enhanced_desc += f"\n\nMathematical Basis: {metadata.mathematical_basis}"

    # Generate confidence documentation from explicit factors if available
    if metadata.confidence_factors:
        enhanced_desc += f"\n\nConfidence Scoring: Confidence calculation based on: {', '.join(metadata.confidence_factors)}"
    elif metadata.confidence_documentation:
        # Fallback to existing documentation if factors are not provided
        enhanced_desc += f"\n\nConfidence Scoring: {metadata.confidence_documentation}"

    if metadata.confidence_formula:
        enhanced_desc += f"\n\nConfidence Formula: {metadata.confidence_formula}"

    return enhanced_desc


def get_tool_specs() -> List[Dict[str, Any]]:
    """Returns a list of all registered tool specifications (legacy format)."""
    return [getattr(func, "tool_spec") for func in TOOL_REGISTRY]


def get_openai_tools() -> List[Dict[str, Any]]:
    """
    Export tool specifications in OpenAI ChatCompletions API format.

    Returns:
        List of OpenAI-compatible tool specifications
    """
    openai_tools = []
    for entry in ENHANCED_TOOL_REGISTRY:
        # Create enhanced description using safe copy
        enhanced_spec = _safe_copy_spec(entry["tool_spec"])
        enhanced_spec["function"]["description"] = (
            _enhance_description_with_confidence_docs(
                enhanced_spec["function"]["description"], entry["metadata"]
            )
        )
        openai_tools.append(_openai_format(enhanced_spec))
    return openai_tools


def get_bedrock_tools() -> List[Dict[str, Any]]:
    """
    Export tool specifications in AWS Bedrock Converse API format.

    Returns:
        List of Bedrock-compatible tool specifications
    """
    bedrock_tools = []
    for entry in ENHANCED_TOOL_REGISTRY:
        # Create enhanced description using safe copy
        enhanced_spec = _safe_copy_spec(entry["tool_spec"])
        enhanced_spec["function"]["description"] = (
            _enhance_description_with_confidence_docs(
                enhanced_spec["function"]["description"], entry["metadata"]
            )
        )
        bedrock_tools.append(_bedrock_format(enhanced_spec))
    return bedrock_tools


def get_enhanced_tool_registry() -> List[Dict[str, Any]]:
    """
    Get the complete enhanced tool registry with metadata.

    Returns:
        List of enhanced tool registry entries
    """
    return ENHANCED_TOOL_REGISTRY.copy()
