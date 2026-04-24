import os,requests,json,time

ACCOUNTS={
    "JUAN":os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO":os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
}

ITEM_CACHE={}
def get_item_context(iid,H):
    if iid in ITEM_CACHE: return ITEM_CACHE[iid]
    try:
        d=requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H,timeout=15).json()
        desc=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,timeout=15).json().get("plain_text","")
    except: return None
    attrs={a.get("id"):a.get("value_name","") for a in (d.get("attributes") or [])}
    variations=[]
    for v in (d.get("variations") or []):
        for ac in v.get("attribute_combinations",[]):
            if ac.get("id")=="COLOR":
                variations.append({"color":ac.get("value_name"),"qty":v.get("available_quantity",0),"price":v.get("price")})
    ctx={
        "id":iid,
        "title":(d.get("title") or ""),
        "condition":d.get("condition"),
        "brand":attrs.get("BRAND",""),
        "model":attrs.get("MODEL",""),
        "category":d.get("category_id",""),
        "price":d.get("price"),
        "qty":d.get("available_quantity",0),
        "desc":desc,
        "variations":variations,
        "is_generic":"generic" in attrs.get("BRAND","").lower() or "generic" in (d.get("title") or "").lower() or "no original" in desc.lower() or "generico" in desc.lower(),
        "is_original":"jbl" in attrs.get("BRAND","").lower() and "generic" not in attrs.get("BRAND","").lower(),
        "is_used":d.get("condition")=="used" or "usado" in (d.get("title") or "").lower(),
        "no_app":"no es compatible con la app" in desc.lower() or "no requiere app" in desc.lower() or "sin app" in desc.lower(),
        "has_usb":"entrada usb" in desc.lower() or "usb-c" in desc.lower() or "usb" in desc.lower(),
    }
    ITEM_CACHE[iid]=ctx
    return ctx

