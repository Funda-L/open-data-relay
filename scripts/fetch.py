import json, os, time, urllib.request, pathlib

OUT = pathlib.Path("data"); OUT.mkdir(exist_ok=True)
SEC_UA = os.environ.get("SEC_UA", "coverage-monitor contact@example.com")

TWSE = {
    "twse_announcements.json": "https://openapi.twse.com.tw/v1/opendata/t187ap04_L",
    "twse_monthly_revenue.json": "https://openapi.twse.com.tw/v1/opendata/t187ap05_L",
    "twse_investor_conf.json": "https://openapi.twse.com.tw/v1/opendata/t187ap38_L",
}
TPEX = {}

US_TICKERS = ["AAOI","ADI","ALAB","AMZN","AOSL","APH","ARW","AVT","BE","CLS","CRDO","CRUS","CRWV",
              "DELL","DIOD","FLEX","GOOGL","HPE","HPQ","IBM","INGM","IONQ","JBL","LFUS","MCHP","META",
              "MPWR","MSFT","MTSI","NBIS","NSIT","NVTS","ON","ORCL","POWI","QBTS","RGTI","SANM","SITM",
              "SMCI","SMTC","SNX","TXN","VICR","VRT","VSH","INFQ","QNT"]

def get(url, ua="Mozilla/5.0"):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def save(name, data):
    (OUT / name).write_bytes(data)
    print("saved", name, len(data), "bytes")

for name, url in {**TWSE, **TPEX}.items():
    try: save(name, get(url))
    except Exception as e: print("FAIL", name, e)

try:
    tickers = json.loads(get("https://www.sec.gov/files/company_tickers.json", SEC_UA))
    cik = {v["ticker"]: f'{v["cik_str"]:010d}' for v in tickers.values()}
    sec = {}
    for t in US_TICKERS:
        if t not in cik: print("no CIK", t); continue
        try:
            d = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik[t]}.json", SEC_UA))
            r = d["filings"]["recent"]
            n = len(r["form"])
            desc = r.get("primaryDocDescription", [""] * n)
            rows = [dict(form=r["form"][i], date=r["filingDate"][i], acc=r["accessionNumber"][i],
                         doc=r["primaryDocument"][i], desc=desc[i]) for i in range(min(40, n))]
            sec[t] = {"cik": cik[t], "name": d.get("name"), "filings": rows}
        except Exception as e: print("FAIL", t, e)
        time.sleep(0.15)
    save("sec_recent_filings.json", json.dumps(sec, ensure_ascii=False, indent=1).encode())
except Exception as e: print("FAIL sec", e)

(OUT / "_updated.txt").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
