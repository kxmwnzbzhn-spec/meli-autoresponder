import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

CLAIM_ID = "5559906352"
PACK_ID  = "2000017809614694"

print("=== CLAIM DETAIL ===")
c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}", headers=H, timeout=15).json()
print(json.dumps(c, indent=2)[:6000])

print("\n=== CLAIM MESSAGES ===")
msgs = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages", headers=H, timeout=15).json()
print(json.dumps(msgs, indent=2)[:8000])

print("\n=== CLAIM EVIDENCES ===")
ev = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/evidences", headers=H, timeout=15).json()
print(json.dumps(ev, indent=2)[:3000])

print("\n=== CLAIM RETURNS (if any) ===")
try:
    rn = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/returns", headers=H, timeout=15).json()
    print(json.dumps(rn, indent=2)[:3000])
except Exception as e:
    print(f"err: {e}")

# Fetch order(s) inside pack
print(f"\n=== PACK {PACK_ID} ===")
p = requests.get(f"https://api.mercadolibre.com/packs/{PACK_ID}", headers=H, timeout=15).json()
print(json.dumps(p, indent=2)[:2000])

if isinstance(p, dict) and p.get("orders"):
    for od in p["orders"][:3]:
        oid = od.get("id")
        oo = requests.get(f"https://api.mercadolibre.com/orders/{oid}", headers=H, timeout=15).json()
        print(f"\n=== ORDER {oid} ===")
        buy = oo.get("buyer",{})
        print(f"buyer: {buy.get('nickname')} id={buy.get('id')} first_name={buy.get('first_name')}")
        for it in (oo.get("order_items") or []):
            itm = it.get("item",{})
            print(f"item: {itm.get('id')} '{itm.get('title')}' qty={it.get('quantity')} price={it.get('unit_price')}")
            for va in (itm.get('variation_attributes') or []):
                print(f"  var_attr: {va.get('id')}={va.get('value_name')}")
        # Shipping status
        sh = oo.get("shipping",{})
        print(f"shipping.id: {sh.get('id')}")
        if sh.get('id'):
            ship = requests.get(f"https://api.mercadolibre.com/shipments/{sh['id']}", headers=H, timeout=15).json()
            print(f"shipping.status: {ship.get('status')} substatus={ship.get('substatus')}")
            print(f"shipping.date_first_visit: {ship.get('status_history',{}).get('date_first_visit')}")
            print(f"shipping.date_delivered: {ship.get('status_history',{}).get('date_delivered')}")
            # Also check tracking history
            for ev in (ship.get("status_history") or {}).items():
                print(f"  hist: {ev}")

# Claim reasons lookup (PDD9949)
print("\n=== REASON DETAIL PDD9949 ===")
try:
    rd = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/reasons/PDD9949?flow=complaints&role=respondent", headers=H, timeout=15).json()
    print(json.dumps(rd, indent=2)[:1500])
except Exception as e:
    print(f"err reason: {e}")
