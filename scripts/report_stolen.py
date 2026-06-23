import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Probe intermediate_check / verification endpoints
for rid,cid in [(143755516,5530358522),(150143661,5530353540)]:
  for p in [
    f"/post-purchase/v1/returns/{rid}/intermediate_check",
    f"/post-purchase/v1/returns/{rid}/verification",
    f"/post-purchase/v1/returns/{rid}/verifications",
    f"/post-purchase/v1/returns/{rid}/inspection",
    f"/post-purchase/v1/returns/{rid}/inspections",
    f"/post-purchase/v1/returns/{rid}/seller_inspection",
    f"/post-purchase/v1/returns/{rid}/seller-verification",
    f"/post-purchase/v1/returns/{rid}/start-review",
    f"/post-purchase/v1/returns/{rid}/start_review",
    f"/marketplace/v2/returns/{rid}/intermediate_check",
    f"/marketplace/v2/returns/{rid}/review",
    f"/marketplace/v2/returns/{rid}/reviews",
    f"/marketplace/v2/returns/{rid}/inspection",
    f"/marketplace/v1/returns/{rid}/reviews",
    f"/marketplace/v1/returns/{rid}/review",
  ]:
    g=requests.get(f"{API}{p}",headers=HJ,timeout=10)
    if g.status_code not in (404,400) or "review" in g.text.lower() or "inspect" in g.text.lower():
      print(f"GET  {p} {g.status_code} {g.text[:200]}")
    po=requests.post(f"{API}{p}",headers=HJ,json={},timeout=10)
    if po.status_code not in (404,400,405):
      print(f"POST {p} {po.status_code} {po.text[:200]}")
    if po.status_code==400 and "required" in po.text.lower():
      print(f"POST {p} {po.status_code} {po.text[:300]}")
