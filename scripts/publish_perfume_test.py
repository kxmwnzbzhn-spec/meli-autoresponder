"""Generate 4 perfume placeholder JPGs + upload to MELI + publish in MLM146239 Adrián."""
import os, requests, io
from PIL import Image, ImageDraw, ImageFont

API="https://api.mercadolibre.com"

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# === 1) Generate 4 placeholder bottles ===
def font(sz,bold=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p,sz) if os.path.exists(p) else ImageFont.load_default()

def bottle(label_text, accent_color, view):
    W,H = 1000,1000
    img = Image.new("RGB",(W,H),"white")
    d = ImageDraw.Draw(img)
    for y in range(H):
        c = 255 - int(20*(y/H)); d.line([(0,y),(W,y)], fill=(c,c,c))
    cx, cy = W//2, H//2+50
    if view=="back":
        cx += 40
    elif view=="angle":
        cx -= 30; cy += 20
    d.ellipse([cx-180, cy+220, cx+180, cy+260], fill=(180,180,180))
    d.rectangle([cx-130, cy-200, cx+130, cy+230], fill=(20,20,30), outline=(10,10,15), width=3)
    d.rectangle([cx-50, cy-260, cx+50, cy-200], fill=(15,15,20), outline=(10,10,15), width=3)
    d.rectangle([cx-60, cy-320, cx+60, cy-260], fill=accent_color, outline=(0,0,0), width=3)
    d.rectangle([cx-110, cy-50, cx+110, cy+150], fill=(240,240,240), outline=(80,80,80), width=2)
    F1=font(36,True); F2=font(22,False); F3=font(28,True); F4=font(30,False)
    b=d.textbbox((0,0),label_text,font=F1); tw=b[2]-b[0]
    d.text((cx-tw//2,cy+10),label_text,font=F1,fill=(20,20,30))
    sub="Esencia premium"
    b=d.textbbox((0,0),sub,font=F2); tw=b[2]-b[0]
    d.text((cx-tw//2,cy+60),sub,font=F2,fill=(80,80,80))
    vol="30 ml"
    b=d.textbbox((0,0),vol,font=F3); tw=b[2]-b[0]
    d.text((cx-tw//2,cy+105),vol,font=F3,fill=accent_color)
    d.text((40,H-60),"Genérico",font=F4,fill=(120,120,120))
    buf=io.BytesIO(); img.save(buf,"JPEG",quality=90); buf.seek(0)
    return buf

views=[("front",(200,80,120)),("angle",(200,80,120)),("label",(200,80,120)),("back",(200,80,120))]

# === 2) Upload to MELI ===
print("\n=== Upload pictures to MELI ===")
picture_ids=[]
for i,(view,color) in enumerate(views):
    buf = bottle("FLORAL", color, view)
    files={"file": (f"perfume_{i+1}.jpg", buf.getvalue(), "image/jpeg")}
    rr=requests.post(f"{API}/pictures/items/upload",
        headers={"Authorization":f"Bearer {AT}"},files=files,timeout=20)
    print(f"  [{i+1}/4 {view}] HTTP {rr.status_code}: {rr.text[:200]}")
    if rr.status_code in (200,201):
        pid=rr.json().get("id")
        if pid: picture_ids.append(pid)

print(f"\nUploaded pictures: {picture_ids}")

# === 3) POST item ===
TITLE = "Aceite Esencial Perfumado Notas Florales 30ml Esencia"  # 53 chars
DESC = (
"Aceite esencial perfumado con notas florales. Aroma duradero, "
"presentación premium en frasco de 30 ml. "
"Producto genérico — ideal para uso personal o como ingrediente "
"en aromaterapia, difusores, sales de baño, velas artesanales.\n\n"
"CARACTERISTICAS\n"
"- Volumen: 30 ml\n"
"- Familia olfativa: Floral\n"
"- Marca: Genérico\n"
"- Concentración: Esencia premium\n\n"
"Envío inmediato. Garantía del vendedor 30 días."
)

payload = {
    "title": TITLE,
    "category_id": "MLM146239",
    "price": 99,
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_special",
    "pictures": [{"id":pid} for pid in picture_ids],
    "attributes": [
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"SCENT","value_name":"Floral"},
    ],
    "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms": [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items/validate ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
print(f"HTTP {rv.status_code}: {rv.text[:1000]}")

print("\n=== POST /items (real) ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ PUBLISHED {iid}")
    print(f"  Permalink: {link}")
    print(f"  Price: ${it.get('price')}  Status: {it.get('status')}")
    rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"  [DESC] HTTP {rd.status_code}: {rd.text[:200]}")
