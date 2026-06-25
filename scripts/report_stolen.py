import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

it=requests.get(f"{API}/items/MLM3035212177",headers=H,timeout=15).json()
print("item:",it.get("title"),"status:",it.get("status"),"qty_total:",it.get("available_quantity"))
print("variations:")
for v in (it.get("variations") or []):
  print(f"  id={v.get('id')} qty={v.get('available_quantity')} price={v.get('price')} attrs={[(a.get('id'),a.get('value_name')) for a in v.get('attribute_combinations',[])]}")
