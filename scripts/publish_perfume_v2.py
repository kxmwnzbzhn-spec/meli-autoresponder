"""Publish 2nd test perfume — gold/oriental themed, in MLM146239 Adrián, SEO title/desc."""
import os, requests, io
from PIL import Image, ImageDraw, ImageFont

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

def font(sz,bold=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p,sz) if os.path.exists(p) else ImageFont.load_default()

GOLD = (212,175,55)
DARK_GOLD = (180,140,30)
BLACK = (18,15,10)

def gold_bottle(label_text, view):
    W,H = 1000,1000
    img = Image.new("RGB",(W,H),"white")
    d = ImageDraw.Draw(img)
    # Warm gradient bg
    for y in range(H):
        v = 250 - int(15*(y/H))
        d.line([(0,y),(W,y)], fill=(v,v-3,v-8))
    cx, cy = W//2, H//2+30
    if view=="back": cx += 60
    elif view=="angle": cx -= 50; cy += 20
    elif view=="detail":
        # Close-up: bigger bottle
        pass
    # Drop shadow
    d.ellipse([cx-200, cy+240, cx+200, cy+280], fill=(200,195,185))
    # Bottle body — squared, dark glass
    d.rectangle([cx-150, cy-210, cx+150, cy+250], fill=BLACK, outline=(5,3,0), width=3)
    # Bottle gold band middle
    d.rectangle([cx-150, cy+30, cx+150, cy+60], fill=DARK_GOLD)
    # Neck
    d.rectangle([cx-55, cy-270, cx+55, cy-210], fill=(10,8,4), outline=(5,3,0), width=2)
    # Gold cap with rounded look
    d.rectangle([cx-75, cy-355, cx+75, cy-270], fill=GOLD, outline=DARK_GOLD, width=3)
    # Cap detail line
    d.rectangle([cx-75, cy-310, cx+75, cy-305], fill=DARK_GOLD)
    # Label — gold framed
    d.rectangle([cx-115, cy-100, cx+115, cy+15], fill=BLACK, outline=GOLD, width=3)
    F1=font(38,True); F2=font(20,False); F3=font(28,True); F4=font(26,False)
    b=d.textbbox((0,0),label_text,font=F1); tw=b[2]-b[0]
    d.text((cx-tw//2,cy-70),label_text,font=F1,fill=GOLD)
    sub="Notas Doradas"
    b=d.textbbox((0,0),sub,font=F2); tw=b[2]-b[0]
    d.text((cx-tw//2,cy-25),sub,font=F2,fill=(230,210,150))
    # Volume on bottle body below label
    vol="100 ML"
    b=d.textbbox((0,0),vol,font=F3); tw=b[2]-b[0]
    d.text((cx-tw//2,cy+150),vol,font=F3,fill=GOLD)
    # Brand watermark
    d.text((40,H-60),"Genérico",font=F4,fill=(140,130,110))
    # Soft highlight on bottle
    for i in range(4):
        d.line([(cx-130, cy-200+i), (cx-130, cy+230)], fill=(60,50,30))
    buf=io.BytesIO(); img.save(buf,"JPEG",quality=90); buf.seek(0)
    return buf

views=[("front","HOMBRE"),("angle","HOMBRE"),("detail","HOMBRE"),("back","HOMBRE")]

print("=== Uploading 4 pictures to MELI ===")
picture_ids=[]
for i,(view,label) in enumerate(views):
    buf = gold_bottle(label, view)
    files={"file": (f"perfume_oro_{i+1}.jpg", buf.getvalue(), "image/jpeg")}
    rr=requests.post(f"{API}/pictures/items/upload",
        headers={"Authorization":f"Bearer {AT}"},files=files,timeout=20)
    if rr.status_code in (200,201):
        pid=rr.json().get("id")
        if pid:
            picture_ids.append(pid)
            print(f"  [{i+1}/4 {view}] ✅ {pid}")
        else:
            print(f"  [{i+1}/4 {view}] HTTP {rr.status_code}: no id")
    else:
        print(f"  [{i+1}/4 {view}] ❌ HTTP {rr.status_code}: {rr.text[:160]}")

print(f"\nTotal uploaded: {len(picture_ids)}")

# === SEO Title (≤60 chars) + Description ===
TITLE = "Aceite Esencial Perfumado Hombre Notas Doradas 100ml"  # 52 chars
SCENT_VALUE = "Amaderado Especiado"
DESC = (
"ACEITE ESENCIAL PERFUMADO PARA HOMBRE | NOTAS DORADAS PREMIUM | 100 ML\n\n"
"Esencia masculina amaderada, especiada y oriental. Una composición olfativa "
"intensa diseñada para acompañarte todo el día con presencia magnética y "
"elegante. Su mezcla equilibrada de notas cálidas y notas amaderadas la hace "
"versátil para uso diario, oficina y ocasiones especiales.\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Salida: mandarina, menta fresca, notas cítricas vibrantes\n"
"• Corazón: canela, cuero suave, notas especiadas cálidas\n"
"• Fondo: ámbar, madera de cedro, pachulí, tabaco dorado\n\n"
"CARACTERÍSTICAS\n"
"• Volumen: 100 ml\n"
"• Familia olfativa: Amaderada Especiada Oriental\n"
"• Concentración: Esencia premium de larga duración\n"
"• Tipo: Aceite esencial perfumado para hombre / unisex\n"
"• Estilo de fragancia: Cálido, masculino, intenso, sofisticado\n\n"
"OCASIONES DE USO\n"
"Perfecta para la oficina, citas nocturnas, eventos sociales, reuniones de "
"negocios y uso diario. Su excelente proyección y fijación la convierten en "
"una opción de fragancia masculina premium.\n\n"
"INSTRUCCIONES DE USO\n"
"Aplicar 2-3 disparos en muñecas, cuello y pulso del brazo. Para mayor "
"duración, aplicar sobre la piel hidratada.\n\n"
"GARANTÍA Y ENVÍO\n"
"• Envío inmediato a todo México\n"
"• Garantía del vendedor: 30 días por cualquier defecto\n"
"• Atención por mensajes a través de Mercado Libre\n\n"
"PALABRAS CLAVE\n"
"perfume hombre, aceite esencial perfumado, fragancia masculina, "
"amaderada oriental, larga duración, 100ml premium, esencia premium hombre, "
"perfume amaderado especiado, fragancia con cuero, notas tabaco, "
"perfume oficina noche, regalo hombre fragancia."
)

payload = {
    "title": TITLE,
    "category_id": "MLM146239",
    "price": 299,
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_special",
    "pictures": [{"id":pid} for pid in picture_ids],
    "attributes": [
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"SCENT","value_name":SCENT_VALUE},
    ],
    "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms": [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ PUBLISHED {iid}")
    print(f"  Permalink: {link}")
    print(f"  Price: ${it.get('price')}  Status: {it.get('status')}")
    rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"  [DESC] HTTP {rd.status_code}")
    # Priority replenish + log
    requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":iid,"account":"ADRIAN","default_qty":1,
              "product_name":TITLE[:200]},timeout=10)
    requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
        json={"account":"ADRIAN","item_id":iid,"action_type":"publish_essential_oil",
              "from_value":"none","to_value":f"cat=MLM146239 price=299",
              "actor":"claude_cowork",
              "details":"perfume oro/oriental en aceites esenciales SEO"},timeout=10)
    print("  [priority + log registered]")
