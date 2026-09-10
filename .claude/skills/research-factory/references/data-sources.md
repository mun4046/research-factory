# 데이터 소스 — PlayMCP 도구 매핑

모든 도구는 PlayMCP 커넥터 소속이다. 도구 이름 접두어(`mcp__claude_ai_PlayMCP__`, `mcp__PlayMCP__` 등)는 실행 환경에 따라 다르므로 뒤쪽 이름으로 찾는다. 페이지에 적을 때는 "출처: PlayMCP koreaStock · 조회 2026-09-08" 형식.

| 용도 | KR | US |
|---|---|---|
| 티커/회사명 해석 | `koreaStock-resolve_stock` | `UsStockInfo-get_stock_info` |
| 현재가·시총·52주 | `koreaStock-stock_get_quote` | `UsStockInfo-get_stock_info` |
| 가격 히스토리(반응 확인) | `koreaStock-stock_get_price_history` | `UsStockInfo-get_historical_stock_prices` |
| 회사 개요·사업 | `koreaStock-dart_get_company_overview`, `opendart-get_company_info` | `UsStockInfo-get_stock_info` |
| 공시·실적 발표(종목별) | `koreaStock-dart_search_filings(stockCode, start_date, end_date)` | SEC EDGAR `data.sec.gov/submissions/CIK{10자리}.json`(`filings.recent`) — 클라우드에서는 `https://r.jina.ai/` 접두어 + `-H "X-Return-Format: text"`로 경유(sec.gov 직접 접근은 egress 차단). CIK는 `sec.gov/files/company_tickers.json`(Jina 경유, python으로 필터)에서 1회 조회 후 frontmatter `cik:`에 저장. 절차는 batch-funnel.md Stage 0-5. 재무 수치는 `UsStockInfo-get_financial_statement` |
| US 공시 캐시(우선) | — | `data/edgar.json` — 로컬 `scripts/edgar_fetch.py`(표준 라이브러리, 06:40 KST 예약 작업)가 생성·push. `tracked`(종목별 최근 30일 공시), `market_8k_signals`(전일 8-K 중 1.01/2.01/1.03/5.02/2.02), `sc13d`, `issues`. `generated_at` 24시간 이내면 아래 두 행 대신 이것을 쓴다 |
| 전 시장 공시 스캔(US) | (KR은 아래 행) | EDGAR Atom `browse-edgar?action=getcurrent&type=8-K…` — **직접 접근이 되는 환경에서만**(클라우드 차단, Jina로도 불가). 규칙은 batch-funnel.md Stage 1d. UA 헤더 필수, 키 불필요 |
| 밸류·리스크 플래그 | `koreaStockAnalyz-get_valuation`, `koreaStockAnalyz-get_risk_flags` | `UsStockInfo-get_recommendations` |
| 종목 뉴스 | `koreaStock-market_get_news`, `NaverSearch-search_news` | `UsStockInfo-get_finance_news`, WebSearch |
| 지수·시장 개요 | `koreaStock-market_get_index` | `UsStockInfo-get_market_overview` |
| 급등락·거래량 상위 | `koreaStock-market_get_movers` — **장중에만 유효**(개장 전 조회 시 0값), `new_high_low`는 미구현. 배치에서는 사용 안 함 | `UsStockInfo-get_market_overview`, `get_recommendations` |
| 섹터 흐름 | (도구 없음 — `market_get_sector`는 업종 지수 OHLCV만 반환) [특징주] 기사·뉴스 헤드라인으로 서술 | (도구 없음 — `get_market_overview` + 특징주 기사) |
| 특징주 기사(배치 후보 풀) | `NaverSearch-search_news(query="[특징주]", sort="date", display=40)` | `NaverSearch-search_news(query="미국 특징주", sort="date", display=30)` — 뉴스핌 [미국 특징주]·이데일리 [美특징주]·한경 wowtv 포함. 보조: 이데일리 RSS `http://rss.edaily.co.kr/edaily_news.xml`(제목에 "특징주" 포함만) |
| 전 시장 공시 스캔(배치) | `opendart-search_disclosures(bgn_de, end_de, corp_cls="Y"\|"K", page_count=100, page_no=1..2)` — corp_code 없이 호출하면 전체. 분류 규칙은 batch-funnel.md Stage 1c | (해당 없음 — US 8-K 스캔은 미구현) |
| 기사 본문 | `https://r.jina.ai/<원문URL>` | 동일. 뉴스핌·이데일리는 유료벽 없이 전문이 열리고, 뉴스핌은 본문 상단에 3줄 요약(`* ` 불릿)이 있어 그것만 읽어도 된다 |

## 호출 규칙

- 종목당 호출 상한: ticker 모드 8회, batch 갱신 4회(시세·뉴스·공시·리스크 중 필요한 것만).
- 뉴스는 최근 30일. 배치에서는 마지막 `updated` 이후만.
- 도구가 오류/빈 응답이면 같은 행의 다른 도구로 1회 대체. 그래도 없으면 해당 항목을 "조회 실패"로 적고 진행.
- WebSearch는 US 뉴스 보조와 섹터 흐름에만 쓴다. 시세를 WebSearch로 찾지 않는다.
- 뉴스 원문 WebFetch가 차단되면(seekingalpha·cnbc 등, 클라우드 egress 프록시) `https://r.jina.ai/<원문URL>`로 1회 재시도한다. 그래도 안 되면 WebSearch 스니펫으로 대체하고 "원문 미확인"을 적는다.
- 로컬 세션에 `agent-reach` 스킬이 있으면 뉴스 단계에서 추가로 쓸 수 있다: 실적 콜·IR 영상 YouTube 자막 요약(yt-dlp), 회사 IR/뉴스 RSS. X·Reddit는 계정이 없어 사용하지 않는다. 클라우드에는 yt-dlp가 없으므로 이 항목은 건너뛴다.
