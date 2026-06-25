import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Items + target prices
PINS=[
  ("MLM5569359030",1199,"Marshall Emberton"),
  ("MLM5569444970",999,"Marshall Willen II"),
  ("MLM3045613145",1199,"Beats Pill Negro Mate"),
  ("MLM5569408564",1199,"Beats Pill Rojo"),
]
for iid,price,name in PINS:
  r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":price},timeout=20)
  print(f"PIN {name} {iid} -> ${price}: HTTP {r.status_code}")
  if r.status_code>=400:
    print(f"  ERR: {r.text[:300]}")
  else:
    j=r.json()
    print(f"  ✓ price now: ${j.get('price')}")
