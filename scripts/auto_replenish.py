"""Auto-replenish bot v3 — Long-running self-redispatching.
Corre por 5h30min haciendo ticks cada 30s. Al final se auto-dispatcha
via GitHub API → bypass del throttling de cron en repos privados.
"""
import os, time, requests, json, sys
API="https://api.mercadolibre.com"
TICK=30
DURATION_SEC = 5*3600 + 30*60  # 5h30m, leave buffer

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

SB_URL=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
SB_KEY=os.environ.get("SUPABASE_ANON_KEY","")
def sb_get(table,q=""):
    if not SB_KEY: return []
    try:
        r=requests.get(f"{SB_URL}/rest/v1/{table}?{q}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=10)
        return r.json() if r.status_code==200 else []
    except: return []

# Load blacklists once at start
cpid_blacklist=set(r["catalog_product_id"] for r in sb_get("meli_catalog_blacklist","select=catalog_product_id"))
# Skip BY ITEM_ID (per user clarification: no SKU-based blacklist)
# Use replenish_blacklist if it has item_id-keyed entries (future)
print(f"loaded cpid_blacklist={len(cpid_blacklist)}")

def refresh(secret_env):
    if secret_env not in os.environ: return None,None
    r=requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ[secret_env]
    },timeout=20).json()
    return r.get("access_token"), r.get("refresh_token")

# Refresh tokens once at start (good for 6h)
sessions={}
for uid,sec,nick in ACCOUNTS:
    at,rt=refresh(sec)
    if at:
        sessions[sec]=(at,rt,uid,nick)
        print(f"[init] {nick} loaded")
    else:
        print(f"[init] {nick} NO TOKEN, skip")

start=time.time()
end=start+DURATION_SEC
print(f"\n=== STARTING LOOP for {DURATION_SEC}s ({DURATION_SEC//60}min) ===")
print(f"start_ts={int(start)} end_ts={int(end)}")

total_revived=0
total_errors=0
tick_num=0
while time.time()<end:
    tick_num+=1
    t0=time.time()
    revived_tick=0; err_tick=0
    for sec,(at,rt,uid,nick) in sessions.items():
        H={"Authorization":f"Bearer {at}"}; HJ={**H,"Content-Type":"application/json"}
        try:
            r=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50&search_type=scan",headers=H,timeout=12)
            if r.status_code!=200:
                # could be token expired (6h passed); try refresh
                if r.status_code==401:
                    new_at,new_rt=refresh(sec)
                    if new_at:
                        sessions[sec]=(new_at,new_rt,uid,nick)
                        print(f"[tick{tick_num} {nick}] token refreshed mid-run")
                continue
            paused=r.json().get("results",[])
        except Exception as e:
            err_tick+=1; continue
        if not paused: continue
        for i in range(0,len(paused),20):
            batch=",".join(paused[i:i+20])
            try:
                mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,sub_status,catalog_product_id,available_quantity"},timeout=15).json()
            except: continue
            for x in mg:
                if x.get("code")!=200: continue
                b=x["body"]; sid=b["id"]
                ss=b.get("sub_status") or []
                if "out_of_stock" not in ss: continue
                cpid=b.get("catalog_product_id")
                if cpid and cpid in cpid_blacklist:
                    continue  # blacklisted CPID, skip
                try:
                    r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=12)
                    if r2.status_code in (200,201):
                        revived_tick+=1
                        print(f"[tick{tick_num} {nick}] {sid} REVIVED")
                except: err_tick+=1
    total_revived+=revived_tick
    total_errors+=err_tick
    if tick_num%10==0 or revived_tick>0:
        print(f"[tick{tick_num} t+{int(time.time()-start)}s] revived_this={revived_tick} total={total_revived} err={err_tick}")
    elapsed=time.time()-t0
    if elapsed<TICK: time.sleep(TICK-elapsed)

print(f"\n=== END loop after {tick_num} ticks ===")
print(f"total_revived={total_revived} total_errors={total_errors}")
new_rts={sec:rt for sec,(at,rt,uid,nick) in sessions.items()}
print(f"FINAL_ROTATED_TOKENS={json.dumps(new_rts)}")

# Self-redispatch to keep the chain going
gh_token=os.environ.get("GH_TOKEN_FOR_SECRETS","")
if gh_token:
    try:
        r=requests.post(
            "https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/actions/workflows/auto_replenish.yml/dispatches",
            headers={"Authorization":f"Bearer {gh_token}","Accept":"application/vnd.github+json","Content-Type":"application/json"},
            json={"ref":"main","inputs":{}},timeout=20
        )
        print(f"\nSELF_REDISPATCH: HTTP {r.status_code}")
    except Exception as e: print(f"redispatch err: {e}")
