# Hypr-Voice

Multi-agent voice orchestration system with Claude AI integration.

## Quick Start

```bash
# Install dependencies
npm run install:all

# Start the system
npm run start
```

## Project Structure

```
Hypr-Voice/
├── src/                      # Python source code
│   └── hypr_voice/          # Main package
├── frontend/                 # Web UI (Next.js 13+)
│   └── app/
├── config/                   # Configuration files
│   └── hypr_voice/
├── runtime/                  # Runtime data (logs, audio, databases)
├── scripts/                  # Utility scripts
├── tests/                    # Test suite
└── docs/                     # Documentation
    ├── user/                # End-user guides
    ├── development/         # Developer docs
    ├── operations/          # Deployment & monitoring
    ├── web-ui/              # Frontend documentation
    ├── plans/               # Implementation plans
    └── archive/             # Completed feature notes
```

## Configuration

Main configuration: `config/hypr_voice/config.yaml`

## Documentation

- [User Guide](docs/user/)
- [Development](docs/development/)
- [Operations](docs/operations/)
- [Web UI](docs/web-ui/)
- [API Reference](docs/api/)

## Environment Setup

```bash
# Python virtual environment (created automatically)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd web-ui && npm install
```

## License

Proprietary - All rights reserved
