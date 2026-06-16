import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

STUCK={
  "MELI_REFRESH_TOKEN_ASVA":[13481398359,13481845083,13547611652,13552676635,13565746685],
  "MELI_REFRESH_TOKEN_WILBERT":[13583110510,13583116852],
}

for secret, qids in STUCK.items():
  rt=os.environ.get(secret)
  if not rt: print(f"no {secret}"); continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
  if r.status_code>=300: print(f"oauth fail {secret}: {r.status_code}"); continue
  AT=r.json()["access_token"]
  H={"Authorization":f"Bearer {AT}"}
  print(f"\n=== {secret} ===")
  for qid in qids:
    d=requests.delete(f"{API}/questions/{qid}",headers=H,timeout=15)
    print(f"  DELETE Q{qid} -> HTTP {d.status_code}: {d.text[:150]}")
