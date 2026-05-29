"""Auto-replenish bot. Cada 30s busca items paused/out_of_stock y los reactiva con qty=1.
Ejecuta 8 ticks (4 min) por corrida. cron */5 lo invoca."""
import os, time, requests, json, sys
API="https://api.mercadolibre.com"
TICK=30
TICKS=8  # ~4 min de trabajo por corrida

ACCOUNTS=[
  (1668713481,"MELI_REFRESH_TOKEN_ASVA","Asva"),
  (2400722448,"MELI_REFRESH_TOKEN_BREN","Bren"),
  (3348766821,"MELI_REFRESH_TOKEN_CLARIBEL","Claribel"),
  (3355056011,"MELI_REFRESH_TOKEN_DILCIE","Dilcie"),
  (2681696373,"MELI_REFRESH_TOKEN_JUAN","Juan"),
  (3338633403,"MELI_REFRESH_TOKEN_RAYMUNDO","Raymundo"),
  (3294280577,"MELI_REFRESH_TOKEN_RMAYCHI","RMAYCHI"),
  (3367276814,"MELI_REFRESH_TOKEN_WILBERT","Wilbert"),
]

def refresh(secret_env):
    if secret_env not in os.environ: return None,None
    r=requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":os.environ[secret_env]
    },timeout=20).json()
    return r.get("access_token"), r.get("refresh_token")

# Refresh tokens once at start
sessions={}
for uid,sec,nick in ACCOUNTS:
    at,rt=refresh(sec)
    if not at:
        print(f"  [{nick}] no token, skip")
        continue
    sessions[sec]=(at,rt,uid,nick)
print(f"Active accounts: {[s[3] for s in sessions.values()]}")

revived_total=0
err_total=0
for t in range(TICKS):
    t0=time.time()
    print(f"\n=== tick {t+1}/{TICKS} ts={int(t0)} ===")
    for sec,(at,rt,uid,nick) in sessions.items():
        H={"Authorization":f"Bearer {at}"}
        HJ={**H,"Content-Type":"application/json"}
        try:
            r=requests.get(f"{API}/users/{uid}/items/search",headers=H,params={"limit":50,"status":"paused","search_type":"scan"},timeout=15)
            if r.status_code!=200:
                print(f"  [{nick}] list_err {r.status_code}")
                continue
            paused=r.json().get("results",[])
        except Exception as e:
            print(f"  [{nick}] list_exc {e}")
            continue
        if not paused: continue
        # check sub_status in batches
        for i in range(0,len(paused),20):
            batch=",".join(paused[i:i+20])
            try:
                mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,sub_status,available_quantity"},timeout=20).json()
            except: continue
            for x in mg:
                if x.get("code")!=200: continue
                b=x["body"]
                sid=b["id"]
                ss=b.get("sub_status") or []
                if "out_of_stock" in ss:
                    try:
                        r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=15)
                        if r2.status_code in (200,201):
                            revived_total+=1
                            print(f"  [{nick}] {sid} REVIVED")
                        else:
                            err_total+=1
                            print(f"  [{nick}] {sid} ERR {r2.status_code} {r2.text[:80]}")
                    except Exception as e:
                        err_total+=1
                        print(f"  [{nick}] {sid} EXC {e}")
    # sleep until next tick
    elapsed=time.time()-t0
    if elapsed < TICK:
        time.sleep(TICK-elapsed)

print(f"\n=== END === revived={revived_total} errors={err_total}")
new_rts={sec:rt for sec,(at,rt,uid,nick) in sessions.items()}
print(f"FINAL_ROTATED_TOKENS={json.dumps(new_rts)}")
