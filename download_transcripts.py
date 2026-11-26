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


def get_video_links(url):
    """Extract unique video IDs in webpage order."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    video_ids = []

    for link in soup.find_all("a", href=True):
        video_id = get_video_id(link["href"])

        if video_id and video_id not in video_ids:
            video_ids.append(video_id)

    return video_ids


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

        video_ids = get_video_links(url)

        print(f"\n{course_title}: {len(video_ids)} videos")

        if not args.dry_run:
            folder.mkdir(parents=True, exist_ok=True)

        for session, video_id in enumerate(video_ids, start=1):
            destination = folder / f"session{session}.md"

            if args.dry_run:
                print(f"{destination.name}: {video_id}")
                continue

            if has_transcript(destination):
                print(f"Skipped: {destination.name}")
                continue

            try:
                text = download_transcript(api, video_id)

                destination.write_text(
                    f"# {course_title}: session {session}\n\n"
                    f"{text}\n",
                    encoding="utf-8",
                )

                print(f"Downloaded: {destination.name}")

            except Exception as error:
                print(f"Failed: {video_id}: {error}")


if __name__ == "__main__":
    main()