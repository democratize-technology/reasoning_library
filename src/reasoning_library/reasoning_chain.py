"""
Reasoning chain data structures.

This module contains the ReasoningStep and ReasoningChain classes for managing
sequences of reasoning steps with metadata and chain-of-thought capabilities.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReasoningStep:
    """
    Represents a single step in a reasoning chain, including its result and metadata.
    """

    step_number: int
    stage: str
    description: str
    result: Any
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    assumptions: Optional[List[str]] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """
    Manages a sequence of ReasoningStep objects, providing chain-of-thought capabilities.
    """

    steps: List[ReasoningStep] = field(default_factory=list)
    _step_counter: int = field(init=False, default=0)

    def add_step(
        self,
        stage: str,
        description: str,
        result: Any,
        confidence: Optional[float] = None,
        evidence: Optional[str] = None,
        assumptions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """
        Adds a new reasoning step to the chain.
        """
        self._step_counter += 1
        step = ReasoningStep(
            step_number=self._step_counter,
            stage=stage,
            description=description,
            result=result,
            confidence=confidence,
            evidence=evidence,
            assumptions=assumptions if assumptions is not None else [],
            metadata=metadata if metadata is not None else {},
        )
        self.steps.append(step)
        return step

    def get_summary(self) -> str:
        """
        Generates a summary of the reasoning chain.
        """
        summary_parts = ["Reasoning Chain Summary:"]
        for step in self.steps:
            summary_parts.append(
                f"  Step {step.step_number} ({step.stage}): {step.description}"
            )
            summary_parts.append(f"    Result: {step.result}")
            if step.confidence is not None:
                summary_parts.append(f"    Confidence: {step.confidence:.2f}")
            if step.evidence:
                summary_parts.append(f"    Evidence: {step.evidence}")
            if step.assumptions:
                summary_parts.append(f"    Assumptions: {', '.join(step.assumptions)}")
            if step.metadata:
                summary_parts.append(f"    Metadata: {step.metadata}")
        return "\n".join(summary_parts)

    def clear(self) -> None:
        """
        Clears all steps from the reasoning chain.
        """
        self.steps = []
        self._step_counter = 0

    @property
    def last_result(self) -> Any:
        """
        Returns the result of the last step in the chain, or None if the chain is empty.
        """
        return self.steps[-1].result if self.steps else None