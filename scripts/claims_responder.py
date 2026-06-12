"""
Sistema auto-responder de reclamos multi-cuenta.

Flujo cada 10 min:
1. Por cada cuenta activa: GET /post-purchase/v1/claims/search?status=opened&player.role=respondent
2. Para cada claim nuevo o cambiado: pull full context (order, claim detail, reason, messages, shipping)
3. Claude AI analiza y produce: { risk_level, strategy, message }
4. Si risk_level=LOW y action != offer_refund/return → POST send-message
5. Si HIGH → solo Telegram con draft
6. Log everything a meli_claim_responses
7. Update meli_claims_tracked

Política de marca:
- SIEMPRE defender producto y empresa
- NUNCA aceptar reembolso o devolución autónomamente
- Tono profesional, no agresivo, no acusatorio
- Cierre fijo: "Saludos cordiales — Elite Market."
- Máx 1000 chars

Idempotencia: no responder a un claim si ya respondimos en las últimas 24h
(verifica meli_claim_responses).
"""
import os, requests, json, time, base64, sys
from datetime import datetime, timezone, timedelta

API = "https://api.mercadolibre.com"
SB  = os.environ["SUPABASE_URL"].rstrip("/")
SBK = os.environ["SUPABASE_SERVICE_KEY"]
SBH = {"apikey": SBK, "Authorization": f"Bearer {SBK}",
       "Content-Type": "application/json", "Prefer": "return=representation"}

CID = os.environ["MELI_APP_ID"]; CSEC = os.environ["MELI_APP_SECRET"]

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","").strip()
TG_BOT  = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

ACCOUNTS = [
  ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
  ("ASVA",     "MELI_REFRESH_TOKEN_ASVA"),
  ("MAYRELY",  "MELI_REFRESH_TOKEN_MAYRELY"),
  ("BREN",     "MELI_REFRESH_TOKEN_BREN"),
  ("JUAN",     "MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("WILBERT",  "MELI_REFRESH_TOKEN_WILBERT"),
  ("AH",       "MELI_REFRESH_TOKEN_AH"),
  ("YC_NEW",   "MELI_REFRESH_TOKEN"),
]

def tg(msg):
    if not TG_BOT or not TG_CHAT:
        print("[tg] no creds"); return
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
            data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},
            timeout=8)
        if r.status_code>=300: print(f"[tg ERR {r.status_code}]")
    except Exception as e:
        print("[tg err]", e)

def log_resp(**kw):
    try:
        requests.post(f"{SB}/rest/v1/meli_claim_responses", headers=SBH, json=kw, timeout=10)
    except Exception as e: print("[log err]", e)

def upsert_tracked(row):
    try:
        requests.post(f"{SB}/rest/v1/meli_claims_tracked",
            headers={**SBH, "Prefer": "return=representation,resolution=merge-duplicates"},
            json=row, timeout=10)
    except Exception as e: print("[upsert err]", e)

