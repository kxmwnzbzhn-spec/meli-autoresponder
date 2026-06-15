import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"}

PACK="2000016898113020"  # delivered pack
SELLER=3417664339
BUYER=None
# Get buyer
o=requests.get(f"{API}/packs/{PACK}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
if o.get("orders"):
  o2=requests.get(f"{API}/orders/{o['orders'][0]['id']}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
  BUYER=(o2.get("buyer") or {}).get("id")
print(f"pack={PACK} buyer={BUYER}")

# Try multiple combinations
attempts=[
  ("post_sale + intent thanks",f"{API}/messages/packs/{PACK}/sellers/{SELLER}?tag=post_sale",
    {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":"prueba","intention":"thanks"}),
  ("post_sale + intent_id 30",f"{API}/messages/packs/{PACK}/sellers/{SELLER}?tag=post_sale",
    {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":"prueba","intention_id":30}),
  ("post_sale + template type review",f"{API}/messages/packs/{PACK}/sellers/{SELLER}?tag=post_sale",
    {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":"prueba","template_id":"review_request"}),
  ("tag rating",f"{API}/messages/packs/{PACK}/sellers/{SELLER}?tag=rating",
    {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":"prueba"}),
  ("tag feedback",f"{API}/messages/packs/{PACK}/sellers/{SELLER}?tag=feedback",
    {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":"prueba"}),
  ("no tag",f"{API}/messages/packs/{PACK}/sellers/{SELLER}",
    {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":"prueba"}),
]
for label,url,body in attempts:
  r=requests.post(url,headers=H,json=body,timeout=12)
  print(f"  [{label}] HTTP {r.status_code}: {r.text[:180]}")

# Check feedbacks/messages-templates endpoints
for url in [
  f"{API}/post-purchase/v1/orders/{o['orders'][0]['id']}/feedbacks",
  f"{API}/post-purchase/v1/orders/{o['orders'][0]['id']}/feedback-requests",
  f"{API}/post-purchase/v1/feedback-templates",
  f"{API}/orders/{o['orders'][0]['id']}/feedback",
  f"{API}/feedback/{o['orders'][0]['id']}",
]:
  r=requests.get(url,headers={"Authorization":f"Bearer {AT}"},timeout=8)
  print(f"  GET {url[-60:]} -> {r.status_code}: {r.text[:200]}")
