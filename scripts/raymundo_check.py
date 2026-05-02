import os, requests
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
sid = me["id"]
counts = {}
for st in ["active","paused","closed","under_review"]:
    s = 0; total = 0
    while True:
        d = requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}", headers=H, timeout=15).json()
        got = d.get("results", []) or []
        if not got: break
        total += len(got)
        s += 100
        if s >= d.get("paging",{}).get("total",0): break
    counts[st] = total
print(f"RAYMUNDO ({me.get('nickname')}):")
for st, n in counts.items():
    print(f"  {st:14}: {n}")
print(f"  ----")
print(f"  TOTAL: {sum(counts.values())}")
