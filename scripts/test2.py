import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SELLER=me["id"]
PACK="2000013319647593"
BUYER=146934931
MSG="Hola, prueba breve sobre disponibilidad en otro color, mil gracias."

# Variants — try different tags/option_ids
for ep, method, body in [
    (f"/messages/packs/{PACK}/sellers/{SELLER}?option=OTHER", "POST",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/packs/{PACK}/sellers/{SELLER}?tag=OTHER", "POST",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/packs/{PACK}/sellers/{SELLER}?option_id=OTHER", "POST",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}", "POST",
     {"option_id":"OTHER","from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/option/OTHER", "PUT",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/option/OTHER", "POST",
     {"option_id":"OTHER","text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/options/OTHER", "POST",
     {"text":MSG,"from":{"user_id":SELLER},"to":{"user_id":BUYER}}),
]:
    if method=="POST":
        rr=requests.post(f"{API}{ep}",headers=HJ,json=body,timeout=15)
    else:
        rr=requests.put(f"{API}{ep}",headers=HJ,json=body,timeout=15)
    print(f"\n{method} {ep}\n  HTTP {rr.status_code}: {rr.text[:400]}")
