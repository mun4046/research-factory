# 배치 퍼널 — batch 모드 절차

주기: 화~토 07:00 KST(`0 22 * * 1-5` UTC). 미국 마감(06:00 KST)과 전날 한국 마감을 한 번에 다룬다.
예산: 갱신 대상 ≤30 종목 + 신규 후보 ≤6 + 다이제스트 1장. 넘으면 워치리스트 우선, 후보는 오래된 순으로 제외.

## Stage 0 — 기존 페이지 갱신
1. `watchlist.md`의 모든 티커 + `pages/entity-*` 중 `status: candidate`이고 `created`가 30일 이내인 페이지를 모은다.
2. `status: candidate`이고 `created`가 30일을 넘긴 페이지는 `status: dormant`로 바꾸고 섹션 5에 기록. 이후 갱신하지 않는다.
3. 각 종목을 `data-sources.md` 규칙(배치 상한 4회)으로 갱신: 지표 표, 새 뉴스 append, 촉매 상태. `updated`가 오늘이면 건너뜀.
4. 갱신 중 눈에 띄는 것(전일 대비 ±5% 이상, 새 공시, 촉매 완료)을 Stage 4용으로 메모.
5. **종목별 공시 추적** — 마지막 `updated` 이후 새 공시가 있으면 섹션 3 촉매 표에 "완료" 행(공시명·날짜·링크)으로 넣고, 정기보고서면 섹션 2 지표·서술도 갱신한다.
   - US (SEC EDGAR, 클라우드에서는 `sec.gov` 직접 접근이 egress 차단되므로 **Jina 프록시 경유**): 
     1. CIK: 페이지 frontmatter에 `cik:`가 있으면 그것을 쓴다. 없으면 한 번만 조회해 frontmatter에 저장 — Bash: `curl -s -H "X-Return-Format: text" https://r.jina.ai/https://www.sec.gov/files/company_tickers.json | python3 -c "import sys,json;t=sys.stdin.read();d=json.loads(t[t.find('{'):]);print([v['cik_str'] for v in d.values() if v['ticker']=='{티커}'])"` (800KB이므로 반드시 python으로 걸러 출력하고 파일 전체를 읽지 않는다).
     2. 공시 목록: `curl -s -H "X-Return-Format: text" https://r.jina.ai/https://data.sec.gov/submissions/CIK{10자리 0패딩}.json` → `filings.recent`의 `form`·`filingDate`·`accessionNumber`·`primaryDocument` 배열(같은 인덱스끼리 한 건). 마지막 `updated` 이후만 본다. 링크는 `https://www.sec.gov/Archives/edgar/data/{cik}/{accessionNumber에서 하이픈 제거}/{primaryDocument}`.
     3. `form`별 처리: `10-K`/`10-Q`(실적·리스크 요인 → 촉매 "완료" + 섹션 2 갱신), `8-K`(촉매; 항목은 알 수 없으므로 뉴스로 보완), `SC 13D`(행동주의 → 촉매), `4`(임원 거래 — **매수만** 뉴스 섹션에 한 줄, 매도·`144`는 무시), `N-PX`·`3`·`S-8`·`424B*` 무시.
     4. 직접 접근이 되는 환경(로컬)에서는 `r.jina.ai/` 접두어를 빼고 `-A "research-factory bot you@example.com"`을 붙여 같은 URL을 호출한다.
   - KR: `koreaStock-dart_search_filings(stockCode, start_date=마지막 updated, end_date=오늘)` — 사업·반기·분기보고서, 주요사항보고서, 공정공시(잠정실적), 단일판매공급계약을 같은 방식으로 반영. IR 개최·안내공시는 무시.

