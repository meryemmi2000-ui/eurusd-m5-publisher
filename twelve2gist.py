import os, time, requests, json, sys

API_KEY  = os.environ["TWELVE_API_KEY"]
GIST_ID  = os.environ["GIST_ID"]
GH_TOKEN = os.environ["GITHUB_TOKEN"]

COUNT = 576   # 48h de M5 = 48*60/5

def fetch_twelvedata_m5(count=COUNT):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "EUR/USD",
        "interval": "5min",
        "outputsize": count,
        "timezone": "UTC",
        "order": "desc"
    }
    r = requests.get(url, params=params, headers={"Authorization": f"apikey {API_KEY}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "values" not in data:
        raise RuntimeError(f"TwelveData error: {json.dumps(data, ensure_ascii=False)[:400]}")
    return data["values"]  # latest-first

def values_to_tsv(values):
    lines = []
    for v in values:
        t = v["datetime"]            # 'YYYY-MM-DD HH:MM:SS' (UTC)
        o,h,l,c = map(float, (v["open"], v["high"], v["low"], v["close"]))
        lines.append(f"{t}\t{o:.5f}\t{h:.5f}\t{l:.5f}\t{c:.5f}")
    return "\n".join(lines)

def upload_gist(tsv):
    payload = {"files": {"eurusd-m5-latest.txt": {"content": tsv}}}
    gr = requests.patch(
        f"https://api.github.com/gists/{GIST_ID}",
        json=payload,
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    gr.raise_for_status()

def main():
    last_err = None
    for attempt in range(3):
        try:
            vals = fetch_twelvedata_m5()
            tsv = values_to_tsv(vals)
            upload_gist(tsv)

            # <<< AJOUT ICI >>>
            with open("eurusd-m5-latest.txt", "w", encoding="utf-8") as f:
                f.write(tsv)
            # <<< FIN AJOUT >>>

            print("OK: Gist mis à jour. Lignes:", len(tsv.splitlines()))
            if tsv:
                print("Top line:", tsv.splitlines()[0])
            return
        except Exception as e:
            last_err = e
            time.sleep(2*(attempt+1))
    print("Échec:", last_err, file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
