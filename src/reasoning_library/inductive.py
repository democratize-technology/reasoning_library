"""
Inductive Reasoning Module.

This module provides functions for simple inductive reasoning, such as
pattern recognition in numerical sequences.
"""

from typing import Any, Dict, List, Optional, Union

import numpy as np
import numpy.typing as npt

from .core import ReasoningChain, ReasoningStep, curry, tool_spec


def _assess_data_sufficiency(sequence_length: int, pattern_type: str) -> float:
    """
    Assess if sufficient data points exist for reliable pattern detection.

    Args:
        sequence_length (int): Number of data points in the sequence
        pattern_type (str): Type of pattern ('arithmetic' or 'geometric')

    Returns:
        float: Data sufficiency factor (0.0-1.0)
    """
    if pattern_type == "arithmetic":
        minimum_required = 4
    elif pattern_type == "geometric":
        minimum_required = 4
    else:
        minimum_required = 3  # Default conservative minimum

    return min(1.0, sequence_length / minimum_required)


def _calculate_pattern_quality_score(
    values: Union[npt.NDArray[np.floating[Any]], List[float]], pattern_type: str
) -> float:
    """
    Calculate pattern quality based on statistical variance metrics.

    Args:
        values: Array of differences (arithmetic) or ratios (geometric)
        pattern_type (str): Type of pattern ('arithmetic' or 'geometric')

    Returns:
        float: Pattern quality factor (0.1-1.0)
    """
    if len(values) <= 1:
        return 0.7  # Conservative for minimal data

    values_array = np.array(values)

    if pattern_type == "arithmetic":
        # Use variance penalty for arithmetic progressions
        mean_abs_diff = np.mean(np.abs(values_array))
        if mean_abs_diff < 1e-10:  # All differences are essentially zero
            return 1.0
        # Amplify variance penalty by using standard deviation relative to mean (coefficient of variation)
        coefficient_of_variation = np.std(values_array) / (mean_abs_diff + 1e-10)
        # Use exponential decay to penalize noisy patterns more severely
        return float(max(0.1, np.exp(-2.0 * coefficient_of_variation)))

    elif pattern_type == "geometric":
        # Use coefficient of variation for geometric progressions
        mean_ratio = np.mean(values_array)
        if np.abs(mean_ratio) < 1e-10:  # Avoid division by zero
            return 0.1
        coefficient_of_variation = np.std(values_array) / (np.abs(mean_ratio) + 1e-10)
        # Use exponential decay to penalize noisy patterns, similar to arithmetic
        return float(max(0.1, np.exp(-2.0 * coefficient_of_variation)))

    return 0.5  # Default for unknown pattern types


def _calculate_arithmetic_confidence(
    differences: npt.NDArray[np.floating[Any]],
    sequence_length: int,
    base_confidence: float = 0.95,
) -> float:
    """
    Calculate confidence for arithmetic progression detection.

    Args:
        differences (np.ndarray): Array of consecutive differences
        sequence_length (int): Length of the original sequence
        base_confidence (float): Base confidence level before adjustments

    Returns:
        float: Adjusted confidence score (0.0-1.0)
    """
    # Data sufficiency factor
    data_sufficiency_factor = _assess_data_sufficiency(sequence_length, "arithmetic")

    # Pattern quality factor
    pattern_quality_factor = _calculate_pattern_quality_score(differences, "arithmetic")

    # Complexity factor (arithmetic is simplest pattern)
    complexity_factor = 1.0 / (1.0 + 0.0)  # complexity_score = 0 for arithmetic

    # Calculate final confidence
    confidence = (
        base_confidence
        * data_sufficiency_factor
        * pattern_quality_factor
        * complexity_factor
    )

    return min(1.0, max(0.0, confidence))


