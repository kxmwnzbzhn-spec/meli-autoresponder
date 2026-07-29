"""
Auto-responder de preguntas pre-venta multi-cuenta con Claude AI.
- Cada 2 min: por cuenta, GET /my/received_questions/search?status=UNANSWERED
- Para cada pregunta: Claude analiza producto+pregunta → respuesta defendiendo Elite Market
- POST /answers (funciona aún si item está paused)
- Log en meli_questions_answered + Telegram alerts en HIGH risk
"""
import os, requests, json, time, base64
from datetime import datetime, timezone, timedelta

API="https://api.mercadolibre.com"
SB=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
ANTHROPIC_KEY=os.environ.get("ANTHROPIC_API_KEY","").strip()
TG_BOT=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

ACCOUNTS=[
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  # ("MAYRELY","MELI_REFRESH_TOKEN_MAYRELY"),  # DEACTIVATED 2026-07-28 (user pidió solo ASVA)
  # ("YERALDIN","MELI_REFRESH_TOKEN_YERALDIN"),  # DEACTIVATED 2026-07-28 (user pidió solo ASVA)
  # ("LUPITA","MELI_REFRESH_TOKEN_LUPITA"),  # DEACTIVATED 2026-07-28 (user pidió solo ASVA)
]

def tg(msg):
    if not TG_BOT or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
          data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},timeout=8)
    except: pass

def log_ans(**kw):
    try:
        requests.post(f"{SB}/rest/v1/meli_questions_answered",headers=SBH,json=kw,timeout=10)
    except Exception as e: print(f"[log] {e}")

def get_token(env_var):
    rt=os.environ.get(env_var)
    if not rt: return None, None
    for _ in range(4):
        try:
            r=requests.post(f"{API}/oauth/token",
              data={"grant_type":"refresh_token","client_id":CID,
                    "client_secret":CSEC,"refresh_token":rt},timeout=15)
            if r.status_code<500: break
            time.sleep(3)
        except: pass
    if r.status_code>=300: return None, None
    t=r.json(); return t["access_token"], t["refresh_token"]

def claude_answer(context):
    if not ANTHROPIC_KEY: return None
    sys_prompt = (
      "Eres el agente de servicio al cliente de Elite Market, tienda mexicana en Mercado Libre. "
      "Tu trabajo: redactar la respuesta a una PREGUNTA pre-venta de un cliente potencial. "
      "REGLAS DURAS (no negociables): "
      "1) Tono PROFESIONAL, AMABLE Y CERCANO — no robótico. La pregunta es pre-venta, queremos convertir. "
      "2) Respuesta CONCRETA al punto preguntado. Si preguntan si es original, dices que SÍ es 100% original con garantía. "
      "3) Si preguntan si está disponible, color, talla, número de serie, factura, garantía — confirma SÍ a lo que apliquen. "
      "4) Si preguntan algo técnico que requiere especificaciones, da el dato técnico relevante del producto. "
      "5) Si preguntan algo que parezca inducir a un descuento o pelear precio, responde amablemente que el precio publicado es el mejor que tenemos. "
      "6) NUNCA aceptes que el producto es 'inspirado' / 'imitación' / 'genérico' si no lo dice el listing explícitamente. Confirma originalidad SIEMPRE para productos de marca registrada. "
      "7) Si el producto en el listing es claramente artesanal/dupe/inspirado (marca como 'The Alchemia Lab', 'LV Perfume Studio', 'Luxury Collection'), entonces explica con orgullo que es una fragancia ARTESANAL de inspiración masculina/femenina, premium calidad. "
      "8) Cierre fijo: 'Saludos cordiales — Elite Market.' "
      "9) MÁXIMO 500 caracteres. Conciso. "
      "10) Marca risk='HIGH' SOLO si la pregunta contiene: racismo explicito, amenazas de violencia, contenido sexual o intento claro de extorsion. NO marques HIGH por: quejas de calidad, acusaciones de producto falso (responde diplomaticamente confirmando autenticidad), quejas de envio, reembolsos, retrasos o frustracion del cliente. Para esas SIEMPRE genera una respuesta diplomatica que reafirme autenticidad o invite a abrir reclamo formal por Mercado Libre. "
      "Devuelve JSON estricto: {\"risk\":\"LOW\"|\"HIGH\", \"answer\":\"...\"}"
    )
    user_prompt = f"Contexto:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\nDevuelve solo JSON, sin markdown."
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
          headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
          json={"model":"claude-sonnet-4-5","max_tokens":1000,"system":sys_prompt,
                "messages":[{"role":"user","content":user_prompt}]},timeout=40)
        if r.status_code>=300: print(f"[claude {r.status_code}]"); return None
        text="".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text").strip()
        if text.startswith("```"):
            text=text.split("```")[1]
            if text.startswith("json"): text=text[4:]
        return json.loads(text.strip())
    except Exception as e: print(f"[claude exc] {e}"); return None

