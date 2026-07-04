import os, json, requests, sys, time

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LUPITA"]

# refresh
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
  timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LUPITA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SOURCES=["MLM5633114418","MLM5633114492"]

DESC_TMPL = """⚠️ ═══════════════════════════════════════
🚨 PRODUCTO CAJA ABIERTA / REACONDICIONADO 🚨
❌ ATENCIÓN: NO ES COMPATIBLE CON LA APP JBL PORTABLE ❌
═══════════════════════════════════════ ⚠️

✅ CALIDAD 1:1 — EXCELENTE ESTADO
✅ 100% FUNCIONAL — Sonido, batería, conectividad Bluetooth impecables
✅ Empaque de caja abierta (revisado y probado por nuestro equipo técnico)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📢 IMPORTANTE — LEE ANTES DE COMPRAR:

🔴 ESTE PRODUCTO NO SE CONECTA CON LA APP OFICIAL JBL PORTABLE.
🔴 Todas las demás funciones operan al 100% (Bluetooth 5.3, JBL Pro Sound, resistencia al agua IP67, PartyBoost/Auracast según modelo).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 QUÉ INCLUYE:
• 1 Bocina JBL Go 4
• 1 Cable de carga USB-C
• Manual de usuario

🎧 CARACTERÍSTICAS PRINCIPALES:
• Sonido JBL Pro potente y nítido
• Bluetooth 5.3 estable hasta 10 metros
• Resistencia al agua y polvo IP67 (sumergible)
• Batería recargable hasta 7 horas de reproducción
• Diseño ultra compacto y ligero
• Correa integrada para llevar a todos lados

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚚 ENVÍO INMEDIATO — Enviamos el mismo día antes de las 3pm.
🛡️ GARANTÍA POR ELITE MARKET — 30 días contra fallas de fábrica.
💯 COMPRA PROTEGIDA MERCADO LIBRE.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cualquier duda antes de comprar, pregunta y te respondemos rápido. Gracias por preferir Elite Market."""

for SRC in SOURCES:
    print(f"\n=== SOURCE {SRC} ===",flush=True)
    s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H,timeout=15).json()
    title_src=s.get("title","?")
    price_src=s.get("price")
    cat=s.get("category_id")
    pics=[p["source"] for p in s.get("pictures",[])[:10]]
    attrs_src=s.get("attributes",[])
    print(f"  src title: {title_src[:80]}",flush=True)
    print(f"  src cat: {cat}  price: ${price_src}",flush=True)
    
    # Build new title: mark as caja abierta
    # Original: "Bocina Portátil Jbl Go 4 Bluetooth, Camuflaje. Color Camuflaje" or "Parlante Jbl Go4 Bluetooth Portátil ..."
    new_title = f"Bocina Jbl Go 4 Bluetooth Ip67 Caja Abierta Excelente Estado"
    if "camuflaje" in title_src.lower() or "camuflaje" in title_src.lower():
        new_title = "Bocina Jbl Go 4 Bluetooth Ip67 Camuflaje Caja Abierta 1:1"
    new_title=new_title[:60]
    
    # Attributes: strip catalog_product_id, condition = used
    new_attrs=[]
    for a in attrs_src:
        aid=a.get("id","")
        if aid in ("SELLER_SKU",): continue
        if a.get("value_name") or a.get("value_id"):
            new_attrs.append({"id":aid,"value_name":a.get("value_name"),"value_id":a.get("value_id")})
    # Force condition=used
    new_attrs=[a for a in new_attrs if a["id"]!="ITEM_CONDITION"]
    new_attrs.append({"id":"ITEM_CONDITION","value_name":"Usado"})
    
    payload={
      "title":new_title,
      "category_id":cat,
      "price":499,
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
    
    print(f"  posting new item: title={new_title}",flush=True)
    p=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
    if "id" in p:
        new_id=p["id"]
        print(f"  ✅ POSTED: {new_id} status={p.get('status')} price=${p.get('price')}",flush=True)
        # Update description
        d=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",
                       headers=H,json={"plain_text":DESC_TMPL},timeout=15)
        print(f"  description: {d.status_code}",flush=True)
        print(f"  URL: {p.get('permalink','?')}",flush=True)
    else:
        print(f"  ❌ FAIL: {json.dumps(p)[:400]}",flush=True)
    time.sleep(1)
