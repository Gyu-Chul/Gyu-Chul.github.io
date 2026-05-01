#!/usr/bin/env python3
"""
Sync team Story posts from the gyuchul-web Astro+Notion build into this repo.

Workflow:
    1. (You run separately) cd ~/Desktop/gyuchul-web && npm install && npm run build
    2. python3 scripts/sync_team_stories.py [--source PATH]
    3. Review `git status`, then `git commit && git push`

Defaults assume the source repo lives at ~/Desktop/gyuchul-web.
Only Notion posts authored by the team (filtered into /team/ at build time)
are picked up. CHUL personal blog stays redirected; GYU has none yet.
"""
from __future__ import annotations
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

DEAD_SLUGS = {
    # Posts referenced in Notion but never built (manually skipped or drafted).
    # Their <a> tags inside listing pages and series-list nav are stripped.
    "chul2ndAnniversary",
    "codingTestProject1",
    "codingTestProject2",
}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def copy_team_pages(src_root: Path, dst_root: Path) -> list[str]:
    """Copy /team/<slug>/ directories. Returns list of slugs synced."""
    src_team = src_root / "dist" / "client" / "team"
    dst_team = dst_root / "team"
    if not src_team.is_dir():
        fail(f"missing build output: {src_team} (run `npm run build` in gyuchul-web first)")

    dst_team.mkdir(exist_ok=True)
    synced = []
    for slug_dir in src_team.iterdir():
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name
        # Skip the (now-empty) project listing — team blog is Story-only.
        if slug == "project":
            continue
        target = dst_team / slug
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(slug_dir, target)
        synced.append(slug)
    return synced


def copy_assets(src_root: Path, dst_root: Path) -> tuple[int, int]:
    """Copy CSS (from server/_astro), JS (from client/_astro), and Notion images."""
    src_server_astro = src_root / "dist" / "server" / "_astro"
    src_client_astro = src_root / "dist" / "client" / "_astro"
    src_images = src_root / "dist" / "client" / "images" / "notion"
    dst_astro = dst_root / "_astro"
    dst_images = dst_root / "images" / "notion"

    dst_astro.mkdir(exist_ok=True)
    dst_images.mkdir(parents=True, exist_ok=True)

    # CSS files needed by team pages — copy any that exist
    css_count = 0
    needed_css = {"_slug_.BUPykhsI.css", "_slug_.Dkcx_5gs.css", "_slug_.S0rDoPdF.css", "story.BanvMVp9.css"}
    if src_server_astro.is_dir():
        for css in src_server_astro.glob("*.css"):
            if css.name in needed_css or css.name.startswith("_slug_") or css.name.startswith("story"):
                shutil.copy2(css, dst_astro / css.name)
                css_count += 1

    # Comments JS (and any other .js Astro emits to client/_astro)
    js_count = 0
    if src_client_astro.is_dir():
        for js in src_client_astro.glob("*.js"):
            shutil.copy2(js, dst_astro / js.name)
            js_count += 1

    # Notion images referenced in any team HTML (or just copy them all — they're small)
    img_count = 0
    if src_images.is_dir():
        for img in src_images.iterdir():
            if img.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
                shutil.copy2(img, dst_images / img.name)
                img_count += 1
    return css_count + js_count, img_count


def strip_dead_anchors(html: str) -> tuple[str, int]:
    """Remove <a ...href="/team/<dead_slug>"...>...</a> blocks. Returns (new_html, count)."""
    removed = 0
    for slug in DEAD_SLUGS:
        pattern = re.compile(
            r'<a\b[^>]*href="/team/' + re.escape(slug) + r'"[^>]*>.*?</a>',
            re.DOTALL,
        )
        html, n = pattern.subn("", html)
        removed += n
    return html, removed


def strip_dead_article_cards(html: str) -> tuple[str, int]:
    """Remove <article>…</article> cards whose only link points to a dead slug.
    Used on listing pages where each post is its own <article>.
    """
    articles = []
    pos = 0
    while True:
        m = re.search(r"<article\b", html[pos:])
        if not m:
            break
        start = pos + m.start()
        end_m = re.search(r"</article>", html[start:])
        if not end_m:
            break
        end = start + end_m.end()
        articles.append((start, end, html[start:end]))
        pos = end

    to_remove = []
    for start, end, content in articles:
        # Only remove if the article links ONLY to a dead slug (not also to a live one)
        live_links = re.findall(r'href="/team/([^"]+)"', content)
        if live_links and all(s in DEAD_SLUGS for s in live_links):
            to_remove.append((start, end))

    for start, end in sorted(to_remove, reverse=True):
        html = html[:start] + html[end:]
    return html, len(to_remove)


def strip_footer_nav(html: str) -> tuple[str, int]:
    """Remove the small-text <nav class=\"footer-nav\"> block from the listing footer."""
    new_html, n = re.subn(
        r'<nav class="footer-nav"[^>]*>.*?</nav>\s*',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )
    return new_html, n


def cleanup_team_html(team_root: Path) -> None:
    for html_path in team_root.glob("*/index.html"):
        # /team/index.html is our redirect template — don't touch
        if html_path.parent.name == "":
            continue
        with open(html_path) as f:
            original = f.read()
        new = original

        # Listing page: strip footer nav AND dead article cards
        if html_path.parent.name == "story":
            new, _ = strip_dead_article_cards(new)
            new, _ = strip_footer_nav(new)
            # Also drop any leftover dead anchors (paranoia)
            new, _ = strip_dead_anchors(new)
        else:
            # Individual post: only strip dead series-item / nav anchors,
            # never remove whole <article> (that wraps the body).
            new, _ = strip_dead_anchors(new)

        if new != original:
            with open(html_path, "w") as f:
                f.write(new)
            print(f"  cleaned: {html_path.relative_to(team_root.parent)}")


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source",
        default=os.path.expanduser("~/Desktop/gyuchul-web"),
        help="path to gyuchul-web (Astro+Notion source repo)",
    )
    p.add_argument(
        "--dest",
        default=str(here),
        help="path to this repo (Gyu-Chul.github.io)",
    )
    args = p.parse_args()

    src = Path(args.source).resolve()
    dst = Path(args.dest).resolve()
    if not (src / "dist" / "client" / "team").exists():
        fail(
            f"no Astro build found at {src}/dist/client/team\n"
            f"run first:  cd {src} && npm install && npm run build"
        )

    print(f"source: {src}")
    print(f"dest:   {dst}\n")

    print("→ copying team pages")
    slugs = copy_team_pages(src, dst)
    for s in sorted(slugs):
        print(f"  {s}")

    print("\n→ copying assets (CSS / JS / Notion images)")
    asset_count, img_count = copy_assets(src, dst)
    print(f"  {asset_count} _astro asset(s), {img_count} image(s)")

    print("\n→ applying cleanup transformations")
    cleanup_team_html(dst / "team")

    print("\n✓ sync complete. Review with `git status` and `git diff`,")
    print("  then commit and push when ready.")


if __name__ == "__main__":
    main()
