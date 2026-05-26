import os, requests
import meli_token
NID="MLM2956944279"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
desc=(
"IMPORTANTE - LEE ANTES DE COMPRAR\n\n"
"El COLOR seleccionado al momento de la compra NO SE GARANTIZA. "
"Este producto se envia con COLOR ALEATORIO segun disponibilidad en almacen. "
"Si el color es decisivo para ti, por favor NO realices la compra; cualquier reclamo "
"por color recibido NO procedera.\n\n"
"---\n\n"
"BOCINA BLUETOOTH PORTATIL - Calidad Premium\n\n"
"- Diseno compacto y ultra portatil, ideal para llevar a cualquier lugar.\n"
"- Bluetooth 5.3 con conexion rapida y estable.\n"
"- Resistente al agua y polvo (IP67).\n"
"- Sonido potente con bajos profundos.\n"
"- Bateria recargable de larga duracion.\n"
"- Acabado y materiales premium.\n\n"
"Producto OEM/generico - no se trata de marca original. Se incluye 1 cable de carga.\n\n"
"Envio inmediato. Cualquier duda, contactanos antes de comprar."
)
for method in ("PUT","POST"):
    fn=requests.put if method=="PUT" else requests.post
    r=fn(f"{API}/items/{NID}/description",headers=HJ,json={"plain_text":desc},timeout=30)
    print(f"{method} -> http={r.status_code} {('' if r.status_code<300 else r.text[:400])}")
    if r.status_code<300: break
g=requests.get(f"{API}/items/{NID}/description",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
print("desc snippet:",(g.get("plain_text") or "")[:120])
print("DONE")
