---
description: Repository Information Overview
alwaysApply: true
---

# AIO-Conf Information

## Summary
AIO-Conf is a minimal configuration system that merges configuration from CLI arguments, environment variables, config files, and defaults. Configuration specs can be defined in JSON and loaded with `AIOConfig`.

## Structure
- **src/aio_conf/**: Main package source code
  - **core.py**: Core implementation with `AIOConfig`, `ConfigSpec`, and `OptionSpec` classes
  - **loader.py**: Configuration loading functionality
  - **writer.py**: Configuration writing/saving functionality
  - **Developer_Toolkit/**: Development utilities for the package
- **tests/**: Test files for the package
- **.github/workflows/**: CI/CD configuration

## Language & Runtime
**Language**: Python
**Version**: Python 3.12+
**Build System**: Poetry
**Package Manager**: Poetry

## Dependencies
**Main Dependencies**:
- pyyaml >= 6.0
- streamlit >= 1.47.1, < 2.0.0
- pysimplegui-4-foss == 4.60.4.1

**Development Dependencies**:
- pytest (implied from workflow)

## Build & Installation
```bash
# Install dependencies
pip install poetry
poetry install

# Build package
poetry build
```

## Testing
**Framework**: pytest
**Test Location**: tests/
**Naming Convention**: test_*.py
**Run Command**:
```bash
poetry run pytest -q
```

## CI/CD
**Workflow**: GitHub Actions
**Configuration**: .github/workflows/python.yml
**Python Version**: 3.12
**Steps**:
1. Checkout code
2. Setup Python 3.12
3. Install dependencies with Poetry
4. Run tests with pytest