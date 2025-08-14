# Hypr-Voice Developer Documentation

## Contribution Workflow

```mermaid
graph LR
    A[Fork Repository] --> B[Create Feature Branch]
    B --> C[Implement Changes]
    C --> D[Run Tests]
    D --> E[Submit PR]
    E --> F{Code Review}
    F -->|Approved| G[Merge to Main]
    F -->|Revisions Needed| B
    G --> H[Release Process]
    
    style A fill:#2e7d32,stroke:#4CAF50
    style H fill:#1565c0,stroke:#1976D2
```

## Code Style Guidelines

- Python PEP8 compliance enforced via flake8
- Type hints required for all function signatures  
- Docstrings using Google style format
- 120 character line limit

## Testing Requirements

```mermaid
pie title Test Coverage
    "Unit Tests" : 65
    "Integration Tests" : 25
    "System Tests" : 10
```

## Release Process

1. Update version in `pyproject.toml`
2. Run changelog generator: `cz changelog`
3. Create signed tag: `cz bump --check-consistency`
4. Push tag to trigger CI/CD pipeline