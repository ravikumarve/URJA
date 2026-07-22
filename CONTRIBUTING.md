# Contributing to URJA

Thank you for your interest in contributing to URJA!

## Code of Conduct

Be respectful, inclusive, and constructive. Disagreement is fine; personal attacks are not.

## How to Contribute

### Bug Reports & Feature Requests

Open a GitHub Issue with:
- **Bug**: Steps to reproduce, expected vs actual behavior, environment details
- **Feature**: Clear description of the problem you're solving, not just the solution

### Pull Requests

1. **Fork the repo** (if you don't have write access)
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Follow the coding standards** in [docs/development/GUIDELINES.md](docs/development/GUIDELINES.md)
4. **Write tests** — 90%+ coverage required for new code
5. **Run the test suite**: `pytest` (backend) + `npx playwright test` (frontend)
6. **Commit with conventional commits**:
   - `feat:` — New feature
   - `fix:` — Bug fix
   - `docs:` — Documentation
   - `refactor:` — Code restructuring
   - `test:` — Test additions/changes
   - `chore:` — Build/config changes
7. **Open a PR** against the `main` branch with a clear description

### PR Checklist

- [ ] Code follows GUIDELINES.md standards
- [ ] Tests pass and coverage >= 90%
- [ ] No lint errors (ruff + ESLint)
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md entry added

## Questions?

Open a Discussion on GitHub or email the maintainer.
