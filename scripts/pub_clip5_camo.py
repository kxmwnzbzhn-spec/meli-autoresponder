import os,json,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

TARGETS=["MLM44712057","MLM48157832","MLM58616124"]
results=[]

for cpid in TARGETS:
    # Catalog listing body — minimal required
    body={
        "catalog_listing": True,
        "catalog_product_id": cpid,
        "price": 999,
        "currency_id": "MXN",
        "available_quantity": 1,
        "buying_mode": "buy_it_now",
        "listing_type_id": "gold_pro",
        "condition": "new",
        "sale_terms": [
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"90 días"}
        ]
    }
    print(f"\n--- Publishing {cpid} ---")
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
    print(f"  POST http={r.status_code}")
    if r.status_code>=300:
        print(f"  ERR: {r.text[:400]}")
        results.append({"cpid":cpid,"err":r.text[:300],"http":r.status_code})
        continue
    new=r.json()
    new_id=new.get("id")
    results.append({"cpid":cpid,"new_id":new_id,"price":new.get("price")})
    print(f"  NEW_ID={new_id} status={new.get('status')} price=${new.get('price')}")
    time.sleep(1)

print("\n=== SUMMARY ===")
print(json.dumps(results,indent=2,ensure_ascii=False))
