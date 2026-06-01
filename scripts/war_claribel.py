#!/usr/bin/env python3
"""War Claribel v8 — Fix root: SUPABASE_SERVICE_KEY + scope normalization + ceiling/floor directives.

Cambios vs v7:
- SB_KEY: lee SERVICE_KEY como prioridad, fallback ANON_KEY, fallback SECRET_KEY
- ABORT si no hay SB_KEY (no permite operar sin bounds para evitar daño)
- Acepta scope en {"item","item_id"} y {"cpid","catalog_product_id"} y "sku"
- Honra directive_type: pin_price (PIN exacto), set_ceiling (techo), set_floor (piso), pin_band (ambos)
- Loggea cada accion en meli_actions_log
"""
import os, time, requests, json, sys
API="https://api.mercadolibre.com"
TICK=60
DURATION_SEC=5*3600+30*60

DEFAULT_FLOOR=1
DEFAULT_CEILING=999999
PAUSED_LOCK={"MLM2890938689"}

SB_URL=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SECRET_KEY") or ""

if not SB_KEY:
    print("[FATAL] no SUPABASE key available — abortando para no operar sin bounds")
    sys.exit(1)

SBH={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}
SBHJ={**SBH,"Content-Type":"application/json","Prefer":"return=minimal"}

def sb_get(table,q=""):
    try:
        r=requests.get(f"{SB_URL}/rest/v1/{table}?{q}",headers=SBH,timeout=10)
        if r.status_code==200: return r.json()
        print(f"[SB GET {table}] HTTP {r.status_code}: {r.text[:100]}")
        return []
    except Exception as e:
        print(f"[SB GET ERR {table}]: {e}"); return []

def sb_post(table, rows):
    if not rows: return
    try:
        requests.post(f"{SB_URL}/rest/v1/{table}",headers=SBHJ,json=rows,timeout=10)
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

SCOPE_ITEM_VALS={"item","item_id"}
SCOPE_CPID_VALS={"cpid","catalog_product_id"}
SCOPE_SKU_VALS={"sku"}

