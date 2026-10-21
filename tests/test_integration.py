import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import download_damodaran as downloader


class TestDownloaderIntegration(unittest.TestCase):

    def test_download_creates_folders_and_report(self):
        page_url = "https://pages.stern.nyu.edu/course.htm"

        slides_url = (
            "https://pages.stern.nyu.edu/"
            "valonlineslides/session1.pdf"
        )
        test_url = (
            "https://pages.stern.nyu.edu/"
            "valonlinetests/session1.pdf"
        )

        slides_bytes = b"%PDF-1.4\nslides content"
        test_bytes = b"%PDF-1.4\ntest and solutions content"

        html = """
        <a href="valonlineslides/session1.pdf">Slides</a>
        <a href="valonlinetests/session1.pdf">
            Post-class test & solution
        </a>
        """

        page = Mock()
        page.url = page_url
        page.text = html
        page.raise_for_status.return_value = None

        def make_pdf(url, content):
            response = Mock()
            response.url = url
            response.raise_for_status.return_value = None
            response.iter_content.return_value = iter([content])
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            return response

        slides = make_pdf(slides_url, slides_bytes)
        test = make_pdf(test_url, test_bytes)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "Finance-Courses"

            env = {
                "OUTPUT_DIR": str(output),
                "VALUATION_URL": page_url,
                "ALLOWED_HOSTS": "pages.stern.nyu.edu,www.stern.nyu.edu",
            }

            with (
                patch.dict(os.environ, env, clear=True),
                patch.object(
                    sys, "argv", ["download_damodaran.py"]
                ),
                patch.object(
                    downloader.requests, "Session"
                ) as session_factory,
            ):
                session = session_factory.return_value.__enter__.return_value
                session.get.side_effect = [page, slides, test]
                downloader.main()

            slides_file = output / "valuation" / "slides" / "session1.pdf"
            test_file = output / "valuation" / "postclass" / "session1.pdf"

            self.assertEqual(slides_file.read_bytes(), slides_bytes)
            self.assertEqual(test_file.read_bytes(), test_bytes)

            report = output / "download_report.csv"
            self.assertTrue(report.is_file())

            with report.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertTrue(
                all(row["status"] == "downloaded" for row in rows)
            )
            self.assertEqual(
                {row["type"] for row in rows},
                {"slides", "postclass"},
            )
            self.assertEqual(session.get.call_count, 3)


if __name__ == "__main__":
    unittest.main()