def get_recent_response(claim_id):
    """Avoid double-responding."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    q = requests.utils.quote(cutoff, safe='')
    try:
        r = requests.get(f"{SB}/rest/v1/meli_claim_responses?claim_id=eq.{claim_id}&ts=gte.{q}&action=eq.message_sent&select=ts",
                         headers=SBH, timeout=8)
        return r.json() if r.status_code==200 else []
    except: return []

def claude_decide(context):
    """Ask Claude to classify + draft."""
    if not ANTHROPIC_KEY:
        return None
    sys_prompt = (
      "Eres el agente de servicio al cliente de Elite Market, una tienda mexicana en Mercado Libre. "
      "Tu trabajo: redactar la respuesta al MEDIADOR o COMPRADOR en un reclamo MELI, "
      "siempre defendiendo a Elite Market y cuidando su imagen, reputación y dinero. "
      "REGLAS DURAS (no negociables): "
      "1) NUNCA ofrezcas reembolso ni etiqueta de devolución por iniciativa propia — eso lo decide el humano. "
      "2) Tono profesional, empático, NO agresivo, NO acusatorio del comprador. "
      "3) Argumentos técnicos sólidos, basados en el producto y su naturaleza. "
      "4) Cierre fijo: 'Saludos cordiales — Elite Market.' "
      "5) Máximo 900 caracteres. "
      "6) Si el caso es ALTO RIESGO (PNR claro con entrega disputada, daño físico documentado, comprador con evidencia visual sólida, "
      "mediator pide refund obligatorio, comprador agresivo o amenaza con bajar reputación), marca risk='HIGH' y NO inventes excusa débil. "
      "Devuelve JSON estrictamente con: "
      "{\"risk\":\"LOW\"|\"HIGH\", \"receiver\":\"mediator\"|\"complainant\", \"strategy\":\"...\", \"message\":\"...\"}"
    )
    user_prompt = (
      f"Contexto del reclamo:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
      "Devuelve solo el JSON, sin markdown, sin texto extra."
    )
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-5","max_tokens":1500,
                  "system":sys_prompt,
                  "messages":[{"role":"user","content":user_prompt}]},
            timeout=45)
        if r.status_code>=300:
            print(f"[claude ERR {r.status_code}] {r.text[:300]}")
            return None
        j = r.json()
        text = "".join(b.get("text","") for b in j.get("content",[]) if b.get("type")=="text")
        # Strip markdown if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"[claude exc] {e}")
        return None

def send_message(AT, claim_id, receiver, message, attachments=None):
    H = {"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    payload = {"receiver_role": receiver, "message": message, "attachments": attachments or []}
    r = requests.post(f"{API}/marketplace/v2/claims/{claim_id}/actions/send-message",
                      headers=H, json=payload, timeout=20)
    return r.status_code, r.text[:400]

def get_token(env_var):
    rt = os.environ.get(env_var)
    if not rt: return None, None
    for _ in range(4):
        try:
            r = requests.post(f"{API}/oauth/token",
                data={"grant_type":"refresh_token","client_id":CID,
                      "client_secret":CSEC,"refresh_token":rt},timeout=15)
            if r.status_code<500: break
            time.sleep(4)
        except: pass
    if r.status_code>=300:
        print(f"[oauth FAIL {env_var}] {r.status_code}")
        return None, None
    t = r.json()
    return t["access_token"], t["refresh_token"]

def build_context(AT, claim, account_nick):
    H = {"Authorization": f"Bearer {AT}"}
    cid = claim["id"]
    ctx = {"claim_id": cid, "account": account_nick,
           "stage": claim.get("stage"), "status": claim.get("status"),
           "reason_id": claim.get("reason_id"), "fulfilled": claim.get("fulfilled"),
           "type": claim.get("type"), "resource": claim.get("resource"),
           "resource_id": claim.get("resource_id"),
           "date_created": claim.get("date_created"),
           "available_actions_seller": []}
    # Available actions
    for p in claim.get("players",[]):
        if p.get("role")=="respondent":
            ctx["available_actions_seller"] = [a.get("action") for a in p.get("available_actions") or []]
    # Reason detail
    if ctx["reason_id"]:
        rs = requests.get(f"{API}/post-purchase/v1/claims/reasons/{ctx['reason_id']}", headers=H, timeout=12)
        if rs.status_code==200:
            rj = rs.json()
            ctx["reason_name"] = rj.get("name"); ctx["reason_detail"] = rj.get("detail")
    # Claim detail
    cd = requests.get(f"{API}/post-purchase/v1/claims/{cid}/detail", headers=H, timeout=12)
    if cd.status_code==200:
        dj = cd.json()
        ctx["detail_title"] = dj.get("title"); ctx["detail_problem"] = dj.get("problem")
        ctx["detail_description"] = dj.get("description")
        ctx["due_date"] = dj.get("due_date"); ctx["action_responsible"] = dj.get("action_responsible")
    # Affects reputation
    ar = requests.get(f"{API}/post-purchase/v1/claims/{cid}/affects-reputation", headers=H, timeout=12)
    if ar.status_code==200:
        arj = ar.json()
        ctx["affects_reputation"] = arj.get("affects_reputation"); ctx["has_incentive"] = arj.get("has_incentive")
    # Messages (last 5)
    msgs = requests.get(f"{API}/marketplace/v2/claims/{cid}/messages", headers=H, timeout=12)
    if msgs.status_code==200:
        ml = msgs.json()
        if isinstance(ml, dict): ml = ml.get("messages") or []
        ctx["messages"] = [{"from": m.get("sender_role"), "to": m.get("receiver_role"),
                            "date": m.get("date_created"),
                            "text": (m.get("message") or "")[:600]} for m in ml[:8]]
    # Order
    if ctx["resource"]=="order" and ctx["resource_id"]:
        o = requests.get(f"{API}/orders/{ctx['resource_id']}", headers=H, timeout=12)
        if o.status_code==200:
            od = o.json()
            items = od.get("order_items",[])
            ctx["product_title"] = items[0]["item"]["title"] if items else None
            ctx["product_id"] = items[0]["item"].get("id") if items else None
            ctx["total_amount"] = od.get("total_amount")
            ctx["buyer_user_id"] = (od.get("buyer") or {}).get("id")
            ctx["buyer_nick"] = (od.get("buyer") or {}).get("nickname")
            ship = od.get("shipping") or {}
            ctx["shipment_id"] = ship.get("id")
            if ship.get("id"):
                s = requests.get(f"{API}/shipments/{ship.get('id')}", headers=H, timeout=10)
                if s.status_code==200:
                    sd = s.json()
                    ctx["shipment_status"] = sd.get("status")
                    ctx["shipment_substatus"] = sd.get("substatus")
                    ctx["tracking"] = sd.get("tracking_number")
                    ctx["delivered_at"] = (sd.get("status_history") or {}).get("date_delivered")
    return ctx

def process_account(nick, env_var):
    AT, NEW_RT = get_token(env_var)
    if not AT:
        print(f"[{nick}] no token, skip"); return None
    H = {"Authorization": f"Bearer {AT}"}
    me = requests.get(f"{API}/users/me", headers=H, timeout=8).json()
    UID = me.get("id")
    if not UID:
        print(f"[{nick}] no UID"); return NEW_RT
    print(f"\n========== {nick} (seller={UID}) ==========")
    sr = requests.get(f"{API}/post-purchase/v1/claims/search",
        headers=H,
        params={"status":"opened", "player.role":"respondent", "player.user_id":UID, "limit":30},
        timeout=15)
    if sr.status_code>=300:
        print(f"[{nick}] claims_search ERR {sr.status_code}: {sr.text[:200]}")
        return NEW_RT
    data = sr.json().get("data",[])
    print(f"[{nick}] {len(data)} open claims")

    for claim in data:
        cid = claim.get("id")
        print(f"\n--- claim {cid} stage={claim.get('stage')} reason={claim.get('reason_id')} ---")
        # Idempotency
        if get_recent_response(cid):
            print(f"  [skip] already responded in last 24h"); continue

        ctx = build_context(AT, claim, nick)

        # Upsert tracked
        upsert_tracked({
          "claim_id": cid, "account_nick": nick, "seller_id": UID,
          "order_id": str(ctx.get("resource_id")) if ctx.get("resource")=="order" else None,
          "shipment_id": str(ctx.get("shipment_id")) if ctx.get("shipment_id") else None,
          "resource": ctx.get("resource"), "type": claim.get("type"),
          "stage": ctx.get("stage"), "status": ctx.get("status"),
          "reason_id": ctx.get("reason_id"), "reason_name": ctx.get("reason_name"),
          "reason_detail": ctx.get("reason_detail"),
          "date_created": claim.get("date_created"),
          "last_updated": claim.get("last_updated"),
          "due_date": ctx.get("due_date"),
          "action_responsible": ctx.get("action_responsible"),
          "affects_reputation": ctx.get("affects_reputation"),
          "has_incentive": ctx.get("has_incentive"),
          "fulfilled": claim.get("fulfilled"),
          "total_amount": ctx.get("total_amount"),
          "product_title": ctx.get("product_title"),
          "buyer_user_id": ctx.get("buyer_user_id"),
          "buyer_nick": ctx.get("buyer_nick"),
          "last_polled_at": datetime.now(timezone.utc).isoformat(),
        })

        if "send_message_to_mediator" not in ctx["available_actions_seller"] and \
           "send_message_to_complainant" not in ctx["available_actions_seller"]:
            print(f"  [skip] no send_message action available (actions={ctx['available_actions_seller']})")
            log_resp(claim_id=cid, account_nick=nick, action="skip_no_action",
                     notes=f"actions={ctx['available_actions_seller']}")
            continue

        decision = claude_decide(ctx)
        if not decision:
            tg(f"⚠️ <b>Reclamo nuevo SIN análisis IA</b>\nCuenta: {nick} · Claim: <code>{cid}</code>\n"
               f"Reason: {ctx.get('reason_id')} {ctx.get('reason_name')}\n"
               f"Producto: {ctx.get('product_title','?')[:80]}\n"
               f"<i>Falta ANTHROPIC_API_KEY o Claude no respondió. Revisa manual.</i>")
            log_resp(claim_id=cid, account_nick=nick, action="notify_no_ai",
                     telegram_notified=True, notes="claude unavailable")
            continue

        risk = (decision.get("risk") or "HIGH").upper()
        receiver = decision.get("receiver") or ("mediator" if ctx.get("stage")=="dispute" else "complainant")
        if receiver not in ("mediator","complainant"): receiver = "mediator"
        msg = (decision.get("message") or "").strip()
        if not msg:
            print("  [skip] empty message from AI"); continue
        if len(msg)>1000:
            msg = msg[:990] + "..."

        # Validate receiver vs available actions
        action_needed = f"send_message_to_{receiver}"
        if action_needed not in ctx["available_actions_seller"]:
            # try alternative
            alts = [a for a in ctx["available_actions_seller"] if a.startswith("send_message_to_")]
            if alts:
                receiver = alts[0].replace("send_message_to_","")
                print(f"  [switch receiver] -> {receiver}")
            else:
                print(f"  [skip] no valid send action"); continue

        if risk == "LOW":
            code, body = send_message(AT, cid, receiver, msg)
            ok = code < 300
            log_resp(claim_id=cid, account_nick=nick, risk_level="LOW",
                     action="message_sent" if ok else "message_failed",
                     receiver_role=receiver, message_text=msg,
                     reason_strategy=decision.get("strategy"),
                     ai_provider="anthropic", ai_model="claude-sonnet-4-5",
                     meli_http_code=code, meli_response=body, telegram_notified=True)
            if ok:
                tg(f"✅ <b>Auto-respuesta enviada (LOW risk)</b>\n"
                   f"Cuenta: <b>{nick}</b> · Claim: <code>{cid}</code> · Reason: {ctx.get('reason_id')}\n"
                   f"Producto: {(ctx.get('product_title') or '?')[:70]}\n"
                   f"Receiver: {receiver}\n"
                   f"Estrategia: <i>{(decision.get('strategy') or '')[:120]}</i>\n"
                   f"Mensaje ({len(msg)} chars):\n<pre>{msg[:600]}</pre>")
            else:
                tg(f"⚠️ <b>FALLÓ envío (LOW risk)</b>\nCuenta: {nick} · Claim: <code>{cid}</code>\n"
                   f"HTTP {code}: {body[:200]}")
        else:  # HIGH
            log_resp(claim_id=cid, account_nick=nick, risk_level="HIGH",
                     action="notify_high_risk", receiver_role=receiver,
                     message_text=msg, reason_strategy=decision.get("strategy"),
                     ai_provider="anthropic", ai_model="claude-sonnet-4-5",
                     telegram_notified=True, notes="awaiting human approval")
            tg(f"🚨 <b>HIGH RISK — REVISA ANTES DE ENVIAR</b>\n"
               f"Cuenta: <b>{nick}</b> · Claim: <code>{cid}</code> · Reason: {ctx.get('reason_id')}\n"
               f"Producto: {(ctx.get('product_title') or '?')[:80]} (${ctx.get('total_amount')})\n"
               f"Comprador: {ctx.get('buyer_nick')}\n"
               f"Due: {ctx.get('due_date')}\n"
               f"Afecta reputación: {ctx.get('affects_reputation')}\n"
               f"Estrategia AI: <i>{(decision.get('strategy') or '')[:200]}</i>\n"
               f"Mensaje propuesto ({len(msg)} chars):\n<pre>{msg[:700]}</pre>\n"
               f"<i>Para enviar: dispara workflow send_mediator_msg con CLAIM_ID={cid}</i>")
    return NEW_RT

def main():
    rotated = {}
    for nick, env in ACCOUNTS:
        try:
            new_rt = process_account(nick, env)
            if new_rt: rotated[env] = new_rt; os.environ[env] = new_rt
        except Exception as e:
            print(f"[{nick}] EXC {e}")
            tg(f"⚠️ Excepción procesando {nick}: {str(e)[:200]}")
    if rotated:
        print(f"\nFINAL_ROTATED_TOKENS={json.dumps(rotated)}")

if __name__=="__main__":
    main()
