import os,json,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

TARGETS=["MLM44712057","MLM48157832","MLM58616124"]
results=[]

for cpid in TARGETS:
    # Fetch product details
    pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    title=pd.get("name","")
    # Find category — try domain_id mapping or default speakers
    cat="MLM59800"
    # Try get child_categories / category_id from settings or domain
    domain=pd.get("domain_id","")
    print(f"\n--- {cpid} ---")
    print(f"  title={title[:70]}")
    print(f"  domain={domain}")
    body={
        "title": title,
        "category_id": cat,
        "catalog_listing": True,
        "catalog_product_id": cpid,
        "price": 999,
        "currency_id": "MXN",
        "available_quantity": 1,
        "buying_mode": "buy_it_now",
        "listing_type_id": "gold_pro",
        "condition": "new",
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"90 días"}
        ]
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
    print(f"  POST http={r.status_code}")
    if r.status_code<300:
        new=r.json()
        new_id=new.get("id")
        print(f"  NEW_ID={new_id} price=${new.get('price')} status={new.get('status')}")
        results.append({"cpid":cpid,"new_id":new_id,"price":new.get("price"),"title":title})
    else:
        print(f"  ERR: {r.text[:500]}")
        results.append({"cpid":cpid,"err":r.text[:300],"http":r.status_code})
    time.sleep(1)

print("\n=== SUMMARY ===")
print(json.dumps(results,indent=2,ensure_ascii=False))
