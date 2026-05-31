#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새 팀 Story 글을 마크다운 파일 하나로 만든다. (완전 정적 — 댓글/조회수 백엔드 의존 없음)

사용법:
  py scripts/new_story.py --new "글 제목"        # posts/<slug>.md 초안 만들기 (템플릿 복사)
  py scripts/new_story.py posts/my-post.md       # 마크다운 -> team/<slug>/index.html 생성 + 목록 갱신
  py scripts/new_story.py --rebuild              # 매니페스트(posts/index.json)로 목록만 재생성

마크다운 front matter (맨 위 --- 사이):
  title:   글 제목                 (필수)
  date:    2026-06-01              (필수, YYYY-MM-DD)
  summary: 한 줄 요약               (선택)
  tags:    Coding Test, 회고        (선택, 쉼표 구분)
  slug:    my-post                 (선택, 기본값은 .md 파일 이름)
  accent:  "#f59e0b"               (선택, 테마 색 / 기본 보라색)

본문은 그 아래에 마크다운으로. 지원: 제목(#,##,###), 문단, **굵게**, *기울임*,
`인라인코드`, [링크](url), ![이미지](/images/notion/x.png), 목록(-, 1.), 인용(>),
표(| a | b |), 코드블록(```lang), 구분선(---).
"""

import sys
import os
import re
import json
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "posts")
MANIFEST = os.path.join(POSTS_DIR, "index.json")
TEAM_DIR = os.path.join(ROOT, "team")
STORY_INDEX = os.path.join(TEAM_DIR, "story", "index.html")
SITE = "https://gyu-chul.github.io"

DEFAULT_ACCENT = "#7c5cff"


# --------------------------------------------------------------------------- #
# Markdown -> HTML (의존성 없는 최소 변환기)
# --------------------------------------------------------------------------- #
def _inline(text):
    """문단/제목/리스트 항목 등 인라인 마크다운 변환. text 는 raw(미escape)."""
    # 1) 코드 스팬을 먼저 빼내서 보호
    spans = []

    def _stash(m):
        spans.append(html.escape(m.group(1)))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", _stash, text)

    # 2) 나머지 텍스트 escape
    text = html.escape(text)

    # 3) 이미지 -> 링크 순서로 (이미지가 먼저)
    text = re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    # 4) 굵게 / 기울임
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)

    # 5) 코드 스팬 복원
    def _restore(m):
        return "<code>%s</code>" % spans[int(m.group(1))]

    text = re.sub(r"\x00(\d+)\x00", _restore, text)
    return text


def md_to_html(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            i += 1
            continue

        # 코드 블록
        m = re.match(r"^```(\w*)\s*$", stripped)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # 닫는 ```
            cls = ' class="language-%s"' % lang if lang else ""
            out.append(
                "<pre><code%s>%s</code></pre>" % (cls, html.escape("\n".join(buf)))
            )
            continue

        # 구분선
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 제목
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, _inline(m.group(2)), level))
            i += 1
            continue

        # 인용
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(" ".join(buf)))
            continue

        # 표 (헤더 + |---| 구분줄)
        if "|" in stripped and i + 1 < n and re.match(
            r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]
        ) and "-" in lines[i + 1]:
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2  # 헤더 + 구분줄
            rows = []
            while i < n and "|" in lines[i].strip() and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join("<th>%s</th>" % _inline(c) for c in header)
            tbody = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in r)
                for r in rows
            )
            out.append(
                "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                % (thead, tbody)
            )
            continue

        # 순서 없는 목록
        if re.match(r"^[-*+]\s+", stripped):
            buf = []
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                buf.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            items = "".join("<li>%s</li>" % _inline(x) for x in buf)
            out.append("<ul>%s</ul>" % items)
            continue

        # 순서 있는 목록
        if re.match(r"^\d+\.\s+", stripped):
            buf = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                buf.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            items = "".join("<li>%s</li>" % _inline(x) for x in buf)
            out.append("<ol>%s</ol>" % items)
            continue

        # 문단 (빈 줄 전까지 합침)
        buf = []
        while i < n and lines[i].strip() and not re.match(
            r"^(#{1,3}\s|```|>|[-*+]\s|\d+\.\s|(-{3,}|\*{3,})$)", lines[i].strip()
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % _inline(" ".join(buf)))

    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Front matter 파싱
