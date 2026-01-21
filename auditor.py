import pandas as pd
import requests
import feedparser
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
RSS_PATHS = ["/feed", "/rss", "/rss.xml", "/feed.xml", "/index.xml"]


def check_rss(base_url):
    urls_to_check = [base_url] + [f"{base_url.rstrip('/')}{path}" for path in RSS_PATHS]

    for url in urls_to_check:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                if len(parsed.entries) > 0:
                    return url
        except Exception:
            continue
    return None


def audit_row(row):
    url = row["URL"]
    logger.info(f"Auditing: {url}")

    found_rss = check_rss(url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        status = (
            "ACCESSIBLE" if resp.status_code == 200 else f"BLOCKED_{resp.status_code}"
        )
    except Exception as e:
        status = f"ERROR_{type(e).__name__}"

    return {
        "S.No": row["S.No"],
        "Source Name": row["Source Name"],
        "Verified_RSS": found_rss,
        "Access_Status": status,
        "Final_Tier": (
            "TIER_1_RSS"
            if found_rss
            else ("TIER_3_BROWSER" if "BLOCKED" in status else "TIER_2_STATIC")
        ),
    }


def main():
    df = pd.read_csv(r"./sources.csv")

    records = df.to_dict("records")

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(audit_row, records))

    output_df = pd.DataFrame(results)
    output_df.to_csv("audit_results.csv", index=False)
    logger.success("Audit complete! Check 'audit_results.csv'")


if __name__ == "__main__":
    main()
