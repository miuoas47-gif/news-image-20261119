#!/usr/bin/env python3
"""Entry checker and local preview server for the news-image-20261119 entry.

This is a small, dependency-free helper for the make.fun bounty
"Sum up 19 November's world news in one image". It does two things:

* ``--check`` — verify the deliverables in this directory meet the
  competition's size and content rules (page exists and shows the poster,
  poster is a real PNG under the size cap, README carries the live
  make.fun badges, LICENSE names an SPDX licence).
* ``--serve`` — preview the ad page on localhost, so the poster and the
  story list can be eyeballed in a browser before submitting.

Only the Python standard library is used; nothing is installed.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import sys

PAGE_NAME = "index.html"
POSTER_NAME = "ad.png"
GUIDE_NAME = "README.md"
LICENCE_NAME = "LICENSE"

PAGE_MAX_BYTES = 2 * 1024 * 1024        # 2 MB, per the competition rules
POSTER_MAX_BYTES = 8 * 1024 * 1024      # 8 MB, per the competition rules
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Fragments the README must contain so GitHub renders the live badges.
BADGE_FRAGMENTS = (
    "https://make.fun/badge/news-image-20261119.svg",
    "https://make.fun/badge/news-image-20261119/miuoas47-gif/"
    "news-image-20261119/rank.svg",
    "https://make.fun/badge/news-image-20261119/miuoas47-gif/"
    "news-image-20261119/reward.svg",
)


class Finding:
    """One check outcome: a label, whether it passed, and a short note."""

    def __init__(self, label: str, ok: bool, note: str = "") -> None:
        self.label = label
        self.ok = ok
        self.note = note

    def render(self) -> str:
        mark = "ok  " if self.ok else "FAIL"
        return f"[{mark}] {self.label}" + (f" — {self.note}" if self.note else "")


def _read_bytes(path: str) -> bytes | None:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def _read_text(path: str) -> str | None:
    blob = _read_bytes(path)
    if blob is None:
        return None
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError:
        return None


def inspect_page(root: str) -> list[Finding]:
    """Check index.html: present, small enough, and showing ad.png."""
    path = os.path.join(root, PAGE_NAME)
    blob = _read_bytes(path)
    if blob is None:
        return [Finding(f"{PAGE_NAME} exists", False, "file is missing")]
    findings = [
        Finding(f"{PAGE_NAME} exists", True),
        Finding(
            f"{PAGE_NAME} within {PAGE_MAX_BYTES // 1024 // 1024} MB",
            len(blob) <= PAGE_MAX_BYTES,
            f"{len(blob)} bytes",
        ),
    ]
    text = blob.decode("utf-8", errors="replace")
    findings.append(
        Finding(
            f"{PAGE_NAME} references {POSTER_NAME}",
            POSTER_NAME in text,
            "src=\"ad.png\" present" if POSTER_NAME in text else "no ad.png reference",
        )
    )
    findings.append(
        Finding(
            f"{PAGE_NAME} shows the poster in an <img> tag",
            "<img" in text and POSTER_NAME in text,
            "img tag with the poster found" if "<img" in text else "no img tag",
        )
    )
    findings.append(
        Finding(
            f"{PAGE_NAME} carries the referral link",
            "make.fun/r/6gvkzysc" in text or "?ref=6gvkzysc" in text,
            "referral code 6gvkzysc found" if "6gvkzysc" in text else "no referral code",
        )
    )
    return findings


def inspect_poster(root: str) -> list[Finding]:
    """Check ad.png: present, a real PNG by its magic bytes, under the cap."""
    path = os.path.join(root, POSTER_NAME)
    blob = _read_bytes(path)
    if blob is None:
        return [Finding(f"{POSTER_NAME} exists", False, "file is missing")]
    return [
        Finding(f"{POSTER_NAME} exists", True),
        Finding(
            f"{POSTER_NAME} is a PNG",
            blob.startswith(PNG_MAGIC),
            "magic bytes match" if blob.startswith(PNG_MAGIC) else "not a PNG header",
        ),
        Finding(
            f"{POSTER_NAME} within {POSTER_MAX_BYTES // 1024 // 1024} MB",
            len(blob) <= POSTER_MAX_BYTES,
            f"{len(blob)} bytes",
        ),
    ]


def inspect_guide(root: str) -> list[Finding]:
    """Check README.md: present and carrying all three live badges."""
    path = os.path.join(root, GUIDE_NAME)
    text = _read_text(path)
    if text is None:
        return [Finding(f"{GUIDE_NAME} exists", False, "file is missing")]
    findings = [Finding(f"{GUIDE_NAME} exists", True)]
    for fragment in BADGE_FRAGMENTS:
        short = fragment.rsplit("/", 1)[-1]
        findings.append(
            Finding(
                f"{GUIDE_NAME} carries badge {short}",
                fragment in text,
                "present" if fragment in text else "missing",
            )
        )
    findings.append(
        Finding(
            f"{GUIDE_NAME} carries the referral link",
            "make.fun/r/6gvkzysc" in text or "?ref=6gvkzysc" in text,
            "referral code 6gvkzysc found" if "6gvkzysc" in text else "no referral code",
        )
    )
    return findings


def inspect_licence(root: str) -> list[Finding]:
    """Check LICENSE: present and naming an SPDX licence identifier."""
    path = os.path.join(root, LICENCE_NAME)
    text = _read_text(path)
    if text is None:
        return [Finding(f"{LICENCE_NAME} exists", False, "file is missing")]
    return [
        Finding(f"{LICENCE_NAME} exists", True),
        Finding(
            f"{LICENCE_NAME} names an SPDX identifier",
            "SPDX-License-Identifier:" in text,
            "identifier found" if "SPDX-License-Identifier:" in text else "no SPDX line",
        ),
    ]


def run_all_checks(root: str) -> list[Finding]:
    """Run every inspection and return the findings in a stable order."""
    findings: list[Finding] = []
    for inspector in (inspect_page, inspect_poster, inspect_guide, inspect_licence):
        findings.extend(inspector(root))
    return findings


def serve_directory(root: str, port: int) -> int:
    """Serve the entry directory over HTTP until interrupted."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=root
    )
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {root} at http://127.0.0.1:{port}/ (Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check or preview the news-image-20261119 entry."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the entry files in this directory",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="serve the entry directory over HTTP for a local preview",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port for --serve (default: 8000)",
    )
    parser.add_argument(
        "--dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="entry directory to check or serve (default: this file's folder)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.serve:
        return serve_directory(args.dir, args.port)
    if args.check:
        findings = run_all_checks(args.dir)
        for finding in findings:
            print(finding.render())
        failed = [f for f in findings if not f.ok]
        if failed:
            print(f"\n{len(failed)} check(s) failed.")
            return 1
        print(f"\nAll {len(findings)} checks passed.")
        return 0
    build_parser().print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
