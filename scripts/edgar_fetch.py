"""SEC EDGAR 로컬 수집기 — data/edgar.json 생성.

클라우드 배치는 sec.gov에 접근할 수 없으므로 이 PC에서 06:40 KST에 돌려 push한다.
표준 라이브러리만 사용. 사용법:
    py -3 scripts/edgar_fetch.py            # data/edgar.json 생성만
    py -3 scripts/edgar_fetch.py --push     # 생성 후 git commit/push
"""
import json, os, re, sys, time, subprocess, glob, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "research-factory bot " + os.environ.get("EDGAR_UA_EMAIL", "you@example.com")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "research-factory")
OUT = os.path.join(REPO, "data", "edgar.json")
TRACK_FORMS = {"10-K", "10-Q", "8-K", "8-K/A", "SC 13D", "SC 13D/A", "4"}
SIGNAL_ITEMS = {"1.01", "2.01", "1.03", "5.02", "2.02"}
LOOKBACK_DAYS = 30
ATOM_PAGES = (0, 100, 200, 300)


def get(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            time.sleep(0.15)  # SEC: 10 req/s 이하
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 * (i + 1)); continue
            raise
        except Exception:
            if i == retries - 1: raise
            time.sleep(2)


def ticker_map():
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "company_tickers.json")
    if not os.path.exists(p) or time.time() - os.path.getmtime(p) > 7 * 86400:
        open(p, "wb").write(get("https://www.sec.gov/files/company_tickers.json"))
    d = json.load(open(p, encoding="utf-8"))
    by_ticker = {v["ticker"].upper(): (int(v["cik_str"]), v["title"]) for v in d.values()}
    by_cik = {int(v["cik_str"]): v["ticker"].upper() for v in d.values()}
    return by_ticker, by_cik


def us_tickers():
    tickers = set()
    wl = os.path.join(REPO, ".claude", "skills", "research-factory", "watchlist.md")
    if os.path.exists(wl):
        sect = None
        for line in open(wl, encoding="utf-8"):
            if line.startswith("## "):
                sect = line[3:].strip()
            elif sect == "US" and "|" in line:
                tickers.add(line.split("|")[0].strip().upper())
    for f in glob.glob(os.path.join(REPO, "pages", "entity-us-*.md")):
        head = open(f, encoding="utf-8").read(1500)
        if re.search(r"^status:\s*dormant", head, re.M):
            continue
        m = re.search(r"^ticker:\s*\"?([A-Za-z.\-]+)\"?", head, re.M)
        if m:
            tickers.add(m.group(1).upper())
    return sorted(t for t in tickers if t)


def per_ticker(tickers, by_ticker):
    since = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    out, issues = {}, []
    for t in tickers:
        if t not in by_ticker:
            issues.append(f"{t}: CIK 없음"); continue
        cik, name = by_ticker[t]
        try:
            d = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
        except Exception as e:
            issues.append(f"{t}: submissions 실패 {e}"); continue
        r = d.get("filings", {}).get("recent", {})
        rows = []
        for form, date, acc, doc, items in zip(r.get("form", []), r.get("filingDate", []), r.get("accessionNumber", []), r.get("primaryDocument", []), r.get("items", [])):
            if form not in TRACK_FORMS or date < since:
                continue
            rows.append({"form": form, "date": date, "items": items or "", "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"})
        out[t] = {"cik": f"{cik:010d}", "name": d.get("name", name), "filings": rows}
    return out, issues


def parse_atom(xml_bytes):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_bytes)
    for e in root.findall("a:entry", ns):
        title = e.findtext("a:title", "", ns)
        summary = e.findtext("a:summary", "", ns)
        link = e.find("a:link", ns)
        m = re.match(r"(.+?) - (.+?) \((\d{10})\)", title)
        if not m:
            continue
        yield {
            "form": m.group(1), "name": m.group(2), "cik": int(m.group(3)),
            "items": re.findall(r"Item (\d+\.\d+)", summary),
            "date": re.search(r"Filed:</b> (\d{4}-\d{2}-\d{2})", summary).group(1) if "Filed:" in summary else "",
            "url": link.get("href") if link is not None else "",
        }


def market_scan(by_cik):
    since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    hits, issues = [], []
    for start in ATOM_PAGES:
        try:
            xml = get(f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&count=100&start={start}&output=atom")
        except Exception as e:
            issues.append(f"8-K atom start={start}: {e}"); break
        page = list(parse_atom(xml))
        for f in page:
            if f["date"] < since:
                continue
            sig = sorted(set(f["items"]) & SIGNAL_ITEMS)
            if sig and f["cik"] in by_cik:
                hits.append({**f, "ticker": by_cik[f["cik"]], "signal_items": sig})
        if page and page[-1]["date"] < since:
            break
    sc13d = []
    try:
        for f in parse_atom(get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC+13D&count=40&output=atom")):
            if f["date"] >= since:
                sc13d.append({**f, "ticker": by_cik.get(f["cik"], "")})
    except Exception as e:
        issues.append(f"SC 13D atom: {e}")
    return hits, sc13d, issues


def main():
    by_ticker, by_cik = ticker_map()
    tickers = us_tickers()
    tracked, issues = per_ticker(tickers, by_ticker)
    hits, sc13d, issues2 = market_scan(by_cik)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lookback_days": LOOKBACK_DAYS,
        "tracked": tracked,
        "market_8k_signals": hits,
        "sc13d": sc13d,
        "issues": issues + issues2,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"tracked {len(tracked)} tickers, {sum(len(v['filings']) for v in tracked.values())} filings; "
          f"market 8-K signals {len(hits)}; SC 13D {len(sc13d)}; issues {len(issues + issues2)}")
    if "--push" in sys.argv:
        run = lambda *a: subprocess.run(["git", "-C", REPO, *a], check=False, capture_output=True, text=True)
        run("pull", "-q", "--rebase")
        run("add", "data/edgar.json")
        if run("diff", "--cached", "--quiet").returncode != 0:
            run("commit", "-q", "-m", f"edgar: {datetime.now().strftime('%Y-%m-%d')} 수집")
            r = run("push", "-q")
            print("pushed" if r.returncode == 0 else f"push failed: {r.stderr.strip()}")
        else:
            print("no change")


if __name__ == "__main__":
    main()
