#!/usr/bin/env python3
"""make.fun entry: copy the finished news image to the output path.

The repository holds the finished image as entry.png (built by
build_image.py). This program simply copies it to /output/entry.png
(or $ENTRY_OUTPUT), so repeated runs with no network produce
byte-identical output.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "entry.png"
DEFAULT_OUTPUT = "/output/entry.png"
MAX_BYTES = 1_048_576  # 1 MiB
JPEG_MAGIC = b"\xff\xd8"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if not SOURCE.is_file():
        print(f"error: source image missing: {SOURCE}", file=sys.stderr)
        return 1

    src_bytes = SOURCE.read_bytes()
    if len(src_bytes) > MAX_BYTES:
        print(f"error: source is {len(src_bytes)} bytes, over the 1 MiB cap",
              file=sys.stderr)
        return 1
    if not (src_bytes.startswith(JPEG_MAGIC) or src_bytes.startswith(PNG_MAGIC)):
        print("error: source is neither JPEG nor PNG", file=sys.stderr)
        return 1

    out_path = Path(os.environ.get("ENTRY_OUTPUT", DEFAULT_OUTPUT))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, out_path)

    written = out_path.read_bytes()
    if sha256(written) != sha256(src_bytes):
        print("error: written file hash does not match source", file=sys.stderr)
        return 1
    if len(written) > MAX_BYTES:
        print("error: written file exceeds the 1 MiB cap", file=sys.stderr)
        return 1
    if not (written.startswith(JPEG_MAGIC) or written.startswith(PNG_MAGIC)):
        print("error: written file is neither JPEG nor PNG", file=sys.stderr)
        return 1

    print(f"wrote {out_path} ({len(written)} bytes, sha256 {sha256(written)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
