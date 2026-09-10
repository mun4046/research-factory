# 클라우드 routine 설정

Claude Code의 `/schedule`(cloud routine)로 매일 배치를 돌린다. routine은 격리된 클라우드 세션에서 저장소를 clone하고, 끝나면 push한다. 로컬 PC가 꺼져 있어도 된다.

## 사전 조건
- claude.ai 커넥터에 **PlayMCP**가 연결돼 있을 것 (routine은 claude.ai 커넥터만 쓸 수 있다. 로컬 MCP는 불가)
- Claude GitHub 앱이 이 저장소에 접근 가능할 것
- 저장소에 `CLAUDE.md`와 `.claude/skills/research-factory/`가 있을 것 (클라우드는 글로벌 설정을 못 보므로 규칙은 저장소 안에 있어야 한다)

## 설정값

| 항목 | 값 |
|---|---|
| 이름 | `research-factory 일일 배치` |
| cron (UTC) | `0 22 * * 1-5` — 화~토 07:00 KST. 미국 마감(06:00 KST)과 전날 한국 마감을 한 번에 |
| 모델 | `claude-sonnet-5` |
| 저장소 | `https://github.com/YOUR-ACCOUNT/YOUR-WIKI` |
| allowed_tools | `Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch` |
| MCP 커넥터 | PlayMCP |

## 프롬프트 (그대로 사용)

```
이 저장소는 LLM Wiki다. 먼저 저장소 루트의 CLAUDE.md를 읽고, 이어서 .claude/skills/research-factory/SKILL.md, 같은 폴더의 watchlist.md, references/ 아래 data-sources.md·entity-ticker.md·batch-funnel.md를 모두 읽어라.

그런 다음 research-factory의 batch 모드를 batch-funnel.md의 Stage 순서대로 실행하라. 오늘 날짜는 실행 시점의 KST(UTC+9) 기준이다 — UTC 22시에 실행되면 KST로는 다음날이므로 그 날짜를 쓴다.

데이터는 PlayMCP 커넥터 도구(koreaStock-*, koreaStockAnalyz-*, opendart-*, UsStockInfo-*, NaverSearch-*)와 WebSearch만 사용한다. 종목 하나에서 도구가 실패하면 그 종목만 건너뛰고 다이제스트의 '데이터 이슈'에 적는다. 전체 실행은 멈추지 않는다.

작업 시작 전 git pull --rebase. 끝나면 index.md와 log.md를 갱신하고 git add -A && git commit -m "research-factory: batch {YYYY-MM-DD}" && git push 한다. git user.name/user.email이 없으면 'research-factory bot' / 'bot@research-factory.local'로 설정한다. push 실패 시 git pull --rebase 후 1회 재시도하고, 그래도 실패하면 중단하고 원인을 보고하라.

마지막에 한국어로 요약 보고: 갱신 N건 / 신규 후보 M건 / dormant 전환 K건 / 데이터 이슈 / 커밋 해시.
```

## 확인
1. 생성 직후 "run now"로 1회 실행 → 5~15분 뒤 저장소에 `research-factory: batch …` 커밋이 오는지 확인
2. `pages/overview-market-{날짜}.md`의 "데이터 이슈" 문단을 읽는다 — 어떤 도구가 막혔는지 배치가 스스로 적는다
3. 같은 날 다시 실행해도 페이지가 중복되지 않는다 (`updated`가 오늘이면 건너뜀)

## 흔한 문제
- `403 You don't have access to a repository` — GitHub 앱 저장소 접근 미허용. 여러 GitHub 계정을 쓰면 claude.ai에 연결된 계정에서 설정해야 한다.
- push 거부 — 로컬에서 먼저 push한 커밋이 있을 때. routine은 pull --rebase 후 1회 재시도한다.
- EDGAR/일부 뉴스 사이트 차단 — 클라우드 egress 정책. 배치는 건너뛰고 기록만 남긴다.
