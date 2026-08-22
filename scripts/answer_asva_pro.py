#!/usr/bin/env python3
"""
ASVA pro context-aware bot.
- Lee item (atributos + descripcion + variaciones + condition + status)
- Templates rigidos para envio / factura / garantia / precio / disponibilidad
- Gemini Flash para preguntas product-specific (aroma, talla, material, color, etc)
- Skip items no activos (MELI rechaza con 400 not_active_item)
- Telegram alert al final
"""
import os, sys, json, time, re, requests
import meli_token

# Cuentas gestionadas por este bot context-aware con Gemini.
# Agregar mas cuentas aqui es "solo" mapear label -> env var.
ACCOUNTS = {
    "ASVA":   os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "KARIME": os.environ.get("MELI_REFRESH_TOKEN_KARIME"),
    "LIGIA":  os.environ.get("MELI_REFRESH_TOKEN_LIGIA"),
}
# ASVA E debe contestar solamente con hechos verificables de la publicacion.
STRICT_EVIDENCE_ACCOUNTS = {"ASVA"}
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_BOT     = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT    = os.environ.get("TELEGRAM_CHAT_ID")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

SYSTEM_PROMPT = """Eres asistente de respuestas de Elite Market en Mercado Libre Mexico.
REGLAS DURAS:
- Responde en espanol neutro, sin acentos especiales (e en vez de e).
- 1 a 2 oraciones, maximo 240 caracteres.
- Tono profesional, amable, NUNCA sumiso, NUNCA agresivo.
- Tutea ('tu' no 'usted'). Saludo breve, cierra con 'Gracias.'
- Sin emojis.
- NUNCA prometas descuentos.
- NUNCA des telefono, WhatsApp ni email externo.
- NUNCA discutas con el comprador.
- NUNCA inventes datos que no esten en el contexto. Si no lo sabes, di que esta en la descripcion.

REGLA MELI OBLIGATORIA (violacion = suspension de publicacion):
- Si el producto se presenta como GENERICO o de nuestra propia marca (Asva Electronics, The Alchemia Lab, LV Perfume Studio, Luxury Collection, o cualquier marca no reconocida), TODAS las respuestas deben sostener eso EXACTAMENTE.
- PROHIBIDO: mencionar marcas ajenas (JBL/Sony/Marshall/Bose/Beats/Xiaomi/Harman/etc). PROHIBIDO decir 'similar a', 'como el', 'tipo', 'parecido' con marcas ajenas. PROHIBIDO admitir clon/imitacion/copia/replica/inspirado. PROHIBIDO comparar con productos de marca.
- Solo hablas del producto de nuestra marca y sus especificaciones concretas.
- Si la pregunta menciona una marca ajena o palabra de autenticidad, NO respondes — devuelves cadena vacia para escalar a humano.


INSTRUCCION DE CONTEXTO:
- Reflejas EXACTAMENTE lo que dice la descripcion. Si la familia olfativa es amaderada y preguntan 'es fresco?', respondes que NO es fresco, es amaderado segun ficha.
- Si preguntan por talla/medida y la descripcion incluye guia de tallas, refierete a ella con valores concretos cuando esten disponibles.
- Si preguntan por material y la descripcion lo indica, citalo textual.
- Si preguntan por algo que no esta en el contexto, di con cortesia que esa informacion no se incluye en la ficha.
"""

# ---- Templates RIGIDOS (preceden a Gemini para temas operativos) ----
TEMPLATES = [
    (r"\b(envio|envi[oa]|enviar|llega|cuanto tarda|tiempo de entrega|cuando lo recibo|cuanto demora)\b",
     "Buen dia, el envio es GRATIS con Mercado Envios. Despachamos en 24 horas habiles y la entrega estimada es de 2 a 5 dias segun zona. Gracias."),
    (r"\b(factura|facturar|fiscal|rfc|cfdi|razon social)\b",
     "Buen dia, si facturamos. Al completar la compra envianos por mensaje privado tus datos fiscales (RFC, razon social, regimen, uso CFDI y correo) y procesamos en 48 horas. Gracias."),
    (r"\b(garantia|warranty|reparar|defecto|devoluci[oo]n|cambio)\b",
     "Buen dia, ofrecemos 30 dias de garantia del vendedor por defectos de fabrica comprobables. Para devoluciones aplica la politica estandar de Mercado Libre. Gracias."),
    (r"\b(precio|descuento|rebaja|negociar|mas barato|mejor precio|mayoreo)\b",
     "Buen dia, el precio publicado es el final e incluye envio gratis. No aplican descuentos adicionales en mensaje. Gracias."),
    (r"\b(stock|existencia|disponibilidad|disponibles|hay disponib|tienen disponib|en almacen)\b",
     None),  # contexto-aware abajo
    (r"\b(original|autentic|replica|pirata|falso|clon|imitacion|fake)\b",
     None),
]