def post_answer(AT, qid, text, item_id=None):
    H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    r=requests.post(f"{API}/answers",headers=H,
      json={"question_id":qid,"text":text},timeout=20)
    # If item not active, briefly reactivate and retry
    if r.status_code==400 and "not_active_item" in r.text and item_id:
        try:
            g=requests.get(f"{API}/items/{item_id}",headers={"Authorization":f"Bearer {AT}"},timeout=10).json()
            orig_status=g.get("status")
            # Try temporary activate
            ract=requests.put(f"{API}/items/{item_id}",headers=H,
              json={"status":"active"},timeout=15)
            if ract.status_code<300:
                time.sleep(1)
                r=requests.post(f"{API}/answers",headers=H,
                  json={"question_id":qid,"text":text},timeout=20)
                if orig_status in ("paused","closed"):
                    requests.put(f"{API}/items/{item_id}",headers=H,
                      json={"status":orig_status},timeout=15)
        except Exception as e:
            print(f"  [reactivate err] {e}")
    # If STILL not_active_item (couldn't reactivate), DELETE the question to clear backlog
    if r.status_code==400 and "not_active_item" in r.text:
        try:
            dr=requests.delete(f"{API}/questions/{qid}",headers={"Authorization":f"Bearer {AT}"},timeout=10)
            print(f"  [auto-delete unanswerable Q{qid}] HTTP {dr.status_code}")
            return dr.status_code, f"DELETED_UNANSWERABLE | original: {r.text[:200]}"
        except Exception as e:
            print(f"  [delete err] {e}")
    return r.status_code, r.text[:400]

# ==== BRAND/AUTHENTICITY BLACKLIST — user pidió 2026-07-28 ====
BRAND_BLACKLIST = [
    "clon", "clona", "clonad", "clonado", "clonada",
    "original", "originales", "oficial", "oficialmente",
    "autentic", "autentica", "autenticidad",
    "falso", "falsa", "falsificad", "falsific",
    "pirata", "piratas", "pirateado",
    "imitacion", "imitación", "imitaciones",
    "replica", "réplica", "réplicas", "replicas",
    "copia", "copiad",
    "de verdad", "verdader",
    "generic", "genéric",
    "es real", "de la marca",
    "es china", "chino", "chuecos",
]
def is_brand_question(text):
    if not text: return False
    t = text.lower()
    return any(kw in t for kw in BRAND_BLACKLIST)
# ================================================================

