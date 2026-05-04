"""Catalog war dedicado para los 2 Bose SoundLink Home en Raymundo.
- Floor $3499, Ceiling $3499 (lock fijo)
- ptw-1 con cap al floor/ceiling
- Solo afecta a las 2 IIDs whitelist (no reactiva nada mas)
"""
import os, requests

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

BOSE_ITEMS = ["MLM2906041435","MLM2906016765"]
FLOOR = 3499
CEILING = 3499  # ya es nuestro precio fijo, no subir mas

r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

results=[]
for iid in BOSE_ITEMS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,params={"attributes":"id,price,status,title"}).json()
    cur=it.get("price")
    title=it.get("title","")[:50]
    status=it.get("status")
    if status != "active":
        print(f"  skip {iid} status={status}")
        continue

    ptw_resp=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    st=ptw_resp.get("status")
    ptw=ptw_resp.get("price_to_win")
    print(f"  {iid} {title}")
    print(f"    cur=${cur} | ptw={st} ptw_p=${ptw}")

    target = cur
    action = "no_action"

    if ptw is not None:
        # Mantener floor/ceiling lock
        candidate = max(FLOOR, min(CEILING, round(ptw - 1, 0)))
        if candidate != cur:
            target = candidate
            action = "adjust"

    if action == "adjust":
        rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price": target},timeout=10)
        ok = rp.status_code == 200
        print(f"    {'✅' if ok else '❌'} ${cur}→${target}: {rp.status_code}")
        results.append({"iid":iid,"old":cur,"new":target,"st":st,"ptw":ptw,"ok":ok})
    else:
        print(f"    ✓ ya optimo ${cur}")
        results.append({"iid":iid,"cur":cur,"st":st,"ptw":ptw,"action":"no_action"})

if TG and TGCID:
    msg="🎯 *Bose Catalog War*\n\n"
    for r in results:
        if r.get("ok"):
            msg+=f"✅ `{r['iid']}` ${r['old']}→${r['new']} (ptw=${r['ptw']} {r['st']})\n"
        else:
            msg+=f"✓ `{r['iid']}` ${r.get('cur','?')} {r.get('st','?')} ptw=${r.get('ptw','?')}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg},timeout=20)
