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
        """
        SECURE: Return error message without exposing sensitive details.

        Prevents information disclosure attacks by not exposing the raw details
        dictionary in string representation. Details are still accessible through
        the .details property for debugging purposes but not exposed in logs or
        user-facing error messages.
        """
        # CRITICAL SECURITY FIX: Never expose raw details in string representation
        # This prevents information disclosure of sensitive data like API keys,
        # passwords, file paths, internal IPs, and other sensitive information
        if self.details:
            # Only expose safe, non-sensitive metadata
            safe_info = []

            # Include only safe keys that don't contain sensitive data
            safe_keys = ['error_code', 'validation_type', 'operation', 'category']
            for key in safe_keys:
                if key in self.details:
                    safe_info.append(f"{key}: {self.details[key]}")

            if safe_info:
                return f"{self.message} (Info: {', '.join(safe_info)})"
            else:
                return self.message
        return self.message

    def get_debug_info(self, include_sensitive: bool = False) -> str:
        """
        SECURE: Get detailed debugging information with explicit permission.

        This method requires explicit permission to access sensitive details,
        preventing accidental information disclosure while still allowing
        developers to debug issues when needed.

        Args:
            include_sensitive: Set to True to include all details including
                             potentially sensitive data. Use with caution.

        Returns:
            Detailed string representation for debugging purposes
        """
        if include_sensitive:
            # Only include sensitive data when explicitly requested
            return f"{self.message} (Details: {self.details})"
        else:
            # Use the safe string representation by default
            return str(self)


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