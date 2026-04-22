import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print("=== ESTADO CUENTA JUAN ===")
print(f"Nickname: {me.get('nickname')}")
print(f"ID: {me.get('id')}")
print(f"Email: {me.get('email')}")
print(f"Site: {me.get('site_id')}")
print(f"Status: {me.get('status')}")
print(f"User Type: {me.get('user_type')}")

status=me.get("status") or {}
print(f"\nStatus detalles:")
print(json.dumps(status,indent=2,ensure_ascii=False))

# site_status / mp_status / list_status
print(f"\nmercadopago_account_type: {me.get('mercadopago_account_type')}")
print(f"mercadopago_tc_accepted: {me.get('mercadopago_tc_accepted')}")

# Restrictions
r=requests.get("https://api.mercadolibre.com/users/me/restrictions",headers=H,timeout=15)
print(f"\n=== RESTRICTIONS ===")
print(f"{r.status_code}: {r.text[:2000]}")

# Puntuacion / reputation
seller=requests.get(f"https://api.mercadolibre.com/users/{me.get('id')}",headers=H,timeout=15).json()
rep=seller.get("seller_reputation") or {}
print(f"\n=== REPUTACION ===")
print(f"Level: {rep.get('level_id')}")
print(f"Power seller: {rep.get('power_seller_status')}")
print(f"Transactions: {json.dumps(rep.get('transactions'),indent=2)}")
print(f"Metrics: {json.dumps(rep.get('metrics'),indent=2)}")

# Questions pendientes
q=requests.get(f"https://api.mercadolibre.com/my/received_questions/search?status=UNANSWERED&limit=50",headers=H,timeout=15).json()
print(f"\n=== QUESTIONS UNANSWERED: {q.get('total',0)} ===")
for qu in q.get("questions",[])[:20]:
    print(f"  q{qu.get('id')} item={qu.get('item_id')} | {qu.get('text','')[:80]}")
