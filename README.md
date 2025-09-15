# Reasoning Library

A Python library demonstrating various reasoning methods formalized through functional programming principles.
This library aims to showcase how complex reasoning can be built from simple, pure functions and composition,
while also providing a structured "chain-of-thought" mechanism similar to the `chain-of-thought-tool` package.

## Features

*   **Structured Reasoning Steps:** Each reasoning operation produces a `ReasoningStep` object, encapsulating the result along with metadata like confidence, stage, evidence, and assumptions.
*   **Reasoning Chain Management:** The `ReasoningChain` class allows for collecting and managing a sequence of `ReasoningStep` objects, providing a summary of the entire reasoning process.
*   **Tool Specification Generation:** Functions intended for use by Large Language Models (LLMs) are decorated to automatically generate JSON Schema tool specifications, enabling seamless integration with LLM function calling APIs.
*   **Deductive Reasoning:** Implementation of basic logical operations (AND, OR, NOT, IMPLIES) and the Modus Ponens rule.
    *   Functions are curried for flexible composition.
*   **Inductive Reasoning:** Simple pattern recognition for numerical sequences (arithmetic and geometric progressions).
    *   Predicts the next number in a sequence.
    *   Describes the identified pattern.

## Installation

This is a self-contained example. To use it, ensure you have the required dependencies. You can use `uv` to install them:

```bash
cd reasoning_library
uv pip install -r requirements.txt
cd ..
```

## Usage

To see the library in action, run the `example.py` script:

```bash
python reasoning_library/example.py
```

### Core Concepts

#### `ReasoningStep`

Represents a single step in a reasoning process. It includes:

*   `step_number`: Sequential identifier for the step.
*   `stage`: A string describing the type of reasoning (e.g., "Deductive Reasoning: Modus Ponens").
*   `description`: A human-readable explanation of what the step did.
*   `result`: The outcome of the reasoning step.
*   `confidence`: (Optional) A float indicating the confidence in the result.
*   `evidence`: (Optional) A string detailing the evidence used.
*   `assumptions`: (Optional) A list of strings outlining assumptions made.
*   `metadata`: (Optional) A dictionary for any additional relevant information.

#### `ReasoningChain`

Manages a collection of `ReasoningStep` objects. Key methods:

*   `add_step(...)`: Adds a new `ReasoningStep` to the chain.
*   `get_summary()`: Returns a formatted string summarizing all steps in the chain.
*   `clear()`: Resets the chain, removing all steps.
*   `last_result`: Property to get the result of the last step.

#### LLM Tool Integration

Functions decorated with `@tool_spec` automatically generate a JSON Schema representation, making them callable by LLMs that support function calling. This allows an LLM to use the library's reasoning capabilities as external tools.

### Deductive Reasoning Example

```python
from reasoning_library.deductive import apply_modus_ponens
from reasoning_library.core import ReasoningChain

chain = ReasoningChain()

# If P is true, and (P -> Q) is true, then Q is true.
result = apply_modus_ponens(True, True, reasoning_chain=chain) # P=True, Q=True
print(f"Modus Ponens (P=True, Q=True): {result}") # Output: True

result = apply_modus_ponens(True, False, reasoning_chain=chain) # P=True, Q=False (P->Q is false)
print(f"Modus Ponens (P=True, Q=False): {result}") # Output: None

print(chain.get_summary())
```

### Inductive Reasoning Example

```python
from reasoning_library.inductive import predict_next_in_sequence, find_pattern_description
from reasoning_library.core import ReasoningChain

chain = ReasoningChain()

seq = [1.0, 2.0, 3.0, 4.0]
chain.add_step(stage="Inductive Reasoning", description=f"Analyzing sequence {seq}", result=seq)
pattern = find_pattern_description(seq, reasoning_chain=chain)
predicted = predict_next_in_sequence(seq, reasoning_chain=chain)

print(f"Sequence: {seq}")
print(f"Pattern: {pattern}")
print(f"Predicted next: {predicted}")

print(chain.get_summary())
```

### LLM Tool Specification Example

```python
import json
from reasoning_library import TOOL_SPECS

# TOOL_SPECS is a list containing the JSON Schema for all registered tools.
# You can "just drop it in" to your LLM's tool configuration.
print(json.dumps(TOOL_SPECS, indent=2))

# This specification list can be provided to any LLM API that supports function calling.
```

## Design Principles

*   **Pure Functions:** Reasoning functions are designed to be pure, producing the same output for the same input and having no side effects (apart from optionally adding steps to a `ReasoningChain` object passed as an argument).
*   **Functional Composition:** Reasoning steps are built by composing smaller, independent functions, promoting modularity and reusability.
*   **Type Hinting:** Used throughout the codebase for clarity and maintainability.

## Extending the Library

This library is designed to be extensible. You can add new reasoning modules (e.g., for Abductive, Analogical, Causal reasoning) by creating new Python files and implementing their logic using the `ReasoningStep` and `ReasoningChain` structures, and decorating functions with `@tool_spec` to expose them to LLMs.
