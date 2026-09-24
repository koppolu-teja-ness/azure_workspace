# Developer Setup

## One-command bootstrap

Run:

```powershell
./scripts/bootstrap.ps1
```

This script performs the following steps:
- Creates `.venv`
- Installs project and dev dependencies
- Verifies pinned versions for Python, `az`, Bicep, `cfn-lint`, and `checkov`

## Manual fallback

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Validation commands

```powershell
python scripts/validate_phase0.py
pytest
ruff check .
mypy src
```
