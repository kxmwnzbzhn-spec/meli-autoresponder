"""Update title of MLM2996221667 + create new listing with original brand mention."""
import os, requests, glob, time
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# === STEP 1: Update title of MLM2996221667 with Option A ===
EXISTING="MLM2996221667"
NEW_TITLE="Fragancia Masculina Premium Notas Doradas Amber Cuero 100ml"
print(f"\n=== Step 1: Update title MLM2996221667 ===")
print(f"  New title: '{NEW_TITLE}' ({len(NEW_TITLE)} chars)")
rt=requests.put(f"{API}/items/{EXISTING}",headers=HJ,json={"title":NEW_TITLE},timeout=15)
print(f"  HTTP {rt.status_code}: {rt.text[:300]}")

# === STEP 2: Get existing pictures from MLM2996221667 (reuse the 5 real images) ===
g=requests.get(f"{API}/items/{EXISTING}",headers=H,timeout=10).json()
existing_pics=g.get("pictures") or []
pic_ids=[p.get("id") for p in existing_pics if p.get("id")]
print(f"\n=== Reusing {len(pic_ids)} existing pictures ===")

# === STEP 3: Create new listing mentioning original brand "1 Million Gold" ===
NEW_LISTING_TITLE="1 Million Gold Hombre Edición Premium 100ml Notas Doradas"  # 58 chars
print(f"\n=== Step 2: Create new listing mentioning original brand ===")
print(f"  Title: '{NEW_LISTING_TITLE}' ({len(NEW_LISTING_TITLE)} chars)")

DESC = (
"1 MILLION GOLD | EDICIÓN PREMIUM HOMBRE | 100 ML\n\n"
"Inspiración: 1 Million Gold. Una composición masculina audaz, intensa y "
"adictiva con notas doradas que evocan poder, éxito y elegancia. Diseñada "
"para el hombre que destaca por su presencia magnética y su estilo refinado.\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Salida: mandarina, menta fresca, cítricos vibrantes\n"
"• Corazón: canela, cuero suave, notas especiadas cálidas\n"
"• Fondo: ámbar dorado, madera de cedro, pachulí, tabaco\n\n"
"CARACTERÍSTICAS\n"
"• Volumen: 100 ml\n"
"• Familia olfativa: Amaderada Especiada Oriental\n"
"• Concentración: Esencia premium de larga duración\n"
"• Marca: Genérico (inspiración original)\n"
"• Tipo: Fragancia masculina premium\n\n"
"OCASIONES DE USO\n"
"Perfecta para oficina, citas nocturnas, eventos sociales y ocasiones "
"especiales. Su excelente proyección y fijación la convierten en una "
"fragancia masculina premium versátil.\n\n"
"GARANTÍA Y ENVÍO\n"
"• Envío inmediato a todo México\n"
"• Garantía del vendedor: 30 días\n\n"
"PALABRAS CLAVE\n"
"1 million gold, fragancia hombre, fragancia masculina premium, "
"100ml hombre, notas doradas, amaderado oriental, amber cuero tabaco, "
"larga duración, esencia hombre premium."
)

payload={
    "title":NEW_LISTING_TITLE,
    "category_id":"MLM146239",
    "price":399,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":[{"id":pid} for pid in pic_ids],
    "attributes":[
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"SCENT","value_name":"Amaderado Especiado"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
print(f"\n[validate] HTTP {rv.status_code}: {rv.text[:600]}")

rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\n[POST] HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ NEW LISTING {iid}")
    print(f"  Permalink: {link}")
    rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"  [DESC] HTTP {rd.status_code}")
    
    # Priority replenish
    requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":iid,"account":"ADRIAN","default_qty":1,
              "product_name":NEW_LISTING_TITLE[:200]},timeout=10)
    # Audit
    requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
        json={"account":"ADRIAN","item_id":iid,"action_type":"publish_essential_oil_brand_mention",
              "from_value":"none","to_value":f"cat=MLM146239 price=399 brand_mention=1MillionGold",
              "actor":"claude_cowork",
              "details":"perfume genérico mencionando marca original 1 Million Gold en categoria aceites"},timeout=10)
    print("  [priority + log registered]")

# Verify new title applied
g2=requests.get(f"{API}/items/{EXISTING}",headers=H,timeout=10).json()
print(f"\n[VERIFY existing] {EXISTING} title='{g2.get('title')}'")
