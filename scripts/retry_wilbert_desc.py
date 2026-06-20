"""Reintentar descripción larga de las 2 sugerencias WILBERT (Mandarin Quetzal + Tláloc)."""
import os, sys, requests, time
sys.path.insert(0, "scripts")
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.get_access_token("WILBERT")
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

DESCS = {
 "MLM5545598222": ("Mandarin Quetzal de The Alchemia Lab — perfume de la colección México en la Piel. Eau de Parfum 100 ml unisex, "
   "elaboración artesanal mexicana de Yucatán. Aroma frutal floral con corazón de jazmín y durazno, fondo aterciopelado de almizcle.\n\n"
   "DETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n• Nombre: Mandarin Quetzal\n"
   "• Eau de Parfum 100 ml\n• Unisex\n• Origen: Yucatán, México\n• Elaboración artesanal\n\n"
   "PIRÁMIDE\n• Salida: mandarina, durazno\n• Corazón: flor jazmín\n• Fondo: almizcle aterciopelado\n\n"
   "PRESENTACIÓN\nBotella ámbar con etiquetado artesanal. Eau de Parfum, formato spray, 100 ml."),
 "MLM5545598280": ("Tláloc Intenso de The Alchemia Lab — perfume de la colección México en la Piel. Eau de Parfum 100 ml unisex, "
   "elaboración artesanal mexicana de Yucatán. Aroma amaderado frutal con notas de piña y bergamota, fondo de pachulí y maderas.\n\n"
   "DETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n• Nombre: Tláloc Intenso\n"
   "• Eau de Parfum 100 ml\n• Unisex\n• Origen: Yucatán, México\n• Elaboración artesanal\n\n"
   "PIRÁMIDE\n• Salida: bergamota, piña\n• Corazón: especias frutales\n• Fondo: madera, pachulí\n\n"
   "PRESENTACIÓN\nBotella ámbar con etiquetado artesanal. Eau de Parfum, formato spray, 100 ml."),
}

for sid, desc in DESCS.items():
    for attempt in (1,2,3):
        r=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":desc},timeout=25)
        print(f"{sid} attempt{attempt}: {r.status_code} {r.text[:150]}")
        if r.status_code in (200,201): break
        time.sleep(8)
