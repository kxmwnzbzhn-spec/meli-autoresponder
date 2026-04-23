import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"ASVA user_id: {USER_ID} nickname: {me.get('nickname')}")

ITEMS={
    "Negro":"MLM5233480022",
    "Azul":"MLM5233454100",
    "Rojo":"MLM2886030837",
    "Morado":"MLM2886136351",
}

# 1) Verificar elegibilidad FULL por item
print("\n=== ELEGIBILIDAD FULL (logistic_type) ===")
for color,iid in ITEMS.items():
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,shipping,logistic_type,inventory_id,user_product_id,tags",headers=H).json()
    ship=d.get("shipping") or {}
    print(f"  {color} {iid}: logistic={d.get('logistic_type')} inv_id={d.get('inventory_id')} mode={ship.get('mode')} tags={(d.get('tags') or [])[:6]}")

# 2) Explorar endpoints FULL
print("\n=== PROBE FULL ENDPOINTS ===")
paths=["/fbm/inbound/shipments","/fbm/inbound-shipments","/fbm/shipments","/fbm/warehouses","/fulfillment/shipments",
       "/logistics/inbound_shipments","/inbound-shipments","/fbm/v1/shipments",
       f"/users/{USER_ID}/fulfillment/warehouses",
       f"/users/{USER_ID}/inbound",
       "/sites/MLM/fbm/warehouses",
       "/sites/MLM/logistics/warehouses"]
for p in paths:
    rp=requests.get(f"https://api.mercadolibre.com{p}",headers=H,timeout=10)
    if rp.status_code!=404 and rp.status_code!=405:
        print(f"  GET {p}: {rp.status_code} | {rp.text[:250]}")

# 3) Verificar si ASVA está enrolada en FULL
print("\n=== FULL ENROLLMENT ===")
rp=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/fbm/enrollment",headers=H,timeout=10)
print(f"  enrollment: {rp.status_code} | {rp.text[:300]}")
rp=requests.get(f"https://api.mercadolibre.com/fbm/sellers/{USER_ID}",headers=H,timeout=10)
print(f"  fbm seller: {rp.status_code} | {rp.text[:300]}")
