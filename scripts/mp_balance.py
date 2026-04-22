import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me.get("id")
print(f"User: {me.get('nickname')} id={uid}")

# Probar endpoints de balance/account
endpoints=[
    "/users/me/mercadopago_account",
    f"/users/{uid}/mercadopago_account",
    f"/users/{uid}/mercadopago_account_link",
    "/account/balance",
    "/v1/account/balance",
    "/users/me/account",
    f"/sellers/{uid}",
]
for ep in endpoints:
    try:
        r=requests.get(f"https://api.mercadolibre.com{ep}",headers=H,timeout=15)
        print(f"\n{ep}: {r.status_code}")
        print(r.text[:400])
    except Exception as e:
        print(f"{ep}: {e}")

# Tambien mercadopago API
print("\n--- MercadoPago API ---")
for ep in ["/v1/account/balance","/account/balance","/users/me/mercadopago_account/balance"]:
    try:
        r=requests.get(f"https://api.mercadopago.com{ep}",headers=H,timeout=15)
        print(f"{ep}: {r.status_code} {r.text[:300]}")
    except Exception as e:
        print(f"{ep}: {e}")

# Reporte de pagos mensual para calcular: GET /users/me/mercadopago_account
# Alternativa: GET orders y sumar 
print("\n--- Orders pending payment release ---")
ord_r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&limit=50",headers=H,timeout=20).json()
total=0; n=0
for o in ord_r.get("results",[]):
    pays=o.get("payments",[])
    for p in pays:
        if p.get("status")=="approved":
            total += p.get("transaction_amount",0)
            n+=1
print(f"Orders paid approved: {n}, total ~${total:,.2f}")
