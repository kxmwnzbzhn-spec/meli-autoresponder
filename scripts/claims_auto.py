"""
Auto-claims bot.

- Read v_returns_admin where status=pending AND escalated_to_meli_at IS NULL AND created_at >= now - 5min
- Map condition -> SRF code
- Find claim+return for the order
- Upload evidence to claim
- POST return-review with SRF
- Update v_returns_admin and meli_claim_auto_log
- Telegram notification
"""
import os, requests, json, sys, time
from datetime import datetime, timezone, timedelta

SB=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
TG_BOT=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

API="https://api.mercadolibre.com"

# Account nick -> env var name for refresh token
ACC_TO_RT = {
  "Wilbert":   "MELI_REFRESH_TOKEN_WILBERT",
  "Claribel":  "MELI_REFRESH_TOKEN_CLARIBEL",
  "Asva":      "MELI_REFRESH_TOKEN_ASVA",
  "ASVA":      "MELI_REFRESH_TOKEN_ASVA",
  "Bren":      "MELI_REFRESH_TOKEN_BREN",
  "BREN":      "MELI_REFRESH_TOKEN_BREN",
  "Juan":      "MELI_REFRESH_TOKEN_JUAN",
  "JUAN":      "MELI_REFRESH_TOKEN_JUAN",
  "Raymundo":  "MELI_REFRESH_TOKEN_RAYMUNDO",
  "Dilcie":    "MELI_REFRESH_TOKEN_DILCIE",
  "Mildred":   "MELI_REFRESH_TOKEN_MILDRED",
  "Mayrely":   "MELI_REFRESH_TOKEN_MAYRELY",
  "Adrian":    "MELI_REFRESH_TOKEN_AH",
  "AH":        "MELI_REFRESH_TOKEN_AH",
  "Angel":     "MELI_REFRESH_TOKEN_ANGEL",
  "YC_NEW":    "MELI_REFRESH_TOKEN",
  "Yiriam":    "MELI_REFRESH_TOKEN",
  "Sonix":     "MELI_REFRESH_TOKEN",
}

# Condition -> SRF
CONDITION_MAP = {
  "robado":    "SRF5",   # paquete vacío / tamperado
  "diferente": "SRF4",   # devolvieron otro producto
  "faltantes": "SRF5",   # falta producto
  "dañado":    "SRF2",
  "danado":    "SRF2",
}
CONDITION_LABEL = {
  "robado":    "📦 PAQUETE VACÍO/ROBADO",
  "diferente": "🔄 PRODUCTO DIFERENTE",
  "faltantes": "⚠️ FALTANTES",
  "dañado":    "💥 PRODUCTO DAÑADO",
  "danado":    "💥 PRODUCTO DAÑADO",
}

def tg(msg):
  if not TG_BOT or not TG_CHAT:
    print("[tg] no creds, skip:", msg[:80]); return
  try:
    requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
      data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},timeout=8)
  except Exception as e:
    print("[tg err]",e)

def log_audit(**kw):
  try:
    requests.post(f"{SB}/rest/v1/meli_claim_auto_log",headers=SBH,json=kw,timeout=10)
  except Exception as e:
    print("[audit err]",e)

def get_token(nick):
  envname=ACC_TO_RT.get(nick) or ACC_TO_RT.get((nick or "").upper())
  if not envname:
    return None,None
  rt=os.environ.get(envname)
  if not rt: return None,None
  for a in range(4):
    try:
      r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
      if r.status_code<500: break
      time.sleep(4)
    except: pass
  if r.status_code>=300:
    print(f"[oauth FAIL {nick}] {r.status_code} {r.text[:160]}"); return None,None
  tok=r.json()
  return tok["access_token"], tok["refresh_token"]

