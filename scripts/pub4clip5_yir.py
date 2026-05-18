import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

CPIDS=[
  ("MLM44714111","Morado"),
  ("MLM44714150","Camuflada"),
  ("MLM37110751","Azul"),
  ("MLM44714337","Rosa"),
]
results=[]
for cpid,color in CPIDS:
    pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers={"Authorization":f"Bearer {T}"}).json()
    title=pd.get("name","")
    print(f"\n{cpid} ({color}): {title[:60]}")
    body={
        "title":title,
        "category_id":"MLM59800",
        "catalog_listing":True,
        "catalog_product_id":cpid,
        "price":999,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "listing_type_id":"gold_pro",
        "condition":"new",
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"90 días"}
        ]
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
    print(f"  POST http={r.status_code}")
    if r.status_code<300:
        new=r.json()
        nid=new.get("id")
        print(f"  ✓ NEW_ID={nid} ${new.get('price')} status={new.get('status')}")
        results.append({"cpid":cpid,"color":color,"new":nid,"title":title[:50]})
    else:
        print(f"  ✗ {r.text[:400]}")
        results.append({"cpid":cpid,"color":color,"err":r.text[:300]})
    time.sleep(1)

print("\n=== SUMMARY ===")
for r in results:
    if r.get("new"):
        print(f"  ✓ {r['color']:<10} {r['cpid']} → {r['new']}")
    else:
        print(f"  ✗ {r['color']:<10} {r['cpid']}: {r.get('err','?')[:120]}")