def war_tick():
    sb_cpid_blacklist=set(r["catalog_product_id"] for r in sb_get("meli_catalog_blacklist","select=catalog_product_id"))
    locked_items=set(r["item_id"] for r in sb_get("meli_no_replenish_items","select=item_id"))
    sb_strat=sb_get("meli_catalog_strategy","select=catalog_product_id,floor,ceiling&active=eq.true")
    FLOOR_CPID={r["catalog_product_id"]:float(r["floor"]) for r in sb_strat if r.get("floor") is not None}
    CEIL_CPID={r["catalog_product_id"]:float(r["ceiling"]) for r in sb_strat if r.get("ceiling") is not None}

    # User directives — keyed by latest per scope_value+type
    _ud=sb_get("meli_user_directives","select=scope,scope_value,directive_type,value_numeric,ts&order=ts.asc")
    PIN_ITEM={}; PIN_CPID={}; PIN_SKU={}
    CEIL_ITEM={}; CEIL_CPID_USER={}; CEIL_SKU={}
    FLOOR_ITEM={}; FLOOR_CPID_USER={}; FLOOR_SKU={}
    for r in _ud:
        sc=(r.get("scope") or "").lower(); v=r.get("scope_value"); dt=(r.get("directive_type") or "").lower(); val=r.get("value_numeric")
        if val is None or not v: continue
        val=float(val)
        if sc in SCOPE_ITEM_VALS:
            if dt=="pin_price": PIN_ITEM[v]=val
            elif dt=="set_ceiling": CEIL_ITEM[v]=val
            elif dt=="set_floor": FLOOR_ITEM[v]=val
            elif dt=="pin_band": CEIL_ITEM[v]=val  # use value as ceiling; floor handled by paired set_floor
        elif sc in SCOPE_CPID_VALS:
            if dt=="pin_price": PIN_CPID[v]=val
            elif dt=="set_ceiling": CEIL_CPID_USER[v]=val
            elif dt=="set_floor": FLOOR_CPID_USER[v]=val
        elif sc in SCOPE_SKU_VALS:
            if dt=="pin_price": PIN_SKU[v]=val
            elif dt=="set_ceiling": CEIL_SKU[v]=val
            elif dt=="set_floor": FLOOR_SKU[v]=val

    ids=[]; off=0
    while True:
        r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        ids.extend(res)
        if len(res)<50 or off>1500: break
        off+=50

    stat={"win":0,"comp":0,"reindex":0,"locked":0,"adjusted":0,"hold":0,"force_down":0,"force_up":0,"force_pin":0,"err":0}
    actions=[]
    for iid in ids:
        if iid in PAUSED_LOCK or iid in locked_items: stat["locked"]+=1; continue
        try:
            g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
            if g.get("status")!="active": continue
            cur=g.get("price"); cpid=g.get("catalog_product_id"); sku=get_sku(g)
            if cur is None: continue
            if cpid and cpid in sb_cpid_blacklist: continue

            # PIN: prioridad absoluta
            pin = PIN_ITEM.get(iid) or (PIN_CPID.get(cpid) if cpid else None) or (PIN_SKU.get(sku) if sku else None)
            if pin is not None:
                if float(cur) != pin:
                    r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":pin},timeout=12)
                    if r2.status_code in (200,201): stat["force_pin"]+=1
                    actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(pin),"actor":"war_claribel","reason":"user_pin","http_status":r2.status_code,"account":"Claribel"})
                continue

            # FLOOR / CEILING: estrategia + override por directivas (la mas restrictiva gana)
            floor=FLOOR_CPID.get(cpid, DEFAULT_FLOOR) if cpid else DEFAULT_FLOOR
            ceil =CEIL_CPID .get(cpid, DEFAULT_CEILING) if cpid else DEFAULT_CEILING

            # Override per directive (TIGHTEN)
            if cpid and cpid in FLOOR_CPID_USER: floor=max(floor, FLOOR_CPID_USER[cpid])
            if cpid and cpid in CEIL_CPID_USER:  ceil =min(ceil , CEIL_CPID_USER[cpid])
            if sku  and sku  in FLOOR_SKU:       floor=max(floor, FLOOR_SKU[sku])
            if sku  and sku  in CEIL_SKU:        ceil =min(ceil , CEIL_SKU[sku])
            if iid  in FLOOR_ITEM:               floor=max(floor, FLOOR_ITEM[iid])
            if iid  in CEIL_ITEM:                ceil =min(ceil , CEIL_ITEM[iid])
            if floor>ceil: floor=ceil  # safety

            # Force down si fuera de techo
            if cur>ceil:
                r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":ceil},timeout=12)
                if r2.status_code in (200,201): stat["force_down"]+=1
                actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(ceil),"actor":"war_claribel","reason":f"force_down ceil={ceil}","http_status":r2.status_code,"account":"Claribel"})
                continue
            if cur<floor:
                r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":floor},timeout=12)
                if r2.status_code in (200,201): stat["force_up"]+=1
                actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(floor),"actor":"war_claribel","reason":f"force_up floor={floor}","http_status":r2.status_code,"account":"Claribel"})
                continue

            # Si no hay cpid -> no podemos calcular war
            if not cpid:
                stat["hold"]+=1; continue

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
                # safety: nunca exceder ceil ni bajar de floor
                target=max(floor, min(target, ceil))
                if target!=cur:
                    r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=12)
                    if r2.status_code in (200,201): stat["adjusted"]+=1
                    actions.append({"item_id":iid,"cpid":cpid,"sku":sku,"action_type":"price_change","before_value":str(cur),"after_value":str(target),"actor":"war_claribel","reason":reason or pst,"http_status":r2.status_code,"account":"Claribel"})
                else:
                    stat["hold"]+=1
            else:
                stat["hold"]+=1
        except Exception as e:
            stat["err"]+=1

    if actions: sb_post("meli_actions_log", actions)
    return len(ids),stat

start=time.time(); end=start+DURATION_SEC
print(f"\n=== LOOP START dur={DURATION_SEC//60}min ===")
tick_n=0
while time.time()<end:
    tick_n+=1
    t0=time.time()
    try:
        scanned,s=war_tick()
        print(f"[t{tick_n} +{int(t0-start)}s] scan={scanned} WIN={s['win']} COMP={s['comp']} REI={s['reindex']} ADJ={s['adjusted']} FD={s['force_down']} FU={s['force_up']} PIN={s['force_pin']} HOLD={s['hold']} LOCK={s['locked']} ERR={s['err']}")
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
