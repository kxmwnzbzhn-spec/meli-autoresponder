#!/usr/bin/env python3
"""War + Activate perfumes Wilbert.
Reglas: floor $599, ceiling $999 (override por item desde stock_config si tiene).
Solo procesa items con keywords perfume / brand fragrance / EDP.
"""
import os, time, json, re, requests

API="https://api.mercadolibre.com"
APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
TG_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

PERFUME_RX = re.compile(r"perfume|fragrance|\bedp\b|\bedt\b|eau de|cologne|alchemia|armaf|odyssey|colonia", re.I)
SPEAKER_RX = re.compile(r"\bjbl\b|\bbose\b|bocina|parlante|altavoz|speaker|sony", re.I)

DEFAULT_FLOOR = 599
DEFAULT_CEILING = 999
UP_STEP_PCT = 0.05
MAX_UP = 30

def refresh():
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
        "client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

def tg(m):
    if not TG_TOKEN or not TG_CHAT: return
    try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id":TG_CHAT,"text":m},timeout=8)
    except: pass

def is_perfume(title):
    t=title or ""
    if SPEAKER_RX.search(t): return False
    return bool(PERFUME_RX.search(t))

def list_items(tok, uid):
    h={"Authorization":f"Bearer {tok}"}
    out=[]
    for st in ("active","paused"):
        off=0
        while True:
            j=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=50&offset={off}",
                           headers=h, timeout=20).json()
            ids=j.get("results",[])
            if not ids: break
            out += ids
            off += 50
            if off >= j.get("paging",{}).get("total",0): break
    return out

def get_items_bulk(tok, ids):
    h={"Authorization":f"Bearer {tok}"}; res={}
    for i in range(0,len(ids),20):
        chunk=ids[i:i+20]
        r=requests.get(f"{API}/items?ids={','.join(chunk)}&attributes=id,title,price,status,catalog_listing,catalog_product_id,available_quantity",
                       headers=h,timeout=25).json()
        for it in r:
            if it.get("code")==200:
                b=it["body"]; res[b.get("id")]=b
    return res

def ptw(tok,iid):
    try:
        r=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",
                       headers={"Authorization":f"Bearer {tok}"},timeout=15)
        if r.status_code==200: return r.json()
    except: pass
    return None

def put_price(tok,iid,p):
    return requests.put(f"{API}/items/{iid}",
        headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"},
        json={"price":p},timeout=15)

def put_active(tok,iid,qty=1):
    return requests.put(f"{API}/items/{iid}",
        headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"},
        json={"available_quantity":qty,"status":"active"},timeout=15)

def main():
    tok=refresh()
    me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {tok}"}).json()
    uid=me["id"]
    print(f"Wilbert UID={uid}")

    # Cargar config si existe
    cfg={}
    try:
        with open("stock_config_wilbert.json") as f:
            cfg=json.load(f)
    except: pass

    ids=list_items(tok,uid)
    items=get_items_bulk(tok,ids)
    perfumes={iid:b for iid,b in items.items() if is_perfume(b.get("title",""))}
    print(f"Total items: {len(ids)}  Perfumes: {len(perfumes)}")

    A={"reactivated":0,"price_down":0,"price_up":0,"no_change":0,
       "floor_block":0,"errors":0,"no_ptw":0,"winning_alone":0,"sharing":0}
    log=[]

    for iid,it in perfumes.items():
        cur=it.get("price"); st=it.get("status"); qty=it.get("available_quantity",0)
        title=(it.get("title","") or "")[:48]
        c=cfg.get(iid,{})
        floor=c.get("floor_price", DEFAULT_FLOOR)
        ceiling=c.get("ceiling_price", DEFAULT_CEILING)

        # Reactivar
        if st=="paused":
            r=put_active(tok,iid,1)
            if r.status_code in (200,201):
                A["reactivated"]+=1
                log.append(f"  ACTIVATE {iid} '{title}'")
                cur=cur or floor
            else:
                A["errors"]+=1
                log.append(f"  ERR_ACTIV {iid} {r.status_code} {r.text[:80]}")
                continue

        pt=ptw(tok,iid)
        if not pt:
            A["no_ptw"]+=1
            continue
        ptw_p=pt.get("price_to_win")
        status=pt.get("status","")
        share_n=pt.get("competitors_sharing_first_place",0)
        is_full=False
        for b in (pt.get("winner") or {}).get("boosts",[]):
            if b.get("id")=="fulfillment" and b.get("status")=="boosted":
                is_full=True; break

        target=None; tag=""
        if status=="winning" and share_n==0:
            A["winning_alone"]+=1
            step=min(MAX_UP,max(1,int(cur*UP_STEP_PCT)))
            target=min(ceiling,cur+step)
            tag="UP_ALONE"
        elif status=="sharing" or (status=="winning" and share_n>0):
            A["sharing"]+=1
            target=(ptw_p or cur)-1
            tag="DOWN_BREAK_TIE"
            if target<floor:
                A["floor_block"]+=1
                log.append(f"  FLOOR_BLOCK {iid} ptw={ptw_p} floor={floor} '{title}'")
                if cur<floor: put_price(tok,iid,floor)
                continue
        else:
            if not ptw_p:
                step=min(MAX_UP,max(1,int(cur*UP_STEP_PCT)))
                target=min(ceiling,cur+step); tag="UP_NOPTW"
            else:
                target=int(ptw_p*0.95) if is_full else int(ptw_p)-1
                tag="DOWN_FULL" if is_full else "DOWN"
                if target<floor:
                    A["floor_block"]+=1
                    log.append(f"  FLOOR_BLOCK {iid} ptw={ptw_p} floor={floor} (FULL={is_full}) '{title}'")
                    if cur<floor: put_price(tok,iid,floor)
                    continue

        target=min(target,ceiling); target=max(target,floor)
        if target==cur:
            A["no_change"]+=1; continue
        r=put_price(tok,iid,target)
        if r.status_code in (200,201):
            if target>cur: A["price_up"]+=1
            else: A["price_down"]+=1
            log.append(f"  {tag} {iid} {cur}→{target} (ptw={ptw_p} st={status} sh={share_n} FULL={is_full}) '{title}'")
        else:
            A["errors"]+=1
            log.append(f"  ERR_PRICE {iid} {r.status_code} {r.text[:80]}")
        time.sleep(0.12)

    print("\n=== RESUMEN PERFUMES ===")
    for k,v in A.items(): print(f"  {k:>14}: {v}")
    print("\n=== ACCIONES ===")
    for l in log: print(l)
    if any(A[k] for k in ("reactivated","price_down","price_up","floor_block")):
        tg(f"💄 war-wilbert-perfumes\n"
           f"react={A['reactivated']} ↑={A['price_up']} ↓={A['price_down']} "
           f"alone={A['winning_alone']} floor={A['floor_block']} err={A['errors']}")

if __name__=="__main__": main()