## Stage 1 — 후보 풀
- KR 랭킹(`market_get_movers`)은 **배치에서 쓰지 않는다** — 07시 KST 개장 전에는 등락률·거래대금·거래량이 전량 0으로 오고, `new_high_low`는 도구 미구현(NOT_IMPLEMENTED)이다(2026-09-09·10 확인). 장중에 도는 `ticker`/`theme` 모드에서만 참고한다. KR 후보 풀은 아래 [특징주] 기사와 Stage 1c 공시로 만든다.
- KR 특징주 기사: `NaverSearch-search_news(query="[특징주]", sort="date", display=40)` — 전 거래일 장중에 나온 [특징주] 기사에서 종목명·등락·이유를 뽑는다. 랭킹에 없어도 기사에 촉매가 명시된 종목은 후보 풀에 넣는다. 여러 종목이 같은 테마(예: 원전주, 광통신주)로 묶이면 테마명을 메모해 Stage 4 "섹터" 문단에 쓴다.
- US 주 소스: `NaverSearch-search_news(query="미국 특징주", sort="date", display=30)` — newspim·edaily의 [미국 특징주]/[美특징주] 기사. 대부분 티커가 본문에 있고(예: "퀄컴(QCOM)", "종목코드: BSX") 촉매가 제목에 있다. 티커가 없으면 `UsStockInfo-get_stock_info`로 회사명을 해석한다. 여기서 최대 20.
- US 보조: `get_market_overview`(지수·VIX·금리·유가는 Stage 4용) + `get_recommendations`. WebSearch("biggest stock movers {날짜}")는 특징주 기사가 5건 미만일 때만 쓴다.
- 하락 특징주도 후보가 될 수 있다(가이던스 철회·사이버공격·행동주의 압박 등). 단, Stage 2에서 "왜 보는지"를 반드시 적는다.
- 이미 `status: candidate` 페이지가 있는 종목은 Stage 0에서 갱신 대상이므로 여기서 다시 뽑지 않는다.

## Stage 1c — 공시 스캔 (KR)
`opendart-search_disclosures(bgn_de=end_de=전 거래일, corp_cls=Y|K, page_count=100)` — 코스피·코스닥 각 2페이지(하루 120~200건씩)로 전일 공시를 모두 받는다. 유형 필터가 없으므로 `report_nm`을 아래 규칙으로 분류한다. 이 단계는 4회 호출로 끝내고, 개별 공시 본문은 읽지 않는다(제목과 회사명으로 충분).

**후보 신호 (후보 풀에 넣고, 워치리스트/기존 페이지 종목이면 섹션 3 촉매 표에 "완료" 행 추가)**
- `단일판매ㆍ공급계약체결` — 수주. 정정([기재정정]) 포함
- `자기주식취득결정`, `자기주식취득신탁계약체결결정` — 자사주 매입
- `영업(잠정)실적`, `연결재무제표기준영업(잠정)실적` — 실적 공시
- `투자판단관련주요경영사항` — 특허·임상·인허가 등(괄호 안 내용을 그대로 촉매에 적는다)
- `타법인주식및출자증권취득결정`, `회사합병결정`, `회사분할결정` — M&A·구조 변화
- `최대주주변경`, `최대주주변경을수반하는주식담보제공계약체결` — 지배구조
- `풍문또는보도에대한해명` — 시장 관심이 쏠린 종목의 신호. 내용은 뉴스로 확인

**경고 신호 (후보로 넣지 않는다. 워치리스트 종목이면 섹션 3에 "리스크" 행 추가, 다이제스트 "데이터 이슈" 아래 "경고 공시" 목록에 기록)**
- `유상증자결정`(희석), `전환사채/신주인수권부사채 발행결정`, `감자결정`
- `영업정지`, `회생절차개시신청`, `횡령ㆍ배임혐의발생`, `소송등의제기`
- `주권매매거래정지`, `상장폐지`, `투자유의안내`, `관리종목`

**무시**
- `임원ㆍ주요주주특정증권등소유상황보고서`, `주식등의대량보유상황보고서`, `최대주주등소유주식변동신고서`(단독으로는 노이즈)
- `일괄신고추가서류`, `투자설명서`, `증권신고서(채무증권)`, `증권발행실적보고서` — 증권사 파생상품 발행
- `기업설명회(IR)개최`, `주주총회소집`, `주주명부폐쇄`, `전환가액의조정`, `전환청구권행사`, `사업보고서/반기보고서` 정기공시
- `flr_nm`이 `유가증권시장본부`/`코스닥시장본부`인 시장안내
- 리츠·스팩·ETF 발행사

후보 신호 종목은 Stage 2로 넘긴다. 공시는 그 자체가 촉매이므로 Stage 2의 "뉴스 촉매" 조건을 충족한 것으로 본다. 단, 시총 필터와 시장별 상위 3개 상한은 그대로 적용한다.

