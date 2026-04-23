import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]

CLAIM_ID="5501400150"
ORDER_ID="2000016049054518"

# 1) Detalle completo del claim
print("=== CLAIM DETAIL ===")
c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}",headers=H,timeout=15).json()
print(json.dumps(c,ensure_ascii=False,indent=2)[:3000])

# 2) Mensajes existentes del claim
print("\n=== MESSAGES ===")
for path in [f"/post-purchase/v1/claims/{CLAIM_ID}/messages",
             f"/messages/claims/{CLAIM_ID}",
             f"/post-purchase/v1/claims/{CLAIM_ID}/review-messages",
             f"/post-purchase/v1/claims/{CLAIM_ID}/expected_resolutions"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"  GET {path}: {rp.status_code}")
    if rp.status_code==200:
        print(f"    {rp.text[:1200]}")

# 3) Acciones disponibles
print("\n=== AVAILABLE ACTIONS ===")
for path in [f"/post-purchase/v1/claims/{CLAIM_ID}/actions",
             f"/post-purchase/v2/claims/{CLAIM_ID}/actions",
             f"/post-purchase/v1/claims/{CLAIM_ID}/players/complainant/actions",
             f"/post-purchase/v1/claims/{CLAIM_ID}/players/respondent/actions"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"  GET {path}: {rp.status_code}")
    if rp.status_code==200:
        print(f"    {rp.text[:1500]}")

# 4) Orden + pack_id + buyer
print("\n=== ORDER ===")
o=requests.get(f"https://api.mercadolibre.com/orders/{ORDER_ID}",headers=H,timeout=15).json()
pack_id=o.get("pack_id")
buyer_id=(o.get("buyer") or {}).get("id")
buyer_nick=(o.get("buyer") or {}).get("nickname")
item_id=(o.get("order_items") or [{}])[0].get("item",{}).get("id")
item_title=(o.get("order_items") or [{}])[0].get("item",{}).get("title")
print(f"  pack_id={pack_id} buyer={buyer_nick}({buyer_id}) item={item_id} '{item_title}'")

# 5) Obtener descripción del item
if item_id:
    d=requests.get(f"https://api.mercadolibre.com/items/{item_id}/description",headers=H).json()
    desc=d.get("plain_text","")
    print(f"\nDescripción del item ({len(desc)} chars):")
    print(desc[:1500])
