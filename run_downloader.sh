#!/usr/bin/env bash

set -euo pipefail

# Always execute from the script's directory
cd "$(dirname "$0")"

run_tests() {
    uv run --env-file .env python -m unittest discover -s tests -v
}

dry_run() {
    uv run --env-file .env download_damodaran.py --dry-run
}

download() {
    uv run --env-file .env download_damodaran.py
}

case "${1:-}" in
    test)
        run_tests
        ;;
    dry-run)
        dry_run
        ;;
    download)
        download
        ;;
    all)
        run_tests
        dry_run

        read -r -p "Proceed with downloads? [y/N] " answer

        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
            download
        fi
        ;;
    *)
        echo "Usage: $0 {test|dry-run|download|all}"
        exit 1
        ;;
esac
