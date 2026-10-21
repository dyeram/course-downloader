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
    "Accounting": "ACCOUNTING_URL",
    "Foundations": "FOUNDATIONS_URL",
    "Valuation": "VALUATION_URL",
}
ALLOWED_HOST = "pages.stern.nyu.edu"
MAX_BYTES = 25 * 1024 * 1024


def allowed(url):
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == ALLOWED_HOST


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


def session_number(url, label, context):
    name = unquote(Path(urlparse(url).path).name)
    for text in (name, label, context):
        match = re.search(r"(?:session|sess|class|lecture|chapter|chap)\s*[-_ ]*(\d{1,2})", text, re.I)
        if match:
            return int(match.group(1))
    return None


def file_type(url, label, context):
    name = unquote(Path(urlparse(url).path).name).lower()
    desc = (label + " " + name).lower()
    if any(word in desc for word in ("solution", "answer", "soln")):
        return "solutions"
    if any(word in desc for word in ("test", "quiz", "postclass")):
        return "postclass_test"
    if any(word in desc for word in ("slide", "presentation", "handout", "notes")):
        return "slides"
    if "postclass" in url.lower() and "test" in url.lower():
        return "postclass_test"
    return "other"


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
    parser.add_argument("--dry-run", action="store_true", help="Preview without downloading or writing files")
    args = parser.parse_args()
    output = Path(os.environ.get("OUTPUT_DIR", "~/Downloads/Finance-Courses")).expanduser()
    courses = {name: os.environ.get(key) for name, key in COURSE_KEYS.items() if os.environ.get(key)}
    if not courses:
        parser.error("No course URLs found. Run with uv run --env-file .env ...")
    rows = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "CourseMaterialsDownloader/1.0"})
        for course, page_url in courses.items():
            if not allowed(page_url):
                print(f"Skipping {course}: URL is not on {ALLOWED_HOST}")
                continue
            print(f"\n{course}: {page_url}")
            try:
                response = session.get(page_url, timeout=30)
                response.raise_for_status()
                if not allowed(response.url):
                    raise ValueError("Course page redirected outside NYU")
                links = get_pdf_links(response.text, response.url)
            except (requests.RequestException, ValueError) as exc:
                print(f"  Could not read course page: {exc}")
                continue
            seen = set()
            for url, label, context in links:
                if url in seen:
                    continue
                seen.add(url)
                number = session_number(url, label, context)
                kind = file_type(url, label, context)
                folder = f"Session_{number:02d}" if number is not None else "Unclassified"
                # Retain the original filename to avoid overwriting distinct PDFs.
                basename = Path(unquote(urlparse(url).path)).name
                basename = re.sub(r"[^A-Za-z0-9._-]", "_", basename)
                dest = output / course / folder / basename
                if args.dry_run:
                    status = "exists" if dest.exists() else "would_download"
                else:
                    try:
                        status = download(session, url, dest)
                    except (requests.RequestException, OSError, ValueError) as exc:
                        status = f"error: {exc}"
                rows.append({"course": course, "session": folder, "type": kind,
                             "label": label, "url": url, "file": str(dest), "status": status})
                print(f"  [{status}] {folder}/{basename} ({kind})")
    if not args.dry_run:
        output.mkdir(parents=True, exist_ok=True)
        report = output / "download_report.csv"
        with report.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["course", "session", "type", "label", "url", "file", "status"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nReport: {report}")
    print(f"\nFound {len(rows)} PDF links. {'Preview only.' if args.dry_run else 'Finished.'}")


if __name__ == "__main__":
    main()
