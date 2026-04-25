import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

REASON_LABELS = {
    "PDD9943": "no es original / no es lo que esperaba",
    "PDD9944": "producto defectuoso/dañado",
    "PNR9501": "no llegó el producto",
    "PDD8975": "producto incompleto",
    "PDD9945": "producto distinto al publicado",
    "PDD8974": "diferente al pedido",
    "PDD8973": "no le gustó",
    "PDR9526": "no recibió el producto",
}

total = 0
for label, env in ACCOUNTS:
    RT = os.environ.get(env, "")
    if not RT:
        print(f"\n=== {label}: sin RT ===")
        continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
        USER_ID = me.get("id")
        
        # Get open claims
        rc = requests.get(
            f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=20",
            headers=H, timeout=15
        ).json()
        claims = rc.get("data") or []
        
        print(f"\n=== {label} ({me.get('nickname')}) — {len(claims)} reclamos abiertos ===")
        for c in claims:
            cid = c.get("id")
            stage = c.get("stage")
            reason_id = c.get("reason_id","")
            reason_label = REASON_LABELS.get(reason_id, reason_id)
            order_id = c.get("resource_id")
            type_ = c.get("type")
            
            # Get order details
            try:
                ord_data = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=H, timeout=10).json()
                buyer = ord_data.get("buyer",{}).get("nickname","?")
                items_titles = [i.get("item",{}).get("title","")[:50] for i in ord_data.get("order_items",[])]
                product = items_titles[0] if items_titles else "?"
                amount = ord_data.get("total_amount", "?")
            except: 
                buyer = "?"; product = "?"; amount = "?"
            
            print(f"  • Claim {cid}")
            print(f"      type={type_} stage={stage}")
            print(f"      motivo: {reason_label} ({reason_id})")
            print(f"      orden: {order_id} | comprador: {buyer} | ${amount}")
            print(f"      producto: {product}")
            total += 1
    except Exception as e:
        print(f"  err: {e}")

print(f"\n========= TOTAL CLAIMS ABIERTOS: {total} =========")
