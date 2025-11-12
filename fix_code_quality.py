#!/usr/bin/env python3
"""
Automated code quality fixes for the reasoning library.
Fixes line length, whitespace, and other style issues.
"""

import os
import re
import sys
from typing import List, Tuple


def fix_line_length(content: str) -> str:
    """Fix lines that are too long by breaking them appropriately."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        if len(line) <= 88:
            fixed_lines.append(line)
            continue

        # Skip if line is a comment or string that can't be safely broken
        if line.strip().startswith('#') or '"""' in line or "'''" in line:
            fixed_lines.append(line)
            continue

        # Try to break at natural breaking points
        if ' and ' in line and not line.strip().startswith('def '):
            # Break at 'and' operators
            parts = line.split(' and ')
            if len(parts) == 2:
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(parts[0] + ' and')
                fixed_lines.append(' ' * (indent + 4) + parts[1])
                continue

        if ' or ' in line and not line.strip().startswith('def '):
            # Break at 'or' operators
            parts = line.split(' or ')
            if len(parts) == 2:
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(parts[0] + ' or')
                fixed_lines.append(' ' * (indent + 4) + parts[1])
                continue

        # Break at long function calls
        if '(' in line and ')' in line and ', ' in line:
            # Find the function name and opening parenthesis
            func_start = line.find('(')
            if func_start > 0:
                func_name = line[:func_start]
                args_part = line[func_start:]

                # Try to break after first argument
                if args_part.count(', ') >= 1:
                    parts = args_part.split(', ', 1)
                    if len(func_name) + len(parts[0]) <= 85:
                        indent = len(line) - len(line.lstrip())
                        fixed_lines.append(func_name + parts[0] + ',')
                        fixed_lines.append(' ' * (func_start + 1) + parts[1])
                        continue

        # If no safe breaking point found, keep as-is
        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_whitespace_around_operators(content: str) -> str:
    """Fix missing whitespace around arithmetic operators."""
    # Fix E226: missing whitespace around arithmetic operator
    patterns = [
        (r'(\w)=(\w)', r'\1 = \2'),  # a=b -> a = b
        (r'(\w)(\+|\-|\*|\/|//|%|<<|>>|&|\||\^)(\w)', r'\1 \2 \3'),  # a+b -> a + b
        (r'(\w)(\+|\-|\*|\/|//|%|<<|>>|&|\||\^)(?=\w)', r'\1 \2'),  # a+ -> a +
        (r'(?<=\w)(\+|\-|\*|\/|//|%|<<|>>|&|\||\^)(\w)', r'\1 \2'),  # +b -> + b
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_unused_variables(content: str, filename: str) -> Tuple[str, List[str]]:
    """Remove or comment out unused variables."""
    lines = content.split('\n')
    fixed_lines = []
    removed_vars = []

    # Simple heuristic for common unused variable patterns
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Common patterns for unused variables in comprehensions
        if 'for ' in line and ' in enumerate(' in line:
            # Check if the loop variable is actually used
            if ' n ' in line or ' e ' in line or ' bound ' in line:
                var_match = re.search(r'for (\w+) in enumerate\(', line)
                if var_match:
                    var_name = var_match.group(1)
                    # Replace with underscore if unused
                    if var_name in ['n', 'e', 'bound']:
                        fixed_line = line.replace(f'for {var_name} in', 'for _ in')
                        fixed_lines.append(fixed_line)
                        removed_vars.append(f"Line {i+1}: {var_name}")
                        continue

        # Remove standalone assignments that are never used
        if re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]*\s*$', line):
            # Check if variable is used in next few lines
            var_match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=', line)
            if var_match:
                var_name = var_match.group(1)
                # Look ahead to see if variable is used
                used_later = False
                for j in range(i+1, min(i+10, len(lines))):
                    if var_name in lines[j]:
                        used_later = True
                        break

                if not used_later and var_name in ['func_name', 'bound']:
                    # Comment out the line
                    fixed_lines.append(line + '  # TODO: remove unused variable')
                    removed_vars.append(f"Line {i+1}: {var_name}")
                    continue

        fixed_lines.append(line)

    return '\n'.join(fixed_lines), removed_vars


def fix_f_strings(content: str) -> str:
    """Fix f-strings without placeholders."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Look for f-strings without variables or expressions
        fstring_match = re.search(r'f["\']([^"\']*)["\']', line)
        if fstring_match and '{' not in fstring_match.group(1):
            # Convert to regular string
            fixed_line = line.replace('f"', '"').replace("f'", "'")
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def add_missing_newlines(content: str) -> str:
    """Add missing newline at end of file."""
    if content and not content.endswith('\n'):
        return content + '\n'
    return content


def fix_line_break_style(content: str) -> str:
    """Fix W504: line break after binary operator."""
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Look for lines that start with an operator (bad style)
        if stripped.startswith((' and ', ' or ', ' + ', ' - ', ' * ', ' / ')):
            # This is a line that starts with an operator - try to fix
            if i > 0:
                prev_line = lines[i-1].rstrip()
                # Combine with previous line
                combined = prev_line + ' ' + stripped
                if len(combined) <= 88:
                    fixed_lines[-1] = combined
                    continue

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_blank_line_spacing(content: str) -> str:
    """Fix blank line spacing issues (E302, E305, E129)."""
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_lines.append(line)

        # Check if this is a function/class definition
        if re.match(r'^\s*(def|class)\s+', line):
            # Ensure there are 2 blank lines before function/class
            if i >= 2:
                prev_two_lines = lines[i-2:i]
                if not (prev_two_lines[0].strip() == '' and prev_two_lines[1].strip() == ''):
                    # Add missing blank line
                    if i > 0 and lines[i-1].strip() != '':
                        fixed_lines.insert(-1, '')

    return '\n'.join(fixed_lines)


def process_file(filepath: str) -> Tuple[str, List[str]]:
    """Process a single file and apply all fixes."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixes_applied = []

    # Apply fixes in order
    content = fix_line_length(content)
    if content != original_content:
        fixes_applied.append("Fixed line length issues")

    content = fix_whitespace_around_operators(content)
    if content != original_content:
        fixes_applied.append("Fixed whitespace around operators")

    content, removed_vars = fix_unused_variables(content, filepath)
    if removed_vars:
        fixes_applied.append(f"Removed unused variables: {', '.join(removed_vars)}")

    content = fix_f_strings(content)
    if content != original_content:
        fixes_applied.append("Fixed f-string formatting")

    content = add_missing_newlines(content)
    if content != original_content and content.endswith('\n'):
        fixes_applied.append("Added missing newline at end of file")

    content = fix_line_break_style(content)
    if content != original_content:
        fixes_applied.append("Fixed line break style")

    content = fix_blank_line_spacing(content)
    if content != original_content:
        fixes_applied.append("Fixed blank line spacing")

    # Write back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Applied fixes: {', '.join(fixes_applied)}")
    else:
        print("  No changes needed")

    return content, fixes_applied


def main():
    """Main function to process all Python files."""
    src_dir = "src/reasoning_library"

    if not os.path.exists(src_dir):
        print(f"Error: {src_dir} directory not found")
        sys.exit(1)

    # Process all Python files
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    process_file(filepath)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    print("\nCode quality fixes completed!")


if __name__ == "__main__":
    main()
