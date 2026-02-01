# Contributing Guidelines

Thank you for your interest in contributing to Hypr-Voice! This document outlines how to contribute to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Contribution Workflow](#contribution-workflow)
3. [Types of Contributions](#types-of-contributions)
4. [Code Review Process](#code-review-process)
5. [Commit Conventions](#commit-conventions)
6. [Pull Request Guidelines](#pull-request-guidelines)
7. [Community Guidelines](#community-guidelines)
8. [Getting Help](#getting-help)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Read the [Development Setup](setup.md) guide
- Set up your development environment
- Familiarized yourself with the [Code Structure](code-structure.md)
- Reviewed the [Coding Standards](coding-standards.md)
- Understood the [Testing Guide](testing.md)

### First-Time Setup

```bash
# 1. Fork the repository
# Click "Fork" on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/Hypr-Voice.git
cd Hypr-Voice

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/Hypr-Voice.git

# 4. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all]"

# 5. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 6. Run tests to verify setup
pytest
```

## Contribution Workflow

### 1. Find an Issue

- Browse [GitHub Issues](https://github.com/yourusername/Hypr-Voice/issues)
- Look for issues labeled `good first issue` for beginners
- Check `help wanted` for areas needing assistance
- Comment on the issue to claim it

### 2. Create a Branch

```bash
# Ensure you're on main and up-to-date
git checkout main
git fetch upstream
git rebase upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-brief-description

# Examples
git checkout -b feature/add-gemini-integration
git checkout -b fix/123-whisper-timeout-error
```

### 3. Make Changes

```bash
# Make your changes
# Edit files, add features, fix bugs, etc.

# Format your code
black src/ tests/
isort src/ tests/

# Run linters
flake8 src/ tests/
mypy src/

# Run tests
pytest

# Run with coverage
pytest --cov=src/hypr_voice --cov-report=term-missing
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(voice): add ElevenLabs provider support

Implement ElevenLabs API integration with fallback to Kokoro.
Includes tests and documentation.

Closes #123"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Click "Compare & pull request" button
```

### 6. Address Review Feedback

- Respond to all review comments
- Make requested changes
- Push updates to branch
- Request re-review when ready

## Types of Contributions

### Bug Fixes

**High Priority**:
- Critical issues affecting functionality
- Security vulnerabilities
- Data loss or corruption bugs

**Process**:
1. Create issue with bug report template
2. Link issue in PR
3. Add test case that reproduces bug
4. Fix the bug
5. Ensure test passes

**Example PR Title**:
```
fix(tts): handle empty text gracefully without crashing

Fixes #156 - Currently crashes when empty text is passed to
TTS synthesis. Now raises ValueError with helpful message.
```

### Features

**Process**:
1. Open issue with feature proposal
2. Get feedback from maintainers
3. Create design document if complex
4. Implement with tests
5. Update documentation

**Example PR Title**:
```
feat(agents): add Gemini Live integration for multimodal agents

Implements Google Gemini Live API for multimodal AI agents.
Includes screen capture, voice interaction, and context awareness.

Closes #89
```

### Documentation

**Types**:
- Fixing typos or errors
- Adding examples
- Improving clarity
- Adding API documentation
- Creating tutorials

**Example PR Title**:
```
docs(api): add WebSocket endpoint documentation

Add comprehensive documentation for WebSocket API including
connection handling, message format, and error codes.
```

### Performance Improvements

**Process**:
1. Benchmark current performance
2. Profile bottlenecks
3. Implement optimization
4. Show performance gains with metrics
5. Ensure no behavior changes

**Example PR Title**:
```
perf(tts): implement streaming synthesis to reduce latency

Reduce perceived latency from 5s to 1s for long texts by
streaming audio chunks while generating. Benchmarks show
5x improvement for texts >500 characters.

Refs #201
```

### Refactoring

**Guidelines**:
- No behavior changes
- Improve code organization
- Enhance readability
- Reduce complexity

**Example PR Title**:
```
refactor(orchestrator): simplify context management logic

Remove redundant state tracking and use single source of truth.
Improves maintainability and reduces bug surface area.
```

### Tests

**Types**:
- Increase test coverage
- Add integration tests
- Fix broken tests
- Improve test reliability

**Example PR Title**:
```
test(whisper): add integration tests for enhanced vocabulary

Add comprehensive tests for vocabulary enhancement feature
including edge cases and error handling.
```

## Code Review Process

### For Contributors

1. **Self-Review**:
   - Review your own code first
   - Ensure all tests pass
   - Check formatting and linting
   - Verify documentation is updated

2. **Request Review**:
   - Assign relevant reviewers
   - Add appropriate labels
   - Link related issues

3. **Address Feedback**:
   - Respond to all comments
   - Explain your reasoning if disagreeing
   - Make requested changes promptly
   - Mark conversations as resolved

4. **Iterate**:
   - Push updates to branch
   - Request re-review when ready
   - Address additional feedback

### For Reviewers

**What to Check**:
- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No hardcoded credentials
- [ ] Error handling appropriate
- [ ] Performance considered
- [ ] Security reviewed
- [ ] Backward compatibility maintained

**Review Guidelines**:
- Be constructive and respectful
- Explain reasoning for suggestions
- Approve if changes are good enough (not perfect)
- Request changes only if necessary

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes

### Scopes

Common scopes:
- `agents`: Agent system
- `voice`: TTS/STT services
- `orchestrator`: Orchestration layer
- `api`: API endpoints
- `docs`: Documentation
- `tests`: Test suite
- `config`: Configuration

### Examples

```bash
# Feature
feat(agents): add context-aware agent with screen capture

Implement EnhancedContextAgent that can capture and analyze
screen content for better context awareness.

Closes #45

# Bug fix
fix(tts): prevent audio cutoff in long synthesis

Add audio padding to prevent premature cutoff when synthesizing
long texts (>1000 characters).

Fixes #78

# Documentation
docs(api): add WebSocket authentication guide

Add step-by-step guide for WebSocket authentication including
token generation and refresh flow.

# Refactoring
refactor(whisper): simplify vocabulary loading logic

Extract vocabulary loading into separate module for better
testability and maintainability.

# Performance
perf(orchestrator): implement request caching

Add LRU cache for frequent requests. Reduces API calls by 60%
for repeated queries.

Benchmarks:
- Before: 1000 API calls for 1000 repeated queries
- After: 400 API calls for 1000 repeated queries

# Test
test(integration): add WebSocket integration tests

Add comprehensive integration tests for WebSocket connection,
message handling, and error scenarios.

# Chore
chore(deps): upgrade anthropic package to 0.8.0

Upgrade to latest version for improved performance and
new features.
```

## Pull Request Guidelines

### PR Title

Follow conventional commits format:

```
feat(scope): brief description
fix(scope): brief description
docs(scope): brief description
```

**Good Examples**:
```
feat(voice): add streaming synthesis support
fix(whisper): handle timeout errors gracefully
docs(contributing): add performance section
```

**Bad Examples**:
```
Add new feature
Fix bug
Update docs
```

### PR Description Template

```markdown
## Summary
Brief description of changes (1-2 sentences).

## Changes
- Added feature X
- Fixed bug Y
- Updated documentation

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass

## Checklist
- [ ] Code follows style guide
- [ ] Self-review performed
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Commits follow convention

## Related Issues
Closes #123
Fixes #456
Related to #789

## Screenshots (if applicable)
[Add screenshots/gifs for UI changes]

## Additional Notes
[Any additional context or considerations]
```

### PR Labels

**Type Labels**:
- `bug`: Bug fixes
- `enhancement`: New features
- `documentation`: Documentation changes
- `performance`: Performance improvements
- `refactoring`: Code refactoring

**Status Labels**:
- `wip`: Work in progress
- `ready-for-review`: Ready for review
- `needs-changes`: Needs changes
- `approved`: Approved

**Priority Labels**:
- `critical`: Urgent fixes
- `high`: High priority
- `medium`: Medium priority
- `low`: Low priority

### Review Process

1. **Automated Checks**:
   - All tests must pass
   - Code must be formatted
   - Coverage must not decrease

2. **Code Review**:
   - At least one approval required
   - All review comments addressed
   - No outstanding requests for changes

3. **Integration**:
   - Maintainer squashes commits
   - Merged to main branch
   - Issue closed automatically

## Community Guidelines

### Code of Conduct

**Be Respectful**:
- Use inclusive language
- Respect different viewpoints
- Give constructive feedback
- Assume good intentions

**Be Collaborative**:
- Work together openly
- Share knowledge freely
- Help others learn
- Welcome newcomers

**Be Professional**:
- Keep discussions focused
- Stay on topic
- Avoid personal attacks
- Follow issue templates

### Communication

**GitHub Discussions**:
- Use for questions and ideas
- Feature proposals
- Architecture discussions
- Help requests

**GitHub Issues**:
- Bug reports
- Specific feature requests
- Documentation issues
- Performance problems

**Pull Requests**:
- Code changes
- Bug fixes
- Feature implementation
- Documentation updates

### Conflict Resolution

1. **Disagreements**:
   - Focus on what is best for the project
   - Consider technical merits
   - Seek compromise
   - Escalate to maintainers if needed

2. **Blockers**:
   - Discuss in issue comments
   - Schedule sync meeting if needed
   - Maintainer makes final decision

## Getting Help

### Resources

- [Documentation](../)
- [API Reference](../api/)
- [Examples](../examples/)
- [Issues](https://github.com/yourusername/Hypr-Voice/issues)
- [Discussions](https://github.com/yourusername/Hypr-Voice/discussions)

### Asking Questions

1. **Search First**:
   - Check existing issues
   - Read documentation
   - Search discussions

2. **Provide Context**:
   - What are you trying to do?
   - What have you tried?
   - What error did you get?
   - Environment details

3. **Use Templates**:
   - Bug reports: Use bug template
   - Features: Use feature template
   - Questions: Use question template

### Reporting Issues

**Bug Report Template**:
```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to...
2. Click on...
3. Scroll down to...
4. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS:
- Python version:
- Hypr-Voice version:

**Logs**
```
Paste relevant logs here
```
```

**Feature Request Template**:
```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives**
What other approaches did you consider?

**Additional Context**
Any other relevant information
```

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- Project README for major contributors

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Next Steps

- Set up your [Development Environment](setup.md)
- Review [Coding Standards](coding-standards.md)
- Learn [Testing Practices](testing.md)
- Find [Good First Issues](https://github.com/yourusername/Hypr-Voice/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

## Resources

- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)

Thank you for contributing to Hypr-Voice!