# --------------------------------------------------------------------------- #
def parse_front_matter(raw):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if not m:
        raise SystemExit(
            "front matter(--- 사이 메타데이터)가 없습니다. posts/_TEMPLATE.md 를 참고하세요."
        )
    meta_block, body = m.group(1), m.group(2)
    meta = {}
    for line in meta_block.split("\n"):
        if not line.strip() or ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body


def hex_to_rgb(hexstr):
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return "%d, %d, %d" % (r, g, b)
    except ValueError:
        return "124, 92, 255"


# --------------------------------------------------------------------------- #
# 날짜 포맷
# --------------------------------------------------------------------------- #
def date_iso(d):  # 2026-04-11
    return d


def date_card(d):  # 2026. 04. 11
    y, m, day = d.split("-")
    return "%s. %s. %s" % (y, m, day)


def date_kr(d):  # 2026년 04월 11일
    y, m, day = d.split("-")
    return "%s년 %s월 %s일" % (y, m, day)


# --------------------------------------------------------------------------- #
# 개별 글 페이지 렌더
# --------------------------------------------------------------------------- #
def render_post(post, body_html):
    title = post["title"]
    summary = post.get("summary", "")
    tags = post.get("tags", [])
    accent = post.get("accent", DEFAULT_ACCENT)
    slug = post["slug"]
    iso = post["date"]
    url = "%s/team/%s" % (SITE, slug)

    tag_spans = "".join('<span class="tag">#%s</span> ' % html.escape(t) for t in tags)

    t = POST_TEMPLATE
    repl = {
        "__TITLE__": html.escape(title),
        "__SUMMARY__": html.escape(summary),
        "__DESC__": html.escape(summary or title),
        "__URL__": url,
        "__ISO__": iso,
        "__DATE_KR__": date_kr(iso),
        "__ACCENT__": accent,
        "__ACCENT_RGB__": hex_to_rgb(accent),
        "__TAGS__": tag_spans,
        "__BODY__": body_html,
    }
    for k, v in repl.items():
        t = t.replace(k, v)
    return t


# --------------------------------------------------------------------------- #
# 목록(story/index.html) 재생성 — 매니페스트 기반, cid 속성 보존
# --------------------------------------------------------------------------- #
CID = "data-astro-cid-la23qyh3"


def render_card(post):
    tags = post.get("tags", [])
    data_tags = ", ".join(tags)
    tag_spans = "".join(
        '<span class="post-tag" %s>#%s</span> ' % (CID, html.escape(t)) for t in tags
    )
    return (
        '<article class="post-card" data-tags="%s" %s> '
        '<a href="/team/%s" class="post-link" %s> '
        '<div class="post-meta" %s> '
        '<time class="post-date" %s>%s</time> '
        "</div> "
        '<h2 class="post-title" %s>%s</h2> '
        '<p class="post-summary" %s>%s</p> '
        '<div class="post-tags" %s>%s</div> '
        '<span class="post-arrow" %s>→</span> '
        "</a> </article>"
    ) % (
        html.escape(data_tags), CID,
        post["slug"], CID,
        CID,
        CID, date_card(post["date"]),
        CID, html.escape(post["title"]),
        CID, html.escape(post.get("summary", "")),
        CID, tag_spans,
        CID,
    )


def render_listing(posts):
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)
    cards = "".join(render_card(p) for p in posts)

    all_tags = []
    for p in posts:
        for t in p.get("tags", []):
            if t not in all_tags:
                all_tags.append(t)
    filters = '<button class="filter-btn active" data-tag="all" %s>All</button> ' % CID
    filters += "".join(
        '<button class="filter-btn" data-tag="%s" %s>#%s</button> '
        % (html.escape(t), CID, html.escape(t))
        for t in all_tags
    )

    t = LISTING_TEMPLATE
    t = t.replace("__COUNT__", str(len(posts)))
    t = t.replace("__FILTERS__", filters)
    t = t.replace("__CARDS__", cards)
    return t


# --------------------------------------------------------------------------- #
# 매니페스트
# --------------------------------------------------------------------------- #
def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_manifest(posts):
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def upsert(posts, entry):
    posts = [p for p in posts if p["slug"] != entry["slug"]]
    posts.append(entry)
    return posts