def telegram(msg):
    if not (TG_BOT and TG_CHAT): return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
                      data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":"true"},
                      timeout=10)
    except Exception: pass

def fetch_item(iid, H):
    try:
        i = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=15).json()
    except Exception as e:
        return None
    try:
        desc = requests.get(f"https://api.mercadolibre.com/items/{iid}/description", headers=H, timeout=15).json().get("plain_text", "")
    except Exception:
        desc = ""
    attrs = {a.get("id"): a.get("value_name", "") for a in (i.get("attributes") or [])}
    variations = []
    for v in (i.get("variations") or []):
        v_attrs = {}
        for ac in v.get("attribute_combinations", []) or []:
            v_attrs[ac.get("id")] = ac.get("value_name")
        v_attrs["available_quantity"] = v.get("available_quantity", 0)
        v_attrs["price"] = v.get("price")
        variations.append(v_attrs)
    return {
        "id": iid,
        "title": i.get("title", ""),
        "status": i.get("status", ""),
        "condition": i.get("condition", ""),
        "price": i.get("price"),
        "available_quantity": i.get("available_quantity", 0),
        "category_id": i.get("category_id", ""),
        "attributes": attrs,
        "variations": variations,
        # No truncar agresivamente: muchas fichas dejan medidas, compatibilidad
        # y contenido de la caja despues de los primeros 1,500 caracteres.
        "description": desc[:8000],
    }

def template_answer(q_text, item):
    q = q_text.lower()
    for pat, tpl in TEMPLATES:
        if re.search(pat, q):
            if tpl is not None:
                return tpl
            # Casos contextuales
            if "stock" in pat or "disponib" in pat:
                if item:
                    if item["variations"]:
                        avail = []
                        for v in item["variations"]:
                            qty = v.get("available_quantity", 0)
                            color = v.get("COLOR") or v.get("SIZE") or v.get("MAIN_COLOR") or ""
                            if qty and color:
                                avail.append(color)
                        if avail:
                            return f"Buen dia, si tenemos disponibilidad en: {', '.join(avail[:8])}. Despachamos en 24 horas habiles. Gracias."
                    if (item.get("available_quantity") or 0) > 0:
                        return "Buen dia, si contamos con stock disponible. Despachamos en 24 horas habiles. Gracias."
                    return "Buen dia, por el momento esa variante esta agotada. Te invitamos a revisar nuestras otras publicaciones. Gracias."
                return "Buen dia, contamos con stock disponible. Despachamos en 24 horas habiles. Gracias."
            if "original" in pat:
                return "Buen dia, si, es producto 100 por ciento original y autentico, con la calidad garantizada por la marca. Gracias."
    return None

def _evidence_is_grounded(evidence, context):
    """Acepta evidencia solo si aparece literalmente en la ficha enviada al modelo."""
    if not evidence: return False
    norm = lambda s: re.sub(r"\s+", " ", str(s or "")).strip().lower()
    ev = norm(evidence)
    return len(ev) >= 3 and ev in norm(context)

