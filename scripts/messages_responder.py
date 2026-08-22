"""
Auto-responder de mensajes post-venta multi-cuenta.

Flujo cada 10 min:
1. Por cada cuenta: GET /messages/orders/search_packs?seller_id=X (recent packs with msgs)
2. Para cada pack: leer mensajes; si último es del comprador (no respondido por seller en >0 min) → procesar
3. Claude analiza y produce respuesta defensiva
4. POST /messages/packs/{pack_id}/sellers/{seller_id}?tag=post_sale

Política Elite Market:
- NUNCA promete reembolso/devolución
- Tono profesional, defensivo, breve
- Si el mensaje es agresivo o pide refund → marcar HIGH risk, NO responder, solo notify
- Idempotente: no responder al mismo pack más de una vez/día
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
  ("ASVA",     "MELI_REFRESH_TOKEN_ASVA"),
  # ("MAYRELY",  "MELI_REFRESH_TOKEN_MAYRELY"),  # DEACTIVATED 2026-07-28 (user pidió solo ASVA)
  # ("YERALDIN", "MELI_REFRESH_TOKEN_YERALDIN"),  # DEACTIVATED 2026-07-28 (user pidió solo ASVA)
  # ("LUPITA",   "MELI_REFRESH_TOKEN_LUPITA"),  # DEACTIVATED 2026-07-28 (user pidió solo ASVA)
]

def tg(m):
    if not TG_BOT or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
            data={"chat_id":TG_CHAT,"text":m,"parse_mode":"HTML","disable_web_page_preview":True},timeout=8)
    except: pass

def log_resp(**kw):
    try:
        requests.post(f"{SB}/rest/v1/meli_messages_responded",headers=SBH,json=kw,timeout=10)
    except Exception as e: print("[log err]", e)

def already_responded_today(pack_id):
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=24)).isoformat()
    q=requests.utils.quote(cutoff,safe='')
    r=requests.get(f"{SB}/rest/v1/meli_messages_responded?pack_id=eq.{pack_id}&ts=gte.{q}&meli_http_code=lt.300&select=id",
                   headers=SBH,timeout=8)
    return r.status_code==200 and len(r.json())>0

def get_token(env_var):
    rt=os.environ.get(env_var)
    if not rt: return None,None
    for _ in range(4):
        try:
            r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
            if r.status_code<500: break
            time.sleep(4)
        except: pass
    if r.status_code>=300: print(f"[oauth FAIL {env_var}] {r.status_code}"); return None,None
    t=r.json(); return t["access_token"], t["refresh_token"]

def parse_text(x):
    txt_field=x.get("text")
    if isinstance(txt_field,dict): return txt_field.get("plain","") or txt_field.get("html","")
    if isinstance(txt_field,str): return txt_field
    return x.get("message","") or ""

def list_recent_packs_with_msgs(AT, seller_id, limit=30):
    """Use messages search endpoint to find packs with recent activity."""
    H={"Authorization":f"Bearer {AT}"}
    # Endpoint: /messages/orders/search_packs/{user_id}/?tag=post_sale
    url=f"{API}/messages/orders/search_packs/{seller_id}/"
    try:
        r=requests.get(url,headers=H,params={"tag":"post_sale","limit":limit},timeout=15)
        if r.status_code==200:
            j=r.json()
            return j.get("results",[]) if isinstance(j,dict) else j
        # Fallback: recent orders endpoint
    except Exception as e: print(f"[search_packs err] {e}")
    # Fallback: use orders/search to get recent orders
    try:
        r=requests.get(f"{API}/orders/search",headers=H,
            params={"seller":seller_id,"sort":"date_desc","limit":limit},timeout=15)
        if r.status_code==200:
            j=r.json()
            results=j.get("results",[])
            packs=[]
            seen=set()
            for o in results:
                pid=str(o.get("pack_id") or o.get("id"))
                if pid in seen: continue
                seen.add(pid)
                packs.append({"id":pid,"order_id":o.get("id")})
            return packs
    except Exception as e: print(f"[orders/search err] {e}")
    return []

def get_pack_messages(AT, pack_id, seller_id):
    H={"Authorization":f"Bearer {AT}"}
    try:
        r=requests.get(f"{API}/messages/packs/{pack_id}/sellers/{seller_id}",
            headers=H,params={"tag":"post_sale","limit":20},timeout=12)
        if r.status_code!=200: return []
        j=r.json()
        msgs=j.get("messages") or j.get("results") or []
        if isinstance(j,list): msgs=j
        return msgs
    except: return []

def get_order_info(AT, order_id):
    H={"Authorization":f"Bearer {AT}"}
    try:
        r=requests.get(f"{API}/orders/{order_id}",headers=H,timeout=10)
        if r.status_code==200: return r.json()
    except: pass
    return None

def get_products_context(AT, order):
    """Carga titulo, atributos y descripcion real de cada producto del pedido."""
    if not order: return []
    H={"Authorization":f"Bearer {AT}"}
    products=[]
    for row in (order.get("order_items") or [])[:6]:
        base=row.get("item") or {}
        iid=base.get("id")
        detail=base
        description=""
        if iid:
            try:
                ir=requests.get(f"{API}/items/{iid}",headers=H,timeout=10)
                if ir.status_code==200: detail=ir.json()
            except: pass
            try:
                dr=requests.get(f"{API}/items/{iid}/description",headers=H,timeout=10)
                if dr.status_code==200:
                    description=(dr.json().get("plain_text") or "")[:8000]
            except: pass
        attrs={a.get("id"):a.get("value_name") for a in (detail.get("attributes") or []) if a.get("id")}
        products.append({
          "item_id":iid,"title":detail.get("title") or base.get("title") or "",
          "quantity":row.get("quantity"),"attributes":attrs,"description":description,
        })
    return products

def _is_technical_message(text):
    t=(text or "").lower()
    keys=("compatible","compatibilidad","medida","tamano","tamaño","color","material",
          "incluye","contenido","bateria","duracion","potencia","watts","resistente",
          "impermeable","bluetooth","funciona","modelo","version","voltaje","cargador")
    return any(k in t for k in keys)

def _evidence_is_grounded(evidence, products):
    norm=lambda s:" ".join(str(s or "").lower().split())
    ev=norm(evidence)
    return len(ev)>=3 and ev in norm(json.dumps(products,ensure_ascii=False))

def claude_decide(context):
    if not ANTHROPIC_KEY: return None
    sys_prompt = (
      "Eres el agente de servicio al cliente de Elite Market, tienda mexicana en Mercado Libre. "
      "Tu trabajo: redactar respuesta a un MENSAJE post-venta del comprador. "
      "REGLAS DURAS (no negociables): "
      "1) NUNCA prometas reembolso ni etiqueta de devolución por iniciativa. "
      "2) Tono profesional, defensivo, breve, NO acusatorio, sin disculpas excesivas. "
      "3) Si el comprador es agresivo/grosero, respuesta FRÍA y DIRECTA. "
      "4) Argumentos técnicos sólidos basados en producto. "
      "5) Cierre fijo: 'Saludos cordiales — Elite Market.' "
      "6) Máximo 600 caracteres. "
      "7) Si el comprador exige reembolso, amenaza con reclamo/baja calificación, o reporta daño/falsificación con foto, marca risk='HIGH' y NO inventes excusas débiles. "
      "8) Si solo pregunta info (cuándo llega, factura, instrucciones), risk='LOW' responde directo. "
      "9) Si el ÚLTIMO mensaje es del seller (no del buyer), risk='SKIP' y message vacío. "
      "10) REGLA ASVA E: antes de contestar sobre especificaciones, compatibilidad, contenido, medidas, color, material o funcionamiento, lee products[].description y products[].attributes. NUNCA inventes ni completes datos por intuicion. Si el dato no aparece, di que no se especifica. "
      "11) No afirmes que el producto es original ni menciones marcas ajenas si la publicacion es generica o de ASVA Electronics. "
      "Devuelve JSON estricto: {\"risk\":\"LOW\"|\"HIGH\"|\"SKIP\",\"strategy\":\"...\",\"message\":\"...\",\"evidence\":\"fragmento literal de descripcion/atributos que respalda cualquier dato tecnico\"}"
    )
    user_prompt=f"Contexto:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\nDevuelve solo JSON, sin markdown."
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-5","max_tokens":1200,
                  "system":sys_prompt,
                  "messages":[{"role":"user","content":user_prompt}]},
            timeout=40)
        if r.status_code>=300: print(f"[claude {r.status_code}] {r.text[:200]}"); return None
        j=r.json()
        text="".join(b.get("text","") for b in j.get("content",[]) if b.get("type")=="text").strip()
        if text.startswith("```"):
            text=text.split("```")[1]
            if text.startswith("json"): text=text[4:]
        return json.loads(text.strip())
    except Exception as e: print(f"[claude exc] {e}"); return None

def send_postsale(AT, pack_id, seller, buyer, msg):
    H={"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"}
    payload={"from":{"user_id":seller},"to":{"user_id":buyer},"text":msg}
    url=f"{API}/messages/packs/{pack_id}/sellers/{seller}?tag=post_sale"
    r=requests.post(url,headers=H,json=payload,timeout=20)
    return r.status_code, r.text[:400]

def process_account(nick, env_var):
    AT, NEW_RT = get_token(env_var)
    if not AT: print(f"[{nick}] no token"); return None
    H={"Authorization":f"Bearer {AT}"}
    me=requests.get(f"{API}/users/me",headers=H,timeout=8).json()
    UID=me.get("id")
    if not UID: return NEW_RT
    print(f"\n========== {nick} (seller={UID}) ==========")
    packs=list_recent_packs_with_msgs(AT, UID, limit=50)
    print(f"  recent packs: {len(packs)}")
    processed=0; sent=0; skipped=0
    for p in packs[:50]:
        pid=str(p.get("id") if isinstance(p,dict) else p)
        if not pid or pid in ("None","0"): continue
        if already_responded_today(pid):
            skipped+=1; continue
        msgs=get_pack_messages(AT, pid, UID)
        if not msgs: continue
        # Sort by date asc to find LAST message
        msgs_sorted=sorted(msgs, key=lambda x: (x.get("message_date",{}).get("created") or x.get("date_created") or ""))
        last=msgs_sorted[-1]
        last_from=(last.get("from") or {}).get("user_id")
        # Skip if last msg is from seller (already responded)
        if last_from == UID: continue
        # Skip auto messages (factura template) — last_from must be buyer
        if not last_from: continue
        buyer_id=last_from
        last_text=parse_text(last)
        if not last_text.strip(): continue

        # Get order info for product context
        oid=None
        if isinstance(p,dict): oid=p.get("order_id") or p.get("id")
        if not oid: oid=pid
        order=get_order_info(AT, oid)
        products=get_products_context(AT,order)
        product=products[0]["title"] if products else ""
        ctx={
          "pack_id":pid,"order_id":str(oid),"account":nick,
          "product":product,"products":products,"order_status":(order or {}).get("status"),"buyer_id":buyer_id,
          "last_buyer_message":last_text,
          "conversation":[{"from":m.get("from",{}).get("user_id"),"text":parse_text(m)[:300]} for m in msgs_sorted[-6:]],
        }
        decision=claude_decide(ctx)
        processed+=1
        if not decision:
            log_resp(account_nick=nick,pack_id=pid,order_id=str(oid),buyer_user_id=buyer_id,
                     product_title=product,buyer_message=last_text[:600],
                     notes="claude_unavailable",telegram_notified=False)
            continue
        risk=(decision.get("risk") or "HIGH").upper()
        if risk=="SKIP":
            skipped+=1; continue
        msg=(decision.get("message") or "").strip()
        evidence=(decision.get("evidence") or "").strip()
        if risk=="LOW" and _is_technical_message(last_text):
            if not evidence or not _evidence_is_grounded(evidence,products):
                print(f"  [grounding fallback] pack={pid} technical answer without valid evidence")
                msg=("Hola, esa informacion no se especifica en la descripcion ni en la ficha tecnica "
                     "de la publicacion. Para evitar darte un dato incorrecto, no podemos confirmarlo. "
                     "Saludos cordiales — Elite Market.")
        if not msg: continue
        if len(msg)>700: msg=msg[:690]+"..."
        if risk=="LOW":
            code,body=send_postsale(AT,pid,UID,buyer_id,msg)
            ok=code<300
            log_resp(account_nick=nick,pack_id=pid,order_id=str(oid),buyer_user_id=buyer_id,
                     product_title=product,buyer_message=last_text[:600],
                     response_text=msg,risk_level="LOW",
                     meli_http_code=code,meli_response=body,telegram_notified=ok)
            if ok:
                sent+=1
                tg(f"💬 <b>Auto-respuesta msg (LOW)</b>\nCuenta: <b>{nick}</b> · Pack: <code>{pid}</code>\nProducto: {product[:70]}\nComprador: {last_text[:200]}\nRespuesta ({len(msg)}c): {msg[:300]}")
            else:
                tg(f"⚠️ <b>FALLÓ msg ({nick})</b>\nPack: <code>{pid}</code>\nHTTP {code}: {body[:200]}")
        else:  # HIGH
            log_resp(account_nick=nick,pack_id=pid,order_id=str(oid),buyer_user_id=buyer_id,
                     product_title=product,buyer_message=last_text[:600],
                     response_text=msg,risk_level="HIGH",
                     telegram_notified=True,notes="awaiting_human")
            tg(f"🚨 <b>HIGH RISK msg — revisa</b>\nCuenta: <b>{nick}</b> · Pack: <code>{pid}</code>\nProducto: {product[:70]}\nComprador: {last_text[:300]}\nDraft AI ({len(msg)}c): {msg[:400]}")
    print(f"  processed={processed} sent={sent} skipped={skipped}")
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
