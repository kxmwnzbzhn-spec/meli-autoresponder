"""Auto-replenish bot v7 (SERVICE_KEY fix) — paginación completa por cuenta + concurrency-safe.
Cambios vs v3:
- Pagina TODOS los paused (no solo 50) en cada tick
- Manejo gracioso de tokens
- Resistente a 429
"""
import os, time, requests, json
API="https://api.mercadolibre.com"
TICK=30
DURATION_SEC = 5*3600 + 30*60

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
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SECRET_KEY") or ""
if not SB_KEY:
    print("[WARN] no SUPABASE key — priority/blacklists no funcionarán")
def sb_get(table,q=""):
    if not SB_KEY: return []
    try:
        r=requests.get(f"{SB_URL}/rest/v1/{table}?{q}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=10)
        return r.json() if r.status_code==200 else []
    except: return []
cpid_blacklist=set(r["catalog_product_id"] for r in sb_get("meli_catalog_blacklist","select=catalog_product_id"))
no_replenish_items=set(r["item_id"] for r in sb_get("meli_no_replenish_items","select=item_id"))
print(f"loaded cpid_blacklist={len(cpid_blacklist)} no_replenish_items={len(no_replenish_items)}")

def refresh(secret_env):
    if secret_env not in os.environ: return None,None
    try:
        r=requests.post(f"{API}/oauth/token",data={
            "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
            "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ[secret_env]
        },timeout=20).json()
        return r.get("access_token"), r.get("refresh_token")
    except: return None,None

sessions={}
for uid,sec,nick in ACCOUNTS:
    at,rt=refresh(sec)
    if at: sessions[sec]=(at,rt,uid,nick); print(f"[init] {nick}")
    else: print(f"[init] {nick} NO_TOKEN skip")

def all_paused(uid,H):
    """Paginate ALL paused items."""
    ids=[]
    off=0
    while True:
        try:
            r=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50&offset={off}",headers=H,timeout=12)
            if r.status_code!=200: return ids,r.status_code
            res=r.json().get("results") or []
            ids.extend(res)
            if len(res)<50 or off>3000: break
            off+=50
        except: break
    return ids,200

start=time.time()
end=start+DURATION_SEC
total_revived=0
tick_num=0
print(f"\n=== LOOP START dur={DURATION_SEC}s ===")
while time.time()<end:
    tick_num+=1
    t0=time.time()
    revived_tick=0
    # === PRIORITY REPLENISH — check FIRST every tick, regardless of OOS status ===
    try:
        priority=[r for r in sb_get("meli_priority_replenish","select=item_id,account,default_qty") if r.get("item_id")]
        for pr in priority:
            iid=pr["item_id"]; acct=pr.get("account"); qty=int(pr.get("default_qty") or 1)
            # find session for this account
            sec_for=None
            for (uid_a,sec_a,nick_a) in ACCOUNTS:
                if nick_a.lower()==(acct or "").lower():
                    sec_for=sec_a; break
            if not sec_for or sec_for not in sessions: continue
            at_p,rt_p,uid_p,nick_p=sessions[sec_for]
            Hp={"Authorization":f"Bearer {at_p}"}
            HJp={**Hp,"Content-Type":"application/json"}
            try:
                g=requests.get(f"{API}/items/{iid}",headers=Hp,timeout=10).json()
                if g.get("status")!="active" or (g.get("available_quantity") or 0)<qty:
                    rr=requests.put(f"{API}/items/{iid}",headers=HJp,json={"status":"active","available_quantity":qty},timeout=10)
                    if rr.status_code in (200,201):
                        print(f"[t{tick_num} PRIORITY {nick_p}] {iid} FORCED active qty={qty}")
            except: pass
    except: pass
    
    for sec,(at,rt,uid,nick) in sessions.items():
        H={"Authorization":f"Bearer {at}"}; HJ={**H,"Content-Type":"application/json"}
        paused,sc=all_paused(uid,H)
        if sc==401:
            # refresh and retry next tick
            new_at,new_rt=refresh(sec)
            if new_at: sessions[sec]=(new_at,new_rt,uid,nick); print(f"[t{tick_num} {nick}] token refreshed")
            continue
        if not paused: continue
        # Multiget in chunks
        for i in range(0,len(paused),20):
            batch=",".join(paused[i:i+20])
            try:
                mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,sub_status,catalog_product_id,inventory_id"},timeout=15).json()
            except: continue
            for x in mg:
                if x.get("code")!=200: continue
                b=x["body"]; sid=b["id"]
                if "out_of_stock" not in (b.get("sub_status") or []): continue
                # Skip Full/FBM: MELI manages stock at warehouse level
                if b.get("inventory_id"): continue
                if sid in no_replenish_items: continue
                cpid=b.get("catalog_product_id")
                if cpid and cpid in cpid_blacklist: continue
                try:
                    r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=12)
                    if r2.status_code in (200,201):
                        revived_tick+=1
                        print(f"[t{tick_num} {nick}] {sid} REVIVED")
                except: pass
    total_revived+=revived_tick
    if tick_num%10==0 or revived_tick>0:
        print(f"[tick{tick_num} t+{int(time.time()-start)}s] revived_this_tick={revived_tick} total={total_revived}")
    elapsed=time.time()-t0
    if elapsed<TICK: time.sleep(TICK-elapsed)

print(f"\n=== END after {tick_num} ticks ===")
print(f"total_revived={total_revived}")
new_rts={sec:rt for sec,(at,rt,uid,nick) in sessions.items()}
print(f"FINAL_ROTATED_TOKENS={json.dumps(new_rts)}")

# Self-redispatch
gh=os.environ.get("GH_TOKEN_FOR_SECRETS","")
if gh:
    try:
        r=requests.post("https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/actions/workflows/auto_replenish.yml/dispatches",
            headers={"Authorization":f"Bearer {gh}","Accept":"application/vnd.github+json","Content-Type":"application/json"},
            json={"ref":"main","inputs":{}},timeout=20)
        print(f"REDISPATCH: HTTP {r.status_code}")
    except Exception as e: print(f"redispatch err: {e}")




