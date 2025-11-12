#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.core import ReasoningChain

# Test the log injection fix
chain = ReasoningChain()

injection = "Normal input\n[ERROR] System compromised by admin!"

# Add a step with malicious input that could poison logs
chain.add_step(
    stage="Test Stage",
    description="Test description",
    result=injection,
    evidence=f"Evidence: {injection}",
    assumptions=[f"Assumption: {injection}"]
)

# Generate summary - if this gets logged, it could poison logs
summary = chain.get_summary()

print("Original injection:", repr(injection))
print("Summary:", repr(summary))
print("Contains injection payload:", injection in summary)
print("Contains newlines:", '\n' in summary)
