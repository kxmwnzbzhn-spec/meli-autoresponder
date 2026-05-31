#!/usr/bin/env python3
"""War Claribel v7 — Supabase ONLY (no hardcoded bounds).
- Lee meli_catalog_strategy (floor/ceiling por CPID) — single source of truth
- Lee meli_user_directives (pin_price override por CPID o item_id) — máxima prioridad
- Lee meli_no_replenish_items (skip)
- Lee meli_catalog_blacklist (skip)
- Loggea cada acción en meli_actions_log
- Long-running 5h30 con tick 60s + self-redispatch
"""
import os, time, requests, json
API="https://api.mercadolibre.com"
TICK=60
DURATION_SEC=5*3600+30*60

DEFAULT_FLOOR=1
DEFAULT_CEILING=999999  # sin restricción si no hay strategy
PAUSED_LOCK={"MLM2890938689"}

SB_URL=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
SB_KEY=os.environ.get("SUPABASE_ANON_KEY","")

def sb_get(table,q=""):
    if not SB_KEY: return []
    try:
        r=requests.get(f"{SB_URL}/rest/v1/{table}?{q}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"},timeout=10)
        return r.json() if r.status_code==200 else []
    except: return []

def sb_post(table, rows):
    if not SB_KEY or not rows: return
    try:
        requests.post(f"{SB_URL}/rest/v1/{table}",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"},
            json=rows, timeout=10)
    except: pass

def refresh():
    r=requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
    },timeout=20).json()
    return r.get("access_token"), r.get("refresh_token")

