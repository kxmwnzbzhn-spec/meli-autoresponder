#!/usr/bin/env python3
"""Daily MELI sales sync — descuenta ventas de las 9 cuentas y actualiza inventory_master."""
import os,json,base64,requests,datetime as dt,sys
import meli_token

CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"
TG_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}

def tok(rt):
    if not rt: return None
    try:
        r=meli_token.refresh(rt)
        return r.json().get("access_token")
    except: return None

ACCOUNTS=[("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW"),("Juan","MELI_REFRESH_TOKEN_JUAN"),("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),("Asva","MELI_REFRESH_TOKEN_ASVA"),("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),("Bren","MELI_REFRESH_TOKEN_BREN")]
EXCLUDED_STATUS={"cancelled","invalid"}

def gh_get(path):
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=GHH)
    if r.status_code==200:
        d=r.json()
        return json.loads(base64.b64decode(d["content"])), d["sha"]
    return None,None

def gh_put(path,obj,msg,sha=None):
    content=base64.b64encode(json.dumps(obj,indent=2,ensure_ascii=False).encode()).decode()
    body={"message":msg,"content":content}
    if sha: body["sha"]=sha
    r=requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",headers={**GHH,"Content-Type":"application/json"},json=body)
    return r.status_code,r.json() if r.text else {}

def tg(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"},timeout=10)
    except: pass

def main():
    today=dt.date.today().isoformat()
    print(f"=== Daily sync {today} ===")

    # Load state
    inv,inv_sha=gh_get("inventory/inventory_master.json")
    map_,map_sha=gh_get("inventory/sku_to_mlm.json")
    unmap,unmap_sha=gh_get("inventory/sku_unmapped_listings.json")
    if not inv:
        print("ERR no inventory_master"); sys.exit(1)

    by_mlm=map_.get("by_mlm",{}) if map_ else {}
    last_order_ids=inv["_meta"].get("_last_order_id_per_account",{}) or inv.get("_last_order_id_per_account",{})

    decrements={}  # sku -> qty
    unmapped_new={}  # mlm -> {"qty":n,"title":...,"account":...}
    daily_log_events=[]
    err=[]

    for name,env in ACCOUNTS:
        T=tok(os.environ.get(env,""))
        if not T:
            print(f"  {name}: NO_TOKEN"); continue
        H={"Authorization":f"Bearer {T}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
        uid=me.get("id")
        if not uid: continue
        # Process orders since last
        last_id=last_order_ids.get(name)
        # Query yesterday and today, sort desc, stop at last_id
        yesterday=(dt.date.today()-dt.timedelta(days=2)).isoformat()
        url_base=f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={yesterday}T00:00:00.000-06:00&sort=date_desc&limit=50"
        off=0; processed=0; new_last_id=last_id
        while True:
            r=requests.get(f"{url_base}&offset={off}",headers=H,timeout=20).json()
            results=r.get("results",[])
            if not results: break
            for o in results:
                oid=str(o.get("id"))
                if last_id and oid==str(last_id):
                    off=99999; break  # stop pagination
                if new_last_id is None:
                    new_last_id=oid  # newest of this run
                if o.get("status") in EXCLUDED_STATUS: continue
                for it in (o.get("order_items") or []):
                    item=it.get("item",{}) or {}
                    mlm=item.get("id"); qty=int(it.get("quantity",0) or 0)
                    title=item.get("title","")
                    sku=by_mlm.get(mlm,{}).get("sku") if isinstance(by_mlm.get(mlm),dict) else by_mlm.get(mlm)
                    if sku:
                        decrements[sku]=decrements.get(sku,0)+qty
                        daily_log_events.append({"ts":o.get("date_created"),"order_id":oid,"account":name,"mlm":mlm,"sku":sku,"qty":qty,"title":title[:50]})
                    else:
                        u=unmapped_new.setdefault(mlm,{"qty":0,"title":title[:80],"accounts":set()})
                        u["qty"]+=qty
                        u["accounts"].add(name)
                processed+=1
            off+=50
            if off>=r.get("paging",{}).get("total",0): break
        last_order_ids[name]=new_last_id
        print(f"  {name}: {processed} orders procesados")

    # Apply decrements
    for sku,qty in decrements.items():
        if sku in inv["skus"]:
            inv["skus"][sku]["stock_bodega"]=max(0,inv["skus"][sku].get("stock_bodega",0)-qty)
        else:
            err.append(f"SKU {sku} en decrements pero no en inventory_master")

    # Recalc totals
    total_b=sum(s.get("stock_bodega",0) for k,s in inv["skus"].items() if not k.startswith("_"))
    total_d=sum(s.get("stock_devolucion",0) for k,s in inv["skus"].items() if not k.startswith("_"))
    inv["_meta"]["stock_bodega_total"]=total_b
    inv["_meta"]["stock_devolucion_total"]=total_d
    inv["_meta"]["last_sync"]=dt.datetime.utcnow().isoformat()+"Z"
    inv["_last_order_id_per_account"]=last_order_ids

    # Persist
    gh_put("inventory/inventory_master.json",inv,f"daily sync {today}: {sum(decrements.values())} units descontados",inv_sha)
    # Daily log
    log_path=f"inventory/logs/sync_{today}.json"
    _,log_sha=gh_get(log_path)
    log_data={"date":today,"decrements":decrements,"events":daily_log_events,"errors":err,"unmapped":{k:{**v,"accounts":list(v["accounts"])} for k,v in unmapped_new.items()}}
    gh_put(log_path,log_data,f"sync log {today}",log_sha)
    # Update unmapped
    if unmapped_new and unmap is not None:
        for mlm,info in unmapped_new.items():
            unmap["pending"].append({"mlm":mlm,"title":info["title"],"qty_seen":info["qty"],"first_seen":today})
        gh_put("inventory/sku_unmapped_listings.json",unmap,f"+{len(unmapped_new)} unmapped",unmap_sha)

    # Telegram report
    low_stock=[(k,s) for k,s in inv["skus"].items() if not k.startswith("_") and s.get("stock_bodega",0)<=s.get("stock_minimo_alerta",5) and s.get("stock_bodega",0)>0]
    agotados=[(k,s) for k,s in inv["skus"].items() if not k.startswith("_") and s.get("stock_bodega",0)==0]
    msg=f"📦 *Sync inventario {today}*\nVendido hoy: {sum(decrements.values())} pzs en {len(decrements)} SKUs\nTotal bodega: {total_b} | Devolución: {total_d}\n"
    if low_stock: msg+=f"\n⚠️ Stock bajo ({len(low_stock)}): "+", ".join(f"{s.get('sku_canonical',k)}({s.get('stock_bodega')})" for k,s in low_stock[:5])
    if agotados: msg+=f"\n🚫 Agotados: {len(agotados)}"
    if unmapped_new: msg+=f"\n❓ Nuevos sin mapear: {len(unmapped_new)}"
    tg(msg)
    print(msg)

if __name__=="__main__": main()
