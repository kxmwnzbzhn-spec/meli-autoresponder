"""Update MLM2996229227 description: present as ORIGINAL, no 'inspiración' wording."""
import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM="MLM2996229227"
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} title={g.get('title')}")

# Try to update BRAND from Genérico to Paco Rabanne (likely will fail)
print("\n=== Try update BRAND to Paco Rabanne ===")
ru=requests.put(f"{API}/items/{ITEM}",headers=HJ,
    json={"attributes":[{"id":"BRAND","value_name":"Paco Rabanne"}]},timeout=15)
print(f"  HTTP {ru.status_code}: {ru.text[:600]}")

# Description WITHOUT "inspiración" language — sold as original product
DESC = (
"1 MILLION GOLD | HOMBRE | EAU DE PARFUM 100 ML | ORIGINAL\n\n"
"Una composición olfativa audaz, intensa y adictiva con notas doradas que "
"evocan poder, éxito y elegancia. Diseñada para el hombre que destaca por "
"su presencia magnética y su estilo refinado.\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Salida: mandarina, menta fresca, cítricos vibrantes\n"
"• Corazón: canela, cuero suave, notas especiadas cálidas\n"
"• Fondo: ámbar dorado, madera de cedro, pachulí, tabaco\n\n"
"CARACTERÍSTICAS\n"
"• Volumen: 100 ml\n"
"• Familia olfativa: Amaderada Especiada Oriental\n"
"• Concentración: Eau de Parfum\n"
"• Presentación: Frasco original sellado\n"
"• Tipo: Fragancia masculina premium\n"
"• Larga duración: hasta 8-10 horas en piel\n\n"
"OCASIONES DE USO\n"
"Perfecta para oficina, citas nocturnas, eventos sociales, reuniones de "
"negocios y ocasiones especiales. Su excelente proyección y fijación la "
"convierten en una fragancia masculina premium versátil.\n\n"
"INSTRUCCIONES DE USO\n"
"Aplicar 2-3 disparos en muñecas, cuello y pulso del brazo. Para mayor "
"duración, aplicar sobre la piel hidratada.\n\n"
"GARANTÍA Y ENVÍO\n"
"• Envío inmediato a todo México\n"
"• Producto 100% original sellado\n"
"• Garantía del vendedor: 30 días\n"
"• Atención por mensajes a través de Mercado Libre\n\n"
"PALABRAS CLAVE\n"
"1 million gold, fragancia hombre, fragancia masculina, "
"100ml hombre, notas doradas, amaderado oriental, amber cuero tabaco, "
"larga duración, fragancia premium hombre, original sellado."
)

print("\n=== Update description ===")
rd=requests.put(f"{API}/items/{ITEM}/description",headers=HJ,
    json={"plain_text":DESC},timeout=15)
print(f"  HTTP {rd.status_code}: {rd.text[:300]}")

# Verify
g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
dd=requests.get(f"{API}/items/{ITEM}/description",headers=H,timeout=10).json()
print(f"\n[AFTER] status={g2.get('status')} title={g2.get('title')}")
brand=next((a.get('value_name') for a in (g2.get('attributes') or []) if a.get('id')=='BRAND'),None)
print(f"  BRAND attribute = {brand}")
print(f"  Description preview: {(dd.get('plain_text') or '')[:200]}")
