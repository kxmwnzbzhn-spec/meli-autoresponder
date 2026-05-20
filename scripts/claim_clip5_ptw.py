import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
MIN_FLOOR=200

for iid in ["MLM5364336572","MLM5364336602"]:
    print(f"\n=== {iid} ===")
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    st=p.get("status"); ptw=p.get("price_to_win")
    print(f"  cur=${cur} PTW={st} ptw=${ptw}")
    if st in ("competing","losing") and ptw:
        target=max(int(ptw)-2, MIN_FLOOR)
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
        print(f"  CLAIM ${cur}→${target} http={r.status_code}")
        time.sleep(1.5)
        p2=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        print(f"  PTW post: {p2.get('status')} ptw={p2.get('price_to_win')}")
    else:
        print(f"  ya winning, no toco")
