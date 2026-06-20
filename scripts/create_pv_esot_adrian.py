"""
Crear catalog_suggestion ADRIAN: Piedra Viva en MLM-ESOTERIC_PERFUMES (Perfumes esotéricos).
Solo BRAND y MODEL son catalog_required → atributos mínimos + algunos opcionales útiles.
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

# EAN nuevo distinto del de aceites
h=hashlib.md5("adrian::tal::piedra viva::esoterico::100ml::ritual yucateco".encode()).hexdigest()
n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
EAN=b+str((10-(s%10))%10); print("EAN:",EAN)

TITLE=("Perfume Esotérico Piedra Viva The Alchemia Lab 100ml | "
       "Ritual Mineral Ancestral Ofrenda Yucatán Perfumería Artesanal Mexicana Espíritu Volcánico Unisex")

ATTRS=[
 {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
 {"id":"MODEL","values":[{"name":"Piedra Viva 100ml"}]},
 {"id":"GTIN","values":[{"name":EAN}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]

DESC=(
"Piedra Viva — perfume esotérico de The Alchemia Lab, parte de la colección México en la Piel. Una fragancia ritual "
"inspirada en la fuerza ancestral de la piedra volcánica yucateca: mineral, seca, especiada y profundamente terrosa. "
"Eau de Parfum 100 ml unisex de perfumería artesanal mexicana.\n\n"
"DETALLES\n"
"• Marca: The Alchemia Lab\n"
"• Colección: México en la Piel\n"
"• Nombre: Piedra Viva\n"
"• Eau de Parfum 100 ml\n"
"• Unisex / Sin género\n"
"• Origen: Yucatán, México\n"
"• Elaboración artesanal en pequeñas tiradas\n"
"• Concebido como objeto ritual y ofrenda olfativa\n\n"
"CARÁCTER OLFATIVO\n"
"• Apertura: notas minerales secas con sequedad hipnótica\n"
"• Corazón: especias cálidas, incienso rosado, aromas terrosos\n"
"• Fondo: madera ahumada que evoca tierra húmeda sobre roca volcánica\n\n"
"RITUAL DE USO\n"
"• Aplicar en puntos de pulso al inicio del día o antes de cualquier rito personal\n"
"• Ideal para meditación, escritura, ceremonias íntimas y como ofrenda olfativa\n"
"• Layering con resinas (incienso, mirra) o maderas (sándalo, oud)\n\n"
"IDEAL PARA\n"
"• Coleccionistas de perfumería de autor mexicana\n"
"• Amantes de fragancias minerales, terrosas y especiadas\n"
"• Personalidades distintivas con afinidad por lo ancestral y lo ritual\n\n"
"PRESENTACIÓN\n"
"Botella ámbar con etiquetado artesanal. Eau de Parfum, formato spray, 100 ml."
)

body={"site_id":"MLM","domain_id":"MLM-ESOTERIC_PERFUMES","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
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
