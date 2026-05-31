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
├── team/                  # 팀 스토리
│   ├── index.html         # → /team/story/ 리다이렉트
│   ├── story/index.html   # 스토리 목록 (posts/index.json 으로 재생성됨)
│   └── <slug>/index.html  # 개별 포스트 (Gyu2ndAnniversary, codingTestProject3~6, …)
├── _astro/                # 팀 페이지용 CSS/JS (Astro 컴파일 산출물)
├── images/
│   ├── team-1.jpg, team-2.jpg
│   └── notion/            # 팀 포스트 본문 이미지
├── posts/                 # 새 글 작성용 마크다운 원고
│   ├── _TEMPLATE.md       # 복사해서 쓰는 템플릿
│   └── index.json         # 글 목록 매니페스트 (목록 페이지의 원본 데이터)
├── scripts/
│   ├── new_story.py       # 마크다운 → 글 HTML 생성 + 목록 갱신 (현재 방식)
│   └── sync_team_stories.py  # (구) Notion→Astro 동기화 — 소스 레포 사라져 미사용
└── .claude/skills/sync-team-stories/  # (구) Notion 동기화 스킬 — 미사용
```

## 개인 블로그

- CHUL: [su9king.github.io](https://su9king.github.io/)
- GYU: 준비 중

## 새 팀 스토리 글쓰기

Notion/Astro 없이 마크다운 파일 하나로 글을 추가한다. (완전 정적 — 댓글/조회수 백엔드 없음)

```bash
# 1) 초안 만들기 (posts/<slug>.md 생성)
py scripts/new_story.py --new "글 제목"

# 2) 만들어진 posts/<slug>.md 의 front matter(title/date/summary/tags) 와 본문을 채운다.
#    본문 이미지는 images/notion/ 에 넣고  ![설명](/images/notion/파일.png)  로 참조.

# 3) 빌드: team/<slug>/index.html 생성 + team/story/index.html 목록 자동 갱신
py scripts/new_story.py posts/<slug>.md

# 4) 로컬 확인
py -m http.server 8765   # → http://localhost:8765/team/story/

# 5) 커밋/푸시
git add team posts && git commit -m "Add story: <제목>" && git push
```

- 목록(`team/story/index.html`)은 `posts/index.json` 매니페스트로 재생성된다.
  목록만 다시 그리려면 `py scripts/new_story.py --rebuild`.
- 마크다운 작성법과 front matter 필드는 [`posts/_TEMPLATE.md`](posts/_TEMPLATE.md) 참고.
- 지원 문법: 제목(#,##,###), 문단, **굵게**, *기울임*, `코드`, [링크](), ![이미지](),
  목록(-, 1.), 인용(>), 표(| a | b |), 코드블록(```lang, 하이라이트 자동), 구분선, 수식($ KaTeX $).

> 예전 방식(`sync_team_stories.py` + `sync-team-stories` 스킬)은 `~/Desktop/gyuchul-web`
> Astro 소스 레포에 의존했는데 그 레포가 사라져 더 이상 동작하지 않는다. 위 마크다운 방식이 현재 표준.
