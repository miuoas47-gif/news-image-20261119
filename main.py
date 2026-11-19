#!/usr/bin/env python3
"""Entrypoint for the news-image-20261119 entry.

    python3 main.py --check    validate the entry files
    python3 main.py --serve    serve this directory over HTTP
    python3 main.py            same as --serve

Validation covers: index.html exists and embeds ad.png, ad.png is a PNG
of at most 8 MB, index.html is at most 2 MB, and README.md carries the
three live make.fun badges for this competition.
"""

import argparse
import functools
import http.server
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_PAGE_BYTES = 2 * 1024 * 1024
COMPETITION = "news-image-20261119"


def report(label, passed, note=""):
    mark = "ok" if passed else "FAIL"
    print(f"[{mark}] {label}" + (f" ({note})" if note else ""))
    return passed


def validate():
    """Run every entry check; return True only if all pass."""
    passed = []

    page = os.path.join(HERE, "index.html")
    page_exists = os.path.isfile(page)
    passed.append(report("index.html present", page_exists))
    page_text = ""
    if page_exists:
        with open(page, encoding="utf-8") as handle:
            page_text = handle.read()
        passed.append(report("index.html embeds ad.png", "ad.png" in page_text))
        passed.append(report(
            "index.html carries the make.fun referral link",
            "make.fun/r/6gvkzysc" in page_text))
        size = os.path.getsize(page)
        passed.append(report(
            "index.html within 2 MB", size <= MAX_PAGE_BYTES,
            f"{size / (1024 * 1024):.2f} MB"))

    image = os.path.join(HERE, "ad.png")
    image_exists = os.path.isfile(image)
    passed.append(report("ad.png present", image_exists))
    if image_exists:
        with open(image, "rb") as handle:
            magic = handle.read(8)
        passed.append(report("ad.png is a PNG file", magic == b"\x89PNG\r\n\x1a\n"))
        size = os.path.getsize(image)
        passed.append(report(
            "ad.png within 8 MB", size <= MAX_IMAGE_BYTES,
            f"{size / (1024 * 1024):.2f} MB"))

    readme = os.path.join(HERE, "README.md")
    readme_exists = os.path.isfile(readme)
    passed.append(report("README.md present", readme_exists))
    if readme_exists:
        with open(readme, encoding="utf-8") as handle:
            readme_text = handle.read()
        passed.append(report(
            "README.md carries make.fun badges",
            "make.fun/badge/" in readme_text))
        passed.append(report(
            "README badges name this competition",
            COMPETITION in readme_text))

    license_path = os.path.join(HERE, "LICENSE")
    license_exists = os.path.isfile(license_path)
    passed.append(report("LICENSE present", license_exists))
    if license_exists:
        with open(license_path, encoding="utf-8") as handle:
            license_text = handle.read()
        passed.append(report(
            "LICENSE is an MIT license", "MIT License" in license_text))

    return passed


def serve(port):
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=HERE)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {HERE} at http://127.0.0.1:{port}/ (Ctrl-C to stop)")
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="validate the entry files and exit")
    mode.add_argument("--serve", action="store_true",
                      help="serve the entry over HTTP")
    parser.add_argument("--port", type=int, default=8000,
                        help="port used by --serve (default 8000)")
    args = parser.parse_args()

    if args.check:
        results = validate()
        good = sum(results)
        print(f"{good}/{len(results)} checks passed."
              if all(results) else "Some checks FAILED.")
        sys.exit(0 if all(results) else 1)
    serve(args.port)


if __name__ == "__main__":
    main()
