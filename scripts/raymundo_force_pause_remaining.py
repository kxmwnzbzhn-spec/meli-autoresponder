"""Pausar TODOS los items active restantes en Raymundo - en loop hasta cero."""
import os, requests, time
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
print(f"Cuenta: {me['nickname']} ({uid})")

for round_n in range(1, 6):
    print(f"\n=== Round {round_n} ===")
    ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        ids.extend(b)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    print(f"  active: {len(ids)}")
    if not ids: break
    for iid in ids:
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
        if rp.status_code == 200:
            print(f"  ⏸️  {iid}")
        else:
            # try with available_quantity 0 first
            print(f"  ❌ {iid}: {rp.status_code} {rp.text[:120]}")
            # fallback: set qty 0 then pause
            rp2 = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":0,"status":"paused"},timeout=15)
            if rp2.status_code == 200:
                print(f"     ⏸️  {iid} (via qty=0)")
            else:
                print(f"     ❌ even with qty=0: {rp2.status_code}")
        time.sleep(0.15)
    print(f"  Esperando 5s antes de revalidar...")
    time.sleep(5)

# Estado final
print("\n=== Estado final ===")
for st in ["active","paused"]:
    rr=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=1",headers=H).json()
    print(f"  {st}: {rr.get('paging',{}).get('total','?')}")

TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")
if TG and TGCID:
    rr_a=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=1",headers=H).json()
    rr_p=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=paused&limit=1",headers=H).json()
    a=rr_a.get('paging',{}).get('total',0)
    p=rr_p.get('paging',{}).get('total',0)
    msg=f"🛑 *Raymundo FORCE PAUSE*\n\nActive: *{a}*\nPaused: *{p}*"
    if a==0: msg+=f"\n\n✅ Todo pausado correctamente"
    else: msg+=f"\n\n⚠️ Aun quedan {a} active"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg},timeout=20)
