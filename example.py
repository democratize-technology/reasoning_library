"""
Example usage of the reasoning_library.
"""

from reasoning_library.deductive import (
    logical_not,
    logical_and,
    logical_or,
    implies,
    apply_modus_ponens,
    chain_deductions,
)
from reasoning_library.inductive import predict_next_in_sequence, find_pattern_description
from reasoning_library.core import ReasoningChain

print("-- Deductive Reasoning Examples (Modus Ponens) --")

my_chain = ReasoningChain()

# Scenario 1: P is true, and (P -> Q) is true. Conclusion: Q is true.
# Example: If it rains (P), the ground is wet (Q). It is raining (P is true) and the implication is valid (P -> Q is true).
print("\nScenario 1: P is true, (P -> Q) is true")
result1 = apply_modus_ponens(p_is_true=True, p_implies_q_is_true=True, reasoning_chain=my_chain)
print(f"Conclusion: Q is {result1}")

# Scenario 2: P is true, but (P -> Q) is false. Conclusion: Cannot deduce Q.
# Example: If it rains (P), the ground is wet (Q). It is raining (P is true), but the implication is false for some reason.
print("\nScenario 2: P is true, (P -> Q) is false")
result2 = apply_modus_ponens(p_is_true=True, p_implies_q_is_true=False, reasoning_chain=my_chain)
print(f"Conclusion: Q is {result2}")

# Scenario 3: P is false, but (P -> Q) is true. Conclusion: Cannot deduce Q.
# Example: If it rains (P), the ground is wet (Q). It is not raining (P is false), even though the rule is valid.
print("\nScenario 3: P is false, (P -> Q) is true")
result3 = apply_modus_ponens(p_is_true=False, p_implies_q_is_true=True, reasoning_chain=my_chain)
print(f"Conclusion: Q is {result3}")

print("\n--- Chaining Deductions Example ---")

# Chained deduction: (A -> B) and (B -> C). If A is true, C must be true.
# 1. Given A is true and (A -> B) is true, we deduce B is true.
# 2. Given B is true and (B -> C) is true, we deduce C is true.

chain_a_true = ReasoningChain()
print("\nChaining A->B->C with A=True:")

# Step 1: Deduce B from A
# We assume (A -> B) is a valid rule.
a_is_true = True
a_implies_b_is_true = True
b_is_true = apply_modus_ponens(a_is_true, a_implies_b_is_true, reasoning_chain=chain_a_true)

# Step 2: Deduce C from B
# We assume (B -> C) is a valid rule.
b_implies_c_is_true = True
c_is_true = apply_modus_ponens(b_is_true, b_implies_c_is_true, reasoning_chain=chain_a_true)
print(f"If A is True, then C is: {c_is_true}")

print("\nChaining A->B->C with A=False:")
chain_a_false = ReasoningChain()
a_is_false = False
# We still assume (A -> B) is a valid rule.
b_from_a_false = apply_modus_ponens(a_is_false, a_implies_b_is_true, reasoning_chain=chain_a_false)
# Since the first step fails, the chain breaks.
c_from_a_false = apply_modus_ponens(b_from_a_false, b_implies_c_is_true, reasoning_chain=chain_a_false)
print(f"If A is False, then C is: {c_from_a_false}")

print("\n--- Inductive Reasoning Examples (Sequence Prediction) ---")

# Arithmetic Progression
seq1 = [1.0, 2.0, 3.0, 4.0]
print(f"\nSequence: {seq1}")
my_chain.add_step(stage="Inductive Reasoning", description=f"Analyzing sequence {seq1}", result=seq1)
pattern1 = find_pattern_description(seq1, reasoning_chain=my_chain)
predicted1 = predict_next_in_sequence(seq1, reasoning_chain=my_chain)
print(f"Pattern: {pattern1}")
print(f"Predicted next: {predicted1}")

# Geometric Progression
seq2 = [2.0, 4.0, 8.0, 16.0]
print(f"\nSequence: {seq2}")
my_chain.add_step(stage="Inductive Reasoning", description=f"Analyzing sequence {seq2}", result=seq2)
pattern2 = find_pattern_description(seq2, reasoning_chain=my_chain)
predicted2 = predict_next_in_sequence(seq2, reasoning_chain=my_chain)
print(f"Pattern: {pattern2}")
print(f"Predicted next: {predicted2}")

# No simple pattern
seq3 = [1.0, 5.0, 2.0, 8.0]
print(f"\nSequence: {seq3}")
my_chain.add_step(stage="Inductive Reasoning", description=f"Analyzing sequence {seq3}", result=seq3)
pattern3 = find_pattern_description(seq3, reasoning_chain=my_chain)
predicted3 = predict_next_in_sequence(seq3, reasoning_chain=my_chain)
print(f"Pattern: {pattern3}")
print(f"Predicted next: {predicted3}")

# Sequence too short
seq4 = [7.0]
print(f"\nSequence: {seq4}")
my_chain.add_step(stage="Inductive Reasoning", description=f"Analyzing sequence {seq4}", result=seq4)
pattern4 = find_pattern_description(seq4, reasoning_chain=my_chain)
predicted4 = predict_next_in_sequence(seq4, reasoning_chain=my_chain)
print(f"Pattern: {pattern4}")
print(f"Predicted next: {predicted4}")

print("\n--- Full Reasoning Chain Summary ---")
print(my_chain.get_summary())

print("\n--- Chain A=True Summary ---")
print(chain_a_true.get_summary())

print("\n--- Chain A=False Summary ---")
print(chain_a_false.get_summary())

from reasoning_library import TOOL_SPECS

print("\n--- Tool Specifications for LLM Integration ---")

import json
for spec in TOOL_SPECS:
    print(json.dumps(spec, indent=2))
    print("\n---\n")

print("\nThese TOOL_SPECS can be passed to an LLM API that supports function calling.")
print("The LLM can then decide which reasoning function to call based on the user's query.")
