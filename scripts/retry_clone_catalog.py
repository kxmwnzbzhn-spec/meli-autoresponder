"""Retry de los fallidos como CATALOGO PURO (sin title/attrs -> MELI hereda GTIN del catalogo).
Salta los que sigan en optin.fake. Dedup nuevamente por si acaso."""
import os, requests, time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
def tok(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TW=tok(RT_W); HW={"Authorization":f"Bearer {TW}"}
TY=tok(RT_Y); HJY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}; HY={"Authorization":f"Bearer {TY}"}
meY=requests.get(f"{API}/users/me",headers=HY,timeout=10).json(); uidY=meY.get("id")

FAILED=["MLM5297098664","MLM2916898793","MLM5297087174","MLM2916908765","MLM2916921607",
"MLM2916932951","MLM2908818917","MLM2908867469","MLM5309542808","MLM2916897169",
"MLM2914422351","MLM2910768325","MLM2910806881","MLM2910768333","MLM2910768335",
"MLM2910806871","MLM5351937060","MLM2931341689","MLM2931612609","MLM2931612611",
"MLM5337919270","MLM5337919290"]

# dedup set
have=set(); ids=[]
for stt in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{uidY}/items/search?status={stt}&limit=50&offset={off}",headers=HY,timeout=15).json()
        res=r.get("results") or []; ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50
for i in range(0,len(ids),20):
    mg=requests.get(f"{API}/items?ids={','.join(ids[i:i+20])}",headers=HY,timeout=15).json()
    for e in mg:
        c=(e.get("body") or {}).get("catalog_product_id")
        if c: have.add(c)

ok=[]; skip=[]; fail=[]
for sid in FAILED:
    try:
        g=requests.get(f"{API}/items/{sid}",headers=HW,timeout=12).json()
        cpid=g.get("catalog_product_id"); cat=g.get("category_id"); price=g.get("price")
        if not cpid:
            fail.append((sid,"sin cpid - no es catalogo")); print(f"NOCAT {sid}"); continue
        if cpid in have:
            skip.append((sid,cpid)); print(f"SKIP {sid} ya esta"); continue
        # CATALOGO PURO: sin title, sin attrs -> MELI hereda todo
        payload={"site_id":"MLM","category_id":cat,"price":price,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
            "condition":"new","catalog_product_id":cpid,"catalog_listing":True,
            "shipping":{"mode":"me2","free_shipping":True}}
        r=requests.post(f"{API}/items",headers=HJY,json=payload,timeout=30)
        if r.status_code<300:
            nid=r.json().get("id"); st=r.json().get("status")
            ok.append((sid,nid,st)); have.add(cpid); print(f"OK {sid} → {nid} ({st})")
        else:
            # extraer codigo de error principal
            t=r.text
            code = "optin.fake" if "optin.fake" in t else ("GTIN" if "GTIN" in t else t[:80])
            fail.append((sid,code)); print(f"FAIL {sid}: {code}")
        time.sleep(0.8)
    except Exception as e:
        fail.append((sid,str(e))); print(f"ERR {sid}: {e}")

print(f"\n=== RETRY RESUMEN ===")
print(f"  OK: {len(ok)} | SKIP: {len(skip)} | FAIL: {len(fail)}")
for s,n,st in ok: print(f"  OK {s} → {n} ({st})")
print("--- aun fallan ---")
for s,c in fail: print(f"  {s}: {c}")
