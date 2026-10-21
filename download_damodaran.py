#!/usr/bin/env python3
"""Download linked course PDFs into course/session folders.

Configuration is read from environment variables (e.g. uv run --env-file .env).
"""
import argparse
import csv
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

COURSE_KEYS = {
    "accounting": "ACCOUNTING_URL",
    "foundations": "FOUNDATIONS_URL",
    "valuation": "VALUATION_URL",
}

ALLOWED_HOSTS = {
    host.strip().lower()
    for host in os.environ["ALLOWED_HOSTS"].split(",")
}

MAX_BYTES = 25 * 1024 * 1024

def allowed(url):
    parsed = urlparse(url)
    print("URL:", repr(url))
    print("Scheme:", repr(parsed.scheme))
    print("Hostname:", repr(parsed.hostname))
    print("Allowed host:", repr(ALLOWED_HOSTS))
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def get_pdf_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for anchor in soup.select("a[href]"):
        url = urljoin(base_url, anchor["href"].strip())
        if not allowed(url) or not urlparse(url).path.lower().endswith(".pdf"):
            continue
        label = anchor.get_text(" ", strip=True)
        parent = anchor.find_parent("tr")
        context = parent.get_text(" ", strip=True) if parent else label
        found.append((url, label, context))
    return found


def file_type(url, label, context):
    path = urlparse(url).path.lower()

    if "slides" in path:
        return "slides"
    if "postclass" in path or "tests" in path:
        return "postclass"
    return "miscellaneous"


def download(session, url, dest):
    if dest.exists():
        return "exists"
    with session.get(url, timeout=30, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        if not allowed(response.url):
            raise ValueError("Redirected outside permitted NYU domain")
        content = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            content.extend(chunk)
            if len(content) > MAX_BYTES:
                raise ValueError("PDF exceeds 25 MB limit")
        if not content.startswith(b"%PDF-"):
            raise ValueError("Response is not a PDF")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as out:
            out.write(content)
    return "downloaded"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without downloading or writing files",
    )
    args = parser.parse_args()

    output = Path(
        os.environ.get("OUTPUT_DIR", "~/Downloads/Finance-Courses")
    ).expanduser()

    courses = {
        name: os.environ[key]
        for name, key in COURSE_KEYS.items()
        if os.environ.get(key)
    }

    if not courses:
        parser.error("No course URLs configured in environment")

    rows = []

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "CourseMaterialsDownloader/1.0"
        })

        for course, page_url in courses.items():
            if not allowed(page_url):
                print(f"Skipping {course}: URL not on allowed hosts")
                continue

            print(f"\n{course}: {page_url}")

            try:
                response = session.get(page_url, timeout=30)
                response.raise_for_status()

                if not allowed(response.url):
                    raise ValueError(
                        "Course page redirected outside allowed hosts"
                    )

                links = get_pdf_links(response.text, response.url)

            except (requests.RequestException, ValueError) as exc:
                print(f"Could not read {course}: {exc}")
                continue

            seen = set()

            for url, label, context in links:
                if url in seen:
                    continue

                seen.add(url)

                folder = file_type(url, label, context)

                if course == "valuation" and folder == "miscellaneous":
                    folder = "valuation-tools"

                basename = Path(unquote(urlparse(url).path)).name
                basename = re.sub(
                    r"[^A-Za-z0-9._-]", "_", basename
                )

                dest = output / course / folder / basename

                if args.dry_run:
                    status = (
                        "exists" if dest.exists()
                        else "would_download"
                    )
                else:
                    try:
                        status = download(session, url, dest)
                    except (
                        requests.RequestException,
                        OSError,
                        ValueError,
                    ) as exc:
                        status = f"error: {exc}"

                rows.append({
                    "course": course,
                    "type": folder,
                    "label": label,
                    "url": url,
                    "file": str(dest),
                    "status": status,
                })

                print(
                    f"  [{status}] "
                    f"{folder}/{basename}"
                )

    if not args.dry_run:
        output.mkdir(parents=True, exist_ok=True)
        report = output / "download_report.csv"

        with report.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "course",
                    "type",
                    "label",
                    "url",
                    "file",
                    "status",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

        print(f"\nReport: {report}")

    print(
        f"\nFound {len(rows)} PDF links. "
        f"{'Preview only.' if args.dry_run else 'Finished.'}"
    )


if __name__ == "__main__":
    main()
