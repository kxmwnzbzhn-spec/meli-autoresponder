"""Batch clona 30 items Wilbert -> Yiriam.
- DEDUP: salta si Yiriam ya tiene el CPID (no canibalizar buy box).
- Fixes: title<=60, copia GTIN, free shipping, catalog_listing=False.
"""
import os, requests, time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
def tok(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TW=tok(RT_W); HW={"Authorization":f"Bearer {TW}"}
TY=tok(RT_Y); HJY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}; HY={"Authorization":f"Bearer {TY}"}
meY=requests.get(f"{API}/users/me",headers=HY,timeout=10).json(); uidY=meY.get("id")

SRC=["MLM5297098664","MLM2916898793","MLM2916908677","MLM5297087174","MLM2916908765",
"MLM2916921607","MLM2916932951","MLM2910806817","MLM2911238257","MLM2908818917",
"MLM2908867469","MLM5309542808","MLM2916897169","MLM2914422351","MLM2910768325",
"MLM2910806881","MLM2910768333","MLM2910880749","MLM2910768335","MLM2910806871",
"MLM2910768369","MLM2910457973","MLM5351937060","MLM5354755946","MLM2931341689",
"MLM2931612609","MLM2931612611","MLM2937969761","MLM5337919270","MLM5337919290"]

# 1) CPIDs que Yiriam YA tiene (active+paused) -> dedup
print("=== Construyendo set CPID de Yiriam ===")
have=set(); ids=[]; off=0
for stt in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{uidY}/items/search?status={stt}&limit=50&offset={off}",headers=HY,timeout=15).json()
        res=r.get("results") or []
        ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50
for i in range(0,len(ids),20):
    mg=requests.get(f"{API}/items?ids={','.join(ids[i:i+20])}",headers=HY,timeout=15).json()
    for e in mg:
        b=e.get("body") or {}
        c=b.get("catalog_product_id")
        if c: have.add(c)
print(f"  Yiriam ya tiene {len(have)} CPIDs únicos")

cloned=[]; skipped=[]; failed=[]
for sid in SRC:
    try:
        g=requests.get(f"{API}/items/{sid}",headers=HW,timeout=12).json()
        if not g.get("id"):
            failed.append((sid,"no existe")); continue
        cpid=g.get("catalog_product_id")
        title=(g.get("title") or "")[:60]
        cat=g.get("category_id"); price=g.get("price")
        pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
        # DEDUP
        if cpid and cpid in have:
            skipped.append((sid,cpid)); print(f"SKIP {sid} (Yiriam ya tiene cpid {cpid})"); continue
        # attrs incl GTIN
        attrs=[]
        for a in (g.get("attributes") or []):
            if a.get("id") in ("BRAND","MODEL","COLOR","GTIN","LINE") and a.get("value_name"):
                attrs.append({"id":a["id"],"value_name":a["value_name"]})
        desc=""
        try:
            d=requests.get(f"{API}/items/{sid}/description",headers=HW,timeout=10).json()
            desc=d.get("plain_text","") or ""
        except: pass
        payload={"site_id":"MLM","title":title,"category_id":cat,"price":price,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
            "condition":"new","pictures":pics,"attributes":attrs,
            "shipping":{"mode":"me2","free_shipping":True}}
        if cpid:
            payload["catalog_product_id"]=cpid; payload["catalog_listing"]=False
        r=requests.post(f"{API}/items",headers=HJY,json=payload,timeout=30)
        if r.status_code<300:
            nid=r.json().get("id")
            cloned.append((sid,nid))
            if cpid: have.add(cpid)
            print(f"OK {sid} → {nid}")
            if desc:
                time.sleep(0.5)
                requests.post(f"{API}/items/{nid}/description",headers=HJY,json={"plain_text":desc},timeout=15)
        else:
            failed.append((sid, r.text[:120]))
            print(f"FAIL {sid}: {r.text[:150]}")
        time.sleep(0.8)
    except Exception as e:
        failed.append((sid,str(e))); print(f"ERR {sid}: {e}")

print(f"\n=== RESUMEN ===")
print(f"  Clonados: {len(cloned)} | Saltados(dedup): {len(skipped)} | Fallidos: {len(failed)}")
print("--- CLONADOS ---")
for s,n in cloned: print(f"  {s} → {n}")
print("--- SALTADOS (Yiriam ya tiene) ---")
for s,c in skipped: print(f"  {s} (cpid {c})")
print("--- FALLIDOS ---")
for s,e in failed: print(f"  {s}: {e}")
