import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
for cid in [5530358522,5530353540]:
  c=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=20).json()
  print(f"\n=== CLAIM {cid} ===")
  for k in ("type","stage","status","reason_id","resolution","expected_resolutions","resource","resource_id","date_created","quantity_type","fulfilled","related_entities","shipping","tracking","tracking_number","return"):
    if k in c: print(f"  {k}: {c.get(k)}")
  # try returns endpoint
  ret=requests.get(f"{API}/post-purchase/v1/claims/{cid}/returns",headers=H,timeout=15)
  print("  /returns:",ret.status_code,ret.text[:400])
  # try expected resolutions
  er=requests.get(f"{API}/post-purchase/v1/claims/{cid}/expected_resolutions",headers=H,timeout=15)
  print("  /expected_resolutions:",er.status_code,er.text[:400])
  # try messages
  m=requests.get(f"{API}/post-purchase/v1/claims/{cid}/messages",headers=H,timeout=15)
  print("  /messages:",m.status_code,m.text[:600])
