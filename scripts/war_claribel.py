#!/usr/bin/env python3
"""War Claribel V6 — Supabase-aware.
- Direct OAuth (no Worker stale issues).
- Lee meli_catalog_blacklist (skipea CPIDs infraccionados).
- Lee meli_replenish_blacklist (skipea por SELLER_SKU sin stock).
- Lee meli_catalog_strategy.floor/ceiling por CPID.
- Reports telemetry a meli_war_log si SUPABASE_ANON_KEY está disponible.
"""
import os, time, requests, json
API="https://api.mercadolibre.com"

tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
NEW_RT=tok.get("refresh_token")
print(f"NEW_RT_CLARIBEL={NEW_RT}")

SB_URL=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
SB_KEY=os.environ.get("SUPABASE_ANON_KEY","")
def sb_get(table,q=""):
    if not SB_KEY: return []
    try:
        r=requests.get(f"{SB_URL}/rest/v1/{table}?{q}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=10)
        return r.json() if r.status_code==200 else []
    except: return []

sku_blacklist=set(r["sku"] for r in sb_get("meli_replenish_blacklist","select=sku"))
cpid_blacklist=set(r["catalog_product_id"] for r in sb_get("meli_catalog_blacklist","select=catalog_product_id"))
strat=sb_get("meli_catalog_strategy","select=catalog_product_id,floor,ceiling&active=eq.true")
FLOOR_BY_CPID={r["catalog_product_id"]:float(r["floor"]) for r in strat if r.get("floor")}
CEIL_BY_CPID={r["catalog_product_id"]:float(r["ceiling"]) for r in strat if r.get("ceiling")}
print(f"sb_loaded sku_bl={len(sku_blacklist)} cpid_bl={len(cpid_blacklist)} floors={len(FLOOR_BY_CPID)} ceils={len(CEIL_BY_CPID)}")

H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]
MIN_FLOOR=200
PAUSED_LOCK={"MLM2890938689"}

ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    ids.extend(res)
    if len(res)<50 or off>1000: break
    off+=50

stat={"win":0,"comp":0,"reindex":0,"locked":0,"nocpid":0,"err":0,"skip_bl":0,"sku_oos":0,"adjusted":0,"paused_oos":0}
acts=[]; telemetry=[]

def get_sku(g):
    for a in (g.get("attributes") or []):
        if a.get("id")=="SELLER_SKU": return a.get("value_name")
    return None

for iid in ids:
    if iid in PAUSED_LOCK: stat["locked"]+=1; continue
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=12).json()
        if g.get("status")!="active": continue
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:25]
        sku=get_sku(g)
        if not cpid: stat["nocpid"]+=1; continue
        # Skip if CPID is in blacklist
        if cpid in cpid_blacklist:
            stat["skip_bl"]+=1
            acts.append(f"{iid} SKIP cpid_blacklist {cpid}")
            continue
        # If SKU is in stock-out blacklist, PAUSE this listing (no debería estar activo)
        if sku and sku in sku_blacklist:
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused","available_quantity":0},timeout=15)
            stat["paused_oos"]+=1
            acts.append(f"{iid} '{title}' sku={sku} OUT_OF_STOCK -> paused http={r2.status_code}")
            continue

        floor=FLOOR_BY_CPID.get(cpid,MIN_FLOOR)
        ceil=CEIL_BY_CPID.get(cpid,999999)

        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        pst=(p.get("status") or "").lower(); ptw=p.get("price_to_win")
        low_ext=None
        try:
            pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
            xs=[]
            for rr in (pr.get("results") or []):
                rid=rr.get("item_id") or rr.get("id"); rp=rr.get("price")
                rst=(rr.get("status") or "active").lower(); rq=rr.get("available_quantity",1)
                if rid and rid!=iid and rp and rst=="active" and rq>0: xs.append(rp)
            xs.sort()
            if xs: low_ext=xs[0]
        except: pass

        target=None; reason=""
        if pst=="not_listed":
            stat["reindex"]+=1
            bump=cur-1 if cur>floor else cur+1
            target=bump; reason="reindex_bump"
        elif pst in ("winning","sharing_first_place"):
            stat["win"]+=1
            if low_ext:
                up=min(int(low_ext)-5,ceil); up=max(up,floor)
                if up>cur: target=up; reason=f"max-up low_ext={low_ext}"
                else: reason=f"hold (low_ext={low_ext})"
            else: reason=f"hold (no comp)"
        elif pst in ("competing","losing"):
            stat["comp"]+=1
            base=int(ptw) if ptw else (int(low_ext) if low_ext else None)
            if base:
                t=max(base-2,floor); t=min(t,ceil)
                if t<cur: target=t; reason=f"CLAIM ptw={ptw} low_ext={low_ext}"
                else: reason=f"floor=${floor} bloquea (ptw={ptw})"
            else: reason="no_ptw_no_low_ext"
        else: reason=f"st={pst}"

        new_price=cur
        if target is not None and target!=cur:
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            if r2.status_code in (200,201):
                new_price=target; stat["adjusted"]+=1
            acts.append(f"{iid} '{title}' sku={sku} ${cur}->${target} [{reason}] http={r2.status_code}")
        else:
            acts.append(f"{iid} '{title}' sku={sku} hold ${cur} [{reason}]")
        telemetry.append({"item_id":iid,"cpid":cpid,"sku":sku,"war_status":pst,"price_before":cur,"price_after":new_price,"ptw":ptw,"low_ext":low_ext,"floor":floor,"ceiling":ceil,"reason":reason})
        time.sleep(0.2)
    except Exception as e:
        stat["err"]+=1
        acts.append(f"ERR {iid}: {e}")

print(f"\n=== war-clb-v6: scanned={len(ids)} WIN={stat['win']} COMP={stat['comp']} REINDEX={stat['reindex']} ADJUSTED={stat['adjusted']} SKIP_BL={stat['skip_bl']} PAUSED_OOS={stat['paused_oos']} LOCKED={stat['locked']} nocpid={stat['nocpid']} ERR={stat['err']} ===")
for a in acts: print(f"  {a}")

# Telemetry to Supabase
if SB_KEY and telemetry:
    try:
        r=requests.post(f"{SB_URL}/rest/v1/meli_war_log",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"},
            json=telemetry,timeout=15)
        print(f"\ntelemetry upload: {r.status_code} ({len(telemetry)} rows)")
    except Exception as e: print(f"telemetry err: {e}")
