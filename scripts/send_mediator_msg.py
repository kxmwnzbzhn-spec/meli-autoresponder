import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CLAIM_ID=5527022434

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

MSG=("Buen día. Agradecemos al comprador su mensaje y a Mercado Libre por el espacio de mediación. "
     "El producto entregado es 100% original, importado, y fue revisado antes del envío. "
     "Por la naturaleza de un Eau de Parfum como Alma de Tenochtitlán (perfil amaderado), la pirámide olfativa evoluciona en piel: "
     "las notas de salida y corazón son volátiles y dejan paso al drydown amaderado entre las 6 y 12 horas posteriores a la aplicación. "
     "A los tres días lo que el comprador percibe corresponde al drydown característico de la fragancia, no a un defecto. "
     "Solicitamos respetuosamente mantener el caso como asesoría brindada sin reembolso, ya que el artículo cumple su descripción. "
     "Quedamos a disposición del comprador para resolver cualquier duda. Saludos cordiales — Elite Market.")
print(f"[MSG LENGTH] {len(MSG)} chars")

payload={"receiver_role":"mediator","message":MSG,"attachments":[]}
r=requests.post(f"{API}/marketplace/v2/claims/{CLAIM_ID}/actions/send-message",
  headers=H,json=payload,timeout=20)
print(f"[POST send-message] HTTP {r.status_code}")
print(f"  body: {r.text[:600]}")

# Verify by reading messages back
m=requests.get(f"{API}/marketplace/v2/claims/{CLAIM_ID}/messages",headers={"Authorization":f"Bearer {AT}"},timeout=15)
print(f"\n[GET messages] HTTP {m.status_code}")
if m.status_code==200:
  msgs=m.json()
  if isinstance(msgs,dict): msgs=msgs.get('messages') or []
  print(f"  total: {len(msgs)}")
  for x in msgs[:5]:
    who=x.get('sender_role'); to=x.get('receiver_role'); st=x.get('status'); mod=(x.get('message_moderation') or {}).get('status')
    txt=(x.get('message') or '')[:100]
    print(f"  {x.get('date_created','')[:19]} | {who}->{to} | status={st} mod={mod} | {txt}")

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
