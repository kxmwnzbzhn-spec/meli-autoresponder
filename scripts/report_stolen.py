import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

reason="Patron fraude KARLOS1986: doble compra simultanea 18-jun 17:30 (Mandarin Quetzal + Templo Oscuro) con motivos distintos. Envio salio completo, original y sellado. Rechazamos devolucion."

# Probe 405 endpoints with GET/PUT/PATCH
endpoints=[
  (5530358522,143755516,"/post-purchase/v1/returns/143755516/reviews"),
  (5530358522,143755516,"/post-purchase/v2/claims/5530358522/returns/143755516/review"),
  (5530358522,143755516,"/post-purchase/v2/claims/5530358522/returns/143755516/reviews"),
  (5530353540,150143661,"/post-purchase/v1/returns/150143661/reviews"),
]
for cid,rid,p in endpoints:
  print(f"\n=== {p} ===")
  # GET to see schema
  g=requests.get(f"{API}{p}",headers=HJ,timeout=15)
  print(f"  GET {g.status_code} {g.text[:600]}")
  # OPTIONS
  o=requests.options(f"{API}{p}",headers=HJ,timeout=15)
  print(f"  OPTIONS {o.status_code} allow={o.headers.get('Allow')} {o.text[:300]}")
  # PUT with body
  pu=requests.put(f"{API}{p}",headers=HJ,json={"status":"failed","description":reason},timeout=15)
  print(f"  PUT {pu.status_code} {pu.text[:300]}")
  pa=requests.patch(f"{API}{p}",headers=HJ,json={"status":"failed","description":reason},timeout=15)
  print(f"  PATCH {pa.status_code} {pa.text[:300]}")
