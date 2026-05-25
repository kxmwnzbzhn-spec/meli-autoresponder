import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
bodies=[
 {"names":{"main":"Tallas Boxers"},"domain_id":"MLM-UNDERPANTS","site_id":"MLM",
  "rows":[{"attributes":[{"id":"SIZE","values":[{"name":"S"}]}]}]},
 {"names":{"main":"Tallas Boxers"},"domain_id":"MLM-UNDERPANTS","site_id":"MLM",
  "attributes":[{"id":"GENDER","values":[{"name":"Sin género"}]}],
  "measure_type":"BODY",
  "rows":[{"attributes":[{"id":"SIZE","values":[{"name":"S"}]}]}]},
]
for i,b in enumerate(bodies):
    r=requests.post(f"{API}/catalog_charts",headers=HJ,json=b,timeout=30)
    print(f"\n=== body {i} -> http={r.status_code}")
    print(r.text[:900])
print("DONE")
