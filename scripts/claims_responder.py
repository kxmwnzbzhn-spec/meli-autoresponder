"""
Sistema auto-responder de reclamos multi-cuenta v2.

Política NUEVA (cambio crítico vs v1):
- SIEMPRE solicitar DEVOLUCIÓN antes de procesar reembolso (cliente NO se queda con producto + dinero)
- Mensaje firme al mediator/complainant insistiendo en devolución previa
- NUNCA aceptar reembolso sin retorno físico del producto
- Cierre fijo: "Saludos cordiales — Elite Market."

Flujo cada 30 min:
1. Por cada cuenta activa: GET /post-purchase/v1/claims/search?status=opened&player.role=respondent
2. Para cada claim: pull contexto + reason + amount
3. Plantilla según reason_id (no LLM para reducir latencia y errores)
4. POST /marketplace/v2/claims/{id}/actions/send-message
5. Log a meli_claim_responses + Telegram alert
6. Idempotencia: no responder mismo claim en <24h

Endpoint confirmado funcional: POST /marketplace/v2/claims/{claim_id}/actions/send-message
Body: {"receiver_role":"mediator|complainant","message":"...","attachments":[]}
"""
import os, requests, json, time
from datetime import datetime, timezone, timedelta

API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
SB=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}
TG_BOT=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

ACCOUNTS=[
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
  ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
  ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
]

TEMPLATES={
  "not_working_item":(
    "Hola, mediador. Lamentamos el inconveniente reportado. El producto fue probado y empaquetado en óptimas "
    "condiciones antes del envío. Solicitamos al comprador que realice la devolución del producto a través del "
    "proceso oficial de MercadoLibre. Una vez recibido el producto en nuestras instalaciones y validado el estado "
    "reportado, procesaremos el reembolso correspondiente sin demoras. Esta es nuestra política estándar para "
    "reclamos por defecto de funcionamiento. Saludos cordiales — Elite Market."
  ),
  "broken_item":(
    "Hola, mediador. El producto fue empacado con material de protección adecuado antes del envío. Solicitamos que "
    "el comprador realice la devolución para inspeccionar el daño reportado y confirmar si corresponde a transporte "
    "o uso. Una vez recibido el producto y validado el estado, procesaremos el reembolso completo. "
    "Saludos cordiales — Elite Market."
  ),
  "damaged_package_broken_item":(
    "Hola. Lamentamos lo ocurrido. Para procesar el reembolso necesitamos que el producto sea devuelto mediante el "
    "proceso de devolución de MercadoLibre. Una vez recibido y revisado en nuestras instalaciones, procesaremos el "
    "reembolso. Saludos cordiales — Elite Market."
  ),
  "damaged_package_not_working_item":(
    "Hola. Lamentamos el inconveniente. Solicitamos la devolución del producto mediante el proceso oficial de "
    "MercadoLibre. Una vez recibido y verificado el estado reportado, procesaremos el reembolso. "
    "Saludos cordiales — Elite Market."
  ),
  "repentant_buyer":(
    "Hola, mediador. El producto entregado coincide exactamente con la descripción, fotografías, modelo y "
    "características publicadas; no existe defecto ni discrepancia con la publicación. Como política aceptamos "
    "devolución por arrepentimiento siempre que el producto regrese en condiciones de venta nueva (caja original "
    "sellada, sin uso, con accesorios completos). Una vez recibido y verificado, procesamos el reembolso. "
    "Saludos cordiales — Elite Market."
  ),
  "different_color_or_size":(
    "Hola, mediador. El producto entregado corresponde al modelo, color y características publicadas en el "
    "anuncio. Solicitamos al comprador realizar devolución para verificación. Una vez recibido y confirmada la "
    "coincidencia con lo descrito, procesaremos el reembolso correspondiente. Saludos cordiales — Elite Market."
  ),
  "fake_different":(
    "Hola, mediador. Garantizamos que el producto entregado es original y proviene de proveedor autorizado. "
    "Solicitamos al comprador realizar devolución para inspección. Si confirmamos irregularidad procederemos con "
    "reembolso total. Caso contrario regresaremos el producto al comprador. Saludos cordiales — Elite Market."
  ),
  "default":(
    "Hola, mediador. Solicitamos al comprador realizar la devolución del producto a través del proceso oficial de "
    "MercadoLibre. Una vez recibido en nuestras instalaciones y validado el estado, procesaremos el reembolso "
    "correspondiente. Saludos cordiales — Elite Market."
  )
}

def tg(msg):
  if not TG_BOT or not TG_CHAT: return
  try:
    requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
      data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},timeout=8)
  except: pass

def log_resp(**kw):
  try:
    requests.post(f"{SB}/rest/v1/meli_claim_responses",headers=SBH,json=kw,timeout=10)
  except Exception as e: print(f"[log err] {e}")

