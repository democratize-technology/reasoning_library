---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description

**Summary**
A clear and concise description of what the bug is.

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Actual Behavior**
A clear and concise description of what actually happened.

## 🔄 Reproduction Steps

```python
# Minimal code to reproduce the issue
from reasoning_library import ReasoningChain

# Step 1: Setup
reasoning_chain = ReasoningChain()

# Step 2: Action that causes the bug
result = reasoning_chain.some_method()

# Step 3: Observe the issue
print(result)  # Expected: X, Actual: Y
```

**Steps to reproduce:**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## 🌍 Environment

**System Information:**
- OS: [e.g., macOS 13.0, Ubuntu 22.04, Windows 11]
- Python version: [e.g., 3.11.0]
- Reasoning Library version: [e.g., 1.0.0]

**Dependencies:**
```bash
# Output of: uv pip list
# Or contents of requirements.txt/pyproject.toml
```

**Installation Method:**
- [ ] pip install reasoning-library
- [ ] uv add reasoning-library
- [ ] Built from source
- [ ] Other: _______________

## 📋 Additional Context

**Error Messages/Logs:**
```
# Include any error messages, stack traces, or relevant logs
```

**Screenshots:**
<!-- If applicable, add screenshots to help explain your problem -->

**Related Issues:**
<!-- Link to any related issues or discussions -->

**Workarounds:**
<!-- Any temporary solutions you've found -->

## ✅ Checklist

- [ ] I have searched existing issues to ensure this is not a duplicate
- [ ] I have provided a minimal code example that reproduces the issue
- [ ] I have included my environment information
- [ ] I have checked that this issue occurs with the latest version

## 🔍 Additional Information

**Is this a regression?**
- [ ] Yes, this worked in version: _______________
- [ ] No, this is a new issue
- [ ] I'm not sure

**Impact:**
- [ ] This blocks my work
- [ ] This is a minor inconvenience
- [ ] This affects production systems
- [ ] This is a security concern

**Priority:**
- [ ] Critical (system unusable)
- [ ] High (major feature broken)
- [ ] Medium (feature partially broken)
- [ ] Low (minor issue)