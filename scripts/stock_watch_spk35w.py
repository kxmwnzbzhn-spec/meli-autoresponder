import os, requests, json
tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_WILBERT"]}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}
# Get 1 paid order
r = requests.get("https://api.mercadolibre.com/orders/search", params={"seller":3367276814,"order.status":"paid","limit":3,"sort":"date_desc"}, headers=h, timeout=20).json()
for o in r.get("results",[])[:2]:
    print(f"=== ORDER {o.get('id')} ===")
    print(json.dumps({k:v for k,v in o.items() if k in ['buyer','shipping','billing_info','date_created','total_amount']}, indent=2, ensure_ascii=False, default=str)[:2000])
    print()
    # Try fetching the order via individual endpoint
    oid = o.get('id')
    r2 = requests.get(f"https://api.mercadolibre.com/orders/{oid}", headers=h, timeout=20).json()
    print(f"  Individual order endpoint extras (buyer detail): {json.dumps(r2.get('buyer',{}), indent=2, ensure_ascii=False, default=str)[:500]}")
    # Try shipping details
    ship_id = (o.get('shipping') or {}).get('id')
    if ship_id:
        r3 = requests.get(f"https://api.mercadolibre.com/shipments/{ship_id}", headers=h, timeout=20)
        if r3.status_code == 200:
            sd = r3.json()
            ra = sd.get('receiver_address') or {}
            print(f"  Shipment receiver_address: name={ra.get('receiver_name')} phone={ra.get('receiver_phone')} zip={ra.get('zip_code')} city={(ra.get('city') or {}).get('name')}")
