#!/usr/bin/env bash

set -euo pipefail

# Always execute from the script's directory
cd "$(dirname "$0")"

run_tests() {
    uv run --env-file .env python -m unittest discover -s tests -v
}

dry_run() {
    uv run --env-file .env download_pdfs.py --dry-run
}

download() {
    uv run --env-file .env download_pdfs.py
}

convert() {
    uv run --env-file .env convert_materials.py
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
    convert)
        convert
        ;;
    all)
        run_tests
        dry_run

        read -r -p "Proceed with downloads and conversion? [y/N] " answer

        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
            download
            convert
        else
            echo "Operation cancelled."
        fi
        ;;
    *)
        echo "Usage: $0 {test|dry-run|download|convert|all}"
        exit 1
        ;;
esac