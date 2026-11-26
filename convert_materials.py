#!/usr/bin/env python3
"""Convert and combine course materials into Markdown."""

import os
import re
from pathlib import Path

import pymupdf


def natural_key(path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def convert_pdfs(folder, destination):
    pdfs = sorted(folder.glob("*.pdf"), key=natural_key)

    if not pdfs:
        return

    with destination.open("w", encoding="utf-8") as out:
        for pdf in pdfs:
            out.write(f"\n\n# {pdf.stem}\n\n")

            with pymupdf.open(pdf) as doc:
                for page in doc:
                    out.write(page.get_text("text"))
                    out.write("\n\n")

    print(f"Converted {len(pdfs)} PDFs: {destination}")


def combine_transcripts(folder, destination):
    files = sorted(
        (
            file for file in folder.glob("*.md")
            if file != destination
        ),
        key=natural_key
    )

    if not files:
        return

    with destination.open("w", encoding="utf-8") as out:
        for file in files:
            out.write(f"\n\n# {file.stem}\n\n")
            out.write(file.read_text(encoding="utf-8"))

    print(f"Combined {len(files)} transcripts: {destination}")


def main():
    output = Path(os.environ["OUTPUT_DIR"]).expanduser()

    if not output.is_dir():
        raise NotADirectoryError(
            f"Invalid output directory: {output}"
        )

    for course in sorted(output.iterdir()):
        if not course.is_dir():
            continue

        name = course.name.replace("_", "-")

        slides = course / "slides"
        postclass = course / "postclass"
        transcripts = slides / "transcript"

        convert_pdfs(
            slides,
            slides / f"{name}-slides.md"
        )

        convert_pdfs(
            postclass,
            postclass / f"{name}-tests-and-solutions.md"
        )

        combine_transcripts(
            transcripts,
            transcripts / f"{name}-transcripts.md"
        )


if __name__ == "__main__":
    main()