
import unittest

from download_damodaran import (
    allowed,
    get_pdf_links,
    session_number,
    file_type,
)


class TestDownloader(unittest.TestCase):

    def test_allowed_urls(self):
        self.assertTrue(
            allowed("https://pages.stern.nyu.edu/course.pdf")
        )
        self.assertFalse(
            allowed("https://example.com/course.pdf")
        )
        self.assertFalse(
            allowed("http://pages.stern.nyu.edu/course.pdf")
        )

    def test_pdf_link_extraction(self):
        html = """
        <a href="session5slides.pdf">Lecture slides</a>
        <a href="session5test.pdf">Post-class test</a>
        <a href="video.mp4">Watch video</a>
        """

        links = get_pdf_links(
            html,
            "https://pages.stern.nyu.edu/course/",
        )

        self.assertEqual(len(links), 2)
        self.assertTrue(links[0][0].endswith("session5slides.pdf"))
        self.assertTrue(links[1][0].endswith("session5test.pdf"))

    def test_session_identification(self):
        url = "https://pages.stern.nyu.edu/session5test.pdf"

        self.assertEqual(
            session_number(url, "Test", "Session 5"),
            5,
        )
        self.assertEqual(
            session_number(url, "Test", "Session 8"),
            5,
        )
        self.assertIsNone(
            session_number(
                "https://pages.stern.nyu.edu/test.pdf",
                "Test",
                "No session information",
            )
        )

    def test_file_classification(self):
        base = "https://pages.stern.nyu.edu/"

        cases = {
            "session5slides.pdf": "slides",
            "session5test.pdf": "postclass_test",
            "session5solutions.pdf": "solutions",
            "session5reading.pdf": "other",
        }

        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                result = file_type(
                    base + filename, filename, ""
                )
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
