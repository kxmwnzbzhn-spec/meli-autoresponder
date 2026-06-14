import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
ITEM="MLM2976325463"

g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
print(f"Time start: {time.strftime('%H:%M:%S')}")
# Send ALL variations, but drop M to 0
v_updates=[]
for v in g.get("variations",[]):
  sz="?"
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE": sz=ac.get("value_name")
  if sz=="M":
    v_updates.append({"id":v["id"],"available_quantity":0})
  else:
    # Keep current qty (don't change S/L)
    v_updates.append({"id":v["id"],"available_quantity":v.get("available_quantity",1)})

p=requests.put(f"{API}/items/{ITEM}",headers=H,json={"variations":v_updates},timeout=15)
print(f"[set M=0, keep S/L] HTTP {p.status_code}")

# Verify drop
g2=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
print(f"State right after drop:")
for v in g2.get("variations",[]):
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      print(f"  {ac.get('value_name')} qty={v.get('available_quantity')}")

# Wait 90s for bot
print(f"\nWaiting 90s... ({time.strftime('%H:%M:%S')})")
time.sleep(90)

g3=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
print(f"\nState after 90s: ({time.strftime('%H:%M:%S')})")
fixed=False
for v in g3.get("variations",[]):
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      sz=ac.get('value_name'); qty=v.get('available_quantity')
      print(f"  {sz} qty={qty}")
      if sz=="M" and qty>=1: fixed=True

print(f"\nBOT-FIX-WORKING: {fixed}")
