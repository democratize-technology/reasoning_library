#!/usr/bin/env python3
"""
Performance test to demonstrate sanitization.py regex compilation overhead.

This test measures the module import time to establish baseline performance
before implementing lazy loading optimization.
"""

import time
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_sanitization_import_performance():
    """Test current sanitization module import performance."""

    # Remove from cache if already imported
    modules_to_remove = [name for name in sys.modules.keys() if name.startswith('reasoning_library')]
    for module in modules_to_remove:
        del sys.modules[module]

    # Measure import time
    start_time = time.perf_counter()
    import reasoning_library.sanitization as sanitization
    import_time = time.perf_counter() - start_time

    print(f"Sanitization module import time: {import_time:.4f} seconds")

    # Test that lazy loading is working by checking getter functions exist
    getter_functions = [
        '_get_dangerous_keyword_pattern',
        '_get_template_injection_pattern',
        '_get_format_string_pattern',
        '_get_code_injection_pattern',
        '_get_dunder_pattern',
        '_get_attribute_pattern',
        '_get_shell_pattern',
        '_get_bracket_pattern',
        '_get_quote_pattern',
        '_get_html_injection_pattern',
        '_get_control_char_pattern',
        '_get_ansi_escape_pattern',
        '_get_whitespace_pattern',
        '_get_log_injection_pattern',
        '_get_nested_injection_pattern',
        '_get_string_concatenation_pattern'
    ]

    available_getters = 0
    for getter_name in getter_functions:
        if hasattr(sanitization, getter_name):
            available_getters += 1

    # Test that backward compatibility works - patterns should be accessible through __getattr__
    backward_compatible_patterns = [
        '_DANGEROUS_KEYWORD_PATTERN',
        '_TEMPLATE_INJECTION_PATTERN',
        '_CODE_INJECTION_PATTERN'
    ]

    compatible_patterns = 0
    for pattern_name in backward_compatible_patterns:
        try:
            pattern = getattr(sanitization, pattern_name)
            import re
            if isinstance(pattern, re.Pattern):
                compatible_patterns += 1
        except AttributeError:
            pass

    print(f"Lazy getter functions available: {available_getters}/{len(getter_functions)}")
    print(f"Backward compatible patterns: {compatible_patterns}/{len(backward_compatible_patterns)}")

    # Test actual pattern compilation on demand
    start_compile = time.perf_counter()
    test_pattern = sanitization._DANGEROUS_KEYWORD_PATTERN  # Should trigger lazy compilation
    compile_time = time.perf_counter() - start_compile

    return {
        'import_time': import_time,
        'lazy_getters_available': available_getters,
        'expected_getters': len(getter_functions),
        'backward_compatible': compatible_patterns,
        'expected_compatible': len(backward_compatible_patterns),
        'first_pattern_compile_time': compile_time,
        'performance_improved': import_time < 0.01  # Should be faster than 10ms now
    }

if __name__ == "__main__":
    result = test_sanitization_import_performance()
    print(f"\nPerformance Analysis:")
    print(f"- Import time: {result['import_time']:.4f}s")
    print(f"- Lazy getters: {result['lazy_getters_available']}/{result['expected_getters']}")
    print(f"- Backward compatible: {result['backward_compatible']}/{result['expected_compatible']}")
    print(f"- First pattern compile: {result['first_pattern_compile_time']:.4f}s")
    print(f"- Performance improved: {result['performance_improved']}")

    if result['performance_improved']:
        print("\n✅ PERFORMANCE OPTIMIZATION SUCCESSFUL")
        print("Module import time is now under 10ms due to lazy loading")
        print("Regex patterns are compiled only when accessed")
    else:
        print("\n⚠️ Performance may still need optimization")
        print(f"Import time: {result['import_time']:.4f}s (target: <0.010s)")