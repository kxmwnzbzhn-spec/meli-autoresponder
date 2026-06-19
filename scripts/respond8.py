import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CC=5530747987

# Try variations
attempts=[
  ("POST /post-purchase/v1/claims/{}/actions/send_message_to_complainant", "POST", f"{API}/post-purchase/v1/claims/{CC}/actions/send_message_to_complainant", {"message":"Hola, lamentamos el inconveniente. Para procesar el reembolso necesitamos que devuelva el producto en su empaque original. Por favor inicie el proceso de devolución."}),
  ("POST /post-purchase/v2/claims/{}/messages", "POST", f"{API}/post-purchase/v2/claims/{CC}/messages", {"message":"test","receiver_role":"complainant"}),
  ("POST /post-purchase/v1/claims/{}/messages", "POST", f"{API}/post-purchase/v1/claims/{CC}/messages", {"message":"test","receiver_role":"complainant"}),
  ("POST /post-purchase/v1/claims/{}/players/seller/actions", "POST", f"{API}/post-purchase/v1/claims/{CC}/players/seller/actions", {"action":"send_message_to_complainant","message":"test"}),
  ("POST /mediations/{}/messages", "POST", f"{API}/mediations/{CC}/messages", {"text":"test"}),
  ("PUT /post-purchase/v1/claims/{}/actions", "PUT", f"{API}/post-purchase/v1/claims/{CC}/actions", {"action":"send_message_to_complainant","message":"test"}),
  ("POST /post-purchase/v1/claims/{}", "POST", f"{API}/post-purchase/v1/claims/{CC}", {"action":"send_message_to_complainant","message":"test"}),
]

for label, method, url, body in attempts:
  try:
    r=requests.request(method,url,headers=H,json=body,timeout=15)
    print(f"\n{label}")
    print(f"  → {r.status_code} {r.text[:300]}")
  except Exception as e:
    print(f"{label}: ERR {e}")
