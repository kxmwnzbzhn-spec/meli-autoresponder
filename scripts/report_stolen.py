import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]

rid=143755516
url=f"{API}/post-purchase/v1/returns/{rid}/return-review"
auth={"Authorization":f"Bearer {AT}"}

# Try x-format-new header + various content-types
configs=[
  ("JSON+xfn-true",{**auth,"Content-Type":"application/json","x-format-new":"true"},json.dumps({"outcome":"fail","reason":"SRF5"})),
  ("JSON+xfn-false",{**auth,"Content-Type":"application/json","x-format-new":"false"},json.dumps({"outcome":"fail","reason":"SRF5"})),
  ("form",{**auth,"Content-Type":"application/x-www-form-urlencoded"},"outcome=fail&reason=SRF5"),
  ("multipart",{**auth},None),
  ("no-content-type",{**auth},json.dumps({"outcome":"fail","reason":"SRF5"})),
  ("text-plain",{**auth,"Content-Type":"text/plain"},json.dumps({"outcome":"fail","reason":"SRF5"})),
  ("empty-body-no-ct",{**auth},""),
  ("xfn-1",{**auth,"Content-Type":"application/json","x-format-new":"1"},json.dumps({"outcome":"fail","reason":"SRF5"})),
]
for lbl,h,b in configs:
  if lbl=="multipart":
    rr=requests.post(url,headers=h,files={"outcome":(None,"fail"),"reason":(None,"SRF5")},timeout=15)
  else:
    rr=requests.post(url,headers=h,data=b,timeout=15)
  print(f"  {lbl} -> {rr.status_code} {rr.text[:200]}")

# Try the SRF reason as URL param
print("\n--- query string variants ---")
for q in ["?outcome=fail&reason=SRF5","?reason=SRF5","?srf=SRF5"]:
  rr=requests.post(url+q,headers={**auth,"Content-Type":"application/json"},json={"outcome":"fail","reason":"SRF5"},timeout=15)
  print(f"  {q} -> {rr.status_code} {rr.text[:200]}")
