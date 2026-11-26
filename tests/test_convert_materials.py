import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from convert_materials import (
    natural_key,
    convert_pdfs,
    combine_transcripts,
    main,
)


class TestConvertMaterials(unittest.TestCase):

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)

    def create_pdf(self, filename, text):
        path = self.folder / filename

        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((50, 50), text)
            doc.save(path)

        return path

    def test_natural_sorting(self):
        files = [
            Path("session10.pdf"),
            Path("session2.pdf"),
            Path("session1.pdf"),
        ]

        result = sorted(files, key=natural_key)

        self.assertEqual(
            [file.name for file in result],
            ["session1.pdf", "session2.pdf", "session10.pdf"],
        )

    def test_pdf_conversion(self):
        self.create_pdf("session1.pdf", "Introduction to finance")
        destination = self.folder / "slides.md"

        convert_pdfs(self.folder, destination)

        self.assertTrue(destination.exists())

        content = destination.read_text(encoding="utf-8")

        self.assertIn("# session1", content)
        self.assertIn("Introduction to finance", content)

    def test_pdf_merging(self):
        self.create_pdf("session10.pdf", "Lecture ten")
        self.create_pdf("session2.pdf", "Lecture two")

        destination = self.folder / "slides.md"

        convert_pdfs(self.folder, destination)

        content = destination.read_text(encoding="utf-8")

        self.assertIn("Lecture two", content)
        self.assertIn("Lecture ten", content)
        self.assertLess(
            content.index("Lecture two"),
            content.index("Lecture ten"),
        )

    def test_empty_pdf_directory(self):
        destination = self.folder / "slides.md"

        convert_pdfs(self.folder, destination)

        self.assertFalse(destination.exists())

    def test_combine_transcripts(self):
        (self.folder / "session10.md").write_text(
            "Lecture ten", encoding="utf-8"
        )
        (self.folder / "session2.md").write_text(
            "Lecture two", encoding="utf-8"
        )

        destination = self.folder / "transcripts.md"

        combine_transcripts(self.folder, destination)

        content = destination.read_text(encoding="utf-8")

        self.assertIn("Lecture two", content)
        self.assertIn("Lecture ten", content)
        self.assertLess(
            content.index("Lecture two"),
            content.index("Lecture ten"),
        )

    def test_repeated_transcript_conversion(self):
        (self.folder / "session1.md").write_text(
            "First lecture", encoding="utf-8"
        )

        destination = self.folder / "transcripts.md"

        combine_transcripts(self.folder, destination)
        original = destination.read_text(encoding="utf-8")

        combine_transcripts(self.folder, destination)
        repeated = destination.read_text(encoding="utf-8")

        self.assertEqual(original, repeated)

    def test_missing_transcript_directory(self):
        folder = self.folder / "transcript"
        destination = folder / "transcripts.md"

        combine_transcripts(folder, destination)

        self.assertFalse(destination.exists())

    def test_empty_transcript_directory(self):
        destination = self.folder / "transcripts.md"

        combine_transcripts(self.folder, destination)

        self.assertFalse(destination.exists())

    def test_invalid_output_directory(self):
        missing = self.folder / "nonexistent"

        with patch.dict(os.environ, {"OUTPUT_DIR": str(missing)}):
            with self.assertRaises(NotADirectoryError):
                main()

    def test_missing_environment_variable(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(KeyError):
                main()

    def test_course_directory_structure(self):
        course = self.folder / "accounting"
        slides = course / "slides"
        postclass = course / "postclass"
        transcripts = slides / "transcript"

        slides.mkdir(parents=True)
        postclass.mkdir()
        transcripts.mkdir()

        self.create_pdf(
            "accounting/slides/session1.pdf",
            "Accounting lecture",
        )

        self.create_pdf(
            "accounting/postclass/test1.pdf",
            "Accounting test",
        )

        (transcripts / "session1.md").write_text(
            "Accounting transcript", encoding="utf-8"
        )

        with patch.dict(
            os.environ, {"OUTPUT_DIR": str(self.folder)}
        ):
            main()

        self.assertTrue(
            (slides / "accounting-slides.md").exists()
        )
        self.assertTrue(
            (postclass / "accounting-tests-and-solutions.md").exists()
        )
        self.assertTrue(
            (transcripts / "accounting-transcripts.md").exists()
        )


if __name__ == "__main__":
    unittest.main()