"""
Standardized Exception Hierarchy for Reasoning Library.

This module defines specific exception types for the reasoning library,
providing clear error categorization and handling patterns.
"""

from typing import Optional, Any, Dict


class ReasoningError(Exception):
    """Base exception class for all reasoning library errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ValidationError(ReasoningError):
    """Raised when input validation fails."""
    pass


class ComputationError(ReasoningError):
    """Raised when mathematical or logical computation fails."""
    pass


class PatternDetectionError(ComputationError):
    """Raised when pattern detection algorithms encounter issues."""
    pass


class TimeoutError(ReasoningError):
    """Raised when computation exceeds allowed time limits."""
    pass


class CacheError(ReasoningError):
    """Raised when caching operations fail."""
    pass


class SecurityError(ReasoningError):
    """Raised when security constraints are violated."""
    pass


class ImportWarning(ReasoningError):
    """Raised when optional dependencies cannot be imported (non-fatal)."""
    pass


class ReasoningChainError(ReasoningError):
    """Raised when reasoning chain operations fail."""
    pass


class ToolSpecificationError(ReasoningError):
    """Raised when tool specification creation or validation fails."""
    pass