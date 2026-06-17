import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5519420804"
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
print(f"PRE: status={g.get('status')} sub_status={g.get('sub_status')} qty={g.get('available_quantity')} sold={g.get('sold_quantity')} health={g.get('health')}")
print(f"title: {g.get('title')}")
print(f"price: ${g.get('price')}")

# Step 1: activate
p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"active"},timeout=20)
print(f"\nACTIVATE: {p1.status_code} {p1.text[:400]}")

# Step 2: set stock to 200
p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":200},timeout=20)
print(f"STOCK 200: {p2.status_code} {p2.text[:400]}")

g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity,sold_quantity,price",headers=H,timeout=15).json()
print(f"\nPOST: {g2}")
