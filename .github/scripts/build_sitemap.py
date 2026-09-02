#!/usr/bin/env python3
"""Regenerate sitemap.xml from the HTML pages in the repo root.

lastmod comes from each file's last git commit date, NOT today's date.
That matters: a sitemap that stamps every page with today on every run
trains crawlers to ignore its lastmod values.
"""

import subprocess
import sys
from pathlib import Path

BASE = "https://lasilvercommunications.com/"

# Pages that should never appear in the sitemap.
EXCLUDE = {"404.html", "google*.html"}

# Anything not listed here gets DEFAULT_PRIORITY.
PRIORITY = {
    "index.html": "1.0",
    "record-framework.html": "0.8",
    "faq.html": "0.8",
}
DEFAULT_PRIORITY = "0.8"
CHANGEFREQ = "monthly"

ROOT = Path(__file__).resolve().parents[2]


def excluded(name: str) -> bool:
    return any(Path(name).match(pat) for pat in EXCLUDE)


def last_commit_date(path: Path) -> str:
    """YYYY-MM-DD of the file's most recent commit; falls back to mtime."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path.name],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return out
    except subprocess.CalledProcessError:
        pass
    import datetime
    return datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()


def loc_for(name: str) -> str:
    # index.html is served at the bare directory URL - list it that way,
    # so it does not compete with itself as a duplicate.
    return BASE if name == "index.html" else BASE + name


def main() -> int:
    pages = sorted(
        p for p in ROOT.glob("*.html") if not excluded(p.name)
    )
    if not pages:
        print("No HTML pages found - refusing to write an empty sitemap.", file=sys.stderr)
        return 1

    # index.html first, then alphabetical.
    pages.sort(key=lambda p: (p.name != "index.html", p.name))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for p in pages:
        lines += [
            "  <url>",
            f"    <loc>{loc_for(p.name)}</loc>",
            f"    <lastmod>{last_commit_date(p)}</lastmod>",
            f"    <changefreq>{CHANGEFREQ}</changefreq>",
            f"    <priority>{PRIORITY.get(p.name, DEFAULT_PRIORITY)}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")

    out = "\n".join(lines) + "\n"
    (ROOT / "sitemap.xml").write_text(out, encoding="utf-8")
    print(f"Wrote sitemap.xml with {len(pages)} URLs:")
    for p in pages:
        print(f"  {loc_for(p.name)}  {last_commit_date(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
