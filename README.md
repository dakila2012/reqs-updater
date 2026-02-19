# reqs-updater

A production-ready CLI tool to parse `requirements.txt` files, fetch the latest PyPI versions for pinned packages (using `==`), and update them if newer versions are available. It preserves exact file formatting, including whitespace, comments, extras, markers, and line endings, with robust edge-case handling, concurrent PyPI fetches, dry-run mode, and graceful error exits for excellent UX.

## Installation

bash
git clone <repository-url>
cd reqs-updater
pip install requests packaging
## Usage

bash
# Show help
python src/main.py --help

# Update default requirements.txt
python src/main.py

# Dry-run update on specific file
python src/main.py requirements-dev.txt --dry-run
## Features

- Parses `requirements.txt` and identifies exactly pinned packages (`==` specifiers)
- Concurrently fetches latest versions from PyPI using `requests` and `ThreadPoolExecutor`
- Updates only if latest version is newer, preserving all formatting, extras (`[extra]`), markers (`; marker`), comments, and whitespace
- `--dry-run` mode to preview changes without modifying files
- Handles invalid lines, non-pinned specs, fetch errors, and file I/O issues without tracebacks

## Dependencies

- `requests` (HTTP requests to PyPI)
- `packaging` (requirement parsing and version comparison)
- `argparse`, `concurrent.futures` (Python stdlib)

## Tests

No tests.

## License

MIT