#!/usr/bin/env python3
"""
Test script to verify abductive reasoning grammar fix.
This demonstrates the current broken behavior and verifies the expected improved output.
"""

from src.reasoning_library.abductive import generate_hypotheses


def test_abductive_grammar_fix():
    """Test that hypotheses are grammatically correct with proper context phrases."""

    # Test case from the document
    observations = ["server responding slowly", "database CPU at 95%", "recent code deploy 2 hours ago"]
    context = "production web application"
    max_hypotheses = 3

    result = generate_hypotheses(
        observations=observations,
        reasoning_chain=None,
        context=context,
        max_hypotheses=max_hypotheses
    )

    print("=== CURRENT OUTPUT ===")
    for i, h in enumerate(result[:3], 1):
        print(f'{i}. {h["hypothesis"]}')

    print("\n=== GRAMMAR CHECKS ===")
    for i, h in enumerate(result[:3], 1):
        hyp = h['hypothesis']
        print(f'\nHypothesis {i}: "{hyp}"')

        # Grammar checks
        if not hyp[0].isupper():
            print(f'❌ FAIL: Should start with capital letter: {hyp}')
            return False

        if len(hyp.split()) < 5:
            print(f'❌ FAIL: Too short, likely incomplete: {hyp}')
            return False

        if hyp.endswith('recent') or hyp.endswith('due to') or hyp.endswith('because of'):
            print(f'❌ FAIL: Incomplete sentence: {hyp}')
            return False

        # Content checks - should use context phrases, not raw keywords
        if ' cpu ' in hyp.lower() and 'high cpu usage' not in hyp.lower():
            print(f'❌ FAIL: Uses raw "cpu" instead of "high CPU usage": {hyp}')
            return False

        if any(word in hyp.lower() for word in ['deploy', 'deployment', 'change']):
            print(f'✅ PASS: Mentions action: {hyp}')
        else:
            print(f'❌ FAIL: Should mention action (deploy/deployment/change): {hyp}')
            return False

        if any(word in hyp.lower() for word in ['database', 'server', 'system', 'application']):
            print(f'✅ PASS: Mentions component: {hyp}')
        else:
            print(f'❌ FAIL: Should mention component (database/server/system/application): {hyp}')
            return False

    print('\n✅ ALL GRAMMAR CHECKS PASSED')
    return True


def test_expected_output():
    """Test the expected output format from the document."""

    observations = ["server responding slowly", "database CPU at 95%", "recent code deploy 2 hours ago"]
    context = "production web application"

    result = generate_hypotheses(
        observations=observations,
        reasoning_chain=None,
        context=context,
        max_hypotheses=3
    )

    expected_patterns = [
        "deploy introduced",
        "experiencing high CPU usage due to",
        "performance regression in"
    ]

    print("\n=== EXPECTED PATTERN CHECKS ===")
    for i, (h, expected_pattern) in enumerate(zip(result[:3], expected_patterns), 1):
        hyp = h['hypothesis'].lower()

        # Check if hypothesis contains expected patterns
        found_pattern = False
        for pattern in expected_patterns:
            if pattern in hyp:
                print(f'✅ Hypothesis {i}: Contains expected pattern "{pattern}"')
                found_pattern = True
                break

        if not found_pattern:
            print(f'⚠️  Hypothesis {i}: "{h["hypothesis"]}" - may not match expected patterns')


if __name__ == "__main__":
    print("Testing abductive reasoning grammar fix...")

    # This should initially fail with current implementation
    success = test_abductive_grammar_fix()

    # Show expected patterns
    test_expected_output()

    if not success:
        print("\n🔧 Grammar issues found - implementation needs to be fixed")
        exit(1)
    else:
        print("\n🎉 All tests passed - grammar is correct!")
        exit(0)