def _calculate_geometric_confidence(
    ratios: List[float], sequence_length: int, base_confidence: float = 0.95
) -> float:
    """
    Calculate confidence for geometric progression detection.

    Args:
        ratios (List[float]): List of consecutive ratios
        sequence_length (int): Length of the original sequence
        base_confidence (float): Base confidence level before adjustments

    Returns:
        float: Adjusted confidence score (0.0-1.0)
    """
    # Data sufficiency factor
    data_sufficiency_factor = _assess_data_sufficiency(sequence_length, "geometric")

    # Pattern quality factor
    pattern_quality_factor = _calculate_pattern_quality_score(ratios, "geometric")

    # Complexity factor (geometric is slightly more complex than arithmetic)
    complexity_factor = 1.0 / (1.0 + 0.1)  # complexity_score = 0.1 for geometric

    # Calculate final confidence
    confidence = (
        base_confidence
        * data_sufficiency_factor
        * pattern_quality_factor
        * complexity_factor
    )

    return min(1.0, max(0.0, confidence))


@tool_spec(
    mathematical_basis="Arithmetic and geometric progression analysis",
    confidence_factors=["data_sufficiency", "pattern_quality", "complexity"],
    confidence_formula="base * data_sufficiency_factor * pattern_quality_factor * complexity_factor",
)
@curry
def predict_next_in_sequence(
    sequence: List[float],
    reasoning_chain: Optional[ReasoningChain],
    *,
    rtol: float = 0.2,
    atol: float = 1e-8,
) -> Optional[float]:
    """
    Attempts to predict the next number in a sequence based on simple arithmetic
    or geometric progression.

    Args:
        sequence (List[float]): A list of numbers (floats).
        reasoning_chain (Optional[ReasoningChain]): An optional ReasoningChain to add steps to.
        rtol (float): Relative tolerance for pattern detection (default: 0.2 for 20% variance).
        atol (float): Absolute tolerance for pattern detection (default: 1e-8).

    Returns:
        Optional[float]: The predicted next number as a float, or None if no simple pattern is found.

    Raises:
        TypeError: If sequence is not a list, tuple, or numpy array.
        ValueError: If sequence is empty.
    """
    # Input validation
    if not isinstance(sequence, (list, tuple, np.ndarray)):
        raise TypeError(
            f"Expected list/tuple/array for sequence, got {type(sequence).__name__}"
        )
    if len(sequence) == 0:
        raise ValueError("Sequence cannot be empty")
    stage = "Inductive Reasoning: Sequence Prediction"
    description = f"Attempting to predict next number in sequence: {sequence}"
    result = None
    confidence = 0.0
    evidence = None
    assumptions = ["Sequence follows a simple arithmetic or geometric progression."]

    if len(sequence) < 2:
        description = f"Sequence {sequence} too short to determine a pattern."
        if reasoning_chain:
            reasoning_chain.add_step(
                stage=stage, description=description, result=None, confidence=0.0
            )
        return None

    # Check for arithmetic progression
    diffs = np.diff(sequence)
    if len(diffs) > 0 and np.allclose(diffs, diffs[0], rtol=rtol, atol=atol):
        result = float(sequence[-1] + diffs[0])
        confidence = _calculate_arithmetic_confidence(diffs, len(sequence))
        description = f"Identified arithmetic progression with common difference: {diffs[0]}. Predicted next: {result}"
        evidence = f"Common difference {diffs[0]} found in {diffs}. Confidence based on pattern quality and data sufficiency."
        if reasoning_chain:
            reasoning_chain.add_step(
                stage=stage,
                description=description,
                result=result,
                confidence=confidence,
                evidence=evidence,
                assumptions=assumptions,
            )
        return result

    # Check for geometric progression
    if all(s != 0 for s in sequence):
        ratios_list = [sequence[i] / sequence[i - 1] for i in range(1, len(sequence))]
        # Add bounds checking to prevent extreme values
        ratios = list(np.clip(ratios_list, -1e6, 1e6))
        if len(ratios) > 0 and np.allclose(ratios, ratios[0], rtol=rtol, atol=atol):
            result = float(sequence[-1] * ratios[0])
            confidence = _calculate_geometric_confidence(ratios, len(sequence))
            description = f"Identified geometric progression with common ratio: {ratios[0]}. Predicted next: {result}"
            evidence = f"Common ratio {ratios[0]} found in {ratios}. Confidence based on pattern quality and data sufficiency."
            if reasoning_chain:
                reasoning_chain.add_step(
                    stage=stage,
                    description=description,
                    result=result,
                    confidence=confidence,
                    evidence=evidence,
                    assumptions=assumptions,
                )
            return result

    description = (
        f"No simple arithmetic or geometric pattern found for sequence: {sequence}"
    )
    if reasoning_chain:
        reasoning_chain.add_step(
            stage=stage, description=description, result=None, confidence=0.0
        )
    return None


