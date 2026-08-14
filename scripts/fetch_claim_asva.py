import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

ORDER_ID = "2000014411673879"

# 1. Fetch order
o = requests.get(f"https://api.mercadolibre.com/orders/{ORDER_ID}", headers=H, timeout=15).json()
print("=== ORDER ===")
print(f"status: {o.get('status')} status_detail: {o.get('status_detail')}")
print(f"date_created: {o.get('date_created')}")
print(f"date_closed: {o.get('date_closed')}")
print(f"buyer: {o.get('buyer',{}).get('nickname')} id={o.get('buyer',{}).get('id')}")
items = o.get("order_items") or []
for it in items:
    itm = it.get("item",{})
    print(f"item: {itm.get('id')} '{itm.get('title')}' qty={it.get('quantity')} price={it.get('unit_price')} cond={itm.get('condition')}")
    for va in (itm.get('variation_attributes') or []):
        print(f"  var_attr: {va.get('id')}={va.get('value_name')}")
shipping = o.get("shipping",{})
print(f"shipping.id: {shipping.get('id')}")

# 2. Find claim
cs = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?resource=order&resource_id={ORDER_ID}", headers=H, timeout=15).json()
print("\n=== CLAIM SEARCH ===")
print(json.dumps(cs, indent=2)[:2000])

claim_id = None
if isinstance(cs, dict) and cs.get("data"):
    claim_id = cs["data"][0].get("id")
elif isinstance(cs, list) and cs:
    claim_id = cs[0].get("id")

if claim_id:
    print(f"\nclaim_id={claim_id}")
    c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{claim_id}", headers=H, timeout=15).json()
    print("\n=== CLAIM DETAIL ===")
    print(json.dumps(c, indent=2)[:3500])

    msgs = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{claim_id}/messages", headers=H, timeout=15).json()
    print("\n=== MESSAGES ===")
    print(json.dumps(msgs, indent=2)[:4000])

    # Evidences
    ev = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{claim_id}/evidences", headers=H, timeout=15).json()
    print("\n=== EVIDENCES ===")
    print(json.dumps(ev, indent=2)[:2000])
else:
    # try v2 endpoint or return endpoint
    ret = requests.get(f"https://api.mercadolibre.com/post-purchase/v2/claims/search?resource=order&resource_id={ORDER_ID}", headers=H, timeout=15).json()
    print("\n=== v2 CLAIM SEARCH ===")
    print(json.dumps(ret, indent=2)[:2000])

print(f"\nCLAIM_ID={claim_id}")
