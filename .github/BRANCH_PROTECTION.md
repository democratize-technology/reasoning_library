# Branch Protection Configuration

This document outlines the recommended branch protection rules for the reasoning-library repository to ensure code quality and security before OSS release.

## Main Branch Protection Rules

Configure the following settings for the `main` branch in GitHub repository settings:

### Required Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

**Required status checks:**
- `Quality Gate` (from test.yml workflow)
- `Security Gate` (from security.yml workflow)
- `Build Documentation` (from docs.yml workflow)

### Required Reviews
- ✅ **Require pull request reviews before merging**
- **Required number of reviewers:** 1
- ✅ **Dismiss stale reviews when new commits are pushed**
- ✅ **Require review from code owners** (if CODEOWNERS file exists)
- ✅ **Restrict reviews to users with write access**

### Additional Restrictions
- ✅ **Restrict pushes that create files larger than 100 MB**
- ✅ **Require signed commits**
- ✅ **Require linear history**
- ✅ **Include administrators** (admins must follow same rules)

### Merge Options
- ✅ **Allow merge commits**
- ✅ **Allow squash merging**
- ❌ **Allow rebase merging** (to maintain linear history)

## Development Branch Protection (develop)

If using a `develop` branch for integration:

### Required Status Checks
- ✅ **Require status checks to pass before merging**
- **Required status checks:**
  - `Quality Gate` (from test.yml workflow)
  - `Security Gate` (from security.yml workflow)

### Required Reviews
- **Required number of reviewers:** 1
- ✅ **Dismiss stale reviews when new commits are pushed**

## Implementation Steps

### 1. Enable Branch Protection via GitHub UI

1. Go to repository **Settings** > **Branches**
2. Click **Add rule** for `main` branch
3. Configure settings as outlined above
4. Repeat for `develop` branch if used

### 2. Alternative: Configure via GitHub CLI

```bash
# Main branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Quality Gate","Security Gate","Build Documentation"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null

# Develop branch protection (if using)
gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Quality Gate","Security Gate"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### 3. Create CODEOWNERS File

Create `.github/CODEOWNERS` to require specific team review:

```
# Global owners
* @reasoning-library/maintainers

# CI/CD workflows require additional security review
/.github/workflows/ @reasoning-library/maintainers @reasoning-library/security

# Security-related files
/pyproject.toml @reasoning-library/maintainers
/.github/dependabot.yml @reasoning-library/security
```

## Quality Gates Summary

The branch protection rules ensure that all changes to `main` must pass:

1. **Code Quality Gates**
   - ✅ Black formatting
   - ✅ isort import sorting
   - ✅ mypy type checking
   - ✅ 85%+ test coverage
   - ✅ All tests pass on Python 3.10-3.12
   - ✅ Multi-platform compatibility (Linux, macOS, Windows)

2. **Security Gates**
   - ✅ Dependency vulnerability scanning
   - ✅ Static application security testing
   - ✅ Supply chain security verification
   - ✅ License compliance checking

3. **Documentation Gates**
   - ✅ API documentation builds successfully
   - ✅ Documentation quality checks pass
   - ✅ No broken internal links

4. **Build Gates**
   - ✅ Package builds successfully
   - ✅ Installation verification
   - ✅ Import testing

## Workflow Integration

The branch protection rules integrate with the GitHub Actions workflows:

- **test.yml** provides the `Quality Gate` status check
- **security.yml** provides the `Security Gate` status check
- **docs.yml** provides the `Build Documentation` status check
- **release.yml** only runs on protected branches, ensuring quality

This configuration ensures that only thoroughly tested, secure, and documented code reaches the main branch, providing confidence for OSS release.