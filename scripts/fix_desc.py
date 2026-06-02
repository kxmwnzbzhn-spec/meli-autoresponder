import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

DESC=("Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA. Diseñados para máxima comodidad y ajuste perfecto durante todo el día.\n\n"
      "🔹 CARACTERISTICAS\n"
      "- Marca: Calvin Klein\n"
      "- Modelo: Brief\n"
      "- Material: Microfibra sedosa de alta calidad\n"
      "- Colores incluidos: Negro, gris oxford y gris cemento (mixto)\n"
      "- Cantidad por pack: 3 boxers\n"
      "- Cintura con elastico ancho y logo Calvin Klein\n\n"
      "🔹 GUIA DE TALLAS (CK Hombre)\n"
      "- Talla S: Cintura 71-76 cm | Cadera 86-91 cm | Peso 55-65 kg\n"
      "- Talla M: Cintura 81-86 cm | Cadera 94-99 cm | Peso 65-75 kg\n"
      "- Talla L: Cintura 91-97 cm | Cadera 102-107 cm | Peso 75-85 kg\n\n"
      "🔹 IMPORTADOS DE USA - 100% original Calvin Klein.\n"
      "🔹 Envio inmediato. Garantia 30 dias por defectos de fabricacion.")

ITEMS=["MLM5444637526","MLM5444848314","MLM5444797814"]
for iid in ITEMS:
    # Try POST first (creates), then PUT (updates)
    r1=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"{iid} POST: HTTP {r1.status_code}: {r1.text[:200]}")
    if r1.status_code not in (200,201):
        r2=requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
        print(f"{iid} PUT: HTTP {r2.status_code}: {r2.text[:200]}")
