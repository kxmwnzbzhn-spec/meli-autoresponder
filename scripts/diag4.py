import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
tok = r['access_token']
SELLER_ID = 3348766821
PACK_ID = 2000012681474781
BUYER_ID = 1404130676
H = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}

# Probar diferentes body formats con tag=post_sale
TESTS = [
    {"from":{"user_id":SELLER_ID}, "to":{"user_id":BUYER_ID}, "text":"prueba 1"},
    {"from":{"user_id":str(SELLER_ID)}, "to":{"user_id":str(BUYER_ID)}, "text":"prueba 2"},
    {"text":"prueba 3"},
    {"from":{"user_id":SELLER_ID}, "to":{"user_id":BUYER_ID}, "text":{"plain":"prueba 4"}},
    {"message":"prueba 5", "from":{"user_id":SELLER_ID}, "to":{"user_id":BUYER_ID}},
]
url = f"https://api.mercadolibre.com/messages/packs/{PACK_ID}/sellers/{SELLER_ID}?tag=post_sale"
for i, body in enumerate(TESTS, 1):
    r = requests.post(url, headers=H, json=body, timeout=15)
    print(f"  [{i}] {r.status_code}: {r.text[:250]}")

# También probar el endpoint que el AUTO-RESPONDER existing uses (cron.yml)
# Veamos si hay un script existente que envíe respuestas a Qs