def gemini_answer(q_text, item, strict_evidence=False):
    if not GEMINI_KEY:
        return None
    if not item:
        return None
    # Construir contexto compacto
    attrs_keep = {}
    KEYS = ["BRAND","MODEL","GENDER","FRAGRANCE_TYPE","OLFACTORY_FAMILY","ITEM_VOLUME",
            "ITEM_VOLUME_UNIT","BATTERY_LIFE","WATER_RESISTANCE","SIZE","SIZE_GRID_ID",
            "MAIN_COLOR","COLOR","MATERIAL","FABRIC_COMPOSITION","SLEEVE_LENGTH",
            "PANTS_RISE","INCLUDES","WITH_BLUETOOTH","WIRELESS","BATTERY_CAPACITY"]
    for k in KEYS:
        v = item["attributes"].get(k)
        if v: attrs_keep[k] = v
    var_summary = []
    for v in item["variations"][:8]:
        bits = []
        for kk in ("COLOR","MAIN_COLOR","SIZE"):
            if v.get(kk): bits.append(f"{kk}={v[kk]}")
        bits.append(f"qty={v.get('available_quantity',0)}")
        var_summary.append(" ".join(bits))
    ctx_lines = [
        f"TITULO: {item['title']}",
        f"PRECIO: ${item.get('price')}",
        f"CONDICION: {item.get('condition')}",
        f"CATEGORIA: {item.get('category_id')}",
        f"ATRIBUTOS: {json.dumps(attrs_keep, ensure_ascii=False)}",
    ]
    if var_summary:
        ctx_lines.append("VARIACIONES: " + " | ".join(var_summary))
    if item["description"]:
        ctx_lines.append(f"DESCRIPCION:\n{item['description']}")
    ctx = "\n".join(ctx_lines)

    if strict_evidence:
        user_prompt = (
            f"{ctx}\n\nPREGUNTA DEL COMPRADOR:\n{q_text}\n\n"
            "Responde SOLO con datos presentes en TITULO, ATRIBUTOS, VARIACIONES o DESCRIPCION. "
            "No conviertas ausencia de informacion en un si. Devuelve JSON estricto con "
            "{\"answer\":\"respuesta breve\",\"evidence\":\"fragmento literal del contexto que respalda el dato\"}. "
            "Si la ficha no contiene el dato, answer debe decir que no se especifica y evidence debe quedar vacio."
        )
    else:
        user_prompt = f"{ctx}\n\nPREGUNTA DEL COMPRADOR:\n{q_text}\n\nResponde."
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 600,
            "candidateCount": 1,
            "thinkingConfig": {"thinkingBudget": 0},
        }
    }
    if strict_evidence:
        body["generationConfig"]["responseMimeType"] = "application/json"
    j = None
    for attempt in range(4):
        try:
            r = requests.post(f"{GEMINI_URL}?key={GEMINI_KEY}", json=body, timeout=40)
        except Exception as e:
            print(f"    gemini exc try{attempt+1}: {e}")
            time.sleep(2*(attempt+1)); continue
        if r.status_code == 200:
            j = r.json(); break
        if r.status_code in (429, 500, 502, 503, 504):
            print(f"    gemini http {r.status_code} try{attempt+1}, backoff")
            time.sleep(2*(attempt+1)); continue
        print(f"    gemini http {r.status_code}: {r.text[:200]}")
        return None
    if not j:
        return None
    try:
        raw = j["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        print(f"    gemini parse fail: {json.dumps(j)[:300]}")
        return None
    if strict_evidence:
        try:
            parsed = json.loads(raw)
            ans = (parsed.get("answer") or "").strip()
            evidence = (parsed.get("evidence") or "").strip()
        except Exception:
            print("    strict grounding: JSON invalido")
            return None
        if evidence:
            if not _evidence_is_grounded(evidence, ctx):
                print(f"    strict grounding: evidencia no encontrada: {evidence[:100]}")
                return None
        elif "no se especifica" not in ans.lower() and "no esta" not in ans.lower():
            print("    strict grounding: respuesta sin evidencia")
            return None
    else:
        ans = raw
    # Sanity cap a 480 chars (limite MELI 2000 - queremos brevedad)
    ans = re.sub(r"\s+", " ", ans).strip()
    if len(ans) > 480:
        ans = ans[:477] + "..."
    # Guardas duras: NUNCA dejar pasar canales externos
    forbidden_patterns = [
        r"whats\s*app", r"wa\.me", r"@gmail", r"@hotmail", r"@outlook",
        r"@yahoo", r"\+52\s*\d", r"\binstagram\b", r"\btiktok\b",
        r"facebook\.com", r"mi[\s-]?correo", r"mi[\s-]?tel[\u00e9]fono",
        r"https?://(?!www\.mercadolibre)",
    ]
    for pat in forbidden_patterns:
        if re.search(pat, ans, re.IGNORECASE):
            print(f"    gemini blocked by pattern: {pat}")
            return None
    return ans

# ==== BRAND/AUTHENTICITY BLACKLIST — user pidió 2026-07-28 ====
# Si pregunta contiene UNA de estas → NO responder, alertar Telegram
BRAND_BLACKLIST = [
    # keywords autenticidad
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
    "es real", "es real?", "de la marca",
    "es china", "chino", "chuecos",
    # marcas ajenas — MELI: no abrir duda sobre otra marca
    "jbl", "sony", "marshall", "bose", "beats", "xiaomi", "harman",
    "flip 7", "flip7", "flip 6", "flip6", "charge 6", "charge6", "charge 5", "charge5",
    "go 4", "go4", "go 3", "go3", "clip 5", "clip5",
    "srs-xb", "srsxb", "srs xb", "xb100",
    "emberton", "willen", "middleton",
    "soundlink", "sound link",
    "pill", "beats pill",
]
def is_brand_question(text: str) -> bool:
    """True if question contains any brand/authenticity keyword."""
    if not text: return False
    t = text.lower()
    for kw in BRAND_BLACKLIST:
        if kw in t:
            return True
    return False

# ==== WHITELIST — items donde el bot SI responde afirmando originalidad ====
# User directive 2026-08-11: BOCINA ORIGINAL JBL GO 5 - siempre responder "es original"
ANSWER_ORIGINAL_WHITELIST = set()
def _load_original_whitelist():
    """Load items from Supabase where bot must respond 'es original' instead of skipping."""
    try:
        sb_url = os.environ.get("SUPABASE_URL","").rstrip("/")
        sb_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
        if not (sb_url and sb_key): return
        rr = requests.get(
            f"{sb_url}/rest/v1/meli_user_directives?directive_type=eq.bot_answer_original_for_jbl&select=scope_value",
            headers={"apikey":sb_key,"Authorization":f"Bearer {sb_key}"},
            timeout=8).json()
        for row in rr or []:
            v = (row.get("scope_value") or "").strip()
            if v: ANSWER_ORIGINAL_WHITELIST.add(v)
        print(f"  [ORIG_WHITELIST] loaded {len(ANSWER_ORIGINAL_WHITELIST)} items")
    except Exception as e:
        print(f"  [ORIG_WHITELIST] err: {e}")
_load_original_whitelist()

def answer_original_template(text: str, item: dict) -> str:
    """Response template for whitelisted JBL-brand items when asked about originality."""
    return ("Buen dia, si es 100% original, nuevo en caja sellada, con garantia del vendedor. Gracias.")
# ================================================================

def craft(q_text, item, strict_evidence=False):
    # Los templates operativos contienen politicas generales. En ASVA E no se
    # usan para evitar afirmar envio, garantia o factura sin respaldo de la ficha.
    a = None if strict_evidence else template_answer(q_text, item)
    if a: return ("template", a)
    a = gemini_answer(q_text, item, strict_evidence=strict_evidence)
    if a: return ("gemini", a)
    # Fallback ultra seguro
    if strict_evidence:
        return ("fallback", "Buen dia, esa informacion no se especifica en la descripcion ni en la ficha tecnica de esta publicacion. Gracias.")
    return ("fallback", "Buen dia, gracias por tu pregunta. Toda la informacion del producto se encuentra detallada en la descripcion de la publicacion. Si hay algo especifico que necesites, con gusto te apoyamos. Gracias.")

def process_account(label, refresh_tok):
    """Procesa preguntas UNANSWERED de una cuenta. Devuelve (answered, skipped, errored)."""
    if not refresh_tok:
        print(f"\n=== {label}: sin refresh_token, skip ===")
        return (0, 0, 0)
    try:
        r = meli_token.refresh(refresh_tok)
        j = r if isinstance(r, dict) else r.json()
    except Exception as e:
        print(f"\n=== {label}: ERROR refresh ({e}) ===")
        return (0, 0, 1)
    at = j.get("access_token")
    if not at:
        print(f"\n=== {label}: token invalido ({j.get('error','?')}) ===")
        return (0, 0, 1)
    H  = {"Authorization": f"Bearer {at}"}
    Hp = {"Authorization": f"Bearer {at}", "Content-Type": "application/json"}
    try:
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    except Exception as e:
        print(f"\n=== {label}: error /me ({e}) ===")
        return (0, 0, 1)
    uid = me.get("id")
    if not uid:
        print(f"\n=== {label}: /me sin id (token expirado) ===")
        return (0, 0, 1)
    print(f"\n=== {label} ({me.get('nickname')} {uid}) ===")
    try:
        q = requests.get(
            f"https://api.mercadolibre.com/questions/search?seller_id={uid}&status=UNANSWERED&limit=50",
            headers=H, timeout=20).json()
    except Exception as e:
        print(f"  err questions: {e}")
        return (0, 0, 1)
    qs = q.get("questions") or []
    print(f"  unanswered: {len(qs)}")
    if not qs:
        return (0, 0, 0)
    items_cache = {}
    answered = skipped_paused = errored = 0
    for ques in qs:
        qid = ques.get("id")
        text = ques.get("text", "")
        iid = ques.get("item_id")
        if iid not in items_cache:
            items_cache[iid] = fetch_item(iid, H)
        item = items_cache[iid]
        title_short = (item["title"][:55] if item else iid)
        if item and item.get("status") and item["status"] != "active":
            skipped_paused += 1
            print(f"  [SKIP {item['status']}] {iid} '{title_short}' Q: '{text[:70]}'")
            continue
        # WHITELIST override: items JBL con directive → responder AFIRMANDO originalidad
        if iid in ANSWER_ORIGINAL_WHITELIST and is_brand_question(text):
            ans = answer_original_template(text, item)
            print(f"  [ORIG_WHITELIST_ANSWER] {iid} '{title_short}'")
            print(f"    Q: '{text[:100]}'")
            print(f"    A: '{ans}'")
            try:
                rp = requests.post("https://api.mercadolibre.com/answers", headers=Hp,
                                   json={"question_id": qid, "text": ans}, timeout=20)
                if rp.status_code in (200, 201):
                    answered += 1
                else:
                    errored += 1
                    print(f"    err {rp.status_code}: {rp.text[:200]}")
            except Exception as e:
                errored += 1
                print(f"    exc: {e}")
            time.sleep(1)
            continue
        # BRAND BLACKLIST: preguntas sobre marca/autenticidad NO se responden automáticamente
        if is_brand_question(text):
            skipped_paused += 1
            print(f"  [BRAND_SKIP] {iid} '{title_short}' Q: '{text[:100]}'")
            telegram(f"⚠️ Pregunta MARCA sin responder\nItem: {iid}\nTitulo: {title_short}\nQ: {text[:200]}\nBuyer: {ques.get('from',{}).get('id','?')}\nPerfil: https://www.mercadolibre.com.mx/perfil/{ques.get('from',{}).get('id','')}\n→ En MELI: Denunciar / Bloquear junto a la pregunta")
            continue
        kind, ans = craft(text, item, strict_evidence=(label in STRICT_EVIDENCE_ACCOUNTS))
        print(f"  [{kind}] {iid} '{title_short}'")
        print(f"    Q: '{text[:100]}'")
        print(f"    A: '{ans}'")
        try:
            rp = requests.post("https://api.mercadolibre.com/answers", headers=Hp,
                               json={"question_id": qid, "text": ans}, timeout=20)
            if rp.status_code in (200, 201):
                answered += 1
            else:
                errored += 1
                print(f"    err {rp.status_code}: {rp.text[:200]}")
        except Exception as e:
            errored += 1
            print(f"    exc: {e}")
        time.sleep(1)
    print(f"  --- {label} respondidas={answered} pausadas={skipped_paused} errores={errored}")
    return (answered, skipped_paused, errored)


def main():
    if not GEMINI_KEY:
        print("WARN: GEMINI_API_KEY missing - solo templates + fallback")

    tot_ans = tot_skip = tot_err = 0
    per_acct = {}
    for label, rt in ACCOUNTS.items():
        a, s_, e_ = process_account(label, rt)
        per_acct[label] = (a, s_, e_)
        tot_ans += a; tot_skip += s_; tot_err += e_

    print(f"\n=== TOTAL respondidas={tot_ans}  pausadas={tot_skip}  errores={tot_err} ===")
    # Telegram: solo si hubo errores o mucho trabajo
    if tot_err or tot_ans >= 5:
        lines = ["<b>MELI answer-pro</b>"]
        for lbl,(a,s_,e_) in per_acct.items():
            lines.append(f"{lbl}: resp {a} / skip {s_} / err {e_}")
        telegram("\n".join(lines))

if __name__ == "__main__":
    main()