def upsert_tracked(row):
  try:
    requests.post(f"{SB}/rest/v1/meli_claims_tracked",
      headers={**SBH,"Prefer":"return=minimal,resolution=merge-duplicates"},json=row,timeout=10)
  except Exception as e: print(f"[tracked err] {e}")

def get_token(env_key):
  rt=os.environ.get(env_key)
  if not rt: return None
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  return r.json()["access_token"] if r.status_code<400 else None

def already_responded_24h(claim_id):
  cutoff=(datetime.now(timezone.utc)-timedelta(hours=24)).isoformat()
  q=requests.utils.quote(cutoff,safe='')
  try:
    r=requests.get(f"{SB}/rest/v1/meli_claim_responses?claim_id=eq.{claim_id}&ts=gte.{q}&action=eq.message_sent&select=ts",headers=SBH,timeout=8)
    return r.status_code==200 and len(r.json())>0
  except: return False

def send_message(AT, claim_id, receiver_role, message):
  H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  payload={"receiver_role":receiver_role,"message":message,"attachments":[]}
  r=requests.post(f"{API}/marketplace/v2/claims/{claim_id}/actions/send-message",headers=H,json=payload,timeout=25)
  return r.status_code, r.text[:500]

def main():
  total_responded=0; total_skipped=0; total_failed=0
  for acct,key in ACCOUNTS:
    AT=get_token(key)
    if not AT:
      print(f"[{acct}] no token, skip"); continue
    H={"Authorization":f"Bearer {AT}"}
    sr=requests.get(f"{API}/post-purchase/v1/claims/search?status=opened&player.role=respondent&limit=50",headers=H,timeout=20)
    if sr.status_code!=200:
      print(f"[{acct}] search HTTP {sr.status_code}"); continue
    claims=sr.json().get("data") or sr.json().get("results") or []
    if not claims: print(f"[{acct}] 0 opened"); continue
    print(f"[{acct}] {len(claims)} opened claims")
    
    for c in claims:
      cid=c["id"]
      
      # Get full claim
      cr=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15)
      if cr.status_code!=200: continue
      full=cr.json()
      stage=full.get("stage")
      reason_id=full.get("reason_id")
      
      # Available seller actions
      actions=[]
      for p in full.get("players",[]):
        if p.get("role")=="respondent":
          actions=[a.get("action") if isinstance(a,dict) else a for a in (p.get("available_actions") or [])]
          break
      
      # Get reason name
      reason_name=None
      try:
        rs=requests.get(f"{API}/post-purchase/v1/claims/reasons/{reason_id}",headers=H,timeout=10)
        if rs.status_code==200: reason_name=rs.json().get("name") or rs.json().get("id")
      except: pass
      
      # Decide receiver
      receiver=None
      if "send_message_to_mediator" in actions: receiver="mediator"
      elif "send_message_to_complainant" in actions: receiver="complainant"
      
      if not receiver:
        print(f"  [{cid}] no message action available (actions={actions})")
        log_resp(claim_id=cid,account_nick=acct,action="skip_no_action",notes=f"actions={actions}",meli_http_code=0)
        total_skipped+=1; continue
      
      # Idempotencia
      if already_responded_24h(cid):
        print(f"  [{cid}] already responded <24h, skip"); total_skipped+=1; continue
      
      # Pick template
      key_lookup=(reason_name or "").lower().replace(" ","_")
      msg=TEMPLATES.get(key_lookup, TEMPLATES["default"])
      
      # SEND
      code,body=send_message(AT,cid,receiver,msg)
      ok=200<=code<300
      status_icon="✅" if ok else "❌"
      print(f"  [{cid}] {status_icon} HTTP {code} → {receiver} ({reason_name}) {body[:200]}")
      
      # Log
      log_resp(claim_id=cid,account_nick=acct,
               action="message_sent" if ok else "send_failed",
               receiver_role=receiver, message_text=msg[:1000],
               reason_strategy=f"{reason_name}/request_return",
               meli_http_code=code, meli_response=body[:500],
               notes="auto-respond v2 / always request return before refund")
      
      # Tracked update
      upsert_tracked({"claim_id":cid,"account_nick":acct,"status":"opened",
                      "stage":stage,"reason_id":reason_id,"reason_name":reason_name,
                      "action_responsible":"respondent",
                      "last_polled_at":datetime.now(timezone.utc).isoformat()})
      
      if ok: total_responded+=1
      else: total_failed+=1; tg(f"❌ Claims bot FAIL {acct} {cid}: HTTP {code}")
      
      time.sleep(0.5)  # rate limit
  
  print(f"\n=== DONE === responded={total_responded} skipped={total_skipped} failed={total_failed}")
  tg(f"🤖 Claims bot v2: ✅{total_responded} ⏭{total_skipped} ❌{total_failed}")

if __name__=="__main__":
  main()
