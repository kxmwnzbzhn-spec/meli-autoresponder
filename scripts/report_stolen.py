import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

reason_text=("El producto devuelto no corresponde con el original. Envio salio completo, sellado y original. "
"Patron fraude: KARLOS1986 abrio dos reclamos simultaneos (Mandarin Quetzal + Templo Oscuro) sobre dos "
"compras entregadas el mismo dia 18-jun 17:30 hrs con motivos distintos.")

rid=143755516
url=f"{API}/post-purchase/v1/returns/{rid}/return-review"

bodies=[
  {"outcome":"fail","reason":"SRF5"},
  {"outcome":"fail","reason":"SRF5","comments":reason_text},
  {"outcome":"fail","reason":"SRF5","description":reason_text},
  {"outcome":"failed","reason":"SRF5"},
  {"outcome":"FAIL","reason":"SRF5"},
  {"outcome":"fail","reason_code":"SRF5"},
  {"status":"fail","reason":"SRF5"},
  {"result":"fail","reason":"SRF5"},
  {"review":{"outcome":"fail","reason":"SRF5"}},
  {"return_review":{"outcome":"fail","reason":"SRF5"}},
  {"outcome":"fail","reason":"SRF5","items":[{"id":"MLM2967772751"}]},
  {"outcome":"fail","reason":"empty_box"},
  {"outcome":"fail","reason":"different_product"},
  {"outcome":"fail","reason":"missing_items"},
  {"outcome":"fail","subreason":"SRF5"},
  {"decision":"fail","reason":"SRF5"},
  {"outcome":"reject","reason":"SRF5"},
  {"outcome":"refused","reason":"SRF5"},
  {"action":"fail","reason":"SRF5"},
]
for b in bodies:
  rr=requests.post(url,headers=HJ,json=b,timeout=15)
  print(f"  body={json.dumps(b)[:80]} -> {rr.status_code} {rr.text[:250]}")
  if rr.status_code in (200,201,204):
    print("  *** SUCCESS ***"); break

# Also try GET to discover schema
print("\n--- GET ---")
g=requests.get(url,headers=HJ,timeout=15)
print(f"  GET -> {g.status_code} {g.text[:400]}")
# OPTIONS
o=requests.options(url,headers=HJ,timeout=15)
print(f"  OPTIONS -> {o.status_code} allow={o.headers.get('Allow')} {o.text[:200]}")
