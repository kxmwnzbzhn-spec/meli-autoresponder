import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]

reason="Patron fraude KARLOS1986 doble compra simultanea 18-jun 17:30 mismas Alchemia 100ml. Paquetes salieron completos y originales. Rechazamos devolucion."

# Try POST on the GET 200 endpoint with various headers and body shapes
rid=143755516
candidates_methods=["POST","PUT"]
candidates_urls=[
  f"/post-purchase/v1/returns/{rid}/reviews",
  f"/post-purchase/v1/returns/{rid}/review",
  f"/post-purchase/v2/returns/{rid}/reviews",
  f"/post-purchase/v2/returns/{rid}/review",
  f"/post-purchase/v1/returns/{rid}/seller_review",
  f"/post-purchase/v1/returns/{rid}/result",
  f"/post-purchase/v1/returns/{rid}/results",
]
candidates_headers=[
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json"},
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"},
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"false"},
  {"Authorization":f"Bearer {AT}","Content-Type":"application/json","Accept":"application/json"},
]
candidates_bodies=[
  {"status":"failed","description":reason},
  {"result":"failed","description":reason},
  {"result":"fail","description":reason},
  {"review_result":"failed","description":reason},
  {"review":"failed","comments":reason},
  {"reason_code":"BUYER_RESPONSIBILITY","description":reason},
  {"reason_code":"FRAUD","description":reason},
  {"reason":"buyer_responsibility","description":reason},
  {"reason":"BUYER_RESPONSIBILITY","description":reason},
  {"resolution":"failed","description":reason},
  {"failed":True,"description":reason},
  {"comments":reason},
]
seen_codes=set()
for m in candidates_methods:
  for u in candidates_urls:
    for h in candidates_headers[:2]:
      for b in candidates_bodies:
        try:
          rr=requests.request(m,f"{API}{u}",headers=h,json=b,timeout=12)
        except: continue
        key=(m,u,rr.status_code,rr.text[:80])
        if rr.status_code not in (400,404,405,500) or key in seen_codes:
          continue
        seen_codes.add(key)
        body_key=list(b.keys())[0]
        if rr.status_code in (200,201,204,422,409):
          print(f"  *** {m} {u} body={b} hdr-extra={list(h.keys())[2:]} -> {rr.status_code} {rr.text[:300]}")
        elif "review" in rr.text.lower() or "status" in rr.text.lower() or "reason" in rr.text.lower():
          print(f"  {m} {u} body={body_key} -> {rr.status_code} {rr.text[:200]}")
