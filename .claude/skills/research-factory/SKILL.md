---
name: research-factory
description: 미국·한국 종목/시장 리서치를 이 위키(LLM Wiki)에 축적하는 파이프라인. 3모드 — ticker(종목 1개 심층 페이지), theme(테마 → 개념 페이지 + 관련 종목), batch(워치리스트 전체 갱신 + 시장 퍼널로 신규 후보 발굴 + 일일 다이제스트). "종목 리서치해줘", "research-factory", "배치 돌려", 티커/회사명 분석 요청, 테마 리서치 요청에 사용. 데이터는 PlayMCP 커넥터(koreaStock/koreaStockAnalyz/opendart/UsStockInfo/NaverSearch)와 WebSearch만 사용한다.
---

# Research-factory

이 위키(repo 루트 `CLAUDE.md`의 규칙)에 종목·시장 리서치 페이지를 만들고 갱신한다. 로컬 세션과 클라우드 routine이 같은 절차를 따른다.

## 실행 전제

- 작업 디렉터리는 repo 루트(`index.md`, `log.md`, `pages/`가 있는 곳). 아니면 중단하고 알린다.
- 데이터 도구는 `references/data-sources.md`의 PlayMCP 도구만 쓴다. 로컬 DART MCP·기타 MCP는 쓰지 않는다(클라우드와 결과가 달라진다).
- API 응답을 `raw/`에 저장하지 않는다. 페이지 본문에 "출처 · 조회일"을 적는다.

## 0단계 — 공통 규율 (모든 모드)

1. `git pull --rebase`. 실패하면 중단하고 원인을 보고한다.
2. `index.md`를 읽는다. 대상 티커/회사명을 언급하는 기존 페이지(`query-*`, `overview-*` 등)를 찾아 새 페이지의 `sources`와 본문 링크에 연결한다.
3. 기존 `entity-*` 페이지가 있으면 **덮어쓰지 않는다**:
   - 섹션 1·2(요약·개요): 바뀐 사실만 수정
   - 섹션 3(촉매): 새 이벤트 append, 기존 이벤트는 상태만 갱신
   - 섹션 4(뉴스): 새 항목을 맨 위에 append. 이미 있는 헤드라인은 넣지 않는다
   - 새 데이터가 기존 서술과 충돌하면 해당 줄에 `⚠ {YYYY-MM-DD} 갱신: 이전 "…"과 충돌` 을 남긴다
4. 페이지 frontmatter `updated`가 오늘이면 그 페이지는 건너뛴다(같은 날 재실행 멱등).
5. 종료 시 `index.md`(Entities → Tickers 섹션)와 `log.md`(맨 아래 append)를 갱신한다.
6. `git add -A && git commit -m "research-factory: {mode} {대상} {YYYY-MM-DD}" && git push`. push 실패 시 `git pull --rebase` 후 1회 재시도, 그래도 실패하면 중단하고 보고한다.

## 모드

### ticker — 종목 1개

입력: 티커 코드 또는 회사명. 시장 판별: 6자리 숫자 → KR, 알파벳 → US, 회사명 → `resolve_stock`(KR) 또는 `get_stock_info`(US)로 해석. 모호하면 사용자에게 묻는다.

1. `references/data-sources.md`의 KR/US 열에서 시세·개요·공시·리스크·뉴스(최근 30일)를 가져온다.
2. `references/entity-ticker.md` 템플릿으로 `pages/entity-{kr|us}-{code}.md`를 생성/갱신한다. `status`는 `watchlist.md`에 있으면 `watchlist`, 아니면 `candidate`.
3. 0단계 5·6 수행. 사용자에게 한 줄 요약과 페이지 경로를 보고하고, `candidate`면 "watchlist.md에 추가하면 배치가 계속 갱신"이라고 알린다.

### theme — 테마

입력: 테마 문장(예: "K-뷰티 수출", "AI 전력 인프라").

1. 뉴스 도구(KR: `NaverSearch-search_news`, `market_get_news` / US: WebSearch, `get_finance_news`)로 최근 30일 테마 흐름과 거론되는 종목을 수집한다.
2. `pages/concept-{slug}.md`를 생성/갱신한다: 테마 정의, 동인, 수혜/피해 구조, 관련 종목 표(시장·티커·역할·링크), 리스크. 내부 링크는 `[[entity-...]]`.
3. 관련 종목 중 상위 3개(시장 합산)를 ticker 모드로 처리한다. 이미 페이지가 있으면 갱신만.
4. 0단계 5·6 수행.

### batch — 정기 배치

입력 없음. `watchlist.md`와 `references/batch-funnel.md`를 읽고 Stage 0 → 1(랭킹·특징주 기사) → 1c(KR 공시 스캔) → 2 → 3 → 4 → 4b(테마 클러스터) → 6(토요일만 주간 요약) → 5 순서로 수행한다. 종목 하나에서 도구가 실패하면 그 종목만 건너뛰고 다이제스트의 "데이터 이슈"에 적는다. 전체 실행은 멈추지 않는다.

## 참조 파일

- `references/data-sources.md` — 용도별 PlayMCP 도구 매핑(KR/US), 실패 시 대체 순서
- `references/entity-ticker.md` — 종목 페이지 템플릿과 각 섹션 작성 규칙
- `references/batch-funnel.md` — 배치 Stage 0~5, 후보 필터 기준, 다이제스트 템플릿, 후보 수명
- `watchlist.md` — 사용자가 편집하는 티커 목록

## 출력 규칙

- 한국어. 개조식보다 완결 문장. 숫자는 단위·조회일과 함께.
- 추정과 사실을 구분한다("~로 보인다" vs "공시 기준").
- 페이지 밖에 별도 보고서 파일을 만들지 않는다. 산출물은 위키 페이지와 log 항목뿐이다.