T,NEW_RT=refresh()
print(f"NEW_RT_CLARIBEL={NEW_RT}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]
print(f"seller={uid} nick={me.get('nickname')}")

def get_sku(g):
    for a in (g.get("attributes") or []):
        if a.get("id")=="SELLER_SKU": return a.get("value_name")
    return None

def war_tick():
    # Re-read Supabase every tick
    sb_cpid_blacklist=set(r["catalog_product_id"] for r in sb_get("meli_catalog_blacklist","select=catalog_product_id"))
    locked_items=set(r["item_id"] for r in sb_get("meli_no_replenish_items","select=item_id"))
    sb_strat=sb_get("meli_catalog_strategy","select=catalog_product_id,floor,ceiling&active=eq.true")
    FLOOR_CPID={r["catalog_product_id"]:float(r["floor"]) for r in sb_strat if r.get("floor")}
    CEIL_CPID={r["catalog_product_id"]:float(r["ceiling"]) for r in sb_strat if r.get("ceiling")}
    
    # USER directives — max priority
    _ud=sb_get("meli_user_directives","select=scope,scope_value,directive_type,value_numeric")
    PIN_CPID={r["scope_value"]:float(r["value_numeric"]) for r in _ud if r.get("scope")=="cpid" and r.get("directive_type")=="pin_price" and r.get("value_numeric")}
    PIN_ITEM={r["scope_value"]:float(r["value_numeric"]) for r in _ud if r.get("scope")=="item_id" and r.get("directive_type")=="pin_price" and r.get("value_numeric")}

    # User pins by SKU → resolve to all CPIDs of that SKU
    PIN_SKU={r["scope_value"]:float(r["value_numeric"]) for r in _ud if r.get("scope")=="sku" and r.get("directive_type")=="pin_price" and r.get("value_numeric")}
    
    ids=[]; off=0
    while True:
        r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        ids.extend(res)
        if len(res)<50 or off>1500: break
        off+=50
    
    stat={"win":0,"comp":0,"reindex":0,"locked":0,"adjusted":0,"hold":0,"force_down":0,"force_pin":0,"err":0}
    actions=[]
    for iid in ids:
        if iid in PAUSED_LOCK or iid in locked_items: stat["locked"]+=1; continue
        try:
            g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
            if g.get("status")!="active": continue
            cur=g.get("price"); cpid=g.get("catalog_product_id"); sku=get_sku(g)
            if not cpid: continue
            if cpid in sb_cpid_blacklist: continue
            
            # USER PIN tiene prioridad absoluta
            pin = PIN_ITEM.get(iid) or PIN_CPID.get(cpid)
            # SKU-level pin: requires resolving SKU; for now use Alegra map alias
            # (the user often says SKU as ELEC-XXX; need a lookup or skip)
            
            if pin is not None:
                if cur != pin:
                    r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":pin},timeout=12)
                    if r2.status_code in (200,201):
                        stat["force_pin"]+=1
                        actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(pin),"actor":"war_claribel","reason":"user_pin","http_status":r2.status_code,"account":"Claribel"})
                continue
            
            floor=FLOOR_CPID.get(cpid, DEFAULT_FLOOR)
            ceil=CEIL_CPID.get(cpid, DEFAULT_CEILING)
            
            if cur>ceil:
                r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":ceil},timeout=12)
                stat["force_down"]+=1
                actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(ceil),"actor":"war_claribel","reason":f"force_down ceil={ceil}","http_status":r2.status_code,"account":"Claribel"})
                continue
            if cur<floor:
                r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":floor},timeout=12)
                stat["force_down"]+=1
                actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(floor),"actor":"war_claribel","reason":f"force_up floor={floor}","http_status":r2.status_code,"account":"Claribel"})
                continue
            
            p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=8).json()
            pst=(p.get("status") or "").lower(); ptw=p.get("price_to_win")
            low_ext=None
            try:
                pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=8).json()
                xs=[rr.get("price") for rr in (pr.get("results") or []) if (rr.get("item_id") or rr.get("id"))!=iid and rr.get("price") and (rr.get("status") or "active").lower()=="active" and (rr.get("available_quantity",1)>0)]
                xs.sort()
                if xs: low_ext=xs[0]
            except: pass
            
            target=None; reason=None
            if pst=="not_listed":
                stat["reindex"]+=1
                bump=max(floor,min(cur-1 if cur>floor else cur+1,ceil))
                target=bump; reason="reindex_bump"
            elif pst in ("winning","sharing_first_place"):
                stat["win"]+=1
                if low_ext:
                    up=max(min(int(low_ext)-5,ceil),floor)
                    if up>cur: target=up; reason=f"max-up low_ext={low_ext}"
            elif pst in ("competing","losing"):
                stat["comp"]+=1
                base=int(ptw) if ptw else (int(low_ext) if low_ext else None)
                if base:
                    t=max(min(base-2,ceil),floor)
                    if t<cur: target=t; reason=f"claim ptw={ptw}"
            
            if target is not None and target!=cur:
                r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=12)
                if r2.status_code in (200,201): stat["adjusted"]+=1
                actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(target),"actor":"war_claribel","reason":reason or pst,"http_status":r2.status_code,"account":"Claribel"})
            else:
                stat["hold"]+=1
        except: stat["err"]+=1
    
    # Bulk log to Supabase
    if actions:
        sb_post("meli_actions_log", actions)
    return len(ids),stat

start=time.time(); end=start+DURATION_SEC
print(f"\n=== LOOP START dur={DURATION_SEC//60}min ===")
tick_n=0
while time.time()<end:
    tick_n+=1
    t0=time.time()
    try:
        scanned,s=war_tick()
        print(f"[t{tick_n} +{int(t0-start)}s] scan={scanned} WIN={s['win']} COMP={s['comp']} REI={s['reindex']} ADJ={s['adjusted']} FD={s['force_down']} PIN={s['force_pin']} HOLD={s['hold']} LOCK={s['locked']} ERR={s['err']}")
    except Exception as e:
        print(f"[t{tick_n}] EXC: {e}")
    el=time.time()-t0
    if el<TICK: time.sleep(TICK-el)

print(f"\n=== END after {tick_n} ticks ===")
_,new_rt=refresh()
print(f"FINAL_RT={new_rt}")
gh=os.environ.get("GH_TOKEN_FOR_SECRETS","")
if gh:
    try:
        r=requests.post("https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/actions/workflows/war_claribel.yml/dispatches",
            headers={"Authorization":f"Bearer {gh}","Accept":"application/vnd.github+json","Content-Type":"application/json"},
            json={"ref":"main","inputs":{}},timeout=20)
        print(f"REDISPATCH: HTTP {r.status_code}")
    except Exception as e: print(f"redispatch err: {e}")