## Stage 1d — 공시 스캔 (US, SEC EDGAR)
접근 경로 두 가지. 먼저 직접 접근을 시도하고, 200이 아니면(클라우드 egress 차단 시 403/000) **Jina text 모드**로 같은 URL을 부른다:
- 직접: `curl -s -A "research-factory bot you@example.com" "<URL>"` — UA에 연락처가 없으면 SEC가 403을 준다. 초당 10회 이하.
- Jina 경유(클라우드): `curl -s -H "X-Return-Format: text" "https://r.jina.ai/<URL>"` — **반드시 text 모드**. 기본(markdown)·html 모드는 Atom 항목이 비어서 온다(2026-09-10 확인). text 모드 출력은 항목마다 `8-K - 회사명 (CIK) (Filer)` 줄, `Filed: 날짜 AccNo: … Size: …` 줄, `Item N.NN: 설명` 줄들이 순서대로 나온다. 한 페이지 100건이 약 60~70KB이므로 Bash에서 `grep -E "^8-K|Item [0-9]|^ *Filed:"`로 걸러 읽고 원문 전체를 컨텍스트에 넣지 않는다.
API 키는 필요 없다.

1. 전일 8-K: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&count=100&start={0,100,200,300}&output=atom` — 4페이지(400건)로 전 거래일(ET) 8-K를 대체로 커버한다. 각 `<entry>`의 `<summary>`에 `Item N.NN: 설명`이 있으니 그것으로 분류한다. 본문은 읽지 않는다.
   - **신호**: `Item 1.01`(중요 계약 체결), `Item 2.01`(인수·자산 취득 완료), `Item 1.03`(파산), `Item 5.02`(CEO/CFO 등 임원 교체), `Item 2.02`(실적 발표 — 실적 시즌엔 수백 건이므로 워치리스트·기존 페이지 종목만 반영)
   - **무시**: `7.01`(Reg FD), `9.01`(첨부), `8.01`(제목만으로 판단 불가), `3.02`, `5.07`(주총 결과), `2.03`(차입)
2. 신호 항목은 회사명·CIK만 있고 티커가 없다. **후보로 올릴 상위 10개만** `https://data.sec.gov/submissions/CIK{10자리, 0패딩}.json`의 `tickers`로 변환한다. `tickers`가 비어 있으면(비상장 채권 발행사·펀드·SPAC 트러스트) 제외.
3. `SC 13D`(행동주의·5% 이상 취득): `...action=getcurrent&type=SC+13D&count=40&output=atom`. 비어 있는 날이 많다. 있으면 신호로 넣는다.
4. 시총 필터($2B)와 시장별 상위 3개 상한은 Stage 2 그대로. 특징주 기사(Stage 1)와 겹치면 "공시+기사"로 우선순위를 올린다.
5. HTTP 403/000(egress 차단)이면 다이제스트 "데이터 이슈"에 "EDGAR 차단"을 적고 건너뛴다.

## Stage 2 — 필터 (순서대로 적용)
1. 이미 `entity-*` 페이지가 있거나 워치리스트에 있으면 제외(Stage 0에서 처리됨)
2. ETF·SPAC·우선주·스팩 제외
3. 시가총액 KR 3,000억 원 / US $2B 미만 제외
4. 최근 7일 내 뉴스 촉매(실적·수주·규제·M&A 등 구체적 사건)가 확인되지 않으면 제외
5. 남은 것 중 시장별 상위 3개 — 기준: 촉매의 구체성 > 거래량 증가 > 등락률

## Stage 3 — 신규 후보 페이지
`entity-ticker.md` 템플릿으로 생성, `status: candidate`. 섹션 4에는 촉매가 된 뉴스 1~3건만. 섹션 1에 "왜 보는지 = 어떤 촉매로 퍼널을 통과했는지"를 적는다.
기사 본문은 **최종 후보(≤6)에 대해서만** `r.jina.ai`로 읽는다 — 후보 풀 전체에는 NaverSearch의 제목·description만 쓴다. 본문에서 숫자(계약 규모·등락률·목표치)를 뽑아 촉매 표에 넣고, 원문 URL을 뉴스 항목에 남긴다. Jina가 차단되면 description으로 쓰고 "원문 미확인"을 적는다.

## Stage 4 — 일일 다이제스트 `pages/overview-market-{YYYYMMDD}.md`

