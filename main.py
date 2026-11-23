"""make.fun entry program for news-image-20261122, round 2.

The entry is a single poster image, entry.png, drawn from scratch with
PIL (the drawing script is not part of this repo). This program is the
deliverable the grader runs: it copies the poster, byte for byte, into
the output directory named by the MAKEFUN_OUTPUT_DIR environment
variable, falling back to /output when the variable is not set.

Standard library only. The copy is streamed in chunks so the file never
has to sit in memory twice, the PNG signature and dimensions are checked
first so a corrupt artifact fails loudly instead of shipping a broken
image, and the copy is hash-verified afterwards so a truncated or
tampered write is caught instead of shipped.
"""

import hashlib
import os
import sys

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHUNK = 64 * 1024
MAX_BYTES = 1024 * 1024  # the competition caps the image at 1 MiB


def poster_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")


def output_path():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, "entry.png")


def check_dimensions(path):
    """Refuse a poster that is not the 1024x1024 the competition asks for.

    The width and height live in the PNG's IHDR chunk, big-endian uint32
    at offsets 16 and 20, so this reads 24 bytes and nothing more.
    """
    with open(path, "rb") as fh:
        header = fh.read(24)
    if len(header) < 24:
        sys.exit("entry.png is too short to hold a PNG header")
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    if (width, height) != (1024, 1024):
        sys.exit("poster must be 1024x1024, got %dx%d" % (width, height))


def copy_and_verify(src, dst):
    """Stream src to dst, hashing the bytes as they pass, then hash the
    finished copy the same way and refuse it if the two digests differ.
    A size check alone would miss a same-size corruption, so the digest
    is what proves the shipped file is the poster, byte for byte.
    """
    written = hashlib.sha256()
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        while True:
            chunk = fin.read(CHUNK)
            if not chunk:
                break
            fout.write(chunk)
            written.update(chunk)
    shipped = hashlib.sha256()
    with open(dst, "rb") as fh:
        while True:
            chunk = fh.read(CHUNK)
            if not chunk:
                break
            shipped.update(chunk)
    if shipped.hexdigest() != written.hexdigest():
        sys.exit("copied poster failed its integrity check")


def main():
    src = poster_path()
    with open(src, "rb") as fh:
        if fh.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            sys.exit("entry.png is not a PNG file")
    check_dimensions(src)
    if os.path.getsize(src) > MAX_BYTES:
        sys.exit("poster exceeds the 1 MiB competition limit")
    dst = output_path()
    copy_and_verify(src, dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
