import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
PACK_ID="2000013380386965"
SELLER=1668713481
BUYER=200789059

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")

MSG=("Buenas tardes. El producto que recibió es 100% original y nuevo. "
     "La bolsa exterior que cubre la caja es nuestro empaque protector estándar, "
     "su función es evitar rayones y golpes a la caja durante el envío. "
     "No todos los perfumes vienen plastificados de fábrica: varias marcas, "
     "especialmente las independientes y artesanales como The Alchemia Lab, "
     "no utilizan envoltura de celofán como sello. "
     "La ausencia de plástico no indica manipulación; el frasco está sellado de origen dentro de su caja original. "
     "Saludos cordiales — Elite Market.")
print(f"[MSG LENGTH] {len(MSG)} chars")

H={"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"}
payload={"from":{"user_id":SELLER},"to":{"user_id":BUYER},"text":MSG}
url=f"{API}/messages/packs/{PACK_ID}/sellers/{SELLER}?tag=post_sale"
r=requests.post(url,headers=H,json=payload,timeout=20)
print(f"[POST send] HTTP {r.status_code}")
print(f"  body: {r.text[:600]}")

# Verify
m=requests.get(f"{API}/messages/packs/{PACK_ID}/sellers/{SELLER}",
  headers={"Authorization":f"Bearer {AT}"},params={"tag":"post_sale","limit":5},timeout=15)
if m.status_code==200:
  mj=m.json()
  msgs=mj.get("messages") or mj.get("results") or []
  if isinstance(mj,list): msgs=mj
  print(f"\n[VERIFY] last {len(msgs)} messages:")
  for x in msgs[:4]:
    f=x.get("from") or {}; t=x.get("to") or {}
    txt_field=x.get("text")
    if isinstance(txt_field,dict): txt=txt_field.get("plain","")
    elif isinstance(txt_field,str): txt=txt_field
    else: txt=x.get("message","") or ""
    dt=x.get("message_date",{}).get("created","") or x.get("date_created","")
    print(f"  {dt[:19]} | from {f.get('user_id')} -> to {t.get('user_id')}: {txt[:150]}")

# Sync RT
try: import nacl.encoding, nacl.public
except: os.system("pip install pynacl -q"); import nacl.encoding, nacl.public
GHT=os.environ.get("GH_PAT")
if GHT and NEW_RT:
  GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
  R="kxmwnzbzhn-spec/meli-autoresponder"
  pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
  pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
  sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
  enc=base64.b64encode(sealed).decode()
  requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_ASVA",
    headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
