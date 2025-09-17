#!/usr/bin/env python
"""Test documentation quality locally before CI runs."""

import html5lib
import subprocess
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def build_docs():
    """Build the documentation."""
    print("Building documentation...")
    result = subprocess.run(
        ["uv", "run", "--with", "sphinx,sphinx-rtd-theme,sphinx-autodoc-typehints,tomli",
         "sphinx-build", "-b", "html", "docs/source", "docs/build/html"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ Documentation build failed:")
        print(result.stderr)
        return False

    print("✅ Documentation built successfully")
    return True


def validate_html():
    """Validate HTML files."""
    errors = 0
    html_files = list(Path("docs/build/html").rglob("*.html"))

    print(f"\nValidating {len(html_files)} HTML files...")

    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Use non-strict parser for Sphinx compatibility
                parser = html5lib.HTMLParser(strict=False)
                document = parser.parse(content)
                if document is None:
                    raise Exception("Failed to parse document")
        except Exception as e:
            print(f"❌ {html_file}: {e}")
            errors += 1

    if errors > 0:
        print(f"\n❌ HTML validation failed. Errors: {errors}")
        return False

    print("✅ All HTML files are valid")
    return True


def check_internal_links():
    """Check for broken internal links."""
    broken_links = []
    html_files = list(Path("docs/build/html").rglob("*.html"))
    existing_files = {f.name for f in html_files}

    print(f"\nChecking internal links...")

    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') or href.startswith('#'):
                continue  # Skip external links and anchors

            # Check if internal link exists
            if href.endswith('.html'):
                link_file = Path(href).name
                if link_file not in existing_files:
                    broken_links.append(f"{html_file}: {href}")

    if broken_links:
        print("❌ Broken internal links found:")
        for link in broken_links:
            print(f"  {link}")
        return False

    print("✅ No broken internal links found")
    return True


def check_essential_files():
    """Check that essential documentation files exist."""
    essential_files = [
        "docs/build/html/index.html",
        "docs/build/html/api.html",
        "docs/build/html/overview.html",
        "docs/build/html/examples.html",
    ]

    print(f"\nChecking essential files...")

    for file_path in essential_files:
        if not Path(file_path).exists():
            print(f"❌ Missing essential file: {file_path}")
            return False

    print("✅ All essential files present")
    return True


def main():
    """Run all documentation quality checks."""
    print("Running documentation quality checks...\n")

    # Install dependencies
    print("Installing dependencies...")
    subprocess.run(
        ["uv", "sync", "--dev"],
        capture_output=True
    )

    # Run all checks
    checks = [
        ("Build Documentation", build_docs),
        ("Validate HTML", validate_html),
        ("Check Internal Links", check_internal_links),
        ("Check Essential Files", check_essential_files),
    ]

    all_passed = True
    results = []

    for name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        print('='*50)
        passed = check_func()
        results.append((name, passed))
        if not passed:
            all_passed = False

    # Print summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")

    print(f"\n{'='*50}")
    if all_passed:
        print("✅ All documentation quality checks passed!")
        print("Documentation is ready for CI/CD.")
        return 0
    else:
        print("❌ Some documentation quality checks failed.")
        print("Please fix the issues before pushing to CI.")
        return 1


if __name__ == "__main__":
    sys.exit(main())