def find_claim_and_return(order_id, AT):
  """Return (claim_id, return_id) or (None, None)"""
  H={"Authorization":f"Bearer {AT}"}
  # 1) search claims by resource=order
  try:
    r=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,
      params={"resource":"order","resource_id":order_id,"limit":10},timeout=15)
    if r.status_code==200:
      data=r.json().get("data",[])
      for c in data:
        cid=c.get("id")
        # related entities may include return
        related=c.get("related_entities",[]) or []
        rid=None
        for re in related:
          if (re.get("type") or "").lower()=="return":
            rid=re.get("id"); break
        if not rid:
          # fetch detail
          rd=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15)
          if rd.status_code==200:
            for re in (rd.json().get("related_entities") or []):
              if (re.get("type") or "").lower()=="return":
                rid=re.get("id"); break
        if rid:
          return cid, rid
      if data:
        return data[0].get("id"), None
  except Exception as e:
    print(f"[search claims err] {e}")
  return None,None

def upload_evidence(claim_id, evidence_urls, AT):
  if not evidence_urls or not claim_id: return 0
  H={"Authorization":f"Bearer {AT}"}
  uploaded=0
  for url in evidence_urls[:6]:
    try:
      img=requests.get(url,timeout=20).content
      files={'file':('evidence.jpg', img,'image/jpeg')}
      r=requests.post(f"{API}/post-purchase/v1/claims/{claim_id}/evidences",
        headers=H,files=files,timeout=25)
      if r.status_code<300:
        uploaded+=1
      else:
        print(f"  [evid {r.status_code}] {r.text[:200]}")
    except Exception as e:
      print(f"  [evid err] {e}")
  return uploaded

def return_review_fail(return_id, srf, AT):
  H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  payload={"outcome":"fail","reason":srf}
  r=requests.post(f"{API}/post-purchase/v1/returns/{return_id}/return-review",
    headers=H,json=payload,timeout=20)
  return r.status_code, r.text[:400]