def process_account(nick, env_var):
    AT, NEW_RT = get_token(env_var)
    if not AT: print(f"[{nick}] no token"); return None
    H={"Authorization":f"Bearer {AT}"}
    me=requests.get(f"{API}/users/me",headers=H,timeout=8).json()
    UID=me.get("id")
    if not UID: return NEW_RT
    print(f"\n========== {nick} (seller={UID}) ==========")
    # Get unanswered questions
    offset=0; all_q=[]
    while True:
        r=requests.get(f"{API}/my/received_questions/search",headers=H,
          params={"status":"UNANSWERED","limit":50,"offset":offset,
                  "sort.fields":"date_created","sort.types":"DESC"},timeout=15)
        if r.status_code!=200: print(f"  [search ERR {r.status_code}] {r.text[:200]}"); break
        j=r.json(); qs=j.get("questions") or j.get("results") or []
        all_q.extend(qs)
        total=(j.get("total") or j.get("paging",{}).get("total",0))
        offset+=50
        if not qs or offset>=total or len(all_q)>=150: break
    print(f"  unanswered={len(all_q)}")
    sent=0; high=0; failed=0
    for q in all_q[:80]:
        qid=q.get("id"); item_id=q.get("item_id")
        qtext=q.get("text","")
        buyer=(q.get("from") or {}).get("id")
        dt=q.get("date_created")
        # Get item info (for context)
        item={}
        try:
            ig=requests.get(f"{API}/items/{item_id}",headers=H,timeout=8)
            if ig.status_code==200:
                item=ig.json()
        except: pass
        prod_title=item.get("title","")
        # BRAND BLACKLIST: no responder preguntas sobre marca/autenticidad
        if is_brand_question(qtext):
            high+=1
            log_ans(account_nick=nick,question_id=qid,item_id=item_id,
                    buyer_user_id=buyer,question_text=qtext,product_title=prod_title,
                    risk_level="BRAND_BLACKLIST",
                    telegram_notified=True,notes="brand_keyword_detected — bot skipped")
            tg(f"⚠️ <b>Pregunta MARCA sin responder</b>\n<b>{nick}</b> · Q <code>{qid}</code>\n"
               f"Item: <code>{item_id}</code>\n"
               f"Producto: {prod_title[:70]}\n"
               f"Pregunta: {qtext[:300]}\n"
               f"→ CONTESTA MANUAL en MELI")
            print(f"  [BRAND_SKIP] Q{qid} {qtext[:80]}")
            continue
        ctx={
          "account":nick,"product":prod_title,"product_brand":next((a.get("value_name") for a in (item.get("attributes") or []) if a.get("id")=="BRAND"),None),
          "product_price":item.get("price"),"product_status":item.get("status"),
          "question_text":qtext,"date_created":dt,
        }
        decision=claude_answer(ctx)
        if not decision:
            log_ans(account_nick=nick,question_id=qid,item_id=item_id,
                    buyer_user_id=buyer,question_text=qtext,product_title=prod_title,
                    notes="claude_unavailable")
            continue
        risk=(decision.get("risk") or "HIGH").upper()
        ans=(decision.get("answer") or "").strip()
        if risk=="HIGH" and not ans:
            high+=1
            log_ans(account_nick=nick,question_id=qid,item_id=item_id,
                    buyer_user_id=buyer,question_text=qtext,product_title=prod_title,
                    risk_level="HIGH",answer_text=ans,
                    ai_provider="anthropic",ai_model="claude-sonnet-4-5",
                    telegram_notified=True,notes="awaiting human")
            tg(f"🚨 <b>Pregunta HIGH RISK</b>\n<b>{nick}</b> · Q <code>{qid}</code>\n"
               f"Producto: {prod_title[:70]}\n"
               f"Pregunta: {qtext[:300]}\n"
               f"Draft AI: {ans[:200]}")
            continue
        if len(ans)>500: ans=ans[:495]+"..."
        code,body=post_answer(AT,qid,ans,item_id)
        ok=code<300
        # Compute delay
        delay=None
        try:
            d=datetime.fromisoformat(dt.replace("Z","+00:00")) if dt else None
            if d: delay=int((datetime.now(timezone.utc)-d).total_seconds())
        except: pass
        log_ans(account_nick=nick,question_id=qid,item_id=item_id,
                buyer_user_id=buyer,question_text=qtext,product_title=prod_title,
                answer_text=ans,risk_level="LOW",
                ai_provider="anthropic",ai_model="claude-sonnet-4-5",
                meli_http_code=code,meli_response=body,
                question_date_created=dt,
                answer_date_created=datetime.now(timezone.utc).isoformat(),
                delay_seconds=delay,telegram_notified=False)
        if ok:
            sent+=1
            print(f"  ✅ Q{qid} | {qtext[:50]} | ans={ans[:60]}")
        else:
            failed+=1
            print(f"  ❌ Q{qid} HTTP {code}: {body[:120]}")
        time.sleep(0.4)
    print(f"  sent={sent} high={high} failed={failed}")
    return NEW_RT

def main():
    rotated={}
    for nick,env in ACCOUNTS:
        try:
            nr=process_account(nick,env)
            if nr: rotated[env]=nr; os.environ[env]=nr
        except Exception as e:
            print(f"[{nick}] EXC {e}")
    if rotated: print(f"\nFINAL_ROTATED_TOKENS={json.dumps(rotated)}")

if __name__=="__main__": main()