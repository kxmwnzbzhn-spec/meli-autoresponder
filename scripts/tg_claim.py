import os,requests
BT=os.environ["TELEGRAM_BOT_TOKEN"]
CID=os.environ["TELEGRAM_CHAT_ID"]
msg="""🚨 *PLAYBOOK RECLAMO ACTIVADO*

*Claim:* `5501400150` (PDD9943)
*Stage:* `opened/claim`
*Producto:* JBL Go 4 Bocina Bluetooth Camuflaje Original Usada
*Monto:* $299
*Comprador:* CRLS\\_DAVID (id 21502445)

*Motivo del comprador (texto exacto):*
_"No es original. El peso y los detalles son distintos al original, no lo detecta la app oficial."_

El comprador adjuntó 1 imagen.

⚠️ *ACCIÓN OBLIGATORIA en las próximas 48h:* responder al comprador.

Los endpoints API de MELI para enviar mensajes al claim están rechazando (limitación de scope de nuestra app).

*👉 Abre MELI web → Ventas → Reclamos → Claim 5501400150 y copia-pega este mensaje:*

```
Hola, lamento el inconveniente con tu bocina JBL Go 4.

Queremos resolverlo rápido. Nuestra publicación indica claramente que es versión OEM de fábrica (NO compatible con la app oficial JBL Portable por no tener la licencia retail). El hardware es 100% original, pero puede presentar pequeñas diferencias estéticas y de peso entre lotes de fábrica.

Te ofrezco 3 opciones, tú eliges:

1) REEMBOLSO TOTAL: te regresamos los $299 y tú nos devuelves el producto usando guía gratuita por Mercado Envíos. Sin gasto.

2) DESCUENTO de $100 y te quedas con la bocina: te regresamos $100 y te la quedas. Compensamos la diferencia.

3) REEMPLAZO por otro modelo si prefieres.

¿Cuál prefieres? Respondemos en menos de 2 horas.

Saludos,
Equipo Sonix Mx
```

*Acciones disponibles en el claim:*
- send\\_message\\_to\\_complainant (*obligatoria ahora*)
- refund
- open\\_dispute
- allow\\_return

Estado: `claim_states[5501400150]` registrado en el bot."""
r=requests.post(f"https://api.telegram.org/bot{BT}/sendMessage",json={"chat_id":CID,"text":msg,"parse_mode":"Markdown"})
print(r.status_code, r.text[:200])