```markdown
---
title: 시장 다이제스트 YYYY-MM-DD
type: overview
tags: [market, daily]
sources: [PlayMCP koreaStock, PlayMCP UsStockInfo]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# 시장 다이제스트 YYYY-MM-DD

## 지수 · 섹터
{KOSPI/KOSDAQ 전일 등락(`market_get_index` — 07시 KST 조회면 전일 종가), 강세·약세 섹터는 [특징주] 기사·뉴스 헤드라인에서 / S&P·NASDAQ·VIX·유가는 `get_market_overview`. `market_get_sector`는 쓰지 않는다(업종 지수 OHLCV만 주고 sector_code 필수). 4~6문장.}

## 워치리스트 변화
| 종목 | 등락 | 무슨 일 |
|---|---|---|
{Stage 0에서 메모한 것만. 없으면 "특이사항 없음".}

## 신규 후보
| 시장 | 종목 | 촉매 | 페이지 |
|---|---|---|---|
{Stage 3 결과. [[entity-...]] 링크.}

## 데이터 이슈
{도구 실패·빈 응답·건너뛴 종목. 없으면 "없음".}
```

## Stage 4b — 테마 클러스터 → concept 페이지
Stage 1의 특징주 기사와 Stage 0 갱신에서 **같은 날 3종목 이상이 하나의 이유로 묶이면** 테마로 본다(예: 원전주, 광통신주, 양자컴퓨팅). KR·US를 합쳐 판단한다(코닝-버라이즌 → 국내 광통신주처럼 시장을 넘는 연결이 흔하다).
1. `index.md` Concepts에서 같은 테마의 `concept-*`가 있으면 갱신, 없으면 `pages/concept-{slug}.md` 생성(slug는 영문 소문자-하이픈, 예: `concept-nuclear-export`, `concept-optical-network`).
2. 페이지 구성: 테마 정의 1문단 / 동인(무슨 사건이 이 테마를 움직이는지) / 관련 종목 표(시장·티커·역할·당일 등락·`[[entity-...]]` 링크, 페이지 없는 종목은 링크 없이 이름만) / 시계열 "테마 흐름"(날짜·사건 append, 최신 위) / 리스크.
3. 갱신 시 "테마 흐름"에 오늘 항목을 append하고 관련 종목 표에 새 종목을 추가한다. 이미 있는 종목은 등락만 갱신.
4. 하루 최대 3개 테마. 4개 이상이면 관련 종목 수가 많은 순.
5. 다이제스트 "지수 · 섹터" 문단 끝에 `테마: [[concept-...]], [[concept-...]]`로 링크한다. `index.md` Concepts 섹션에 추가.

## Stage 6 — 주간 요약 (토요일 실행일에만)
KST 기준 실행일이 토요일이면 Stage 5 전에 `pages/overview-week-{YYYY}-W{주차}.md`를 만든다(ISO 주차, 예: `overview-week-2026-W37.md`). 이번 주 `overview-market-*` 5장과 `entity-*` 변경 이력을 읽어 작성한다. 새 API 호출은 하지 않는다.

```markdown
---
title: 주간 요약 {YYYY}-W{주차} ({월/일}~{월/일})
type: overview
tags: [market, weekly]
sources: [overview-market-{YYYYMMDD} ×5]
created: / updated:
---

# 주간 요약 {YYYY}-W{주차}

## 이번 주 시장
{KOSPI/KOSDAQ/S&P/NASDAQ 주간 등락과 주도 테마 3~5문장. [[concept-...]] 링크.}

## 워치리스트 주간 성적
| 종목 | 주간 등락 | 이번 주 핵심 사건 | 촉매 상태 변화 |

## 후보 판정
| 종목 | 등록일 | 등록 이유 | 이후 흐름 | 권고 |
{권고: 워치리스트 승격 / 계속 관찰 / dormant 전환 권고. 판단 근거 한 줄. 사용자가 watchlist.md에 넣어야 승격되므로 여기서는 권고만 한다.}

## 다음 주 일정
{entity-* 섹션 3의 "예정" 이벤트 중 다음 주에 걸리는 것. 없으면 "확인된 일정 없음".}

## 데이터 이슈 누적
{이번 주 다이제스트의 데이터 이슈 합계. 반복되는 도구 실패가 있으면 명시.}
```

`index.md` Overviews에 추가, `log.md`에는 batch 항목 안에 "주간 요약 생성"을 한 줄 덧붙인다.

## Stage 5 — 마무리
- `index.md`: Tickers 섹션에 신규 후보 추가, Overviews에 다이제스트 추가, dormant 전환은 설명에 표시
- `log.md`: `## [YYYY-MM-DD] batch | 시장 다이제스트` + 갱신 N건 / 신규 M건 / dormant K건 / 이슈
- commit·push (SKILL.md 0단계 6)
