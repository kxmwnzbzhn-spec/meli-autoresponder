import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}
ITEM="MLM2976325463"
g=requests.get(f"{API}/items/{ITEM}?include_attributes=all",headers=H,timeout=15).json()
# Print all variations + their full data
for v in g.get("variations") or []:
  print(f"=== variation {v.get('id')} ===")
  print(json.dumps(v,ensure_ascii=False,indent=2))

# Also check chart
for a in g.get("attributes",[]):
  if a.get("id") in ("SIZE_GRID_ID","SIZE_GRID_ROW_ID"):
    print(f"[main attr] {a.get('id')}: {a.get('value_name')} (vid={a.get('value_id')})")

# Chart info
chart_id="5915675"
ch=requests.get(f"{API}/catalog/charts/{chart_id}",headers=H,timeout=15)
print(f"\n[chart {chart_id}] HTTP {ch.status_code}")
print(ch.text[:3000])
