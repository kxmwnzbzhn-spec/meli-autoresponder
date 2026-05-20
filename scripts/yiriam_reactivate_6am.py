#!/usr/bin/env python3
"""Reactivar Yiriam mañana 6am Mérida (= 12:00 UTC).

Lógica:
1) Si ya corrió hoy → idempotent skip
2) Lista TODOS los items paused de Yiriam
3) Para cada paused:
   - Si está en do_not_reactivate → skip
   - Si sub=out_of_stock → set qty=1 + activate (replenish)
   - Si sub=paused_by_seller → activate
4) Re-enable workflow war_yiriam_perfumes vía API
5) Telegram alert
"""
import os,requests,json,base64,datetime as dt
from datetime import timezone, timedelta
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN"); TC=os.environ.get("TELEGRAM_CHAT_ID")
REPO="kxmwnzbzhn-spec/meli-autoresponder"
WAR_WF_ID=277666461  # war_yiriam_perfumes

DO_NOT_REACTIVATE={
  "MLM5363034852",
  "MLM5291786710",  # closed permanent
  "MLM5353056250",  # paused permanent
  "MLM2909179597",  # paused 19-may
  "MLM5291788552",
  "MLM5291776046",
  "MLM5291772440",
  "MLM2909183135",
  "MLM2909179599",
  "MLM5363147396",
  "MLM5363023018",
}

def tg(m):
    if TG and TC: 
        try: requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TC,"text":m,"parse_mode":"Markdown"},timeout=10)
        except: pass

# Idempotency: track in repo
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
TZ_M=timezone(timedelta(hours=-6))
today=dt.datetime.now(TZ_M).date().isoformat()
STATE_PATH="inventory/yiriam_reactivate_state.json"
st_r=requests.get(f"https://api.github.com/repos/{REPO}/contents/{STATE_PATH}",headers=GHH).json()
state={"last_run":None}
state_sha=None
if "content" in st_r:
    state=json.loads(base64.b64decode(st_r["content"]))
    state_sha=st_r["sha"]
if state.get("last_run")==today:
    print(f"Ya ejecutado hoy {today}, skip idempotent")
    raise SystemExit(0)

# Auth MELI
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me.get("id")
if not uid:
    tg(f"⚠️ Yiriam reactivate FAIL — sin uid")
    raise SystemExit(1)

# List all paused
ids=[]; off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=paused&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break

print(f"Paused items: {len(ids)}")
reactivated=[]; skipped=[]; errors=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    mg=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,sub_status,available_quantity",headers=H).json()
    for x in mg:
        b=x.get("body",{}) or {}
        iid=b.get("id")
        if not iid: continue
        if iid in DO_NOT_REACTIVATE:
            skipped.append((iid,"do_not_reactivate")); continue
        sub=b.get("sub_status",[])
        qty=b.get("available_quantity",0)
        title=(b.get("title") or "")[:50]
        # Reactivate strategy
        if "out_of_stock" in sub:
            r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
            import time; time.sleep(0.3)
            r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            if r2.status_code<300: reactivated.append((iid,title,"out_of_stock→active"))
            else: errors.append((iid,f"out_of_stock activate http={r2.status_code}"))
        elif "paused_by_seller" in sub:
            r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
            if r.status_code<300: reactivated.append((iid,title,"paused_by_seller→active"))
            else: errors.append((iid,f"paused activate http={r.status_code}"))
        else:
            skipped.append((iid,f"sub={sub}"))

# Re-enable war workflow
war_resp=requests.put(f"https://api.github.com/repos/{REPO}/actions/workflows/{WAR_WF_ID}/enable",headers=GHH)
print(f"war wf enable http={war_resp.status_code}")

# Update state
state["last_run"]=today
state["reactivated_count"]=len(reactivated)
state["error_count"]=len(errors)
state["timestamp"]=dt.datetime.now(timezone.utc).isoformat()
new_b64=base64.b64encode(json.dumps(state,indent=2,ensure_ascii=False).encode()).decode()
body={"message":f"yir reactivate run {today}","content":new_b64}
if state_sha: body["sha"]=state_sha
requests.put(f"https://api.github.com/repos/{REPO}/contents/{STATE_PATH}",headers={**GHH,"Content-Type":"application/json"},json=body)

print(f"\n=== Reactivated: {len(reactivated)} | Skipped: {len(skipped)} | Errors: {len(errors)} ===")
for iid,title,reason in reactivated: print(f"  ✓ {iid} '{title}' [{reason}]")
for iid,reason in skipped[:5]: print(f"  - {iid} {reason}")
for iid,reason in errors[:5]: print(f"  ✗ {iid} {reason}")

msg=f"🌅 *Yiriam reactivado 6am Mérida ({today})*\nReactivados: *{len(reactivated)}*\nSkipped: {len(skipped)}\nErrores: {len(errors)}\nWar wf: {'✓' if war_resp.status_code<300 else '✗'}"
tg(msg)
