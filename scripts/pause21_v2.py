import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Get all open claims for seller respondent
cs=requests.get(f"{API}/post-purchase/v1/claims/search?status=opened&player.role=respondent&limit=100",headers=H,timeout=20).json()
claims=cs.get("data") or cs.get("results") or []
print(f"open ASVA claims: {len(claims)}")
print()

# Find ones related to "empty package" or "missing items"
for c in claims:
  cid=c.get("id")
  full=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=10).json()
  reason=full.get("reason_id","")
  res=full.get("resource_id")
  stage=full.get("stage")
  status=full.get("status")
  # Get reason name
  try:
    rn=requests.get(f"{API}/post-purchase/v1/claims/reasons/{reason}",headers=H,timeout=5).json().get("name","")
  except: rn=""
  # Find order title
  title=""
  if res and full.get("resource")=="order":
    try:
      o=requests.get(f"{API}/orders/{res}",headers=H,timeout=10).json()
      title=(o.get("order_items",[{}])[0].get("item",{}).get("title","") or "")[:60]
    except: pass
  # Actions available
  acts=[]
  for p in full.get("players",[]):
    if p.get("role")=="respondent":
      acts=[a.get("action") if isinstance(a,dict) else a for a in (p.get("available_actions") or [])]
  flag=""
  rnl=(rn or "").lower()
  if "vacio" in rnl or "empty" in rnl or "missing" in rnl or "incomplete" in rnl or "incompleto" in rnl:
    flag=" 🚨 PAQUETE_VACIO_FRAUDE"
  print(f"  claim {cid} | order {res} | {stage}/{status} | reason={reason} '{rn}'{flag}")
  print(f"    title: {title}")
  print(f"    actions: {acts}")
