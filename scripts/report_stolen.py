import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]

# IMPORTANT: only probe with return 150143661 which is still open
rid=150143661
url=f"{API}/post-purchase/v1/returns/{rid}/return-review"
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Try path-based variants (don't touch the open return with body=empty)
candidates=[
  ("POST",f"{API}/post-purchase/v1/returns/{rid}/return-review?outcome=fail&reason=SRF5",HJ,None),
  ("POST",f"{API}/post-purchase/v1/returns/{rid}/return-review?action=fail",HJ,None),
  ("POST",f"{API}/post-purchase/v1/returns/{rid}/return-review",HJ,json.dumps({"resource_reviews":[{"seller_status":"fail","reason_id":"SRF5"}]})),
  ("POST",f"{API}/post-purchase/v1/returns/{rid}/return-review",HJ,json.dumps({"resource_reviews":[{"status":"fail","reason_id":"SRF5"}]})),
  ("POST",f"{API}/post-purchase/v1/returns/{rid}/return-review",HJ,json.dumps([{"status":"fail","reason":"SRF5"}])),
  ("POST",f"{API}/post-purchase/v1/returns/{rid}/return-review",HJ,json.dumps({"reviews":[{"status":"fail","reason":"SRF5"}]})),
]
for m,u,h,b in candidates:
  rr=requests.request(m,u,headers=h,data=b,timeout=15)
  print(f"  {u.split('?')[-1] if '?' in u else 'body='+str(b)[:60]} -> {rr.status_code} {rr.text[:250]}")
  if rr.status_code in (200,201,204):
    print("  *** SUCCESS ***")
    # verify
    import time; time.sleep(1)
    rv=requests.get(f"{API}/marketplace/v2/returns/{rid}/reviews",headers=HJ,timeout=10)
    print(f"  REVIEW STATE: {rv.text[:600]}")
    break
