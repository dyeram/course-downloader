import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import download_damodaran as downloader


class TestDownloaderIntegration(unittest.TestCase):
    def test_download_creates_session_folder_and_report(self):
        page_url = "https://pages.stern.nyu.edu/course.htm"
        pdf_url = "https://pages.stern.nyu.edu/session5test.pdf"
        pdf_bytes = b"%PDF-1.4\nexample PDF contents"
        html = '<a href="session5test.pdf">Session 5 Test</a>'

        page = Mock()
        page.url = page_url
        page.text = html
        page.raise_for_status.return_value = None

        pdf = Mock()
        pdf.url = pdf_url
        pdf.raise_for_status.return_value = None
        pdf.iter_content.return_value = iter([pdf_bytes])
        pdf.__enter__ = Mock(return_value=pdf)
        pdf.__exit__ = Mock(return_value=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "Finance-Courses"
            env = {
                "OUTPUT_DIR": str(output),
                "ACCOUNTING_URL": page_url,
            }
            with patch.dict(os.environ, env, clear=True), \
                 patch.object(sys, "argv", ["download_damodaran.py"]), \
                 patch.object(downloader.requests, "Session") as session_factory:
                session = session_factory.return_value.__enter__.return_value
                session.get.side_effect = [page, pdf]
                downloader.main()

            saved_pdf = output / "Accounting" / "Session_05" / "session5test.pdf"
            self.assertEqual(saved_pdf.read_bytes(), pdf_bytes)

            report = output / "download_report.csv"
            self.assertTrue(report.is_file())
            with report.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "downloaded")
            self.assertEqual(rows[0]["session"], "Session_05")
            self.assertEqual(session.get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
