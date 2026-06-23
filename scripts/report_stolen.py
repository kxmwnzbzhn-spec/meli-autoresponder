import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# SRF5 = robado/empty_box/tamperado
PAIRS=[(143755516,5530358522,"Mandarin Quetzal"),(150143661,5530353540,"Templo Oscuro")]

for rid,cid,name in PAIRS:
  print(f"\n=== RETURN {rid} (claim {cid}) {name} ===")
  payload={"outcome":"fail","reason":"SRF5"}
  rr=requests.post(f"{API}/post-purchase/v1/returns/{rid}/return-review",headers=HJ,json=payload,timeout=25)
  print(f"  POST return-review SRF5 -> {rr.status_code} {rr.text[:400]}")