def process_row(row):
  rid=row["id"]; cond=(row.get("condition") or "").lower().strip()
  nick=row.get("account_nick") or ""
  oid=row.get("order_id"); ship=row.get("shipment_id"); pack=row.get("pack_id")
  evurls=row.get("evidence_urls") or []
  notes=row.get("notes") or ""

  emoji=CONDITION_LABEL.get(cond,"❓")

  # SAFETY: skip if not in our actionable conditions
  if cond not in CONDITION_MAP:
    print(f"  [skip] cond={cond} not actionable")
    log_audit(return_row_id=rid,account_nick=nick,order_id=oid,shipment_id=ship,pack_id=pack,
              condition=cond,action="skip_not_actionable",notes=f"cond={cond}")
    return False

  if len(evurls)<2:
    print(f"  [skip] only {len(evurls)} evidences, need >=2")
    log_audit(return_row_id=rid,account_nick=nick,order_id=oid,shipment_id=ship,pack_id=pack,
              condition=cond,action="skip_no_evidence",notes=f"evidences={len(evurls)}")
    return False

  srf=CONDITION_MAP[cond]

  AT,new_rt=get_token(nick)
  if not AT:
    print(f"  [skip] no token for {nick}")
    log_audit(return_row_id=rid,account_nick=nick,order_id=oid,shipment_id=ship,pack_id=pack,
              condition=cond,action="skip_no_token",srf_code=srf,notes=f"nick={nick}")
    tg(f"⚠️ <b>NO TOKEN para {nick}</b> — row {rid}\nCondición: {emoji}\nOrden: {oid}\nRevisa el GH secret MELI_REFRESH_TOKEN_{nick.upper()}")
    return False

  # save rotated rt back to env for next iteration
  envname=ACC_TO_RT.get(nick) or ACC_TO_RT.get((nick or "").upper())
  if envname and new_rt:
    os.environ[envname]=new_rt

  cid, rret = find_claim_and_return(oid, AT)
  if not cid:
    print(f"  [no claim found] order={oid}")
    log_audit(return_row_id=rid,account_nick=nick,order_id=oid,shipment_id=ship,pack_id=pack,
              condition=cond,action="skip_no_claim",srf_code=srf,notes="no_claim_found")
    tg(f"❓ <b>Reclamo no encontrado en MELI</b>\nCuenta: {nick} · Orden: {oid}\nCondición: {emoji}\nFotos: {len(evurls)} · Notas: {notes[:80]}\n<i>Posible: el comprador aún no abrió devolución. Reintento en 2 min.</i>")
    return False

  # Upload evidence (best-effort)
  up=0
  try:
    up=upload_evidence(cid, evurls, AT)
  except Exception as e:
    print(f"  [evid raise] {e}")

  if not rret:
    print(f"  [claim sin return aún] cid={cid}")
    log_audit(return_row_id=rid,account_nick=nick,order_id=oid,shipment_id=ship,pack_id=pack,
              condition=cond,action="evidence_only",srf_code=srf,claim_id=cid,
              notes=f"evidences_uploaded={up} (no return yet)")
    tg(f"📎 <b>{up} evidencias subidas</b> al claim {cid}\nCuenta: {nick} · Orden: {oid}\nCondición: {emoji}\n<i>Aún no hay return_id, no se hizo review_fail. Reintento en 2 min.</i>")
    return False

  # POST return-review fail
  code,body=return_review_fail(rret, srf, AT)
  ok = code<300
  print(f"  [review_fail] HTTP {code}: {body[:200]}")

  log_audit(return_row_id=rid,account_nick=nick,order_id=oid,shipment_id=ship,pack_id=pack,
            condition=cond,action="review_fail",srf_code=srf,claim_id=cid,return_id=rret,
            meli_http_code=code,meli_response=body[:400],
            notes=f"evidences_uploaded={up} ok={ok}")

  if ok:
    # Update v_returns_admin via underlying table 'returns'
    try:
      now_iso=datetime.now(timezone.utc).isoformat()
      requests.patch(f"{SB}/rest/v1/returns?id=eq.{rid}",headers=SBH,
        json={"escalated_to_meli_at":now_iso,"escalated_claim_id":cid,"status":"escalated"},timeout=10)
    except Exception as e:
      print(f"  [patch err] {e}")
    tg(f"✅ <b>RECLAMO MELI INICIADO ({srf})</b>\n"
       f"Cuenta: <b>{nick}</b>\n"
       f"Orden: <code>{oid}</code>\n"
       f"Condición: {emoji}\n"
       f"Claim ID: <code>{cid}</code> · Return ID: <code>{rret}</code>\n"
       f"Evidencias subidas: {up}/{len(evurls)}\n"
       f"Notas: {notes[:120]}\n"
       f"<i>MELI revisará en mediación.</i>")
  else:
    tg(f"⚠️ <b>review-fail FALLÓ ({srf})</b>\n"
       f"Cuenta: <b>{nick}</b> · Orden: <code>{oid}</code> · Claim: <code>{cid}</code>\n"
       f"HTTP {code}: {body[:200]}\n"
       f"<i>Row: {rid}</i>")
  return ok

def main():
  cutoff=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
  url=f"{SB}/rest/v1/v_returns_admin?status=eq.pending&escalated_to_meli_at=is.null&created_at=lte.{cutoff}&select=*&order=created_at.asc&limit=50"
  r=requests.get(url,headers=SBH,timeout=15)
  if r.status_code>=300:
    print(f"[supabase ERR] {r.status_code} {r.text[:300]}"); sys.exit(1)
  rows=r.json()
  print(f"=== {len(rows)} pending rows ===")
  fired=0; skipped=0
  for row in rows:
    print(f"\n→ row {row['id'][:8]} | cond={row.get('condition')} | nick={row.get('account_nick')} | order={row.get('order_id')}")
    try:
      if process_row(row): fired+=1
      else: skipped+=1
    except Exception as e:
      print(f"  [process raise] {e}")
      log_audit(return_row_id=row['id'],account_nick=row.get('account_nick'),
                order_id=row.get('order_id'),condition=row.get('condition'),
                action="exception",notes=str(e)[:200])
  print(f"\n=== END fired={fired} skipped={skipped} ===")

if __name__=="__main__":
  main()
