import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
ITEM="MLM2976325463"

g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
m_id=None
for v in g.get("variations",[]):
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE" and ac.get("value_name")=="M":
      m_id=v["id"]; print(f"[M variation id] {m_id} qty={v.get('available_quantity')}")
      break

# Force M to qty=0
upd=requests.put(f"{API}/items/{ITEM}",headers=H,
  json={"variations":[{"id":m_id,"available_quantity":0}]},timeout=15)
print(f"[force M=0] HTTP {upd.status_code}")

# Verify zero
g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
for v in g2.get("variations",[]):
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      print(f"  size={ac.get('value_name')} qty={v.get('available_quantity')}")

# Wait 75s for bot to react
print("\n[waiting 75s for bot to detect+repone M=1...]")
time.sleep(75)

# Check final state
g3=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
print("\n[final state after wait]")
fixed=False
for v in g3.get("variations",[]):
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      sz=ac.get("value_name"); qty=v.get('available_quantity')
      print(f"  size={sz} qty={qty}")
      if sz=="M" and qty>=1: fixed=True
print(f"\nBOT-WORKING: {fixed}")
