import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
ats=requests.get(f"{API}/categories/MLM194118/attributes",headers=H,timeout=15).json()
for a in ats:
  if a["id"] in ("SOCKS_TYPE","LENGTH_TYPE","SIZE","GENDER","COLOR","MAIN_COLOR"):
    print(f"\n=== {a['id']} ({a.get('name')}) ===")
    vs=a.get("values") or []
    for v in vs[:20]:
      print(f"  {v.get('id')}: {v.get('name')}")
