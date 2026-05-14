import os,json,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

TARGETS=["MLM48244979","MLM44829344","MLM66701777"]
results=[]
for cpid in TARGETS:
    pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    title=pd.get("name","")
    domain=pd.get("domain_id","")
    # category — default to MLM59800 (Bocinas) for speakers
    cat="MLM59800"
    if "fragrance" in domain.lower() or "perfume" in domain.lower(): cat="MLM1271"
    attrs={a.get("id"):a.get("value_name") for a in (pd.get("attributes") or [])}
    print(f"\n--- {cpid} ---")
    print(f"  title={title[:70]}")
    print(f"  domain={domain} cat={cat}")
    print(f"  COLOR={attrs.get('COLOR')} MODEL={attrs.get('MODEL')}")
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
        print(f"  NEW_ID={new.get('id')} price=${new.get('price')} status={new.get('status')}")
        results.append({"cpid":cpid,"new_id":new.get("id"),"title":title})
    else:
        print(f"  ERR: {r.text[:500]}")
        results.append({"cpid":cpid,"err":r.text[:400],"http":r.status_code})
    time.sleep(1)

print("\n=== SUMMARY ===")
print(json.dumps(results,indent=2,ensure_ascii=False))
