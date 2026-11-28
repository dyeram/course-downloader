import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from download_transcripts import (
    get_video_id,
    get_session_id,
    get_video_links,
    download_transcript,
    has_transcript,
)


class TestTranscriptDownloader(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.folder = Path(self.temp_dir.name)

    def test_standard_youtube_url(self):
        url = "https://www.youtube.com/watch?v=qofdyX0vudk"
        self.assertEqual(get_video_id(url), "qofdyX0vudk")

    def test_short_youtube_url(self):
        url = "https://youtu.be/qofdyX0vudk"
        self.assertEqual(get_video_id(url), "qofdyX0vudk")

    def test_youtube_playlist_url(self):
        url = "https://youtu.be/qofdyX0vudk?list=ABC&index=9"
        self.assertEqual(get_video_id(url), "qofdyX0vudk")

    def test_invalid_video_id(self):
        url = "https://youtu.be/invalid"
        self.assertIsNone(get_video_id(url))

    def test_non_youtube_url(self):
        url = "https://example.com/watch?v=qofdyX0vudk"
        self.assertIsNone(get_video_id(url))

    def test_get_session_id_numeric(self):
        self.assertEqual(get_session_id("1"), "1")
        self.assertEqual(get_session_id("12"), "12")

    def test_get_session_id_alphanumeric(self):
        self.assertEqual(get_session_id("2A"), "2A")
        self.assertEqual(get_session_id("2b"), "2B")

    def test_get_session_id_introduction(self):
        self.assertEqual(get_session_id("Intro"), "0")
        self.assertEqual(get_session_id("Preview"), "0")
        self.assertEqual(get_session_id("Introduction"), "0")

    def test_get_session_id_whitespace(self):
        self.assertEqual(get_session_id(" 2A "), "2A")

    def test_get_session_id_invalid(self):
        self.assertIsNone(get_session_id("Unknown"))
        self.assertIsNone(get_session_id(""))

    @patch("download_transcripts.requests.get")
    def test_video_links_order_and_duplicates(self, mock_get):
        mock_get.return_value.text = """
        <table>
            <tr>
                <td>Preview</td>
                <td><a href="https://youtu.be/abcdefghijk">Video</a></td>
            </tr>
            <tr>
            <td>1</td>
            <td><a href="https://youtu.be/lmnopqrstuv">Video</a></td>
            </tr>
            <tr>
            <td>2A</td>
            <td><a href="https://youtu.be/12345678901">Video</a></td>
            </tr>
        </table>
        """

        result = get_video_links("https://example.com")

        self.assertEqual(result, [
            ("0", "abcdefghijk"),
            ("1", "lmnopqrstuv"),
            ("2A", "12345678901"),
        ])

        mock_get.assert_called_once()

    @patch("download_transcripts.requests.get")
    def test_no_video_links(self, mock_get):
        mock_get.return_value.text = """
        <html>
            <a href="slides.pdf">Slides</a>
        </html>
        """

        self.assertEqual(
            get_video_links("https://example.com"),
            []
        )

    @patch("download_transcripts.TextFormatter")
    def test_download_transcript(self, mock_formatter):
        api = Mock()

        mock_formatter.return_value.format_transcript.return_value = (
            "Example transcript text."
        )

        result = download_transcript(api, "qofdyX0vudk")

        api.fetch.assert_called_once_with(
            "qofdyX0vudk",
            languages=["en"]
        )

        mock_formatter.return_value.format_transcript.assert_called_once_with(
            api.fetch.return_value
        )

        self.assertEqual(result, "Example transcript text.")

    def test_missing_transcript(self):
        path = self.folder / "session1.md"
        self.assertFalse(has_transcript(path))

    def test_empty_transcript(self):
        path = self.folder / "session1.md"
        path.write_text("", encoding="utf-8")

        self.assertFalse(has_transcript(path))

    def test_transcript_placeholder(self):
        path = self.folder / "session1.md"
        path.write_text(
            "# Corporate Finance: session 1\n\n",
            encoding="utf-8"
        )

        self.assertFalse(has_transcript(path))

    def test_completed_transcript(self):
        path = self.folder / "session1.md"
        path.write_text(
            "# Corporate Finance: session 1\n\n"
            "Example transcript content.",
            encoding="utf-8"
        )

        self.assertTrue(has_transcript(path))


if __name__ == "__main__":
    unittest.main()