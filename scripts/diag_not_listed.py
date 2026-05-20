"""Diagnosticar MLM2940047227 y MLM2940047233 — por qué están not_listed"""
import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

for iid in ["MLM2940047227","MLM2940047233"]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    print(f"\n=== {iid} ===")
    print(f"  status={g.get('status')} sub={g.get('sub_status')}")
    print(f"  health={g.get('health')} catalog_listing={g.get('catalog_listing')}")
    print(f"  cpid={g.get('catalog_product_id')} domain={g.get('domain_id')}")
    print(f"  listing_type={g.get('listing_type_id')} cat={g.get('category_id')}")
    print(f"  title='{g.get('title')}'")
    # PTW
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: status={p.get('status')} ptw={p.get('price_to_win')}")
    # Competition endpoint
    try:
        c=requests.get(f"{API}/items/{iid}/catalog_competitors",headers=H,timeout=10).json()
        print(f"  catalog_competitors: {len(c.get('results') or []) if isinstance(c,dict) else c}")
    except: pass
