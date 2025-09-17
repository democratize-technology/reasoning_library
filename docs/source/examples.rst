Examples
========

This page contains usage examples for reasoning-library.

Basic Usage
-----------

.. code-block:: python

   from reasoning_library.core import ReasoningChain
   from reasoning_library.deductive import apply_modus_ponens

   # Create a reasoning chain
   chain = ReasoningChain()

   # Apply deductive reasoning
   result = apply_modus_ponens(True, True, reasoning_chain=chain)
   print(f"Result: {result}")

   # Get the reasoning summary
   print(chain.get_summary())

Chain of Thought Example
------------------------

.. code-block:: python

   from reasoning_library.chain_of_thought import ChainOfThoughtReasoner

   reasoner = ChainOfThoughtReasoner()
   result = reasoner.reason(
       problem="Solve: 2 + 2",
       context="Basic arithmetic"
   )
   print(result.explanation)

Inductive Reasoning Example
---------------------------

.. code-block:: python

   from reasoning_library.inductive import predict_next_in_sequence
   from reasoning_library.core import ReasoningChain

   chain = ReasoningChain()
   sequence = [1.0, 2.0, 3.0, 4.0]

   next_value = predict_next_in_sequence(sequence, reasoning_chain=chain)
   print(f"Next value in sequence: {next_value}")

Advanced Examples
-----------------

More complex examples and use cases are available in the ``examples/`` directory of the repository.