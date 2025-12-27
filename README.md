# Library Management System

A distributed library system with multiple servers and client processes.

## Structure
- `src/` - Source code
- `data/` - Data files (JSON, logs)
- `scripts/` - Helper scripts

## Usage
```bash
# From project root
python scripts/run_system.py clients/user1.txt clients/user2.txt ...

# Or directly
cd src
python -m main user1.txt user2.txt ...