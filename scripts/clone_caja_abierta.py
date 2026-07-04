import os, json, requests, sys, time

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LUPITA"]

r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
  timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LUPITA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SOURCES=["MLM5633114418","MLM5633114492"]

def desc_for(model_name):
    return f"""⚠️ ═══════════════════════════════════════
🚨 PRODUCTO CAJA ABIERTA / REACONDICIONADO 🚨
❌ ATENCIÓN: NO ES COMPATIBLE CON LA APP JBL PORTABLE ❌
═══════════════════════════════════════ ⚠️

✅ CALIDAD 1:1 — EXCELENTE ESTADO
✅ 100% FUNCIONAL — Sonido, batería, conectividad Bluetooth impecables
✅ Empaque de caja abierta (revisado y probado por nuestro equipo técnico)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📢 IMPORTANTE — LEE ANTES DE COMPRAR:

🔴 ESTE PRODUCTO NO SE CONECTA CON LA APP OFICIAL JBL PORTABLE.
🔴 Todas las demás funciones operan al 100% (Bluetooth 5.3, JBL Pro Sound, resistencia al agua IP67).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 QUÉ INCLUYE:
• 1 Bocina JBL {model_name}
• 1 Cable de carga USB-C
• Manual de usuario

🎧 CARACTERÍSTICAS PRINCIPALES:
• Sonido JBL Pro potente y nítido
• Bluetooth 5.3 estable
• Resistencia al agua y polvo IP67 (sumergible)
• Batería recargable de larga duración
• Diseño resistente y portátil

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚚 ENVÍO INMEDIATO — Enviamos el mismo día antes de las 3pm.
🛡️ GARANTÍA POR ELITE MARKET — 30 días contra fallas de fábrica.
💯 COMPRA PROTEGIDA MERCADO LIBRE.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cualquier duda antes de comprar, pregunta y te respondemos rápido. Gracias por preferir Elite Market."""

def extract_pic_url(p):
    for k in ("secure_url","url","source"):
        if p.get(k): return p[k]
    return None

def detect_model(title):
    t=title.lower()
    if "charge 6" in t or "charge6" in t: return "Charge 6","1799"
    if "charge 5" in t or "charge5" in t: return "Charge 5","1499"
    if "go 4" in t or "go4" in t: return "Go 4","499"
    if "go 3" in t or "go3" in t: return "Go 3","399"
    if "clip 5" in t or "clip5" in t: return "Clip 5","799"
    if "flip 7" in t or "flip7" in t: return "Flip 7","1799"
    if "flip 6" in t or "flip6" in t: return "Flip 6","1299"
    if "xtreme" in t: return "Xtreme","3999"
    return "Bluetooth","999"

for SRC in SOURCES:
    print(f"\n=== SOURCE {SRC} ===",flush=True)
    s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H,timeout=15).json()
    title_src=s.get("title","?")
    price_src=s.get("price")
    cat=s.get("category_id")
    fam=s.get("family_name") or title_src
    pics_raw=s.get("pictures",[])
    pics=[extract_pic_url(p) for p in pics_raw[:10]]
    pics=[u for u in pics if u]
    attrs_src=s.get("attributes",[])
    print(f"  src title: {title_src[:80]}",flush=True)
    print(f"  src cat: {cat}  price: ${price_src}  pics: {len(pics)}  family: {fam[:50]}",flush=True)
    
    model, default_price = detect_model(title_src)
    is_camo="camuflaje" in title_src.lower() or "camuflado" in title_src.lower()
    color = "Camuflaje" if is_camo else "Negro"
    new_title = f"Bocina Jbl {model} Bluetooth Ip67 Caja Abierta Excelente Estado"[:60]
    new_price = int(default_price)
    
    new_attrs=[]
    seen=set()
    for a in attrs_src:
        aid=a.get("id","")
        if aid in ("SELLER_SKU","ITEM_CONDITION"): continue
        if aid in seen: continue
        seen.add(aid)
        entry={"id":aid}
        if a.get("value_id"): entry["value_id"]=a["value_id"]
        elif a.get("value_name"): entry["value_name"]=a["value_name"]
        else: continue
        new_attrs.append(entry)
    new_attrs.append({"id":"ITEM_CONDITION","value_name":"Usado"})
    
    # Family name for caja abierta variant — distinct from catalog
    new_family = f"JBL {model} Caja Abierta Reacondicionado"
    
    payload={
      "family_name":new_family,
      "category_id":cat,
      "price":new_price,
      "currency_id":"MXN",
      "available_quantity":1,
      "buying_mode":"buy_it_now",
      "condition":"used",
      "listing_type_id":"gold_pro",
      "pictures":[{"source":u} for u in pics],
      "attributes":new_attrs,
      "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                    {"id":"WARRANTY_TIME","value_name":"30 días"}],
      "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False,"logistic_type":"drop_off"}
    }
    
    print(f"  posting: title={new_title} price=${new_price} model={model}",flush=True)
    p=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
    if "id" in p:
        new_id=p["id"]
        print(f"  ✅ POSTED: {new_id} status={p.get('status')} price=${p.get('price')}",flush=True)
        d=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",
                       headers=H,json={"plain_text":desc_for(model)},timeout=15)
        print(f"  description: {d.status_code}",flush=True)
        print(f"  URL: {p.get('permalink','?')}",flush=True)
    else:
        print(f"  ❌ FAIL: {json.dumps(p)[:600]}",flush=True)
    time.sleep(1)
