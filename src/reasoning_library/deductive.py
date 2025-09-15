"""
Deductive Reasoning Module.

This module provides functions for deductive logic, including basic logical operations
and the Modus Ponens rule, implemented using a functional programming style.
"""

from typing import Any, Callable, List, Optional, Tuple

from .core import ReasoningChain, ReasoningStep, curry, tool_spec

# --- Base Logical Primitives (Pure Functions) ---


@curry
def logical_not(p: bool) -> bool:
    return not p


def logical_not_with_confidence(p: bool) -> Tuple[bool, float]:
    """
    Logical NOT operation with confidence scoring.

    Args:
        p (bool): The input proposition.

    Returns:
        tuple: (NOT p, confidence) where confidence is 1.0 for deterministic operation.

    Raises:
        TypeError: If p is not a boolean.
    """
    if not isinstance(p, bool):
        raise TypeError(f"Expected bool for p, got {type(p).__name__}")
    result = not p
    return result, 1.0


@curry
def logical_and(p: bool, q: bool) -> bool:
    return p and q


def logical_and_with_confidence(p: bool, q: bool) -> Tuple[bool, float]:
    """
    Logical AND operation with confidence scoring.

    Args:
        p (bool): First proposition.
        q (bool): Second proposition.

    Returns:
        tuple: (p AND q, confidence) where confidence is 1.0 for deterministic operation.

    Raises:
        TypeError: If p or q is not a boolean.
    """
    if not isinstance(p, bool):
        raise TypeError(f"Expected bool for p, got {type(p).__name__}")
    if not isinstance(q, bool):
        raise TypeError(f"Expected bool for q, got {type(q).__name__}")
    result = p and q
    return result, 1.0


@curry
def logical_or(p: bool, q: bool) -> bool:
    return p or q


def logical_or_with_confidence(p: bool, q: bool) -> Tuple[bool, float]:
    """
    Logical OR operation with confidence scoring.

    Args:
        p (bool): First proposition.
        q (bool): Second proposition.

    Returns:
        tuple: (p OR q, confidence) where confidence is 1.0 for deterministic operation.

    Raises:
        TypeError: If p or q is not a boolean.
    """
    if not isinstance(p, bool):
        raise TypeError(f"Expected bool for p, got {type(p).__name__}")
    if not isinstance(q, bool):
        raise TypeError(f"Expected bool for q, got {type(q).__name__}")
    result = p or q
    return result, 1.0


@curry
def implies(p: bool, q: bool) -> bool:
    """Logical IMPLICATION (P -> Q is equivalent to NOT P OR Q)."""
    return bool(logical_or(logical_not(p), q))


def implies_with_confidence(p: bool, q: bool) -> Tuple[bool, float]:
    """
    Logical IMPLICATION with confidence scoring.

    Args:
        p (bool): Antecedent proposition.
        q (bool): Consequent proposition.

    Returns:
        tuple: (p implies q, confidence) where confidence is 1.0 for deterministic operation.

    Raises:
        TypeError: If p or q is not a boolean.
    """
    if not isinstance(p, bool):
        raise TypeError(f"Expected bool for p, got {type(p).__name__}")
    if not isinstance(q, bool):
        raise TypeError(f"Expected bool for q, got {type(q).__name__}")
    result = logical_or(logical_not(p), q)
    return result, 1.0


# --- Composed Deductive Reasoning: Modus Ponens ---


@curry
def check_modus_ponens_premises(p: bool, q: bool) -> bool:
    """
    Checks if the premises for Modus Ponens are met:
    (P -> Q) AND P
    """
    return bool(logical_and(implies(p, q), p))


def check_modus_ponens_premises_with_confidence(p: bool, q: bool) -> Tuple[bool, float]:
    """
    Checks if the premises for Modus Ponens are met with confidence scoring.

    Args:
        p (bool): The antecedent proposition P.
        q (bool): The consequent proposition Q.

    Returns:
        tuple: (premises_valid, confidence) where confidence is 1.0 for deterministic check.

    Raises:
        TypeError: If p or q is not a boolean.
    """
    if not isinstance(p, bool):
        raise TypeError(f"Expected bool for p, got {type(p).__name__}")
    if not isinstance(q, bool):
        raise TypeError(f"Expected bool for q, got {type(q).__name__}")
    result = logical_and(implies(p, q), p)
    # For modus ponens premises: confidence is always 1.0 since it's a deterministic logical check
    return result, 1.0


@tool_spec(
    mathematical_basis="Formal deductive logic using Modus Ponens inference rule",
    confidence_factors=["premise_truth_value"],
)
@curry
def apply_modus_ponens(
    p_is_true: bool,
    p_implies_q_is_true: bool,
    reasoning_chain: Optional[ReasoningChain] = None,
) -> Optional[bool]:
    """
    Applies the Modus Ponens rule: If P is true and (P -> Q) is true, then Q is true.

    Args:
        p_is_true (bool): The truth value of proposition P.
        p_implies_q_is_true (bool): The truth value of the implication (P -> Q).
        reasoning_chain (Optional[ReasoningChain]): An optional ReasoningChain to record the step.

    Returns:
        Optional[bool]: The conclusion (True) if deduced, otherwise None.
    """
    conclusion = None
    description = f"Attempting Modus Ponens with P={p_is_true} and (P -> Q)={p_implies_q_is_true}."
    stage = "Deductive Reasoning: Modus Ponens"
    confidence = 0.0
    evidence = f"Premise P is {p_is_true}, Premise (P -> Q) is {p_implies_q_is_true}."
    assumptions = ["Propositions P and (P -> Q) are true"]

    if p_is_true and p_implies_q_is_true:
        conclusion = True
        description = f"Modus Ponens: Concluded Q is True from P={p_is_true} and (P -> Q)={p_implies_q_is_true}."
        confidence = 1.0  # High confidence for deductive logic
    else:
        description = f"Modus Ponens: Cannot conclude Q from P={p_is_true} and (P -> Q)={p_implies_q_is_true}."
        confidence = 0.0

    if reasoning_chain:
        reasoning_chain.add_step(
            stage=stage,
            description=description,
            result=conclusion,
            confidence=confidence,
            evidence=evidence,
            assumptions=assumptions,
        )
    return conclusion


# --- Higher-Order Function for Chaining Deductions ---


def chain_deductions(
    reasoning_chain: ReasoningChain, *functions: Callable[[Any], Any]
) -> Callable[[Any], Any]:
    """
    Composes multiple deductive functions into a single chain, adding steps to the provided ReasoningChain.
    Each function in the chain takes the output of the previous one as input.
    """

    def composed_function(initial_input: Any) -> Any:
        result = initial_input
        for i, func in enumerate(functions):
            # Each function in the chain is expected to return a result that can be passed to the next.
            # If the function itself adds to the chain, it should handle that internally.
            # If a function returns None, it means deduction failed at that step.
            result = func(result)
            if result is None:  # If any step fails to deduce, the chain breaks
                # The individual function should have added a step indicating failure
                return None
        return result

    return composed_function
