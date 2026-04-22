import os,requests
BT=os.environ["TELEGRAM_BOT_TOKEN"]
CID=os.environ["TELEGRAM_CHAT_ID"]
msg="""💰 *Saldo estimado Mercado Pago — Juan (Sonix Mx)*

Base: 92 ordenes pagadas.

```
Estado              #        Bruto
delivered           2    $    798.00
shipped            23    $  8,477.00
ready_to_ship      66    $ 44,205.40
pending             1    $    549.00
-------------------------------
TOTAL              92    $ 54,029.40
```

*💵 Ya disponible (entregadas):*        `$798.00`
*🚚 Retenido (en camino):*              `$52,682.40`
*📦 Pendiente (por despachar):*         `$549.00`
*📊 TOTAL BRUTO NETO:*                  `$54,029.40`

⚠️ *Nota:* Este es el total bruto de las ventas. MELI descontará:
- Comisión ~16% (~$8,644)
- Costo envío gratis (~$80 x orden = ~$7,360)
- *Neto real despues de fees: ~$38,025*

MELI libera cada pago ~14 dias despues de confirmada la entrega.

_Para saldo exacto consulta https://www.mercadopago.com.mx/activities_"""
r=requests.post(f"https://api.telegram.org/bot{BT}/sendMessage",json={"chat_id":CID,"text":msg,"parse_mode":"Markdown"})
print(r.status_code, r.text[:200])
