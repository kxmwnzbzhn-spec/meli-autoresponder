"""Test send via action_guide OTHER option (free text)."""
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
MSG=("Hola, te escribimos de la tienda. Lamentablemente tuvimos una sobreventa del modelo "
     "Bose SoundLink Home en color Negro y no contamos con stock para despacharte esa pieza. "
     "Tenemos disponibilidad del mismo modelo en color Gris Plata, nuevo y sellado al mismo precio. "
     "¿Te interesa que te lo enviemos en Gris Plata? Si prefieres, podemos procesar el reembolso "
     "completo. Quedamos atentos. Disculpa la molestia.")

# Try several variants of the endpoint
for path, body in [
    (f"/messages/action_guide/packs/{PACK}/option/OTHER",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/option/OTHER?option_id=OTHER",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/option/REQUEST_VARIANTS",
     {"template_id":"TEMPLATE___REQUEST_VARIANTS___1"}),
    (f"/messages/packs/{PACK}/sellers/{SELLER}?tag=action_guide",
     {"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/option/OTHER",
     {"text":MSG}),
    (f"/messages/action_guide/packs/{PACK}/option/OTHER",
     {"message":{"text":MSG}}),
]:
    rr=requests.post(f"{API}{path}",headers=HJ,json=body,timeout=15)
    print(f"\n{path}\n  body={json.dumps(body)[:80]}\n  HTTP {rr.status_code}: {rr.text[:400]}")
