import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# (source_id, cpid, price, name_hint) — from preview
ITEMS=[
    ("MLM5569282738","MLM61262890",499,"JBL Go 4 Celeste"),
    ("MLM3045607131","MLM44710313",499,"JBL Go 4 Roja"),
    ("MLM3045609271","MLM65056521",499,"Dzyp Go 4 Rosa"),
    ("MLM5569353088","MLM46998439",499,"JBL Go 4 Rojo"),
    ("MLM5569446604","MLM25912333",690,"Sony SRS-XB100"),
    ("MLM5569350350","MLM68969359",499,"JBL Go 4 Negro"),
    ("MLM3045615611","MLM41991186",699,"Sony SRS-XB100 Negro"),
    ("MLM5569353878","MLM63973616",499,"JBL Go 4 Rosado"),
    ("MLM3045609843","MLM66806041",499,"JBL Go 4 Rosa Pálido"),
    ("MLM5569359030","MLM2020109296",1199,"Marshall Emberton"),
    ("MLM3045613145","MLM2021493918",1199,"Beats Pill Negro"),
    ("MLM3059642403","MLM2022828333",1199,"Bose Soundlink Silver"),
    ("MLM5569408564","MLM2021495500",1199,"Beats Pill Rojo"),
    ("MLM5569444970","MLM2021121410",999,"Marshall Willen II"),
    ("MLM3048991273","MLM37110181",399,"JBL Clip 5 usada 1"),
    ("MLM3054168351","MLM37110181",399,"JBL Clip 5 usada 2"),
]

results=[]
for src,cpid,price,name in ITEMS:
    print(f"\n=== {name} (src={src} cpid={cpid} price=${price}) ===",flush=True)
    payload={
        "catalog_product_id":cpid,
        "category_id":"MLM59800",
        "price":price,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "condition":"used",
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
        results.append((src,new_id,name,price,cpid))
    else:
        # Retry with condition=new
        print(f"  ⚠️ FAIL used, retry as new: {p.get('message','?')[:200]}",flush=True)
        payload["condition"]="new"
        p2=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
        if "id" in p2:
            new_id=p2["id"]
            print(f"  ✅ POSTED (as new): {new_id} price=${p2.get('price')}",flush=True)
            results.append((src,new_id,name,price,cpid))
        else:
            print(f"  ❌ FAIL both: {json.dumps(p2)[:600]}",flush=True)
            results.append((src,None,name,None,cpid))
    time.sleep(0.5)

print(f"\n=== SUMMARY ===",flush=True)
for src,new_id,name,price,cpid in results:
    print(f"  {src} -> {new_id} | {name} ${price}",flush=True)
