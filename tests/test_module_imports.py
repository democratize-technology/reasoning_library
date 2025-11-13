#!/usr/bin/env python3
"""
Test module imports to ensure all modules can be imported correctly.

This test file specifically targets import statements and module-level
constants to achieve 100% test coverage.
"""

import pytest


class TestModuleImports:
    """Test that all modules can be imported successfully."""

    def test_import_reasoning_library_main_module(self):
        """Test importing the main reasoning_library module."""
        import reasoning_library
        # Test that we can access the version
        assert hasattr(reasoning_library, '__version__')

    def test_import_all_submodules(self):
        """Test importing all submodules of reasoning_library."""
        from reasoning_library import abductive
        from reasoning_library import chain_of_thought
        from reasoning_library import constants
        from reasoning_library import core
        from reasoning_library import deductive
        from reasoning_library import exceptions
        from reasoning_library import inductive
        from reasoning_library import null_handling
        from reasoning_library import validation

        # Test that modules have expected attributes
        assert hasattr(abductive, 'generate_hypotheses')
        assert hasattr(chain_of_thought, 'chain_of_thought_step')
        assert hasattr(constants, 'COMPUTATION_TIMEOUT')
        assert hasattr(core, 'ReasoningChain')
        assert hasattr(deductive, 'apply_modus_ponens')
        assert hasattr(exceptions, 'ValidationError')
        assert hasattr(inductive, 'predict_next_in_sequence')
        assert hasattr(null_handling, 'handle_optional_params')
        assert hasattr(validation, 'validate_string_list')

    def test_import_specific_functions(self):
        """Test importing specific functions and classes."""
        from reasoning_library.abductive import generate_hypotheses, _extract_keywords_with_context
        from reasoning_library.core import ReasoningChain, tool_spec
        from reasoning_library.exceptions import ValidationError

        # Test that imports are callable or instantiable
        assert callable(generate_hypotheses)
        assert callable(_extract_keywords_with_context)
        assert callable(ReasoningChain)
        assert callable(tool_spec)
        assert issubclass(ValidationError, Exception)


class TestConstantsModule:
    """Test the constants module imports and values."""

    def test_import_security_constants(self):
        """Test importing security-related constants."""
        from reasoning_library.constants import (
            MAX_OBSERVATION_LENGTH,
            MAX_CONTEXT_LENGTH,
            COMPUTATION_TIMEOUT,
            MAX_SEQUENCE_LENGTH,
        )

        # Test that security constants are positive numbers
        assert MAX_OBSERVATION_LENGTH > 0
        assert MAX_CONTEXT_LENGTH > 0
        assert COMPUTATION_TIMEOUT > 0
        assert MAX_SEQUENCE_LENGTH > 0

    def test_import_confidence_constants(self):
        """Test importing confidence calculation constants."""
        from reasoning_library.constants import (
            CONFIDENCE_MIN,
            CONFIDENCE_MAX,
            BASE_CONFIDENCE_CHAIN_OF_THOUGHT,
        )

        # Test confidence bounds
        assert 0.0 <= CONFIDENCE_MIN <= 1.0
        assert 0.0 <= CONFIDENCE_MAX <= 1.0
        assert CONFIDENCE_MAX > CONFIDENCE_MIN
        assert 0.0 <= BASE_CONFIDENCE_CHAIN_OF_THOUGHT <= 1.0