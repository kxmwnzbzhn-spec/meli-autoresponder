"""
Bot de reclamos v4:
- POLÍTICA AÑADIDA: si el reclamo es >30 días después de la entrega → declinar por compra protegida expirada
- Sigue: SIN FIRMA, aceptar devolución en reclamos dentro de 30 días
- Poll TODAS las cuentas, cron */30 min
- Endpoint: POST /marketplace/v2/claims/{id}/actions/send-message
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

# Sin firma. Termina con "Quedamos atentos."
TEMPLATES_ACCEPT={
  "not_working_item":(
    "Hola, lamentamos el inconveniente. Aceptamos la devolución del producto. Por favor inicia el proceso desde "
    "la sección Mis Compras en MercadoLibre. Una vez que recibamos el producto en nuestras instalaciones "
    "procesaremos el reembolso correspondiente. Quedamos atentos."),
  "broken_item":(
    "Hola, lamentamos el daño reportado. Aceptamos la devolución. Por favor inicia el proceso de devolución "
    "desde Mis Compras en MercadoLibre. Una vez recibido el producto procesaremos el reembolso completo. "
    "Quedamos atentos."),
  "damaged_package_broken_item":(
    "Hola, lamentamos el daño en empaque y producto. Aceptamos la devolución. Por favor inicia el proceso "
    "desde Mis Compras en MercadoLibre. Al recibir el producto procesaremos el reembolso. Quedamos atentos."),
  "damaged_package_not_working_item":(
    "Hola, lamentamos el inconveniente. Aceptamos la devolución. Por favor inicia el proceso desde Mis Compras "
    "en MercadoLibre. Una vez recibido procesaremos el reembolso. Quedamos atentos."),
  "repentant_buyer":(
    "Hola, aceptamos la devolución. Por favor inicia el proceso desde Mis Compras en MercadoLibre. Solicitamos "
    "que el producto regrese en condiciones de venta nueva (caja original sellada, sin uso, con accesorios "
    "completos). Una vez recibido y verificado procesamos el reembolso. Quedamos atentos."),
  "different_color_or_size":(
    "Hola, aceptamos la devolución. Por favor inicia el proceso desde Mis Compras en MercadoLibre. Una vez "
    "recibido el producto procesaremos el reembolso correspondiente. Quedamos atentos."),
  "fake_different":(
    "Hola, garantizamos que el producto proviene de proveedor autorizado. Aceptamos la devolución para "
    "inspección. Por favor inicia el proceso desde Mis Compras en MercadoLibre. Al recibirlo procederemos "
    "con el reembolso o regresaremos el producto según corresponda. Quedamos atentos."),
  "different_item_other":(
    "Hola, lamentamos el inconveniente. Aceptamos la devolución. Por favor inicia el proceso desde Mis Compras "
    "en MercadoLibre. Al recibir el producto procesaremos el reembolso. Quedamos atentos."),
  "default":(
    "Hola, aceptamos la devolución del producto. Por favor inicia el proceso de devolución desde la sección "
    "Mis Compras en MercadoLibre. Una vez recibido el producto procesaremos el reembolso correspondiente. "
    "Quedamos atentos.")
}

# Plantilla para >30 días post-entrega (Compra Protegida expirada)
TEMPLATE_EXPIRED_30D=(
  "Hola, lamentamos el inconveniente. Sin embargo, la garantía de Compra Protegida de MercadoLibre tiene una "
  "vigencia de 30 días posteriores a la entrega del producto, y este plazo ya expiró en tu compra. Por esta "
  "razón no nos es posible aceptar la devolución ni procesar reembolso a través de esta vía. Quedamos atentos."
)

def tg(msg):
  if not TG_BOT or not TG_CHAT: return
  try:
    requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
      data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},timeout=8)
  except: pass

def log_resp(**kw):
  try: requests.post(f"{SB}/rest/v1/meli_claim_responses",headers=SBH,json=kw,timeout=10)
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

def get_delivered_date(AT, order_id):
  """Devuelve datetime o None"""
  if not order_id: return None
  H={"Authorization":f"Bearer {AT}"}
  try:
    r=requests.get(f"{API}/orders/{order_id}",headers=H,timeout=12)
    if r.status_code!=200: return None
    o=r.json()
    sid=o.get("shipping",{}).get("id")
    if not sid: return None
    # Get shipment
    s=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=12)
    if s.status_code!=200: return None
    sj=s.json()
    # Probe multiple delivery date fields
    candidates=[]
    if sj.get("status_history",{}).get("date_delivered"): candidates.append(sj["status_history"]["date_delivered"])
    if sj.get("date_delivered"): candidates.append(sj["date_delivered"])
    if sj.get("date_first_visit"): candidates.append(sj["date_first_visit"])
    sh=sj.get("status_history",{})
    if isinstance(sh,dict):
      for k,v in sh.items():
        if "deliv" in k.lower() and v: candidates.append(v)
    for d in candidates:
      try:
        if "Z" in d: d=d.replace("Z","+00:00")
        return datetime.fromisoformat(d)
      except: continue
    return None
  except Exception as e:
    print(f"  [delivery date err] {e}")
    return None

def main():
  total_responded=0; total_skipped=0; total_failed=0; total_expired=0
  now=datetime.now(timezone.utc)
  
  for acct,key in ACCOUNTS:
    AT=get_token(key)
    if not AT: print(f"[{acct}] no token"); continue
    H={"Authorization":f"Bearer {AT}"}
    sr=requests.get(f"{API}/post-purchase/v1/claims/search?status=opened&player.role=respondent&limit=50",headers=H,timeout=20)
    if sr.status_code!=200: print(f"[{acct}] search HTTP {sr.status_code}"); continue
    claims=sr.json().get("data") or sr.json().get("results") or []
    if not claims: print(f"[{acct}] 0 opened"); continue
    print(f"[{acct}] {len(claims)} opened claims")
    
    for c in claims:
      cid=c["id"]
      cr=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15)
      if cr.status_code!=200: continue
      full=cr.json()
      stage=full.get("stage"); reason_id=full.get("reason_id")
      order_id=full.get("resource_id") if full.get("resource")=="order" else None
      
      actions=[]
      for p in full.get("players",[]):
        if p.get("role")=="respondent":
          actions=[a.get("action") if isinstance(a,dict) else a for a in (p.get("available_actions") or [])]
          break
      
      receiver=None
      if "send_message_to_mediator" in actions: receiver="mediator"
      elif "send_message_to_complainant" in actions: receiver="complainant"
      
      if not receiver:
        log_resp(claim_id=cid,account_nick=acct,action="skip_no_action",notes=f"actions={actions}",meli_http_code=0)
        total_skipped+=1; continue
      
      if already_responded_24h(cid):
        print(f"  [{cid}] already responded <24h"); total_skipped+=1; continue
      
      # Get reason name
      reason_name=None
      try:
        rs=requests.get(f"{API}/post-purchase/v1/claims/reasons/{reason_id}",headers=H,timeout=10)
        if rs.status_code==200: reason_name=rs.json().get("name") or rs.json().get("id")
      except: pass
      
      # === REGLA 30 DÍAS POST-ENTREGA ===
      delivered=get_delivered_date(AT, order_id)
      use_expired_template=False
      days_since_delivery=None
      if delivered:
        days_since_delivery=(now-delivered).days
        if days_since_delivery>30:
          use_expired_template=True
      
      if use_expired_template:
        msg=TEMPLATE_EXPIRED_30D
        strategy=f"{reason_name}/decline_compra_protegida_expired_{days_since_delivery}d"
        total_expired+=1
      else:
        key_lookup=(reason_name or "").lower().replace(" ","_")
        msg=TEMPLATES_ACCEPT.get(key_lookup, TEMPLATES_ACCEPT["default"])
        strategy=f"{reason_name}/accept_return"
      
      code,body=send_message(AT,cid,receiver,msg)
      ok=200<=code<300
      icon="✅" if ok else "❌"
      tag="EXPIRED_30D" if use_expired_template else "accept"
      ddays=f"{days_since_delivery}d" if days_since_delivery is not None else "?"
      print(f"  [{cid}] {icon} HTTP {code} → {receiver} ({reason_name}) [{tag}, entregado hace {ddays}]")
      
      log_resp(claim_id=cid,account_nick=acct,
               action="message_sent" if ok else "send_failed",
               receiver_role=receiver, message_text=msg[:1000],
               reason_strategy=strategy,
               meli_http_code=code, meli_response=body[:500],
               notes=f"bot v4 / delivered={delivered.isoformat() if delivered else 'unknown'} / days={days_since_delivery}")
      
      upsert_tracked({"claim_id":cid,"account_nick":acct,"status":"opened",
                      "stage":stage,"reason_id":reason_id,"reason_name":reason_name,
                      "action_responsible":"respondent",
                      "last_polled_at":now.isoformat()})
      
      if ok: total_responded+=1
      else: total_failed+=1
      time.sleep(0.4)
  
  print(f"\n=== DONE === responded={total_responded} (expired_30d={total_expired}, accept={total_responded-total_expired}) skipped={total_skipped} failed={total_failed}")
  tg(f"🤖 Claims bot v4: ✅{total_responded} (expirados {total_expired}) ⏭{total_skipped} ❌{total_failed}")

if __name__=="__main__": main()
