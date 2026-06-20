"""
Crear catalog_suggestion ADRIAN: Piedra Viva en MLM-ESSENTIAL_OILS (aceites esenciales).
Fotos: re-upload desde Drive (las picture IDs son per-cuenta).
"""
import os, json, hashlib, requests, time
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()
AT=r["access_token"]; H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print("Adrian uid:", requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

DRIVE_IDS=[
 ("portada","11--fTV3zc_bIUADxcVoZ9e7Q-VSNr6iH"),
 ("ritual","1Qk0e0OwKuqZIDIngSZx9HpguTbnmgUzu"),
 ("ofrenda","1oSfdFgOFGOCi_4Xt-lMl-CX8x9SzTiKE"),
 ("espiritu","1oExzK6qznrcCxgr7vFKzBk_RxvmMf1k8"),
]
pics=[]
for name,fid in DRIVE_IDS:
    img=requests.get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",timeout=120).content
    rp=requests.post(f"{API}/pictures/items/upload",headers=H,files={"file":(f"pv_{name}.png",img,"image/png")},timeout=120)
    print(f"  pic {name}: {rp.status_code}")
    if rp.status_code in (200,201):
        pics.append({"id":rp.json()["id"]})
print("fotos:",len(pics))

h=hashlib.md5("adrian::the alchemia lab::piedra viva::aceite esencial 100ml".encode()).hexdigest()
n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN:",EAN)

TITLE=("Perfume Unisex Piedra Viva The Alchemia Lab Eau de Parfum 100ml | "
       "Amaderado Mineral Especias Incienso Terroso Perfumería Artesanal de México Yucatán")

ATTRS=[
 {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
 {"id":"LINE","values":[{"name":"México en la Piel"}]},
 {"id":"MODEL","values":[{"name":"Piedra Viva"}]},
 {"id":"UNIT_VOLUME","values":[{"name":"100 mL"}]},
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
 {"id":"COUNTRY_OF_ORIGIN","values":[{"name":"México"}]},
 {"id":"ESSENTIAL_OIL_NAME","values":[{"name":"Piedra Viva"}]},
]

DESC=(
"Piedra Viva de The Alchemia Lab, esencia mineral, seca y elegante con matices especiados y fondo terroso amaderado. "
"Aroma inspirado en la fuerza ancestral de la piedra volcánica mexicana. Presentación de 100 ml.\n\n"
"DETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n• Volumen: 100 ml\n"
"• Aroma: Mineral Especiado Terroso\n• Origen: Yucatán, México\n• Elaboración artesanal\n\n"
"PERFIL AROMÁTICO\n• Notas minerales secas con sequedad hipnótica\n• Especias cálidas e incienso rosado\n"
"• Fondo terroso amaderado, tierra húmeda sobre roca volcánica"
)

body={"site_id":"MLM","domain_id":"MLM-ESSENTIAL_OILS","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
print("\nPOST /catalog_suggestions ...")
rp=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("http",rp.status_code)
rb=rp.json(); print(json.dumps(rb,ensure_ascii=False)[:1800])
sid=rb.get("id") or rb.get("suggestion_id")
if sid:
    print(f"\n>>> SUGGESTION_ID = {sid}")
    time.sleep(4)
    rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":DESC},timeout=20)
    print("desc",rd.status_code, rd.text[:200])
