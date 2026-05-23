#!/usr/bin/env python3
"""Check ventas Wilbert hoy vs cap del día. Si excede → pausa todo + disable war."""
import os, json, requests, sys, time
from datetime import datetime, timezone, timedelta
import meli_token

API="https://api.mercadolibre.com"
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
TG_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")
GH_TOKEN=os.environ.get("GH_TOKEN_OPS")  # PAT con repo+actions
OWNER=os.environ.get("REPO_OWNER","kxmwnzbzhn-spec")
REPO="meli-autoresponder"

def tg(m):
    if not TG_TOKEN or not TG_CHAT: return
    try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id":TG_CHAT,"text":m},timeout=8)
    except: pass

def refresh():
    r=meli_token.refresh(RT)
    return r.json()["access_token"]

# Cargar config
with open("wilbert_sales_caps.json") as f:
    cfg=json.load(f)

# Fecha CDMX hoy
now_cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
today_str = now_cdmx.strftime("%Y-%m-%d")
cap = cfg["caps_by_date"].get(today_str, cfg["default_cap"])
print(f"Hoy CDMX: {today_str}  cap: {cap}")

if not cfg.get("auto_pause_enabled"):
    print("auto_pause disabled — exit")
    sys.exit(0)

tok = refresh()
me = requests.get(f"{API}/users/me", headers={"Authorization":f"Bearer {tok}"}, timeout=15).json()
uid = me["id"]
print(f"Wilbert UID={uid}")

# Buscar orders hoy (desde 00:00 CDMX = 06:00 UTC)
since_utc = (now_cdmx.replace(hour=0,minute=0,second=0,microsecond=0) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")

H={"Authorization":f"Bearer {tok}"}
units = 0
orders_count = 0
revenue = 0.0
off=0
while True:
    j=requests.get(f"{API}/orders/search?seller={uid}&order.date_created.from={since_utc}&limit=50&offset={off}",
                   headers=H,timeout=20).json()
    res=j.get("results",[])
    if not res: break
    for o in res:
        st=o.get("status")
        if st in ("paid","confirmed","shipped","delivered"):
            orders_count += 1
            for oi in o.get("order_items",[]):
                units += oi.get("quantity",1)
                revenue += float(oi.get("unit_price",0)) * oi.get("quantity",1)
    off += 50
    if off >= j.get("paging",{}).get("total",0): break

print(f"Orders pagadas hoy: {orders_count}  units: {units}  revenue: ${revenue:,.0f}")
print(f"Cap: {cap}  → {units}/{cap} ({100*units/max(cap,1):.0f}%)")

# Decisión
if units >= cap:
    msg = f"🛑 WILBERT CAP HIT: {units}/{cap} unid hoy ({today_str})\nDisparando pause_wilbert + disable war_wilbert"
    print(msg); tg(msg)
    if GH_TOKEN:
        h_gh={"Authorization":f"Bearer {GH_TOKEN}","Accept":"application/vnd.github+json"}
        # Pausar Wilbert
        r1=requests.post(f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/pause_wilbert.yml/dispatches",
                         headers=h_gh, json={"ref":"main","inputs":{}}, timeout=15)
        print(f"  pause_wilbert dispatch: {r1.status_code}")
        # Disable war_wilbert (encontrar id)
        wfs=requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows?per_page=100&page=4",
                         headers=h_gh, timeout=15).json()
        target=None
        for p in (1,2,3,4):
            wfs=requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows?per_page=100&page={p}",
                             headers=h_gh, timeout=15).json()
            for w in wfs.get("workflows",[]):
                if w["path"].endswith("/war_wilbert.yml"):
                    target=w["id"]; break
            if target: break
        if target:
            r2=requests.put(f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{target}/disable",
                            headers=h_gh, timeout=15)
            print(f"  war_wilbert disable: {r2.status_code}")
        # Marcar paused_today_at
        cfg["paused_today_at"] = now_cdmx.isoformat()
        with open("wilbert_sales_caps.json","w") as f:
            json.dump(cfg,f,indent=2,ensure_ascii=False)
elif units >= cap * 0.8:
    tg(f"⚠️ Wilbert {units}/{cap} (80%) — cerca del tope")
