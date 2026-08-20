#!/usr/bin/env python3
import json
import os
import requests

API = "https://api.mercadolibre.com"

r = requests.post(f"{API}/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_ROCIOANGEL"],
}, timeout=20)
r.raise_for_status()
tok = r.json()
with open("/tmp/rocio_rotated_token", "w") as fh:
    fh.write(tok.get("refresh_token", ""))
H = {"Authorization": f"Bearer {tok['access_token']}"}
me = requests.get(f"{API}/users/me", headers=H, timeout=15)
me.raise_for_status()
uid = me.json()["id"]
print(f"ACCOUNT_UID={uid}", flush=True)

ids = []
for status in ("active", "paused"):
    offset = 0
    while True:
        q = requests.get(
            f"{API}/users/{uid}/items/search",
            headers=H,
            params={"status": status, "limit": 50, "offset": offset},
            timeout=20,
        )
        q.raise_for_status()
        batch = q.json().get("results") or []
        ids.extend(batch)
        if len(batch) < 50:
            break
        offset += 50

matches = []
for start in range(0, len(ids), 20):
    group = ids[start:start + 20]
    mg = requests.get(
        f"{API}/items",
        headers=H,
        params={"ids": ",".join(group), "attributes": "id,title,status,permalink"},
        timeout=20,
    )
    mg.raise_for_status()
    for row in mg.json():
        if row.get("code") != 200:
            continue
        item = row.get("body") or {}
        title = item.get("title") or ""
        compact = "".join(ch.lower() for ch in title if ch.isalnum())
        if "go4" in compact or "go5" in compact:
            matches.append({
                "id": item.get("id"),
                "title": title,
                "status": item.get("status"),
                "permalink": item.get("permalink"),
            })

matches.sort(key=lambda x: (x["title"].lower(), x["id"]))
print("GO45_JSON=" + json.dumps(matches, ensure_ascii=False), flush=True)
print(f"TOTAL_GO45={len(matches)}", flush=True)
