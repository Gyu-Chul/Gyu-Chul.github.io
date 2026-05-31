---
title: 글 제목을 여기에
date: 2026-06-01
summary: 목록에 보일 한 줄 요약
tags: 회고, Coding Test
slug: my-first-post
accent: "#7c5cff"
---

여기부터 본문입니다. 마크다운으로 자유롭게 작성하세요.

## 소제목

문단을 쓰고 **굵게**, *기울임*, `인라인 코드`, [링크](https://example.com) 를 쓸 수 있어요.

- 목록 항목 1
- 목록 항목 2
- 목록 항목 3

순서 있는 목록:

1. 첫째
2. 둘째

이미지는 `images/notion/` 폴더에 넣고 이렇게 참조합니다:

![이미지 설명](/images/notion/파일이름.png)

```python
print("코드 블록도 됩니다 (하이라이트 자동)")
```

| 항목 | 설명 |
| --- | --- |
| 표 | 도 됩니다 |

> 인용문도 됩니다.

---

작성이 끝나면 이 파일을 복사해서 새 이름으로 저장하고 (예: posts/2026-team-mt.md),
front matter 의 title / date / summary / tags / slug 을 바꾼 뒤 아래 명령을 실행하세요:

    py scripts/new_story.py posts/2026-team-mt.md