# --------------------------------------------------------------------------- #
# 명령
# --------------------------------------------------------------------------- #
def slugify(title):
    s = title.lower()
    s = re.sub(r"[^\w가-힣]+", "-", s, flags=re.U).strip("-")
    return s or "post"


def cmd_new(title):
    os.makedirs(POSTS_DIR, exist_ok=True)
    slug = slugify(title)
    path = os.path.join(POSTS_DIR, slug + ".md")
    if os.path.exists(path):
        raise SystemExit("이미 있습니다: %s" % path)
    stub = TEMPLATE_MD.replace("__TITLE__", title).replace("__SLUG__", slug)
    with open(path, "w", encoding="utf-8") as f:
        f.write(stub)
    print("초안 생성: %s" % os.path.relpath(path, ROOT))
    print("→ 본문을 채운 뒤:  py scripts/new_story.py %s" % os.path.relpath(path, ROOT))


def cmd_build(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        raw = f.read()
    meta, body = parse_front_matter(raw)

    if "title" not in meta or "date" not in meta:
        raise SystemExit("front matter 에 title, date 는 필수입니다.")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", meta["date"]):
        raise SystemExit("date 는 YYYY-MM-DD 형식이어야 합니다: %s" % meta["date"])

    slug = meta.get("slug") or os.path.splitext(os.path.basename(md_path))[0]
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    entry = {
        "slug": slug,
        "title": meta["title"],
        "date": meta["date"],
        "summary": meta.get("summary", ""),
        "tags": tags,
        "accent": meta.get("accent", DEFAULT_ACCENT),
    }

    body_html = md_to_html(body)
    page = render_post(entry, body_html)

    out_dir = os.path.join(TEAM_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print("글 페이지: %s" % os.path.relpath(out_path, ROOT))

    posts = upsert(load_manifest(), entry)
    save_manifest(posts)
    with open(STORY_INDEX, "w", encoding="utf-8") as f:
        f.write(render_listing(posts))
    print("목록 갱신: %s  (총 %d편)" % (os.path.relpath(STORY_INDEX, ROOT), len(posts)))


def cmd_rebuild():
    posts = load_manifest()
    with open(STORY_INDEX, "w", encoding="utf-8") as f:
        f.write(render_listing(posts))
    print("목록 재생성 완료 (총 %d편)" % len(posts))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return
    if argv[1] == "--new":
        if len(argv) < 3:
            raise SystemExit('사용법: py scripts/new_story.py --new "글 제목"')
        cmd_new(argv[2])
    elif argv[1] == "--rebuild":
        cmd_rebuild()
    else:
        md_path = argv[1]
        if not os.path.exists(md_path):
            raise SystemExit("파일이 없습니다: %s" % md_path)
        cmd_build(md_path)


# --------------------------------------------------------------------------- #
# 템플릿들
# --------------------------------------------------------------------------- #
TEMPLATE_MD = """---
title: __TITLE__
date: 2026-01-01
summary: 한 줄 요약을 적어주세요
tags: 회고
slug: __SLUG__
accent: "#7c5cff"
---

여기부터 본문입니다. 마크다운으로 자유롭게 작성하세요.

## 소제목

문단을 쓰고 **굵게**, *기울임*, `코드`, [링크](https://example.com) 를 쓸 수 있어요.

- 목록 항목 1
- 목록 항목 2

이미지는 images/notion/ 에 넣고 이렇게 참조합니다:

![설명](/images/notion/파일이름.png)

```python
print("코드 블록도 됩니다")
```

> 인용문도 됩니다.
"""

POST_TEMPLATE = """<!DOCTYPE html><html lang="ko"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>__TITLE__ | GYUCHUL Blog</title><meta name="description" content="__DESC__"><link rel="canonical" href="__URL__"><meta property="og:type" content="article"><meta property="og:title" content="__TITLE__ | GYUCHUL Blog"><meta property="og:description" content="__DESC__"><meta property="og:url" content="__URL__"><meta property="og:site_name" content="GYUCHUL Blog"><meta property="article:published_time" content="__ISO__"><meta property="article:author" content="GyuChul Team"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="__TITLE__ | GYUCHUL Blog"><meta name="twitter:description" content="__DESC__"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+KR:wght@400;500;600&display=swap" rel="stylesheet"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"><link rel="stylesheet" href="/_astro/_slug_.Dkcx_5gs.css">
<link rel="stylesheet" href="/_astro/_slug_.BUPykhsI.css">
<link rel="stylesheet" href="/_astro/_slug_.S0rDoPdF.css"></head> <body style="--accent: __ACCENT__; --accent-rgb: __ACCENT_RGB__;"> <div class="reading-progress" id="reading-progress"></div> <header class="header"> <div class="header-inner"> <a href="/team/story" class="back-btn"> <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"> <path d="M19 12H5M12 19l-7-7 7-7"></path> </svg> <span>Stories</span> </a> <span class="header-title">GYUCHUL / STORY</span> </div> </header> <article class="article"> <div class="article-header"> <div class="meta"> <span class="type-badge story"> STORY </span> <time>__DATE_KR__</time> </div> <h1>__TITLE__</h1> <p class="summary">__SUMMARY__</p> <div class="tags">__TAGS__</div> </div> <div class="article-content prose">__BODY__</div> <div class="share-buttons"> <span class="share-label">공유하기</span> <button class="share-btn" id="copy-link" title="링크 복사"> <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"> <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path> <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path> </svg> </button> <button class="share-btn" id="share-twitter" title="Twitter에 공유"> <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"> <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path> </svg> </button> </div> <footer class="article-footer"> <a href="/team/story" class="footer-back"> <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"> <path d="M19 12H5M12 19l-7-7 7-7"></path> </svg> <span>목록으로 돌아가기</span> </a> </footer> </article> <button class="scroll-to-top" id="scroll-top" title="맨 위로"> <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"> <path d="M18 15l-6-6-6 6"></path> </svg> </button> <div class="lightbox" id="lightbox"> <button class="lightbox-close" id="lightbox-close">&times;</button> <img class="lightbox-img" id="lightbox-img" src="" alt=""> </div> <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script> <script>(function(){
  if (window.hljs) document.querySelectorAll('.prose pre code').forEach(function(b){ window.hljs.highlightElement(b); });
  if (window.renderMathInElement) window.renderMathInElement(document.querySelector('.prose'), { delimiters: [ { left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false } ], throwOnError: false });

  var progressBar = document.getElementById('reading-progress');
  var scrollTopBtn = document.getElementById('scroll-top');
  window.addEventListener('scroll', function(){
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    var scrolled = (window.scrollY / docHeight) * 100;
    if (progressBar) progressBar.style.width = Math.min(scrolled, 100) + '%';
    if (scrollTopBtn) { if (window.scrollY > 500) scrollTopBtn.classList.add('visible'); else scrollTopBtn.classList.remove('visible'); }
  });
  if (scrollTopBtn) scrollTopBtn.addEventListener('click', function(){ window.scrollTo({ top: 0, behavior: 'smooth' }); });

  var copyLinkBtn = document.getElementById('copy-link');
  var shareTwitterBtn = document.getElementById('share-twitter');
  if (copyLinkBtn) copyLinkBtn.addEventListener('click', async function(){ await navigator.clipboard.writeText(window.location.href); copyLinkBtn.classList.add('copied'); setTimeout(function(){ copyLinkBtn.classList.remove('copied'); }, 2000); });
  if (shareTwitterBtn) shareTwitterBtn.addEventListener('click', function(){ var text = encodeURIComponent(document.title); var url = encodeURIComponent(window.location.href); window.open('https://twitter.com/intent/tweet?text=' + text + '&url=' + url, '_blank'); });

  var lightbox = document.getElementById('lightbox');
  var lightboxImg = document.getElementById('lightbox-img');
  var lightboxClose = document.getElementById('lightbox-close');
  document.querySelectorAll('.prose img').forEach(function(img){ img.addEventListener('click', function(){ if (lightbox && lightboxImg) { lightboxImg.src = img.src; lightboxImg.alt = img.alt; lightbox.classList.add('active'); document.body.style.overflow = 'hidden'; } }); });
  function closeLightbox(){ if (lightbox) { lightbox.classList.remove('active'); document.body.style.overflow = ''; } }
  if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
  if (lightbox) lightbox.addEventListener('click', function(e){ if (e.target === lightbox) closeLightbox(); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeLightbox(); });
})();</script> </body></html>"""

LISTING_TEMPLATE = """<!DOCTYPE html><html lang="ko" data-astro-cid-la23qyh3> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Stories | GYUCHUL Blog</title><meta name="description" content="GyuChul 팀의 이야기 - 경험, 성장, 그리고 배움"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet"><link rel="stylesheet" href="/_astro/_slug_.Dkcx_5gs.css">
<link rel="stylesheet" href="/_astro/story.BanvMVp9.css"></head> <body data-astro-cid-la23qyh3> <header class="header" data-astro-cid-la23qyh3> <div class="header-inner" data-astro-cid-la23qyh3> <a href="/team" class="back-link" data-astro-cid-la23qyh3> <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-astro-cid-la23qyh3> <path d="M19 12H5M12 19l-7-7 7-7" data-astro-cid-la23qyh3></path> </svg> </a> <a href="/team" class="logo" data-astro-cid-la23qyh3> <span class="logo-text" data-astro-cid-la23qyh3>GYUCHUL</span> <span class="logo-divider" data-astro-cid-la23qyh3>/</span> <span class="logo-sub" data-astro-cid-la23qyh3>STORIES</span> </a> <div class="search-box" data-astro-cid-la23qyh3> <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-astro-cid-la23qyh3> <circle cx="11" cy="11" r="8" data-astro-cid-la23qyh3></circle> <path d="M21 21l-4.35-4.35" data-astro-cid-la23qyh3></path> </svg> <input type="text" id="search-input" placeholder="Search..." autocomplete="off" data-astro-cid-la23qyh3> </div> </div> </header> <main class="main" data-astro-cid-la23qyh3> <section class="hero" data-astro-cid-la23qyh3> <div class="hero-content" data-astro-cid-la23qyh3> <div class="hero-icon" data-astro-cid-la23qyh3> <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" data-astro-cid-la23qyh3> <path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 3-1-1.56-2.78-3-5-3a4.91 4.91 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06z" data-astro-cid-la23qyh3></path> <path d="M10 2c1 .5 2 2 2 5" data-astro-cid-la23qyh3></path> </svg> </div> <h1 class="hero-title" data-astro-cid-la23qyh3>Team Stories</h1> <p class="hero-desc" data-astro-cid-la23qyh3>우리 팀의 경험, 성장, 그리고 배움</p> <div class="hero-stats" data-astro-cid-la23qyh3> <span class="stat-number" data-astro-cid-la23qyh3>__COUNT__</span> <span class="stat-label" data-astro-cid-la23qyh3>stories</span> </div> </div> </section> <section class="filter-section" data-astro-cid-la23qyh3> <div class="filter-container" data-astro-cid-la23qyh3> __FILTERS__</div> </section> <section class="posts-section" data-astro-cid-la23qyh3> <div class="posts-container" data-astro-cid-la23qyh3> <div class="posts-list" data-astro-cid-la23qyh3> __CARDS__ </div> <div class="no-results" id="no-results" style="display: none;" data-astro-cid-la23qyh3> <p data-astro-cid-la23qyh3>검색 결과가 없습니다</p> </div> </div> </section> </main> <footer class="footer" data-astro-cid-la23qyh3> <div class="footer-inner" data-astro-cid-la23qyh3> <a href="/team" class="footer-logo" data-astro-cid-la23qyh3>GYUCHUL BLOG</a> </div> </footer> <script type="module">const i=document.getElementById("search-input"),r=document.querySelectorAll(".filter-btn"),f=document.querySelectorAll(".post-card"),u=document.getElementById("no-results");let l="all";function d(){const t=i?.value.toLowerCase().trim()||"";let e=0;f.forEach(n=>{const a=n.querySelector(".post-title")?.textContent?.toLowerCase()||"",o=n.querySelector(".post-summary")?.textContent?.toLowerCase()||"",s=n.getAttribute("data-tags")?.toLowerCase()||"",c=!t||a.includes(t)||o.includes(t)||s.includes(t),m=l==="all"||s.includes(l.toLowerCase());c&&m?(n.classList.remove("hidden"),e++):n.classList.add("hidden")}),u&&(u.style.display=e===0?"block":"none")}i?.addEventListener("input",d);r.forEach(t=>{t.addEventListener("click",()=>{l=t.getAttribute("data-tag")||"all",r.forEach(e=>e.classList.remove("active")),t.classList.add("active"),d()})});</script></body></html>"""


if __name__ == "__main__":
    main(sys.argv)
