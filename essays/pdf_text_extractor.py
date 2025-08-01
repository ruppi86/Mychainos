#!/usr/bin/env python3
"""
pdf_text_extractor.py – Bulk-extract text from PDF documents
================================================================

Usage
-----
$ python pdf_text_extractor.py                   # scan current folder recursively
$ python pdf_text_extractor.py --output-format txt  # write .txt instead of .md

The script walks **spirida-mycelic/docs/** and every sub-directory. For each
`*.pdf` file it tries to extract textual content with **pdfminer.six**. If that
package is not installed it falls back to **PyPDF2**. When neither backend is
available it prints an explanatory error message with guidance on how to
install `pdfminer.six` (recommended).

Extracted text is written to the *same directory* under the same base-name but
with the chosen extension (default `.md`). Existing files are over-written.

Dependencies
------------
Install the preferred backend via pip:
    pip install pdfminer.six             # high-quality extraction (recommended)
    pip install PyPDF2                   # simple fallback

This tool contains **no external imports** beyond those two packages so it will
run in the base Python environment once a backend is available.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

# ----------------------------------------------------------------------------
# Backend selection
# ----------------------------------------------------------------------------

_BACKEND = None  # type: str | None

try:
    from pdfminer.high_level import extract_text  # type: ignore

    def _extract(pdf_path: Path) -> str:  # pragma: no cover
        """Extract text using pdfminer."""
        return extract_text(str(pdf_path)) or ""

    _BACKEND = "pdfminer.six"
except ModuleNotFoundError:  # pragma: no cover
    try:
        import PyPDF2  # type: ignore

        def _extract(pdf_path: Path) -> str:  # pragma: no cover
            """Extract text using PyPDF2 (simpler, may lose layout)."""
            text_chunks: list[str] = []
            with pdf_path.open("rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                for page in reader.pages:
                    chunk = page.extract_text() or ""
                    text_chunks.append(chunk)
            return "\n".join(text_chunks)

        _BACKEND = "PyPDF2"
    except ModuleNotFoundError:
        _BACKEND = None


def _discover_pdfs(root: Path) -> Iterable[Path]:
    """Yield all PDF files under *root* (recursive)."""
    yield from root.rglob("*.pdf")


def _write_output(text: str, pdf_path: Path, ext: str) -> Path:
    """Write *text* next to *pdf_path* with extension *ext* (dot optional)."""
    if not ext.startswith("."):
        ext = "." + ext
    out_path = pdf_path.with_suffix(ext)
    out_path.write_text(text, encoding="utf-8", errors="replace")
    return out_path


def _main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Bulk-extract text from PDFs")
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parent,
        type=Path,
        help="Root directory to scan (default: script directory)",
    )
    parser.add_argument(
        "--output-format",
        choices=["md", "txt"],
        default="md",
        help="Extension / format for extracted files (default: md)",
    )
    args = parser.parse_args(argv)

    if _BACKEND is None:
        msg = (
            "No PDF extraction backend found. Install one of:\n"
            "    pip install pdfminer.six  # high-quality (recommended)\n"
            "    pip install PyPDF2        # basic fallback\n"
        )
        print(msg, file=sys.stderr)
        sys.exit(1)

    root: Path = args.root.expanduser().resolve()
    ext: str = args.output_format

    pdf_files = list(_discover_pdfs(root))
    if not pdf_files:
        print(f"No PDF files found under {root}")
        return

    print(f"Using backend: {_BACKEND}")
    print(f"Found {len(pdf_files)} PDF file(s) – extracting…")

    for pdf_path in pdf_files:
        rel = pdf_path.relative_to(root)
        print(f"  • {rel}")
        try:
            text = _extract(pdf_path)
            out_path = _write_output(text, pdf_path, ext)
            print(f"    → wrote {out_path.relative_to(root)}")
        except Exception as exc:  # pragma: no cover
            print(f"    ⚠️  failed: {exc}")

    print("Done.")


if __name__ == "__main__":  # pragma: no cover
    _main() 