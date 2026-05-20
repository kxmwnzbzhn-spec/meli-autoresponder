"""V4: SIN title, dejar que MELI lo herede del catálogo"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Sin title
payload={
    "site_id":"MLM",
    "category_id":"MLM1271",
    "price":798,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "catalog_product_id":"MLM69794803",
    "catalog_listing":True,
}

print("=== TRY 1: sin title ===")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    new_id=r.json().get("id")
    print(f"  NEW: {new_id} ✅")
else:
    print(f"  body={r.text[:500]}")
    
    # TRY 2: con title exact del catalog name
    payload2={**payload, "title":"Perfume Dark Oud Cacao The Alchemia Lab Eau De Parfum 100ml"}
    print(f"\n=== TRY 2: title exacto del catálogo (60 chars) ===")
    print(f"  title len={len(payload2['title'])}")
    r2=requests.post(f"{API}/items",headers=HJ,json=payload2,timeout=30)
    print(f"  http={r2.status_code}")
    if r2.status_code<300:
        print(f"  NEW: {r2.json().get('id')} ✅")
    else:
        print(f"  body={r2.text[:500]}")
        
        # TRY 3: solo title trimmed sin ñ
        payload3={**payload, "title":"Perfume The Alchemia Lab Dark Oud Cacao 100 ml"}
        print(f"\n=== TRY 3: simple ASCII no Eau De Parfum ===")
        r3=requests.post(f"{API}/items",headers=HJ,json=payload3,timeout=30)
        print(f"  http={r3.status_code}")
        if r3.status_code<300:
            print(f"  NEW: {r3.json().get('id')} ✅")
        else:
            print(f"  body={r3.text[:500]}")
