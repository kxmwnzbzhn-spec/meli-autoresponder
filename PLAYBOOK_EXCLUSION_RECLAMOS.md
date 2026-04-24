# PLAYBOOK EXCLUSIÓN DE RECLAMOS MELI — Validado y funcionando

## Los 5 puntos que MELI evalúa para excluir un reclamo

1. **Motivo sin evidencia técnica del comprador** → percepción subjetiva (no peritaje)
2. **Respuesta consistente y transparente** → responder siempre, tono cordial, sin evasivas
3. **Evidencia verificable del producto** → serial SN, UPC, EAN, fotos de caja
4. **Canales oficiales de verificación** → portal marca, teléfono oficial, peritaje autorizado
5. **Alternativas razonables (buena fe)** → devolución voluntaria + reembolso condicional si canal oficial confirma

## Caso validado
- **Reclamo 5502336104** (Go 4 Negra Usada, comprador afirmó "no es original")
- Bot MELI excluyó exitosamente el 24-abr-2026
- Aplicamos los 5 puntos en 3 mensajes ≤350 chars + Solicitud de Exclusión

## Plantillas maestras (≤350 chars c/u)

### Mensaje 1 — Saludo + confirmación originalidad
Hola, buen dia. Gracias por su compra y por comunicarse. Le confirmo que el producto es original y fue enviado como [CONDICION] en buen estado, tal como se describe en la publicacion. Puede validar el serial SN en [portal_oficial] o llamando a [telefono]. Quedo atento a cualquier duda. Saludos cordiales.

### Mensaje 2 — Devolución amigable
Si prefiere no conservar el producto, con gusto procesamos una devolucion voluntaria. Le pido que envie con su empaque y accesorios completos. Al recibirlo verifico el estado y procesamos el reembolso correspondiente. Mi intencion es resolver de forma amistosa. Quedo atento a su preferencia.

### Mensaje 3 — Cierre cordial + aviso MELI
He tratado de ofrecerle dos opciones claras: verificar la autenticidad por canal oficial, o procesar devolucion con reembolso tras recibir el producto. Quedo en espera de su respuesta. Si no logramos avanzar, solicitare al equipo de Mercado Libre que revise el caso. Agradezco su comprension.

### Formulario Solicitud de Exclusión (≤350 chars)
El producto fue publicado y vendido como [CONDICION], tal como consta en la descripcion. Es [PRODUCTO] original con caja, serial SN verificable y codigos UPC/EAN oficiales [MARCA]. Ofreci reembolso total si canal oficial confirma inautenticidad. El comprador no aporta peritaje tecnico ni dictamen oficial. Afirmacion subjetiva sin sustento.

**Motivo dropdown (1ª opción disponible):**
- "El producto coincide con la publicación"
- "El reclamo no fue por falla del producto"
- "Otro"

**Adjunto:** screenshot descripción + foto caja con serial SN + UPC/EAN legibles (PDF combinado ideal)

## Timing ritual
1. Al recibir notificación → Mensaje 1
2. 3-4h después → Mensaje 2
3. Al día siguiente → Mensaje 3
4. Después del M3 → Formulario Solicitud de Exclusión
5. 48h sin avance → "Abrir disputa" + evidencia

## Cuándo NO aplicar (resolver directo en su lugar)
- Evidencia real aportada (video defecto, dictamen técnico)
- Producto efectivamente no coincide con descripción
- Compra errónea del vendedor
- Problemas de envío/entrega

## Historial
| Fecha | Claim ID | Motivo | Resultado |
|---|---|---|---|
| 24-abr-2026 | 5502336104 | PDD9943 no es original | ✅ Excluido |
| pendiente | 5501400150 | PDD9943 no compatible app | 🔄 En trámite |
