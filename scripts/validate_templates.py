#!/usr/bin/env python3
"""MarkdownテンプレートにH1見出しと内容があることを検査する。"""

from __future__ import annotations

import argparse
from pathlib import Path


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    for template in sorted(path.glob("*.md")):
        text = template.read_text(encoding="utf-8").strip()
        if not text.startswith("# "):
            errors.append(f"{template}: H1見出しがありません")
        if len(text.splitlines()) < 4:
            errors.append(f"{template}: 内容が不足しています")
    if not list(path.glob("*.md")):
        errors.append(f"{path}: Markdownテンプレートがありません")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="テンプレートディレクトリ")
    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"ディレクトリがありません: {args.directory}")
        return 1
    errors = validate(args.directory)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {len(list(args.directory.glob('*.md')))} template(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
