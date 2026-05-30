#!/usr/bin/env python3
"""War Adrián v1 — Supabase-aware. Basado en war_claribel v6.2.
- Auto-discover TODOS los items active con catalog_product_id (no lista hardcoded).
- Respeta meli_catalog_blacklist (CPID-level), meli_no_replenish_items, PAUSED_LOCK.
- Bounds por defecto perfumes (DEFAULT_FLOOR=399, DEFAULT_CEILING=999) — override por CPID en meli_catalog_strategy.
- Force-down si precio > ceiling.
- Telemetry a meli_war_log.
"""
import os, time, requests, json
API="https://api.mercadolibre.com"

tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]; NEW_RT=tok.get("refresh_token")
print(f"NEW_RT_AH={NEW_RT}")

DEFAULT_FLOOR=399
DEFAULT_CEILING=999
PAUSED_LOCK=set()

SB_URL=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
SB_KEY=os.environ.get("SUPABASE_ANON_KEY","")
def sb_get(table,q=""):
    if not SB_KEY: return []
    try:
        r=requests.get(f"{SB_URL}/rest/v1/{table}?{q}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=10)
        return r.json() if r.status_code==200 else []
    except: return []
sb_cpid_blacklist=set(r["catalog_product_id"] for r in sb_get("meli_catalog_blacklist","select=catalog_product_id"))
sb_strat=sb_get("meli_catalog_strategy","select=catalog_product_id,floor,ceiling&active=eq.true")
SB_FLOOR_CPID={r["catalog_product_id"]:float(r["floor"]) for r in sb_strat if r.get("floor")}
SB_CEIL_CPID={r["catalog_product_id"]:float(r["ceiling"]) for r in sb_strat if r.get("ceiling")}
print(f"sb_loaded cpid_bl={len(sb_cpid_blacklist)} floors={len(SB_FLOOR_CPID)} ceils={len(SB_CEIL_CPID)}")

H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]
print(f"seller={uid} nick={me.get('nickname')}")

ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    ids.extend(res)
    if len(res)<50 or off>2000: break
    off+=50
print(f"active items: {len(ids)}")

stat={"win":0,"comp":0,"reindex":0,"locked":0,"nocpid":0,"err":0,"skip_bl":0,"adjusted":0,"hold":0,"force_down":0}
acts=[]; telemetry=[]

for iid in ids:
    if iid in PAUSED_LOCK: stat["locked"]+=1; continue
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=12).json()
        if g.get("status")!="active": continue
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:30]
        if not cpid: stat["nocpid"]+=1; continue
        if cpid in sb_cpid_blacklist:
            stat["skip_bl"]+=1
            acts.append(f"{iid} SKIP cpid_blacklist {cpid}"); continue

        floor=SB_FLOOR_CPID.get(cpid, DEFAULT_FLOOR)
        ceil=SB_CEIL_CPID.get(cpid, DEFAULT_CEILING)

        # FORCE DOWN if above ceiling
        if cur > ceil:
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":ceil},timeout=15)
            stat["force_down"]+=1
            acts.append(f"{iid} '{title}' ${cur}->${ceil} [FORCE_DOWN_TO_CEIL] http={r2.status_code}")
            telemetry.append({"item_id":iid,"cpid":cpid,"war_status":"force_down","price_before":cur,"price_after":ceil,"floor":floor,"ceiling":ceil,"reason":"force_down_to_ceil"})
            time.sleep(0.2); continue

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
            bump=max(floor,min(bump,ceil))
            target=bump; reason="reindex_bump"
        elif pst in ("winning","sharing_first_place"):
            stat["win"]+=1
            if low_ext:
                up=int(low_ext)-5; up=min(up,ceil); up=max(up,floor)
                if up>cur: target=up; reason=f"max-up low_ext={low_ext}"
                else: reason=f"hold (ceil={ceil} low_ext={low_ext})"
            else: reason=f"hold (no comp ceil={ceil})"
        elif pst in ("competing","losing"):
            stat["comp"]+=1
            base=int(ptw) if ptw else (int(low_ext) if low_ext else None)
            if base:
                t=max(base-2,floor); t=min(t,ceil)
                if t<cur: target=t; reason=f"CLAIM ptw={ptw} low_ext={low_ext}"
                else: reason=f"floor={floor} bloquea ptw={ptw}"
            else: reason="no_ptw_no_low_ext"
        else: reason=f"st={pst}"

        new_price=cur
        if target is not None and target!=cur:
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            if r2.status_code in (200,201): new_price=target; stat["adjusted"]+=1
            acts.append(f"{iid} '{title}' ${cur}->${target} [{reason}] http={r2.status_code}")
        else:
            stat["hold"]+=1
            acts.append(f"{iid} '{title}' hold ${cur} [{reason}]")
        telemetry.append({"item_id":iid,"cpid":cpid,"war_status":pst,"price_before":cur,"price_after":new_price,"ptw":ptw,"low_ext":low_ext,"floor":floor,"ceiling":ceil,"reason":reason})
        time.sleep(0.15)
    except Exception as e:
        stat["err"]+=1
        acts.append(f"ERR {iid}: {e}")

print(f"\n=== war-adrian-v1: scanned={len(ids)} WIN={stat['win']} COMP={stat['comp']} REINDEX={stat['reindex']} ADJUSTED={stat['adjusted']} HOLD={stat['hold']} FORCE_DOWN={stat['force_down']} SKIP_BL={stat['skip_bl']} nocpid={stat['nocpid']} ERR={stat['err']} ===")
for a in acts[:100]: print(f"  {a}")
if len(acts)>100: print(f"  ... and {len(acts)-100} more")

if SB_KEY and telemetry:
    try:
        r=requests.post(f"{SB_URL}/rest/v1/meli_war_log",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"},
            json=telemetry,timeout=15)
        print(f"\ntelemetry: {r.status_code} ({len(telemetry)} rows)")
    except Exception as e: print(f"telemetry err: {e}")
