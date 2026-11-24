import unittest

from download_damodaran import allowed, get_pdf_links, file_type


class TestDownloader(unittest.TestCase):

    def test_allowed_urls(self):
        self.assertTrue(
            allowed("https://pages.stern.nyu.edu/course.pdf")
        )
        self.assertTrue(
            allowed("https://www.stern.nyu.edu/course.pdf")
        )
        self.assertFalse(
            allowed("https://example.com/course.pdf")
        )
        self.assertFalse(
            allowed("http://pages.stern.nyu.edu/course.pdf")
        )

    def test_pdf_link_extraction(self):
        html = """
        <a href="/~adamodar/pdfiles/valonlineslides/session1.pdf">
            Slides
        </a>
        <a href="/~adamodar/pdfiles/valonlinetests/session1.pdf">
            Post-class test & solution
        </a>
        <a href="https://youtu.be/example">Watch video</a>
        """

        links = get_pdf_links(
            html,
            "https://www.stern.nyu.edu/course/",
        )

        self.assertEqual(len(links), 2)

        self.assertTrue(
            links[0][0].endswith("valonlineslides/session1.pdf")
        )
        self.assertTrue(
            links[1][0].endswith("valonlinetests/session1.pdf")
        )

    def test_file_classification(self):
        base = "https://www.stern.nyu.edu/~adamodar/pdfiles/"

        cases = {
            "valonlineslides/session1.pdf": "slides",
            "valonlinetests/session1.pdf": "postclass",
            "Accounting101/postclass/session1.pdf": "postclass",
            "valuationtools/problem1.pdf": "supplementary",
        }

        for path, expected in cases.items():
            with self.subTest(path=path):
                result = file_type(base + path, "", "")
                self.assertEqual(result, expected)

    def test_get_pdf_links_skips_empty_labels(self):
        html = """
        <html>
            <body>
                <a href="/~adamodar/pdfiles/acf4E/webcastslides/session1.pdf"></a>
                <a href="/~adamodar/pdfiles/valonlineslides/session1.pdf">Slides</a>
            </body>
        </html>
        """

        base_url = "https://www.stern.nyu.edu/~adamodar/New_Home_Page/webcastvalonline.htm"

        links = get_pdf_links(html, base_url)

        self.assertEqual(len(links), 1)
        self.assertEqual(
            links[0][0],
            "https://www.stern.nyu.edu/~adamodar/pdfiles/valonlineslides/session1.pdf",
        )
        self.assertEqual(links[0][1], "Slides")

if __name__ == "__main__":
    unittest.main()