def craft_answer(question,ctx):
    q=question.lower()
    if not ctx: return "Buen dia, gracias por su pregunta. Revise la descripcion para mas detalles. Saludos."
    
    # Disponibilidad / stock
    if any(k in q for k in ["disponibl","hay","stock","existencia","tiene"]):
        if ctx["variations"]:
            avail=[v["color"] for v in ctx["variations"] if v["qty"]>0]
            if avail:
                return f"Buen dia, si tenemos disponibilidad en los colores: {', '.join(avail)}. Despachamos en 24h habiles. Gracias."
        if ctx["qty"]>0:
            return "Buen dia, si tenemos disponibilidad inmediata. Despachamos en 24h habiles. Gracias."
        return "Buen dia, por el momento no tenemos stock de ese color. Ofrecemos otros colores disponibles. Gracias."
    
    # Colores
    if any(k in q for k in ["color","colores","tienen el","tiene el","tiene en"]):
        if ctx["variations"]:
            cols=[v["color"] for v in ctx["variations"]]
            return f"Buen dia, tenemos disponibles: {', '.join(cols)}. Seleccione su color al agregar al carrito. Gracias."
        return "Buen dia, el color especifico se indica en el titulo y las imagenes de la publicacion. Gracias."
    
    # Originalidad
    if any(k in q for k in ["original","autentic","replica","pirata","falso","generic","verdader"]):
        if ctx["is_generic"]:
            return "Buen dia, como se indica en la descripcion, este es un producto generico de importacion, no es de marca reconocida. Funciona como bocina Bluetooth estandar con todas las caracteristicas descritas. Gracias."
        if ctx["is_original"]:
            return "Buen dia, es producto original con caja, serial SN y codigos UPC/EAN oficiales. Puede verificar autenticidad en el portal oficial de la marca. Gracias."
        return "Buen dia, el producto y sus caracteristicas se describen expresamente en la publicacion. Por favor lea la descripcion completa. Gracias."
    
    # Condicion (usado vs nuevo)
    if any(k in q for k in ["nuevo","usado","seminuev","estado","condicion"]):
        if ctx["is_used"]:
            return "Buen dia, el producto es USADO en excelente estado de funcionamiento, tal como se indica en la publicacion. Puede presentar marcas minimas de uso normal. Gracias."
        if ctx["condition"]=="new":
            return "Buen dia, el producto es NUEVO en caja. Gracias."
        return "Buen dia, la condicion se indica en la publicacion. Gracias."
    
    # App / compatibilidad
    if any(k in q for k in ["app","aplicacion","portable","auracast","bluetooth","conecta"]):
        if ctx["no_app"]:
            return "Buen dia, este modelo opera como bocina Bluetooth estandar. NO es compatible con aplicacion movil JBL Portable ni con Auracast, tal como se indica en la descripcion. Gracias."
        return "Buen dia, el producto conecta por Bluetooth 5.3 estandar con cualquier telefono o tablet. Los detalles de compatibilidad estan en la descripcion. Gracias."
    
    # USB
    if any(k in q for k in ["usb","cable","puerto","cargador","carga"]):
        if ctx["has_usb"]:
            return "Buen dia, cuenta con puerto USB-C para carga. Incluye cable USB-C. Gracias."
        return "Buen dia, los detalles de puertos y accesorios estan en la descripcion. Gracias."
    
    # IP67 / agua
    if any(k in q for k in ["ip67","ip68","agua","alberca","playa","lluvia","sumerg","resiste"]):
        return "Buen dia, el producto cuenta con certificacion IP67: resistente al polvo y al agua. Puede usarse en alberca, playa o lluvia sin problema. Gracias."
    
    # Bateria
    if any(k in q for k in ["bateria","duracion","horas","autonom"]):
        return "Buen dia, la autonomia y detalles de bateria se indican en la descripcion del producto. Incluye cable de carga. Gracias."
    
    # Envio
    if any(k in q for k in ["envio","enviar","llega","tarda","dia","recibo","mandar"]):
        return "Buen dia, envio GRATIS con Mercado Envios. Despacho en 24h habiles y entrega estimada 2 a 5 dias segun zona. Gracias."
    
    # Factura
    if any(k in q for k in ["factura","facturar","fiscal","rfc","cfdi"]):
        return "Buen dia, si facturamos. Al completar la compra envienos por mensaje privado sus datos fiscales (RFC, razon social, uso CFDI, email) y procesamos en 48h. Gracias."
    
    # Garantia
    if any(k in q for k in ["garantia","warranty","reparar","falla","defecto"]):
        if ctx["is_used"]:
            return "Buen dia, ofrecemos 30 dias de garantia del vendedor por defectos de fabrica comprobables con video. Al ser producto usado no aplica garantia oficial del fabricante. Gracias."
        return "Buen dia, ofrecemos garantia del vendedor de 30 dias por defectos de fabrica comprobables con video. Gracias."
    
    # Precio / descuento
    if any(k in q for k in ["precio","descuento","rebaja","negociar","menos","mayoreo","varias","paquete"]):
        return f"Buen dia, el precio publicado de ${ctx['price']} es el final e incluye envio gratis. No aplican descuentos adicionales. Gracias."
    
    # Caja / accesorios
    if any(k in q for k in ["caja","accesorio","incluye","viene con"]):
        return "Buen dia, los accesorios incluidos se listan en la descripcion de la publicacion. Producto entregado en su empaque original. Gracias."
    
    return f"Buen dia, gracias por su pregunta. Todas las caracteristicas, accesorios, garantia y detalles de envio estan especificados en la descripcion de la publicacion. Le invito a leerla completa. Gracias."

total=0
for label,rt in ACCOUNTS.items():
    if not rt:
        print(f"\n=== {label}: sin token ===")
        continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r:
        print(f"\n=== {label}: token invalido ===")
        continue
    TOKEN=r["access_token"]
    H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    USER_ID=me["id"]
    print(f"\n=== {label} ({me.get('nickname')} {USER_ID}) ===")
    
    q=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=50",headers=H,timeout=20).json()
    qs=q.get("questions") or []
    print(f"  unanswered: {len(qs)}")
    
    for ques in qs:
        qid=ques.get("id")
        text=ques.get("text","")
        iid=ques.get("item_id")
        ctx=get_item_context(iid,H)
        ans=craft_answer(text,ctx)
        title_short=(ctx.get("title","") if ctx else "")[:40]
        print(f"  [{iid} '{title_short}'] Q: '{text[:70]}'")
        print(f"    A: '{ans[:100]}'")
        rp=requests.post("https://api.mercadolibre.com/answers",headers=H,json={"question_id":qid,"text":ans},timeout=15)
        if rp.status_code in (200,201):
            total+=1
        else:
            print(f"    err {rp.status_code}: {rp.text[:200]}")
        time.sleep(1)

print(f"\n=== TOTAL: {total} respondidas ===")
