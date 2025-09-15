"""
Chain of Thought Reasoning Module.

This module provides universal LLM functions for managing conversational reasoning chains
with thread-safe conversation management and confidence scoring.
"""

import re
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from .core import ReasoningChain, tool_spec

# Thread-safe conversation management with bounded storage
_conversations: OrderedDict[str, ReasoningChain] = OrderedDict()
_conversations_lock = threading.RLock()
_MAX_CONVERSATIONS = 1000  # Configurable limit to prevent memory DoS


def _validate_conversation_id(conversation_id: str) -> str:
    """
    Validate conversation_id to prevent injection attacks.

    Args:
        conversation_id (str): The conversation ID to validate.

    Returns:
        str: The validated conversation ID.

    Raises:
        ValueError: If conversation_id is invalid.
    """
    if not isinstance(conversation_id, str):
        raise ValueError("conversation_id must be a string")
    if not re.match(r"\A[a-zA-Z0-9_-]{1,64}\Z", conversation_id):
        raise ValueError(
            "Invalid conversation_id format. Must be 1-64 alphanumeric characters, underscores, or hyphens."
        )
    return conversation_id


def _evict_oldest_conversations_if_needed() -> None:
    """
    Evict oldest conversations if we exceed the maximum limit.
    Must be called within _conversations_lock context.
    """
    while len(_conversations) >= _MAX_CONVERSATIONS:
        # Remove the oldest conversation (FIFO/LRU)
        _conversations.popitem(last=False)


def _get_or_create_conversation(conversation_id: str) -> ReasoningChain:
    """
    Thread-safe helper to get or create a ReasoningChain for a conversation.

    NOTE: This function assumes it's called within _conversations_lock context.
    It does NOT acquire the lock itself to prevent nested locking issues.

    Args:
        conversation_id (str): Validated unique identifier for the conversation.

    Returns:
        ReasoningChain: The reasoning chain for this conversation.
    """
    if conversation_id in _conversations:
        # Move to end (mark as recently used for LRU)
        _conversations.move_to_end(conversation_id)
        return _conversations[conversation_id]

    # Evict oldest conversations if needed
    _evict_oldest_conversations_if_needed()

    # Create new conversation
    _conversations[conversation_id] = ReasoningChain()
    return _conversations[conversation_id]


