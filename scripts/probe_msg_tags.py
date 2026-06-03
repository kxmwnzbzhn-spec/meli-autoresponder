"""Probe valid MELI message tags for seller-initiated messages."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SELLER=me["id"]

# Use one of the blocked orders for probing
ORDER="2000016751999156"
PACK="2000013319647593"
BUYER=146934931
MSG="Test"

# Try different tag values
for tag in ["post_sale","out_of_stock","stock_unavailable","seller_post_sale","SAC_SAC_AFTER_SALE","ORDER_BLOCK","question","ASKING"]:
    url=f"{API}/messages/packs/{PACK}/sellers/{SELLER}?tag={tag}"
    body={"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}
    rr=requests.post(url,headers=HJ,json=body,timeout=15)
    print(f"  tag={tag}: HTTP {rr.status_code}: {rr.text[:300]}")

# Try without tag
url=f"{API}/messages/packs/{PACK}/sellers/{SELLER}"
rr=requests.post(url,headers=HJ,json={"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG},timeout=15)
print(f"\n  no tag: HTTP {rr.status_code}: {rr.text[:300]}")

# Try messages endpoint variants
for path in [
    f"/post-purchase/v1/messages/packs/{PACK}/sellers/{SELLER}",
    f"/messages/action_guide/packs/{PACK}/option/STOCK_UNAVAILABLE",
    f"/messages/orders/{ORDER}/sellers/{SELLER}",
]:
    rr=requests.post(f"{API}{path}",headers=HJ,json={"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG},timeout=15)
    print(f"  {path}: HTTP {rr.status_code}: {rr.text[:200]}")

# Look at the action_guide for this pack to see what's allowed
for path in [
    f"/messages/action_guide/packs/{PACK}",
    f"/messages/options/packs/{PACK}/sellers/{SELLER}",
    f"/messages/option/STOCK_UNAVAILABLE",
]:
    rr=requests.get(f"{API}{path}",headers=H,timeout=15)
    print(f"  GET {path}: HTTP {rr.status_code}: {rr.text[:600]}")
