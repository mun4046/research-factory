# LLM Wiki Schema

이 문서는 Claude가 이 위키(repo 루트)를 유지하는 방법을 정의한다.
Karpathy의 LLM Wiki 패턴(https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)을 기반으로 한다.
로컬 세션과 클라우드 routine 모두 이 문서를 따른다.

---

## 디렉터리 구조

```
./                (repo 루트 — private GitHub repo)
├── raw/          # 원본 소스 (불변 — 절대 수정하지 않음). 사용자가 넣는 PDF·리포트만
├── data/         # 로컬 스크립트가 생성하는 기계 데이터 (edgar.json — scripts/edgar_fetch.py). 배치가 읽기만 한다
├── pages/        # Claude가 생성·유지하는 마크다운 위키 페이지
├── index.md      # 콘텐츠 카탈로그 (모든 pages/ 항목 목록)
├── log.md        # 시간순 append-only 활동 로그
└── .claude/skills/research-factory/   # 종목·시장 리서치 파이프라인 (SKILL.md 참조)
```

---

## 핵심 원칙

1. **raw/ 는 불변**: 원본 소스는 절대 수정하지 않는다. 읽기만. API 응답(시세·뉴스·공시)은 raw/에 저장하지 않는다 — 재조회 가능하므로 페이지에 "출처 · 조회일"만 적는다.
2. **pages/ 는 Claude 소유**: Claude가 생성·수정·삭제한다. 사용자는 읽기만.
3. **index.md 는 항상 최신**: 모든 ingest/수정 후 반드시 업데이트.
4. **log.md 는 append-only**: 기존 항목 절대 수정하지 않음. 항상 맨 아래에 추가.
5. **교차 참조 유지**: 새 소스 ingest 시 기존 관련 pages도 업데이트.
6. **모순 명시**: 새 정보가 기존 주장과 충돌하면 해당 페이지의 해당 줄에 `⚠ {YYYY-MM-DD} 갱신: 이전 "…"과 충돌` 형태로 표시. 조용히 덮어쓰지 않는다.

---

## Git 규칙

이 위키는 로컬과 클라우드 routine이 함께 쓴다. 모든 작업은:

1. 시작: `git pull --rebase`. 실패하면 중단하고 보고.
2. 종료: `git add -A && git commit -m "{작업유형}: {요약} {YYYY-MM-DD}" && git push`. push 실패 시 `git pull --rebase` 후 1회 재시도, 그래도 실패하면 중단하고 보고.
3. 커밋 없이 끝내지 않는다. 변경이 없으면 커밋하지 않는다.

---

## 작업 워크플로우

### Ingest (새 소스 추가)
사용자가 새 소스를 raw/에 넣거나 URL/텍스트를 직접 제공할 때:

1. 소스를 읽는다
2. 사용자와 핵심 내용 논의 (필요시)
3. `pages/` 에 요약 페이지 작성: `pages/src-{slug}.md`
4. 관련 엔티티·개념 페이지 업데이트 (없으면 생성)
5. `index.md` 업데이트
6. `log.md` 에 항목 추가: `## [YYYY-MM-DD] ingest | {제목}`

### Query (질의)
사용자가 질문할 때:

1. `index.md` 를 읽어 관련 페이지 파악
2. 관련 `pages/` 파일 읽기
3. 인용과 함께 답변 합성
4. 가치 있는 답변은 새 페이지로 `pages/` 에 저장
5. `log.md` 에 항목 추가: `## [YYYY-MM-DD] query | {질문 요약}`

### Research (종목·시장 리서치)
`.claude/skills/research-factory/SKILL.md`를 따른다. 모드: `ticker` / `theme` / `batch`.
`log.md` 항목: `## [YYYY-MM-DD] research | {mode} {대상}` (batch는 `## [YYYY-MM-DD] batch | 시장 다이제스트`)

### Lint (건강 점검)
사용자가 점검 요청 시:

- 페이지 간 모순 탐지
- 최신 소스에 의해 대체된 낡은 주장
- 인바운드 링크 없는 고아 페이지
- 언급만 되고 자체 페이지 없는 중요 개념
- 누락된 교차 참조
- 웹 검색으로 채울 수 있는 데이터 공백
- `log.md` 에 항목 추가: `## [YYYY-MM-DD] lint | 점검 완료`

---

## 페이지 파일명 규칙

| 유형 | 패턴 | 예시 |
|------|------|------|
| 소스 요약 | `src-{slug}.md` | `src-llm-wiki-karpathy.md` |
| 개념/테마 | `concept-{slug}.md` | `concept-rag.md`, `concept-k-beauty-export.md` |
| 엔티티(인물) | `person-{slug}.md` | `person-karpathy.md` |
| 엔티티(도구) | `tool-{slug}.md` | `tool-obsidian.md` |
| 엔티티(종목) | `entity-{kr\|us}-{code}.md` | `entity-kr-214450.md`, `entity-us-nvda.md` |
| 질의 결과 | `query-{slug}.md` | `query-llm-vs-rag.md` |
| 개요/종합 | `overview-{slug}.md` | `overview-llm-wiki.md` |
| 일일 시장 다이제스트 | `overview-market-{YYYYMMDD}.md` | `overview-market-20260908.md` |

종목 코드: KR은 6자리 숫자, US는 심볼 소문자.

---

## 페이지 형식

```markdown
---
title: {제목}
type: {src|concept|person|tool|entity|query|overview}
tags: [tag1, tag2]
sources: [src-slug1.md, src-slug2.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

{본문 — 마크다운, 내부 링크는 [[페이지명]] 형식}
```

종목 페이지(`type: entity`)는 `market`, `ticker`, `status: watchlist|candidate|dormant` 필드가 추가되며, 본문 섹션은 `.claude/skills/research-factory/references/entity-ticker.md` 템플릿을 따른다.

---

## index.md 형식

각 항목: `- [[파일명]] — 한 줄 설명 (날짜)`
섹션: Sources / Concepts / Entities (Persons · Tools · Tickers) / Queries / Overviews
같은 이름의 섹션을 두 번 만들지 않는다. 항목은 해당 섹션에만 추가한다.

---

## log.md 형식

```
## [YYYY-MM-DD] {ingest|query|research|batch|lint} | {제목/설명}
- {간단한 변경 내용 요약}
```

`grep "^## \[" log.md | tail -5` 로 최근 5개 파악 가능.

---

## Notion 연동 (로컬 세션에서만)

중요한 페이지는 Notion MCP를 통해 사용자의 Notion 워크스페이스에도 동기화할 수 있다.
사용자가 요청 시 `mcp__plugin_notion_notion__notion-create-pages` 또는 `notion-update-page` 를 사용.
