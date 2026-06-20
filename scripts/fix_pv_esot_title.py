"""
Quitar la palabra 'Esotérico' del título de MLM3034200499.
Intenta PUT primero; si falla, DELETE + recreate con título limpio.
"""
import os, json, hashlib, requests, time
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
AT=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

SID_OLD="MLM3034200499"
NEW_TITLE=("Perfume Piedra Viva The Alchemia Lab Eau de Parfum 100ml | "
           "Mineral Ancestral Especias Incienso Madera Terrosa Yucatán Perfumería Artesanal Mexicana Unisex")

# 1) GET state
r=requests.get(f"{API}/catalog_suggestions/{SID_OLD}",headers=H,timeout=20)
print("GET old:",r.status_code, json.dumps(r.json(),ensure_ascii=False)[:400])

# 2) try PUT title
print("\n--- PUT title ---")
rp=requests.put(f"{API}/catalog_suggestions/{SID_OLD}",headers=HJ,json={"title":NEW_TITLE},timeout=20)
print("PUT:",rp.status_code, rp.text[:300])

if rp.status_code in (200,201):
    print("Title updated OK")
    raise SystemExit(0)

# 3) si no, DELETE
print("\n--- DELETE ---")
rd=requests.delete(f"{API}/catalog_suggestions/{SID_OLD}",headers=H,timeout=20)
print("DELETE:",rd.status_code, rd.text[:300])

# 4) recrear con título limpio, nueva EAN para no duplicar
DRIVE_IDS=[
 ("portada","11--fTV3zc_bIUADxcVoZ9e7Q-VSNr6iH"),
 ("ritual","1Qk0e0OwKuqZIDIngSZx9HpguTbnmgUzu"),
 ("ofrenda","1oSfdFgOFGOCi_4Xt-lMl-CX8x9SzTiKE"),
 ("espiritu","1oExzK6qznrcCxgr7vFKzBk_RxvmMf1k8"),
]
pics=[]
for name,fid in DRIVE_IDS:
    img=requests.get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",timeout=120).content
    rpi=requests.post(f"{API}/pictures/items/upload",headers=H,files={"file":(f"pv_{name}.png",img,"image/png")},timeout=120)
    print(f"  pic {name}: {rpi.status_code}")
    if rpi.status_code in (200,201): pics.append({"id":rpi.json()["id"]})

h=hashlib.md5("adrian::tal::piedra viva::esot v2 sin palabra::100ml".encode()).hexdigest()
n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN:",EAN)

ATTRS=[
 {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
 {"id":"MODEL","values":[{"name":"Piedra Viva 100ml"}]},
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]
DESC=(
"Piedra Viva — perfume de The Alchemia Lab, parte de la colección México en la Piel. Fragancia inspirada en la "
"fuerza ancestral de la piedra volcánica yucateca: mineral, seca, especiada y profundamente terrosa. Eau de Parfum "
"100 ml unisex de perfumería artesanal mexicana.\n\n"
"DETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n• Nombre: Piedra Viva\n"
"• Eau de Parfum 100 ml\n• Unisex\n• Origen: Yucatán, México\n• Elaboración artesanal\n\n"
"CARÁCTER OLFATIVO\n• Apertura: notas minerales secas con sequedad hipnótica\n"
"• Corazón: especias cálidas, incienso rosado, aromas terrosos\n"
"• Fondo: madera ahumada que evoca tierra húmeda sobre roca volcánica\n\n"
"IDEAL PARA\n• Coleccionistas de perfumería de autor mexicana\n"
"• Amantes de fragancias minerales, terrosas y especiadas\n"
"• Personalidades distintivas\n\nPRESENTACIÓN\nBotella ámbar con etiquetado artesanal. Eau de Parfum, spray, 100 ml."
)
body={"site_id":"MLM","domain_id":"MLM-ESOTERIC_PERFUMES","type":"EDIT","title":NEW_TITLE,"attributes":ATTRS,"pictures":pics}
print("\nPOST recreate ...")
rp2=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("http",rp2.status_code)
rb=rp2.json(); print(json.dumps(rb,ensure_ascii=False)[:1500])
sid=rb.get("id") or rb.get("suggestion_id")
if sid:
    print(f"\n>>> NEW SUGGESTION_ID = {sid}")
    time.sleep(4)
    rd2=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":DESC},timeout=20)
    print("desc",rd2.status_code, rd2.text[:200])
