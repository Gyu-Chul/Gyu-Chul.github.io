---
name: sync-team-stories
description: Sync new Notion-authored team Story posts from the gyuchul-web Astro+Notion source into this repo as static HTML, refresh _astro CSS / Notion images, strip dead links and the small-text footer nav, then ask the user to commit + push. Use when the user says "노션 새 글 반영", "팀 스토리 동기화", "sync team blog", or after writing a new team Story post in Notion.
---

# Sync team stories from Notion → this repo

Pipeline that converts a freshly-written Notion team Story post into a static HTML page in this repo. Reuses the existing Astro+Notion build in `~/Desktop/gyuchul-web` for the actual rendering, then copies and cleans the output.

## Trigger

Invoke whenever the user signals "I added a new team Story post in Notion, please reflect it on the site" — e.g. "노션 새 글 반영해", "팀 스토리 동기화", "sync team blog".

## Prerequisites

- `~/Desktop/gyuchul-web` repo must exist and contain the Astro project with a working `.env` (NOTION_API_KEY, NOTION_DATABASE_ID).
- `node_modules` may be missing on a fresh clone — `npm install` will be run if needed.
- This repo (`Gyu-Chul.github.io`) is the destination.

## Steps

1. **Build the Notion-driven HTML** in the source repo. The build itself is what queries Notion and renders to HTML, so it must run cleanly:

   ```bash
   cd ~/Desktop/gyuchul-web && npm install && npm run build
   ```

   If `npm install` is already done, you can skip it. The build outputs to `dist/`.

2. **Run the sync script** from this repo. It copies new `/team/<slug>/` directories, refreshes `_astro/*.css` (from `dist/server/_astro/` since Astro's vercel adapter splits CSS there) and `_astro/*.js` (from `dist/client/_astro/`), refreshes `images/notion/`, and applies the cleanup transformations:

   ```bash
   cd ~/Desktop/Gyu-Chul.github.io && python3 scripts/sync_team_stories.py
   ```

   Cleanup does:
   - **Dead-link stripping** — removes `<a href="/team/<unbuilt-slug>">…</a>` references for posts that exist in the listing markup but were never built (`chul2ndAnniversary`, `codingTestProject1`, `codingTestProject2`). Surgical (anchor only — never touches the surrounding `<article>` body).
   - **Listing card stripping** — on `team/story/index.html`, drops `<article>` cards whose only link goes to a dead slug.
   - **Footer-nav removal** — drops the cheap-looking small-text `<nav class="footer-nav">` from `team/story/index.html`.

3. **Verify locally**:

   ```bash
   cd ~/Desktop/Gyu-Chul.github.io && python3 -m http.server 8765 &
   open http://localhost:8765/team/story/
   ```

   Confirm the new post(s) appear on the listing and individual pages render with full styling. Kill the server when done: `lsof -ti:8765 | xargs kill`.

4. **Show diff and ask for commit/push approval**:

   ```bash
   cd ~/Desktop/Gyu-Chul.github.io && git status --short && git diff --stat
   ```

   Then ask the user explicitly before pushing — pushing to `main` of this user-pages repo is publicly visible, so it requires a clear go-ahead in the conversation. When approved:

   ```bash
   cd ~/Desktop/Gyu-Chul.github.io && git add team _astro images/notion && git commit -m "Sync team Story posts from Notion" && git push origin main
   ```

## Scope guarantees

- **Only team Story posts** are synced. Astro's build already filters by `Author=GyuChul` and `Category=Story` for `/team/`. The script copies the whole `dist/client/team/*` directory minus the empty `project/` listing.
- **CHUL personal blog stays redirected** — `/chul/*` redirect templates in this repo are NOT overwritten because the script only touches `/team/*`, `/_astro/*`, `/images/notion/*`.
- **GYU personal blog is left as "coming soon"** — unaffected.
- **Main pages (index, gyu, projects, projects/ragit)** — unaffected.

## When something looks off

- **CSS missing on live site** → confirm `.nojekyll` exists at the repo root (GitHub Pages skips underscore-prefixed dirs by default).
- **Some referenced CSS is 404** → the Astro build hash changed; re-run `sync_team_stories.py` so the new hashed filenames are copied.
- **A new post links to a draft post that was never built** → add the unbuilt slug to `DEAD_SLUGS` in `scripts/sync_team_stories.py` and re-run.
- **Cache shows old version after push** → hard refresh (`Cmd+Shift+R`) or open in incognito; GH Pages cache TTL is ~10 min.

## Future migration note

This skill currently depends on `~/Desktop/gyuchul-web` to do the Notion → HTML rendering. When that source repo is eventually deleted (after `gyuchul.space` domain expiry and full Vercel cleanup), this skill must be rewritten as a self-contained Python/Node script that calls the Notion API directly. The cleanup pipeline (dead-link stripping, footer-nav removal) is already self-contained in `scripts/sync_team_stories.py` and can be reused.
