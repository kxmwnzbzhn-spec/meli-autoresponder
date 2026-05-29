import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
IDS=["MLM5374722276","MLM5374718702","MLM2945214721","MLM2945250605","MLM2954229423"]
for sid in IDS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    print(f"\n{sid}")
    print(f"  status={g.get('status')} sub={g.get('sub_status')} price=${g.get('price')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')}")
    print(f"  title='{g.get('title')}'")
    print(f"  url={g.get('permalink')}")
