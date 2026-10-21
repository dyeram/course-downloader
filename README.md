
# Damodaran Online Course Materials Downloader

A simple Python script to download and organise PDF teaching materials from Prof. Aswath Damodaran's [online classes](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/onlineclass.htm)

## Supported Courses

Currently supports three courses:

- Accounting
- Foundations of Finance
- Valuation

Other courses have not been tested yet.

## Setup

Requires Python and [uv](https://docs.astral.sh/uv/).

Install dependencies:

```bash
uv sync
```

Create a `.env` file in the project directory:

```dotenv
OUTPUT_DIR=~/Downloads/Finance-Courses
ACCOUNTING_URL=https://pages.stern.nyu.edu/~adamodar/New_Home_Page/webcastacctg.htm
FOUNDATIONS_URL=https://pages.stern.nyu.edu/~adamodar/New_Home_Page/webcastfoundationsonline.htm
VALUATION_URL=https://pages.stern.nyu.edu/~adamodar/New_Home_Page/webcastvalonline.htm
ALLOWED_HOSTS=pages.stern.nyu.edu,www.stern.nyu.edu
```

## Usage

Preview downloads:

```bash
uv run --env-file .env python download_damodaran.py --dry-run
```

Download PDFs:

```bash
uv run --env-file .env python download_damodaran.py
```

Files are organised by course and material type. Existing files are skipped, and results are recorded in `download_report.csv`.

## Tests

```bash
uv run --env-file .env python -m unittest discover -s tests -v
```

## Limitations

- Only PDFs directly linked from the three configured course pages are downloaded.
- Other courses have not been tested yet.
- Filename collisions are not automatically resolved.
- Changes to the NYU webpages may affect the script.

## Disclaimer

This is an independent project intended for personal educational use. It is not affiliated with or endorsed by NYU Stern School of Business or Aswath Damodaran.

Course materials remain the intellectual property of their respective copyright holders. No course PDFs are included in this repository.

