# Research-factory

미국·한국 종목/시장 리서치를 **매일 자동으로 축적하는 개인 위키** 템플릿. Claude Code 스킬 하나와 위키 규칙(Karpathy의 LLM Wiki 패턴)으로 이루어져 있고, 클라우드 routine이 매일 아침 저장소를 clone해 페이지를 쓰고 push한다.

> A Claude Code skill + wiki schema that accumulates US/KR stock research into a git-backed markdown wiki every morning. Korean-first; the skill instructions are in Korean.

## 무엇이 쌓이나

| 페이지 | 내용 |
|---|---|
| `pages/entity-{kr\|us}-{코드}.md` | 종목 1장 — 요약 / 개요·지표 5줄 / 촉매 표 / 뉴스 시계열 / 변경 이력 |
| `pages/concept-{테마}.md` | 같은 날 3종목 이상이 묶이는 테마 (원전, 광통신, 유가 …) — 자동 생성 |
| `pages/overview-market-{날짜}.md` | 일일 다이제스트 — 지수·테마·워치리스트 변화·신규 후보·데이터 이슈 |
| `pages/overview-week-{주차}.md` | 토요일 주간 요약 — 후보 승격/탈락 권고, 다음 주 일정 |
| `index.md`, `log.md` | 목차와 append-only 활동 로그 |

## 어떻게 돌아가나

```
07:05 KST  클라우드 routine ── clone ─▶ batch 모드 ─▶ commit/push
                                     │
                                     ├ Stage 0  워치리스트·후보 페이지 갱신 (시세·뉴스·공시)
                                     ├ Stage 1  후보 풀: 국내 [특징주] 기사, 미국 [미국 특징주] 기사
                                     ├ Stage 1c KR 전 시장 공시 스캔 (DART) — 수주·자사주·잠정실적·특허/임상
                                     ├ Stage 1d US 8-K 스캔 (SEC EDGAR) — 접근 가능할 때만
                                     ├ Stage 2  필터: 시총·ETF 제외·촉매 유무 → 시장별 3개
                                     ├ Stage 3  신규 후보 페이지
                                     ├ Stage 4  일일 다이제스트 + 4b 테마 클러스터 → concept 페이지
                                     └ Stage 6  토요일 주간 요약
07:40 KST  로컬 PC `git pull` ─▶ Obsidian에 반영
```

3가지 모드: `ticker`(종목 1개 심층) · `theme`(테마 → 개념 페이지 + 관련 종목) · `batch`(위 파이프라인).
데이터는 **PlayMCP 커넥터**(카카오 제공: koreaStock·koreaStockAnalyz·opendart·UsStockInfo·NaverSearch)와 WebSearch만 쓴다 — 로컬과 클라우드에서 같은 도구를 써야 결과가 일관되기 때문.

## 설치 (약 20분)

1. **이 템플릿으로 private 저장소 생성** — "Use this template" → private. 리서치 결과는 개인 데이터이므로 공개하지 않는다.
2. **로컬 clone** — OneDrive·Dropbox 같은 동기화 폴더 **밖**에 둔다(git 잠금 충돌).
3. **claude.ai에서 PlayMCP 커넥터 연결** — https://claude.ai/customize/connectors → PlayMCP(`https://playmcp.kakao.com/mcp`) 추가. 무료.
4. **Claude GitHub 앱에 저장소 접근 허용** — https://github.com/settings/installations → Claude → Repository access에 이 저장소 추가. 이걸 빼먹으면 routine 생성 시 `403 You don't have access to a repository`가 난다.
5. **이메일 교체** — `.claude/skills/research-factory/references/` 안의 `you@example.com`을 본인 이메일로 (SEC EDGAR가 User-Agent에 연락처를 요구).
6. **워치리스트** — `.claude/skills/research-factory/watchlist.md`에 종목을 넣는다.
7. **routine 생성** — Claude Code에서 `/schedule` 실행 후 [docs/routine-setup.md](docs/routine-setup.md)의 프롬프트·설정을 그대로 사용. 첫 실행은 "run now"로 돌려 push까지 되는지 확인.
8. (선택) **Obsidian**으로 clone 폴더를 vault로 열고, 작업 스케줄러에 07:40 `git pull`을 등록.
9. (선택, 미국 공시) 클라우드는 SEC EDGAR에 접근하지 못하므로 로컬 PC에서 `py -3 scripts/edgar_fetch.py --push`를 **06:40 KST**에 예약 실행한다. 표준 라이브러리만 쓰며 `data/edgar.json`(종목별 최근 30일 10-K/10-Q/8-K/13D/Form 4 + 전일 8-K 신호 항목)을 만들어 push하고, 배치는 이 파일을 우선 읽는다. `EDGAR_UA_EMAIL` 환경변수 또는 스크립트 상단의 이메일을 본인 것으로 바꿀 것.

## 로컬에서 바로 쓰기

clone 폴더에서 Claude Code를 열고:

```
research-factory ticker 삼성전자
research-factory theme AI 전력 인프라
research-factory batch
```

## 구조

```
CLAUDE.md                              위키 규칙 (Claude용) — 디렉터리·페이지 형식·git 규율
.claude/skills/research-factory/
  SKILL.md                             모드별 절차와 공통 규율
  watchlist.md                         관심 종목
  references/
    data-sources.md                    용도별 PlayMCP 도구 매핑, 폴백 순서
    entity-ticker.md                   종목 페이지 템플릿
    batch-funnel.md                    배치 Stage 0~6, 필터 기준, 공시 분류 규칙
docs/routine-setup.md                  클라우드 routine 설정
scripts/edgar_fetch.py                 로컬 EDGAR 수집기 (선택) → data/edgar.json
pages/  raw/  index.md  log.md         위키 본체 (raw/는 사용자가 넣는 원본만)
```

## 알아둘 제약

- KR 시세 랭킹 API는 개장 전(07시) 조회 시 0을 돌려주므로 배치는 기사·공시 기반으로 후보를 찾는다.
- SEC EDGAR는 클라우드 egress에서 차단된다. 로컬 `scripts/edgar_fetch.py`가 만든 `data/edgar.json`이 있으면 그것을 쓰고, 없으면 미국 공시 추적을 건너뛰고 다이제스트에 기록한다.
- 일부 미국 뉴스 사이트(seekingalpha·cnbc)는 클라우드에서 원문 접근이 막혀 검색 스니펫으로 대체된다.
- 배치 1회 비용은 워치리스트 크기에 비례한다. 기본 상한: 갱신 30종목 + 신규 후보 2개.

## 라이선스

MIT. 리서치 결과물의 투자 판단 책임은 사용자에게 있다.
