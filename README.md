# Damodaran Online Course Materials Downloader

A Python script to download and organise PDF teaching materials and YouTube transcripts from Aswath Damodaran's [online classes](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/onlineclass.htm) at NYU Stern.

## Supported Courses

- Accounting
- Foundations of Finance
- Corporate Finance
- Valuation

## Setup

Requires Python and [uv](https://docs.astral.sh/uv/).

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```dotenv
OUTPUT_DIR=~/Downloads/Finance-Courses
ACCOUNTING_URL=https://pages.stern.nyu.edu/~adamodar/New_Home_Page/webcastacctg.htm
FOUNDATIONS_URL=https://pages.stern.nyu.edu/~adamodar/New_Home_Page/webcastfoundationsonline.htm
CORPORATE_FINANCE_URL=https://pages.stern.nyu.edu/adamodar/New_Home_Page/webcastcfonline.htm
VALUATION_URL=https://pages.stern.nyu.edu/~adamodar/New_Home_Page/webcastvalonline.htm
ALLOWED_HOSTS=pages.stern.nyu.edu,www.stern.nyu.edu
```

Comment out the course URLs you do not wish to download.

## Usage

| Command | Description |
|---|---|
| `./run_downloader.sh test` | Run unit and integration tests |
| `./run_downloader.sh dry-run` | Preview downloads |
| `./run_downloader.sh download` | Download PDFs |
| `./run_downloader.sh transcripts-dry-run` | Preview transcript downloads |
| `./run_downloader.sh transcripts` | Download YouTube transcripts |
| `./run_downloader.sh convert` | Convert PDFs to Markdown and aggregate transcripts |
| `./run_downloader.sh all` | Test, preview and confirm downloads and conversion |

## Output

PDFs are organised by course into `slides/`, `postclass/` and `supplementary/` directories.

Existing PDFs are skipped. Results are recorded in `download_report.csv`, which is overwritten on each download run.

Lecture slides and post-class tests and solutions are converted into separate aggregated Markdown files using [PyMuPDF](https://github.com/pymupdf).

YouTube transcripts are automatically downloaded using [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api), saved in webpage order in the `slides/transcript/` directory of each course and aggregated using the conversion command. Existing completed transcripts are skipped.

Files are aggregated in natural filename order. Existing aggregated Markdown files are overwritten oneach conversion run. Original PDFs and individual transcripts are preserved.

## Tests

Tests use Python's built-in `unittest` framework, mocked HTTP responses and temporary directories.

## Limitations

- Only directly linked PDFs are downloaded.
- Videos, transcripts and spreadsheets are currently not supported.
- PDF conversion is limited to embedded text and may produce formatting or character encoding errors.
- Supplementary PDFs are not automatically converted.
- Filename collisions are not automatically resolved.
- YouTube may temporarily block automated transcript requests.
- Transcript numbering follows webpage video order and may differ from actual lecture session numbers.
- Changes to the course webpages may affect functionality.
- Transcript numbering follows webpage video order and may differ from actual lecture session numbers (to be fixed).

## Disclaimer

This independent project is intended for personal educational use and is not affiliated with NYU Stern or Aswath Damodaran.

Course materials remain the intellectual property of their respective copyright holders. No course materials are included in this repository.
