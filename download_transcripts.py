#!/usr/bin/env python3
"""Download YouTube transcripts for Damodaran's courses."""

import argparse
import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from download_pdfs import COURSE_KEYS

def get_video_id(url):
    """Extract a YouTube video ID from a URL."""
    parsed = urlparse(url)

    if parsed.hostname == "youtu.be":
        video_id = parsed.path.strip("/")

    elif parsed.hostname in (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    ):
        video_id = parse_qs(parsed.query).get("v", [""])[0]

    else:
        return None

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return video_id

    return None


def get_session_id(label):
    label = label.strip().lower()

    if label in ("preview", "intro", "introduction", "0"):
        return "0"

    match = re.fullmatch(r"(?:session\s+)?(\d+[a-z]?)", label)

    if match:
        return match.group(1).upper()

    return None
    

def get_video_links(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    video_links = []
    seen = set()

    for link in soup.find_all("a", href=True):
        video_id = get_video_id(link["href"])

        if not video_id or video_id in seen:
            continue

        row = link.find_parent("tr")
        first_cell = row.find(["td", "th"]) if row else None

        label = first_cell.get_text(strip=True) if first_cell else ""
        session = get_session_id(label)

        if session is None:
            print(f"Warning: Unrecognised session: {label!r}")
            continue

        video_links.append((session, video_id))
        seen.add(video_id)

    return video_links


def download_transcript(api, video_id):
    """Retrieve a transcript without timestamps."""
    transcript = api.fetch(video_id, languages=["en"])
    return TextFormatter().format_transcript(transcript)


def has_transcript(path):
    """Check whether a file contains more than a heading."""
    if not path.exists():
        return False

    lines = path.read_text(encoding="utf-8").splitlines()

    return any(
        line.strip()
        for line in lines
        if not line.startswith("# ")
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output = Path(os.environ["OUTPUT_DIR"]).expanduser()
    api = YouTubeTranscriptApi()

    for course, env_key in COURSE_KEYS.items():
        url = os.environ[env_key]
        course_title = course.replace("_", " ").title()

        folder = output / course / "slides" / "transcript"

        video_links = get_video_links(url)

        print(f"\n{course_title}: {len(video_links)} videos")

        if not args.dry_run:
            folder.mkdir(parents=True, exist_ok=True)

        for session, video_id in video_links:
            destination = folder / f"session{session}.md"

            heading = (
                "Introduction" if session == "0"
                else f"Session {session}"
            )

            if args.dry_run:
                print(f"{destination.name}: {video_id} ({heading})")
                continue

            if has_transcript(destination):
                print(f"Skipped: {destination.name}")
                continue

            try:
                text = download_transcript(api, video_id)

                destination.write_text(
                    f"# {course_title}: {heading}\n\n"
                    f"{text}\n",
                    encoding="utf-8",
                )

                print(f"Downloaded: {destination.name}")

            except Exception as error:
                print(f"Failed: {video_id}: {error}")


if __name__ == "__main__":
    main()