import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Only Go 4 CPIDs, as CATALOG NEW $499 qty=1
GO4=[
    ("MLM61262890","Celeste"),
    ("MLM44710313","Roja"),
    ("MLM65056521","Dzyp Rosa"),
    ("MLM46998439","Rojo"),
    ("MLM68969359","Negro"),
    ("MLM63973616","Rosado"),
    ("MLM66806041","Rosa Pálido"),
]

results=[]
for cpid,cname in GO4:
    print(f"\n=== {cname} ({cpid}) ===",flush=True)
    payload={
        "catalog_product_id":cpid,
        "category_id":"MLM59800",
        "price":499,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "condition":"new",
        "listing_type_id":"gold_pro",
        "catalog_listing":True,
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                      {"id":"WARRANTY_TIME","value_name":"30 días"}]
    }
    p=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
    if "id" in p:
        new_id=p["id"]
        print(f"  ✅ POSTED: {new_id} status={p.get('status')} price=${p.get('price')} title={p.get('title','?')[:60]}",flush=True)
        print(f"  URL: {p.get('permalink','?')}",flush=True)
        results.append((cname,cpid,new_id))
    else:
        print(f"  ❌ FAIL: {json.dumps(p)[:600]}",flush=True)
        results.append((cname,cpid,None))
    time.sleep(0.5)

print(f"\n=== SUMMARY ===",flush=True)
for cname,cpid,nid in results:
    print(f"  {cname} (CPID {cpid}) -> {nid}",flush=True)
