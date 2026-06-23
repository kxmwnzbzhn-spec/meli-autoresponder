import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]

reason="Patron fraude KARLOS1986. Envio salio completo y original. Rechazamos devolucion."

# Aggressive probe on /marketplace/v2/returns/{rid}/reviews with many shapes
rid=143755516
candidate_methods=["POST","PUT"]
candidate_bodies=[
  ({"status":"failed","description":reason},"json"),
  ({"status":"failed","reason_code":"BUYER_RESPONSIBILITY","description":reason},"json"),
  ({"review":{"status":"failed","description":reason}},"json"),
  ({"result":"failed","description":reason},"json"),
  ({"results":["failed"],"description":reason},"json"),
  ([{"status":"failed","description":reason}],"json_array"),
  ({"status":"failed","description":reason},"form"),
]
candidate_headers=[
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json"},
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"},
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json","Accept":"application/json","User-Agent":"mlapi/1.0"},
]
url=f"{API}/marketplace/v2/returns/{rid}/reviews"
for m in candidate_methods:
  for body,t in candidate_bodies:
    for h in candidate_headers:
      kwargs={"headers":h,"timeout":12}
      if t=="json":
        kwargs["json"]=body
      elif t=="form":
        kwargs["data"]=body
      else:
        kwargs["json"]=body
      try: rr=requests.request(m,url,**kwargs)
      except Exception as e: continue
      if rr.status_code!=405:
        print(f"{m} body={str(body)[:60]} hdr={list(h.keys())[2:]} -> {rr.status_code} {rr.text[:200]}")

# Also try same shape but with /marketplace/v1/ instead of v2
for v in ["v1","v2"]:
  for path in [f"/marketplace/{v}/returns/{rid}/reviews",f"/marketplace/{v}/returns/{rid}/review"]:
    for m in ["POST","PUT"]:
      url=f"{API}{path}"
      rr=requests.request(m,url,headers={"Authorization":f"Bearer {AT}","Content-Type":"application/json"},json={"status":"failed","description":reason},timeout=10)
      if rr.status_code!=405:
        print(f"{m} {path} -> {rr.status_code} {rr.text[:200]}")