@tool_spec
def chain_of_thought_step(
    conversation_id: str,
    stage: str,
    description: str,
    result: Any,
    confidence: Optional[float] = None,
    evidence: Optional[str] = None,
    assumptions: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Add a step to a conversation's chain of thought reasoning process.

    Creates a new reasoning chain if the conversation doesn't exist.
    Uses conservative confidence scoring where unspecified confidence defaults to 0.8.

    Args:
        conversation_id (str): Unique identifier for the conversation.
        stage (str): The reasoning stage (e.g., "Analysis", "Synthesis", "Conclusion").
        description (str): Description of the reasoning step.
        result (Any): The result or conclusion of this step.
        confidence (Optional[float]): Confidence score 0.0-1.0, defaults to 0.8.
        evidence (Optional[str]): Supporting evidence for this step.
        assumptions (Optional[list]): List of assumptions made in this step.
        metadata (Optional[dict]): Additional metadata for this step.

    Returns:
        dict: Contains step_number, conversation_id, and success status.
    """
    # Validate conversation_id to prevent injection attacks
    try:
        conversation_id = _validate_conversation_id(conversation_id)
    except ValueError as e:
        return {
            "step_number": -1,
            "conversation_id": conversation_id,
            "success": False,
            "error": str(e),
        }

    if confidence is None:
        confidence = 0.8  # Conservative default for chain-of-thought steps

    # Ensure confidence is within valid range
    confidence = max(0.0, min(1.0, confidence))

    # Fix race condition: move conversation creation inside lock context
    with _conversations_lock:
        chain = _get_or_create_conversation(conversation_id)

        step = chain.add_step(
            stage=stage,
            description=description,
            result=result,
            confidence=confidence,
            evidence=evidence,
            assumptions=assumptions if assumptions is not None else [],
            metadata=metadata if metadata is not None else {},
        )

    return {
        "step_number": step.step_number,
        "conversation_id": conversation_id,
        "success": True,
        "confidence": confidence,
    }


@tool_spec
def get_chain_summary(conversation_id: str) -> Dict[str, Any]:
    """
    Get a formatted summary of the reasoning chain for a conversation.

    Includes overall confidence score calculated as the minimum confidence
    of all steps (conservative approach - weakest link determines reliability).

    Args:
        conversation_id (str): Unique identifier for the conversation.

    Returns:
        dict: Contains summary text, step count, and overall confidence score.
    """
    # Validate conversation_id to prevent injection attacks
    try:
        conversation_id = _validate_conversation_id(conversation_id)
    except ValueError as e:
        return {
            "summary": f"Invalid conversation ID: {e}",
            "step_count": 0,
            "overall_confidence": 0.0,
            "success": False,
            "error": str(e),
        }

    with _conversations_lock:
        if conversation_id not in _conversations:
            return {
                "summary": f"No reasoning chain found for conversation '{conversation_id}'.",
                "step_count": 0,
                "overall_confidence": 0.0,
                "success": False,
            }

        chain = _conversations[conversation_id]

        # Calculate overall confidence as minimum of all step confidences
        overall_confidence = 1.0  # Start with maximum confidence
        if chain.steps:
            confidences = [
                step.confidence for step in chain.steps if step.confidence is not None
            ]
            if confidences:
                overall_confidence = min(confidences)  # Conservative approach
            else:
                overall_confidence = 0.8  # Default if no confidences specified
        else:
            overall_confidence = 0.0  # No steps means no confidence

        return {
            "summary": chain.get_summary(),
            "step_count": len(chain.steps),
            "overall_confidence": overall_confidence,
            "conversation_id": conversation_id,
            "success": True,
        }


@tool_spec
def clear_chain(conversation_id: str) -> Dict[str, Any]:
    """
    Clear the reasoning chain for a specific conversation.

    Removes the conversation from memory entirely. This action cannot be undone.

    Args:
        conversation_id (str): Unique identifier for the conversation to clear.

    Returns:
        dict: Contains success status and confirmation message.
    """
    # Validate conversation_id to prevent injection attacks
    try:
        conversation_id = _validate_conversation_id(conversation_id)
    except ValueError as e:
        return {
            "message": f"Invalid conversation ID: {e}",
            "conversation_id": conversation_id,
            "steps_removed": 0,
            "success": False,
            "error": str(e),
        }

    with _conversations_lock:
        if conversation_id in _conversations:
            # Get step count before clearing for confirmation
            step_count = len(_conversations[conversation_id].steps)
            del _conversations[conversation_id]

            return {
                "message": f"Cleared reasoning chain for conversation '{conversation_id}' ({step_count} steps removed).",
                "conversation_id": conversation_id,
                "steps_removed": step_count,
                "success": True,
            }
        else:
            return {
                "message": f"No reasoning chain found for conversation '{conversation_id}' to clear.",
                "conversation_id": conversation_id,
                "steps_removed": 0,
                "success": False,
            }


def get_active_conversations() -> List[str]:
    """
    Get a list of all active conversation IDs.

    This is a utility function for debugging and monitoring, not exposed as a tool.

    Returns:
        list: List of active conversation IDs.
    """
    with _conversations_lock:
        return list(_conversations.keys())


def get_conversation_stats() -> Dict[str, Any]:
    """
    Get statistics about all active conversations.

    This is a utility function for debugging and monitoring, not exposed as a tool.

    Returns:
        dict: Statistics including total conversations and step counts.
    """
    with _conversations_lock:
        stats: Dict[str, Any] = {
            "total_conversations": len(_conversations),
            "conversation_details": {},
        }

        for conv_id, chain in _conversations.items():
            confidences = [
                step.confidence for step in chain.steps if step.confidence is not None
            ]
            overall_confidence = min(confidences) if confidences else 0.0

            stats["conversation_details"][conv_id] = {
                "step_count": len(chain.steps),
                "overall_confidence": overall_confidence,
                "last_result": chain.last_result,
            }

        return stats
