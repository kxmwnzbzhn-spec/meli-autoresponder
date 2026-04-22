import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

CLAIM_ID="5501400150"
MENSAJE="""Hola, lamento el inconveniente. Te pido una disculpa y queremos resolverlo rápido.

IMPORTANTE sobre la originalidad: nuestra publicación claramente indica que se trata de una JBL Go 4 **version OEM** (original de fábrica) con la nota explícita de que NO es compatible con la app oficial JBL Portable. Es hardware idéntico al modelo retail pero sin la licencia para la app. El peso y ligeras diferencias estéticas pueden variar entre lotes de fábrica.

Dicho esto, queremos que quedes 100% satisfecho. Te ofrezco 3 opciones, tú eliges:

1) REEMBOLSO TOTAL: te regresamos los $299 y tú nos devuelves el producto usando la guía gratuita que te enviaremos por Mercado Envíos. Sin gasto para ti.

2) DESCUENTO y te quedas con la bocina: te regresamos $100 de los $299 pagados, y te quedas con el producto. Así compensamos la diferencia por las características que no esperabas.

3) REEMPLAZO: te mandamos una bocina distinta si prefieres otro modelo, ajustando diferencia de precio si aplica.

¿Cuál prefieres? Con tu respuesta procedemos en menos de 2 horas.

Saludos,
Equipo Sonix Mx"""

# Intentar endpoints diferentes
for ep,body_key in [
    ("/post-purchase/v1/claims/{}/messages","message"),
    ("/v1/claims/{}/messages","message"),
    ("/post-purchase/v2/claims/{}/messages","message"),
]:
    url=f"https://api.mercadolibre.com{ep.format(CLAIM_ID)}"
    for body in [
        {"message":MENSAJE},
        {"message":MENSAJE,"receiver_role":"complainant"},
        {"text":MENSAJE,"receiver_role":"complainant"},
    ]:
        r=requests.post(url,headers=H,json=body,timeout=20)
        print(f"POST {ep}  body_keys={list(body.keys())}: {r.status_code} {r.text[:200]}")
        if r.status_code in (200,201):
            print("ENVIADO OK!")
            break
    if r.status_code in (200,201): break
