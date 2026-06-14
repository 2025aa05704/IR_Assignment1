"""
build_pdf.py
------------
Render report/Report.md into a styled report/Report.pdf (with screenshots).

Pipeline:
    Markdown -> HTML (python-markdown) -> PDF (headless Google Chrome)

Usage:
    python report/build_pdf.py

Requires: `markdown` (pip install markdown) and Google Chrome installed.
Relative image paths in Report.md (e.g. screenshots/bits_lab_app.png) resolve
because Report.html is written next to Report.md.
"""

import os
import shutil
import subprocess
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(HERE, "Report.md")
HTML_FILE = os.path.join(HERE, "Report.html")
PDF_FILE = os.path.join(HERE, "Report.pdf")

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt; line-height: 1.55; color: #1a1a1a; margin: 0;
}
h1 { font-size: 22pt; margin: 0 0 6pt; padding-bottom: 6pt; border-bottom: 3px solid #2c5f8a; color: #1f3b54; }
h2 { font-size: 15pt; margin: 18pt 0 6pt; padding-bottom: 3pt; border-bottom: 1px solid #c9d6e3; color: #244b6b; page-break-after: avoid; }
h3 { font-size: 12.5pt; margin: 12pt 0 4pt; color: #2c5f8a; page-break-after: avoid; }
p { margin: 5pt 0; }
a { color: #1565c0; text-decoration: none; word-break: break-all; }
ul, ol { margin: 5pt 0 5pt 18pt; }
li { margin: 2pt 0; }
code { font-family: "SFMono-Regular", Menlo, Consolas, monospace; font-size: 9.5pt; background: #f1f3f5; padding: 1px 4px; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 10px 12px; overflow: auto; white-space: pre-wrap; word-wrap: break-word; font-size: 9.5pt; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { margin: 8pt 0; padding: 4pt 12pt; border-left: 4px solid #c9d6e3; color: #555; background: #f8fafc; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #b9c4cf; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #eaf1f8; font-weight: 600; }
tr:nth-child(even) td { background: #fafcfe; }
img { max-width: 100%; height: auto; border: 1px solid #ccc; border-radius: 4px; margin: 8pt 0; page-break-inside: avoid; }
hr { border: 0; border-top: 1px solid #dde3ea; margin: 14pt 0; }
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IR Assignment 1 - Report (Group 63)</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_chrome():
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chrome"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def main():
    with open(MD_FILE, "r", encoding="utf-8") as fh:
        md_text = fh.read()

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
    )
    html = HTML_TEMPLATE.format(css=CSS, body=body)
    with open(HTML_FILE, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Wrote {HTML_FILE}")

    chrome = find_chrome()
    if not chrome:
        print("ERROR: Google Chrome / Chromium not found; HTML written but no PDF.",
              file=sys.stderr)
        sys.exit(2)

    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_FILE}",
        f"file://{HTML_FILE}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not os.path.exists(PDF_FILE):
        # Older Chrome builds use --headless instead of --headless=new
        cmd[1] = "--headless"
        proc = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(PDF_FILE):
        print(f"Wrote {PDF_FILE} ({os.path.getsize(PDF_FILE)} bytes)")
    else:
        print("ERROR: PDF was not produced.", file=sys.stderr)
        print(proc.stdout, proc.stderr, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

