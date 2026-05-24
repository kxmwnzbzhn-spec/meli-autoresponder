#!/usr/bin/env python3
"""Yiriam sales cap — pausa TODO si ventas hoy >= cap.

Lee config de inventory/yiriam_sales_cap.json:
  {"cap": 50, "date": "YYYY-MM-DD", "triggered": false, "paused_count": 0, "active_at_trigger": []}

Cuenta ventas de HOY (date_created CDMX) excl. cancelled.
Si >= cap → pausa todos los items active, marca triggered=true, alerta.
NO reactiva automáticamente — usuario lo hace cuando quiera.
"""
import os,requests,json,base64,datetime as dt
from datetime import timezone, timedelta
import meli_token

RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN"); TC=os.environ.get("TELEGRAM_CHAT_ID")
REPO="kxmwnzbzhn-spec/meli-autoresponder"
CFG_PATH="inventory/yiriam_sales_cap.json"
KEEP_ACTIVE={"MLM2950839631","MLM5291774150","MLM5291785036","MLM5363034838","MLM2940662359","MLM2940047221","MLM2950827385","MLM2909183147","MLM5390372034","MLM2950790163","MLM2950801625","MLM5364336572","MLM2950827407","MLM5390371996","MLM2950790175","MLM2950801553"}  # NO pausar (orden usuario 2026-05); mantener activos hasta aviso

def tg(msg):
    if TG and TC:
        try: requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TC,"text":msg,"parse_mode":"Markdown"},timeout=10)
        except: pass

# Auth MELI
T=meli_token.refresh(RT).json().get("access_token")
if not T:
    print("AUTH_FAIL"); raise SystemExit(1)
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me.get("id")
if not uid:
    print(f"NO_UID: {me}"); raise SystemExit(1)

# Load config from repo
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
cfg_resp=requests.get(f"https://api.github.com/repos/{REPO}/contents/{CFG_PATH}",headers=GHH).json()
if "content" in cfg_resp:
    cfg=json.loads(base64.b64decode(cfg_resp["content"]))
    cfg_sha=cfg_resp["sha"]
else:
    cfg={"cap":50,"date":"","triggered":False,"paused_count":0,"active_at_trigger":[]}
    cfg_sha=None

TZ_CDMX=timezone(timedelta(hours=-6))
today=dt.datetime.now(TZ_CDMX).date().isoformat()
# Reset si cambió el día
if cfg.get("date")!=today:
    cfg={"cap":cfg.get("cap",50),"date":today,"triggered":False,"paused_count":0,"active_at_trigger":[]}
    print(f"RESET para nuevo día {today} cap={cfg['cap']}")

# Si ya disparó → idempotente, no hace más
if cfg["triggered"]:
    print(f"Ya disparado hoy ({today}). Cap {cfg['cap']} alcanzado. Pausa total ejecutada antes ({cfg['paused_count']} items). Sin acción.")
    raise SystemExit(0)

# Count today's sales (CDMX TZ)
date_from=f"{today}T00:00:00.000-06:00"
url=f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50"
sold_count=0
off=0
while True:
    r=requests.get(f"{url}&offset={off}",headers=H,timeout=20).json()
    results=r.get("results",[])
    if not results: break
    for o in results:
        if o.get("status") in ("cancelled","invalid"): continue
        for it in (o.get("order_items") or []):
            sold_count+=int(it.get("quantity",0) or 0)
    off+=50
    if off>=r.get("paging",{}).get("total",0): break

print(f"Ventas Yiriam hoy ({today}): {sold_count}/{cfg['cap']}")

if sold_count < cfg["cap"]:
    # Aún no llega al cap, salir
    print(f"  Cap aún no alcanzado ({sold_count}<{cfg['cap']}). No-op.")
    raise SystemExit(0)

# ALCANZÓ EL CAP — pausar todo
print(f"\n🛑 CAP ALCANZADO {sold_count}>={cfg['cap']} — PAUSANDO TODO YIRIAM")
ids=[]
for st in ("active",):
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H,timeout=15).json()
        res=r.get("results",[])
        if not res: break
        ids+=res; off+=100
        if off>=r.get("paging",{}).get("total",0): break

print(f"  {len(ids)} items active a pausar")
paused=0; errs=0
for iid in ids:
    if iid in KEEP_ACTIVE:
        print(f"    keep-active (whitelist usuario): {iid}"); continue
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    if r.status_code<300: paused+=1
    else: errs+=1; print(f"    ✗ {iid} http={r.status_code}")

cfg["triggered"]=True
cfg["paused_count"]=paused
cfg["active_at_trigger"]=ids
cfg["triggered_at"]=dt.datetime.utcnow().isoformat()+"Z"

# Persist config
new_b64=base64.b64encode(json.dumps(cfg,indent=2,ensure_ascii=False).encode()).decode()
body={"message":f"yiriam_sales_cap TRIGGERED {today}: paused {paused}","content":new_b64}
if cfg_sha: body["sha"]=cfg_sha
u=requests.put(f"https://api.github.com/repos/{REPO}/contents/{CFG_PATH}",headers={**GHH,"Content-Type":"application/json"},json=body)
print(f"  cfg commit http={u.status_code}")

msg=f"🛑 *YIRIAM SALES CAP ALCANZADO*\n\nVentas hoy: *{sold_count}* / cap {cfg['cap']}\nPausados: *{paused}* items\nErrores: {errs}\n\nNo se reactivará hasta orden manual."
tg(msg)
print(f"\n{msg}")
