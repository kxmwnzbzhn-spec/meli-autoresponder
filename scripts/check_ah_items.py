import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
# Sample IDs I published today
SAMPLES=["MLM2969816519","MLM2969816535","MLM2969849549","MLM2969825393","MLM2969976211","MLM2969827063","MLM2967772739"]
for sid in SAMPLES:
    r=requests.get(f"{API}/items/{sid}",headers=H,timeout=10)
    if r.status_code==200:
        b=r.json()
        print(f"{sid} status={b.get('status')} sub={b.get('sub_status')} seller={b.get('seller_id')} price={b.get('price')} title={(b.get('title') or '')[:50]}")
    else:
        print(f"{sid} HTTP {r.status_code} {r.text[:120]}")
