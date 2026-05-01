# Gyu-Chul.github.io

GYUCHUL 팀 웹사이트 — 정적 HTML/CSS 기반.

## 배포

- GitHub Pages 자동 배포 (main 브랜치 → `https://gyu-chul.github.io/`)
- 커스텀 도메인 없음 (이전 `www.gyuchul.space` 는 만료 예정)

## 구조

```
.
├── index.html             # 메인 랜딩
├── 404.html               # 404 + 구 URL 리다이렉트 폴백
├── sitemap.xml
├── robots.txt
├── .nojekyll              # GH Pages가 _astro/ 디렉터리도 서빙하게 함
├── gyu/index.html         # GYU 프로필
├── chul/                  # 모두 https://su9king.github.io/ 로 리다이렉트
│   ├── index.html
│   └── blog/
│       ├── index.html
│       ├── tech/index.html
│       └── life/index.html
├── team/                  # 팀 스토리 (Notion 빌드 결과)
│   ├── index.html         # → /team/story/ 리다이렉트
│   ├── story/index.html   # 스토리 목록
│   └── <slug>/index.html  # 개별 포스트 (Gyu2ndAnniversary, codingTestProject3~6)
├── _astro/                # 팀 페이지용 CSS/JS (Astro 컴파일 산출물)
├── images/
│   ├── team-1.jpg, team-2.jpg
│   └── notion/            # 팀 포스트 본문 이미지
├── .claude/skills/sync-team-stories/  # Notion → HTML 동기화 스킬
└── scripts/sync_team_stories.py       # 동기화 헬퍼 스크립트
```

## 개인 블로그

- CHUL: [su9king.github.io](https://su9king.github.io/)
- GYU: 준비 중

## 새 팀 스토리 반영

노션에 새 글 작성 후 Claude Code 에서 "노션 새 글 반영" 또는 "팀 스토리 동기화" 라고 하면 [`sync-team-stories`](.claude/skills/sync-team-stories/SKILL.md) 스킬이 발동돼서 빌드/복사/클린업/푸시까지 처리.

수동으로 하려면:
```bash
cd ~/Desktop/gyuchul-web && npm run build
cd ~/Desktop/Gyu-Chul.github.io && python3 scripts/sync_team_stories.py
git status && git diff --stat
git add team _astro images/notion && git commit -m "Sync team stories" && git push
```
