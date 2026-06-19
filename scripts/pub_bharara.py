import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5510952004"
g=requests.get(f"{API}/items/{IID}?attributes=id,title,status,sub_status,available_quantity,price",headers=H,timeout=15).json()
print(f"PRE: {g}")

# Force qty=0
p1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":0},timeout=20)
print(f"QTY=0: {p1.status_code}")
# Pause
p2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"paused"},timeout=20)
print(f"PAUSE: {p2.status_code}")
# Close (irreversible)
p3=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"closed"},timeout=20)
print(f"CLOSE: {p3.status_code} {p3.text[:300]}")
# Delete
p4=requests.put(f"{API}/items/{IID}",headers=HJ,json={"deleted":"true"},timeout=20)
print(f"DELETE: {p4.status_code} {p4.text[:300]}")

g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers=H,timeout=15).json()
print(f"POST: {g2}")
