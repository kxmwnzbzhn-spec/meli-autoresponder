import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
tok = r['access_token']
me = requests.get("https://api.mercadolibre.com/users/me", headers={"Authorization":f"Bearer {tok}"}).json()
SELLER_ID = me["id"]
print(f"seller_id={SELLER_ID}")

CID = "5505476644"
ORDER_ID = "2000016146467848"

# Buscar pack_id de la orden
H = {"Authorization": f"Bearer {tok}"}
o = requests.get(f"https://api.mercadolibre.com/orders/{ORDER_ID}", headers=H).json()
PACK_ID = o.get("pack_id") or ORDER_ID
BUYER_ID = (o.get("buyer") or {}).get("id")
print(f"pack_id={PACK_ID} buyer_id={BUYER_ID}")

# Obtener uno de los mensajes existentes para ver formato
m = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/messages", headers=H).json()
print(f"\nMensaje existente sample:")
if m and isinstance(m, list):
    for msg in m[:2]:
        print(f"  sender={msg.get('sender_role')} keys={list(msg.keys())}")
        for k in ['date_created','message','message_id','attributes']:
            v = msg.get(k)
            if v: print(f"    {k}: {str(v)[:120]}")

# Probar API de mensajes 2.0 (packs)
H2 = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}

URLS = [
    ("POST", f"https://api.mercadolibre.com/messages/packs/{PACK_ID}/sellers/{SELLER_ID}?tag=post_sale", 
        {"from":{"user_id":SELLER_ID}, "to":{"user_id":BUYER_ID}, "text":{"plain":"test playbook 5puntos prueba"}}),
    ("POST", f"https://api.mercadolibre.com/messages/packs/{PACK_ID}/sellers/{SELLER_ID}", 
        {"from":{"user_id":SELLER_ID}, "to":{"user_id":BUYER_ID}, "text":"test 2"}),
    # Multipart approach
    ("POST_MULTIPART", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/messages", 
        {"text":"prueba multipart"}),
]
for method, url, body in URLS:
    try:
        if method == "POST":
            r = requests.post(url, headers=H2, json=body, timeout=15)
        else:  # multipart
            r = requests.post(url, headers={"Authorization":f"Bearer {tok}"}, data=body, files={"dummy":("","")}, timeout=15)
        print(f"\n{method} {url[-90:]}")
        print(f"  → {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"  ERR: {e}")