@tool_spec(
    mathematical_basis="Arithmetic and geometric progression analysis",
    confidence_factors=["data_sufficiency", "pattern_quality", "complexity"],
)
@curry
def find_pattern_description(
    sequence: List[float],
    reasoning_chain: Optional[ReasoningChain],
    *,
    rtol: float = 0.2,
    atol: float = 1e-8,
) -> str:
    """
    Describes the pattern found in a numerical sequence.

    Args:
        sequence (List[float]): A list of numbers (floats).
        reasoning_chain (Optional[ReasoningChain]): An optional ReasoningChain to add steps to.
        rtol (float): Relative tolerance for pattern detection (default: 0.2 for 20% variance).
        atol (float): Absolute tolerance for pattern detection (default: 1e-8).

    Returns:
        str: A string describing the pattern, or 'No simple pattern found.'

    Raises:
        TypeError: If sequence is not a list, tuple, or numpy array.
        ValueError: If sequence is empty.
    """
    # Input validation
    if not isinstance(sequence, (list, tuple, np.ndarray)):
        raise TypeError(
            f"Expected list/tuple/array for sequence, got {type(sequence).__name__}"
        )
    if len(sequence) == 0:
        raise ValueError("Sequence cannot be empty")
    stage = "Inductive Reasoning: Pattern Description"
    description = f"Attempting to describe pattern in sequence: {sequence}"
    result_str = "No simple pattern found."
    confidence = 0.0
    evidence = None
    assumptions = ["Sequence follows a simple arithmetic or geometric progression."]

    if len(sequence) < 2:
        result_str = "Sequence too short to determine a pattern."
        if reasoning_chain:
            reasoning_chain.add_step(
                stage=stage, description=description, result=result_str, confidence=0.0
            )
        return result_str

    # Check for arithmetic progression
    diffs = np.diff(sequence)
    if len(diffs) > 0 and np.allclose(diffs, diffs[0], rtol=rtol, atol=atol):
        result_str = f"Arithmetic progression with common difference: {diffs[0]}"
        # Use higher base confidence for pattern description than prediction
        confidence = _calculate_arithmetic_confidence(
            diffs, len(sequence), base_confidence=0.9
        )
        evidence = f"Common difference {diffs[0]} found in {diffs}. Confidence based on pattern quality and data sufficiency."
        if reasoning_chain:
            reasoning_chain.add_step(
                stage=stage,
                description=description,
                result=result_str,
                confidence=confidence,
                evidence=evidence,
                assumptions=assumptions,
            )
        return result_str

    # Check for geometric progression
    if all(s != 0 for s in sequence):
        ratios_list2 = [sequence[i] / sequence[i - 1] for i in range(1, len(sequence))]
        # Add bounds checking to prevent extreme values
        ratios = list(np.clip(ratios_list2, -1e6, 1e6))
        if len(ratios) > 0 and np.allclose(ratios, ratios[0], rtol=rtol, atol=atol):
            result_str = f"Geometric progression with common ratio: {ratios[0]}"
            # Use higher base confidence for pattern description than prediction
            confidence = _calculate_geometric_confidence(
                ratios, len(sequence), base_confidence=0.9
            )
            evidence = f"Common ratio {ratios[0]} found in {ratios}. Confidence based on pattern quality and data sufficiency."
            if reasoning_chain:
                reasoning_chain.add_step(
                    stage=stage,
                    description=description,
                    result=result_str,
                    confidence=confidence,
                    evidence=evidence,
                    assumptions=assumptions,
                )
            return result_str

    if reasoning_chain:
        reasoning_chain.add_step(
            stage=stage,
            description=description,
            result=result_str,
            confidence=confidence,
        )
    return result_str
