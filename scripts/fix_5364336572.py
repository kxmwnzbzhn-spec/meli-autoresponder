import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
FLOOR=899; CEIL=999
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5364336572"
g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
cur=g.get("price"); print(f"cur=${cur} status={g.get('status')}")
p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
st=p.get("status"); ptw=p.get("price_to_win")
print(f"PTW: {st} ptw=${ptw}")
if st in ("competing","losing","sharing_first_place") and ptw:
    target=max(int(ptw)-2, FLOOR); target=min(target, CEIL)
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
    print(f"CLAIM ${cur}→${target} (floor=${FLOOR} ceil=${CEIL}) http={r.status_code}")
elif st=="winning":
    # asegurar dentro de rango
    if cur>CEIL:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":CEIL},timeout=15)
        print(f"cap to ceiling ${cur}→${CEIL} http={r.status_code}")
    elif cur<FLOOR:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":FLOOR},timeout=15)
        print(f"raise to floor ${cur}→${FLOOR} http={r.status_code}")
    else:
        print(f"winning dentro de rango, hold ${cur}")
time.sleep(1.5)
p2=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
print(f"POST: price=${g2.get('price')} PTW={p2.get('status')}")
