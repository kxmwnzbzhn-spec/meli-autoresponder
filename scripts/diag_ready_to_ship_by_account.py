"""Conteo ready_to_ship por cuenta + substatus."""
import os, requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
ACCOUNTS = [
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
]

cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
date_from = (cdmx - timedelta(days=3)).replace(hour=0,minute=0,second=0,microsecond=0).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

per_account = {}
for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT:
        per_account[label] = "sin token"; continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",
            data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
            timeout=15).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        per_account[label] = f"err {e}"; continue
    
    counts = defaultdict(int)
    seen = set()  # dedup shipments
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",headers=H,timeout=20).json()
        results = rr.get("results",[])
        if not results: break
        for o in results:
            sh = o.get("shipping",{}) or {}
            sh_id = sh.get("id")
            if not sh_id or sh_id in seen: continue
            seen.add(sh_id)
            try:
                sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
                ss = sd.get("status","")
                sub = sd.get("substatus","") or "-"
            except: continue
            if ss == "ready_to_ship":
                counts[sub] += 1
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    per_account[label] = dict(counts)
    print(f"[{label}] {dict(counts)}")

print("\n=== RESUMEN ready_to_ship por cuenta ===")
print(f"{'Cuenta':10} {'printed':>8} {'picked_up':>10} {'r2print':>8} {'TOTAL':>6}")
total_p = total_pu = total_r2p = 0
for label, _ in ACCOUNTS:
    d = per_account.get(label, {})
    if isinstance(d, str):
        print(f"{label:10} {d}")
        continue
    p = d.get("printed",0); pu = d.get("picked_up",0); r2p = d.get("ready_to_print",0)
    other = sum(v for k,v in d.items() if k not in ("printed","picked_up","ready_to_print"))
    total = p + pu + r2p + other
    total_p += p; total_pu += pu; total_r2p += r2p
    extra = f" + otros:{other}" if other else ""
    print(f"{label:10} {p:>8} {pu:>10} {r2p:>8} {total:>6}{extra}")
print(f"{'TOTAL':10} {total_p:>8} {total_pu:>10} {total_r2p:>8} {total_p+total_pu+total_r2p:>6}")
