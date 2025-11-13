#!/usr/bin/env python3
"""
Debug script to understand keyword extraction behavior.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _extract_keywords

# Test the function to understand its behavior
test_texts = [
    "server cpu memory slow performance",
    "database network latency connection",
    "application deployment error processing"
]

for i, text in enumerate(test_texts, 1):
    result = _extract_keywords(text)
    print(f"Test {i}: '{text}'")
    print(f"Result: {result}")
    print()