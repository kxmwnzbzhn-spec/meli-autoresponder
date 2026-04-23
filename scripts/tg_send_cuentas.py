import os,requests,json
TOK=os.environ["TELEGRAM_BOT_TOKEN"]
CHAT=os.environ["TELEGRAM_CHAT_ID"]

MSG="""🗂 *Cuentas MELI conectadas a la app*

*App ID:* `5211907102822632`

━━━━━━━━━━━━━━━━

*1. JUAN* (principal)
• Nickname: `HFCBHDGAE33468`
• Secret: `MELI_REFRESH_TOKEN`
• Uso: JBL Go 4 unificada MLM2883448187 ($599, 6 variantes)
• Estado: ✅ Gold power seller

*2. CLARIBEL*
• Nickname: `CX20260420180750`
• Secret: `MELI_REFRESH_TOKEN_CLARIBEL`
• Uso: Clones perfumes + bocinas
• Estado: ✅ Activa

*3. ASVA ELECTRONICS* (nueva hoy)
• User ID: `1668713481`
• Nickname: `ASVAELECTRONICS`
• Secret: `MELI_REFRESH_TOKEN_ASVA`
• Uso: Flip 7 genérica $299 x 4 colores
• Estado: ✅ Activa (498u disponibles)
  - Negro: MLM5233480022 (179u)
  - Azul: MLM5233454100 (82u)
  - Rojo: MLM2886030837 (35u)
  - Morado: MLM2886136351 (202u)
• Pendiente: activar MercadoAds + FULL

*4. RAYMUNDO SANTA CRUZ GÓMEZ*
• User ID: `3338633403`
• Nickname: `RG20260415180857`
• Email: enviamesantacruz1@gmail.com
• Secret: `MELI_REFRESH_TOKEN_RAYMUNDO` ⚠️ PENDIENTE
• Estado: OAuth hecho, refresh\\_token no persistido (GH\\_PAT vacío)
• Acción: generar nuevo code desde link de auth

━━━━━━━━━━━━━━━━

*Link auth nueva cuenta:*
https://auth.mercadolibre.com.mx/authorization?response\\_type=code&client\\_id=5211907102822632&redirect\\_uri=https://oauth.pstmn.io/v1/callback

*Secrets GitHub:*
• MELI\\_APP\\_ID, MELI\\_APP\\_SECRET
• MELI\\_REFRESH\\_TOKEN (Juan)
• MELI\\_REFRESH\\_TOKEN\\_CLARIBEL
• MELI\\_REFRESH\\_TOKEN\\_ASVA
• MELI\\_REFRESH\\_TOKEN\\_RAYMUNDO ⚠️
• TELEGRAM\\_BOT\\_TOKEN, TELEGRAM\\_CHAT\\_ID"""

r=requests.post(f"https://api.telegram.org/bot{TOK}/sendMessage",
    json={"chat_id":CHAT,"text":MSG,"parse_mode":"Markdown","disable_web_page_preview":True})
print(f"send: {r.status_code}")
if r.status_code!=200:
    print(r.text[:600])
