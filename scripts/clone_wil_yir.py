"""Clona 4 items Wilbert -> Yiriam con mismas características.
2911241921, 5346655686, 5297098664, 5297087174"""
import os, requests, time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
def tok(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TW=tok(RT_W); HW={"Authorization":f"Bearer {TW}"}
TY=tok(RT_Y); HJY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}; HY={"Authorization":f"Bearer {TY}"}

SRC=["MLM2911241921","MLM5346655686","MLM5297098664","MLM5297087174"]
results=[]
for sid in SRC:
    print(f"\n=== origen Wilbert {sid} ===")
    g=requests.get(f"{API}/items/{sid}",headers=HW,timeout=12).json()
    title=g.get("title"); cat=g.get("category_id"); price=g.get("price"); cpid=g.get("catalog_product_id")
    pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
    attrs=[]
    for a in (g.get("attributes") or []):
        if a.get("id") in ("BRAND","MODEL","COLOR","LINE","GTIN") and a.get("value_name"):
            attrs.append({"id":a["id"],"value_name":a["value_name"]})
    # descripcion
    desc=""
    try:
        d=requests.get(f"{API}/items/{sid}/description",headers=HW,timeout=10).json()
        desc=d.get("plain_text","") or ""
    except: pass
    print(f"  '{title[:42]}' cat={cat} price=${price} cpid={cpid} pics={len(pics)}")

    # Construir payload Yiriam
    base={"site_id":"MLM","title":title,"category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
        "condition":"new","pictures":pics,"attributes":attrs}
    if cpid:
        base["catalog_product_id"]=cpid
        base["catalog_listing"]=False  # estructura que funciona sin opt-in
    r=requests.post(f"{API}/items",headers=HJY,json=base,timeout=30)
    print(f"  CLONE http={r.status_code}")
    if r.status_code<300:
        nid=r.json().get("id"); st=r.json().get("status")
        print(f"  NEW: {nid} ✅ status={st}")
        results.append((sid,nid))
        if desc:
            time.sleep(1)
            rd=requests.post(f"{API}/items/{nid}/description",headers=HJY,json={"plain_text":desc},timeout=15)
            print(f"  desc http={rd.status_code}")
    else:
        print(f"  body={r.text[:300]}")
    time.sleep(1)

print("\n=== MAPEO Wilbert→Yiriam ===")
for s,n in results: print(f"  {s} → {n}")
