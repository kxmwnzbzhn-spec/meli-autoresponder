"""Procesa un evento MELI: fetch order details, decrement stock, register COGS, alert."""
import os,sys,json,requests,psycopg2
import meli_token
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
DSN=os.environ["SUPABASE_DB_URL"]
TG_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN"); TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

event_id=os.environ.get("EVENT_ID")
topic=os.environ.get("TOPIC")
resource=os.environ.get("RESOURCE")
user_id=os.environ.get("USER_ID")

if not event_id:
    print("no EVENT_ID"); sys.exit(1)

def tg(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"},timeout=10)
    except: pass

def tok_for_account(cur,user_id):
    cur.execute("SELECT id, nickname, refresh_token_secret FROM accounts WHERE meli_user_id=%s",(user_id,))
    row=cur.fetchone()
    if not row: return None,None,None
    aid,nick,secret_name=row
    rt=os.environ.get(secret_name,"")
    if not rt: return aid,nick,None
    r=meli_token.refresh(rt).json()
    return aid,nick,r.get("access_token")

conn=psycopg2.connect(DSN); cur=conn.cursor()
cur.execute("SELECT id, topic, resource, user_id, raw_payload, processing_status FROM events WHERE id=%s FOR UPDATE",(event_id,))
row=cur.fetchone()
if not row:
    print(f"event {event_id} not found"); sys.exit(1)
eid,etopic,eres,euser,payload,status=row
if status=="done":
    print(f"event {event_id} already done"); sys.exit(0)

cur.execute("UPDATE events SET processing_status='processing', attempts=attempts+1 WHERE id=%s",(eid,))

aid,nick,T=tok_for_account(cur,euser)
if not T:
    cur.execute("UPDATE events SET processing_status='error', processing_error=%s WHERE id=%s",("no auth",eid))
    conn.commit(); sys.exit(1)
H={"Authorization":f"Bearer {T}"}

# Fetch resource details
if etopic=="orders_v2" and eres.startswith("/orders/"):
    o=requests.get(f"https://api.mercadolibre.com{eres}",headers=H).json()
    if o.get("status") in ("cancelled","invalid"):
        cur.execute("UPDATE events SET processing_status='skipped', processed_at=NOW(), processing_error='order cancelled' WHERE id=%s",(eid,))
        conn.commit(); print("skipped: cancelled"); sys.exit(0)
    decrements=[]
    for it in (o.get("order_items") or []):
        item=it.get("item",{})
        mlm=item.get("id"); qty=int(it.get("quantity",0) or 0)
        # Variation + warehouse aware: resolve_sale_target → (sku, warehouse)
        variation_id = item.get("variation_id")
        if variation_id:
            cur.execute("SELECT sku, warehouse FROM resolve_sale_target(%s,%s)",(mlm,int(variation_id)))
        else:
            cur.execute("SELECT sku, warehouse FROM resolve_sale_target(%s,NULL)",(mlm,))
        row=cur.fetchone()
        if not row or not row[0]:
            print(f"unmapped MLM {mlm} variation_id={variation_id}")
            tg(f"⚠️ MLM no mapeado: `{mlm}` variation={variation_id} order=`{o.get('id')}`")
            continue
        sku, sale_warehouse = row[0], row[1]
        try:
            cur.execute("SELECT apply_stock_delta(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (sku,sale_warehouse,-qty,'sale',eid,str(o.get("id")),mlm,aid,f"order {o.get('id')}"))
            mid=cur.fetchone()[0]

            # --- Sprint 1: COGS registration ---
            # Llamar consume_cost después de stock OK. Si falla (no hay cost_layer),
            # NO abortar venta — capturar advertencia y seguir. Stock ya decrementó.
            cogs_total=None
            try:
                cur.execute("SELECT consume_cost(%s,%s,%s,%s,%s)",
                    (sku,sale_warehouse,qty,str(o.get("id")),mid))
                cogs_total=float(cur.fetchone()[0] or 0)
            except psycopg2.errors.RaiseException as ce:
                err=str(ce)[:300]
                tg(f"⚠️ COGS no registrado: `{sku}` qty={qty} order=`{o.get('id')}`\n{err}")
                cur.execute("UPDATE events SET processing_error = COALESCE(processing_error,'') || %s WHERE id=%s",
                    (f" cogs_warn:{sku}",eid))
            except Exception as ce:
                err=str(ce)[:300]
                tg(f"⚠️ COGS error inesperado: `{sku}` order=`{o.get('id')}`\n{err}")

            decrements.append((sku,qty,mid,cogs_total))
        except psycopg2.errors.RaiseException as e:
            tg(f"⚠️ OVERSELL detectado!\nSKU `{sku}` mlm `{mlm}`\nOrden `{o.get('id')}` qty={qty}\n{str(e)[:200]}")
            cur.execute("ROLLBACK")
            cur.execute("UPDATE events SET processing_status='error', processing_error=%s WHERE id=%s",(f"oversell:{sku}",eid))
            conn.commit(); sys.exit(2)
    cur.execute("UPDATE events SET processing_status='done', processed_at=NOW(), account_id=%s WHERE id=%s",(aid,eid))
    # Check low stock
    for sku,_,_,_ in decrements:
        cur.execute("""SELECT p.alert_threshold, COALESCE(SUM(s.qty),0) FROM products p LEFT JOIN stock s ON s.sku=p.sku AND s.warehouse='bodega_main' WHERE p.sku=%s GROUP BY p.alert_threshold""",(sku,))
        r=cur.fetchone()
        if r and r[1] is not None and r[1]<=(r[0] or 5):
            tg(f"⚠️ Stock bajo: `{sku}` quedan {r[1]} (alerta<{r[0]})")
    conn.commit()
    # Mensaje de venta con cogs si disponible
    def _fmt(s,q,mid,cogs):
        base=f"{s} ×{q}"
        return f"{base} (cogs ${cogs:.0f})" if cogs else base
    tg(f"✓ Venta {nick}: "+", ".join(_fmt(*d) for d in decrements))
    print(f"✓ processed {len(decrements)} decrements")
elif etopic=="claims":
    # Devolución MELI. Resource: /claims/{id} o /post-purchase/v1/claims/{id}
    claim_id = eres.rstrip("/").split("/")[-1]
    # Fetch claim detail (probar ambos endpoints)
    c = None
    for url in (f"https://api.mercadolibre.com/post-purchase/v2/claims/{claim_id}",
                f"https://api.mercadolibre.com/post-purchase/v1/claims/{claim_id}",
                f"https://api.mercadolibre.com{eres}"):
        try:
            r = requests.get(url, headers=H, timeout=20)
            if r.status_code == 200:
                c = r.json(); break
        except Exception:
            continue
    if not c:
        cur.execute("UPDATE events SET processing_status='error', processing_error=%s WHERE id=%s",(f"claim fetch failed: {claim_id}",eid))
        conn.commit(); sys.exit(1)

    # ¿Es una devolución que resultó en producto físicamente devuelto?
    # Reglas (conservadoras):
    #   - status='closed'
    #   - resolution.reason indica producto devuelto (varía: 'product_returned','returned','accept_return','refund_with_return',...)
    status = c.get('status') or c.get('claim_status')
    resolution = c.get('resolution') or {}
    reason = resolution.get('reason') or resolution.get('applied_coverage') or ''
    is_return = (
        status == 'closed'
        and (
            'return' in reason.lower()
            or reason in ('product_returned','returned','accept_return','refund_with_return')
        )
    )
    if not is_return:
        cur.execute("UPDATE events SET processing_status='skipped', processed_at=NOW(), processing_error=%s WHERE id=%s",
                    (f"claim no-return: status={status} reason={reason}", eid))
        conn.commit(); print(f"skipped claim {claim_id}: not a return"); sys.exit(0)

    # Resolver order_id relacionado
    order_id = None
    # Diferentes lugares donde MELI guarda la referencia
    if c.get('resource') and isinstance(c.get('resource'), dict):
        order_id = c['resource'].get('id') if c['resource'].get('type') == 'order' else None
    if not order_id:
        order_id = c.get('order_id') or c.get('resource_id')
    if not order_id and c.get('resources'):
        for res in c['resources']:
            if res.get('type') == 'order':
                order_id = res.get('id'); break
    if not order_id:
        cur.execute("UPDATE events SET processing_status='error', processing_error=%s WHERE id=%s",
                    (f"claim {claim_id} sin order_id resolvible", eid))
        conn.commit(); sys.exit(1)

    # Fetch order para obtener items y variations
    o = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=H, timeout=20).json()
    refund = (resolution.get('refund') or {}).get('amount') or o.get('total_amount')

    processed = []
    for it in (o.get('order_items') or []):
        item = it.get('item', {})
        mlm = item.get('id'); qty = int(it.get('quantity', 0) or 0)
        variation_id = item.get('variation_id')
        # Resolver SKU
        if variation_id:
            cur.execute("SELECT sku FROM resolve_sale_target(%s,%s)",(mlm,int(variation_id)))
        else:
            cur.execute("SELECT sku FROM resolve_sale_target(%s,NULL)",(mlm,))
        row = cur.fetchone()
        if not row or not row[0]:
            tg(f"⚠️ Devolución MLM no mapeado: claim={claim_id} mlm={mlm}")
            continue
        sku = row[0]
        # Llamar process_return
        try:
            cur.execute(
                """SELECT process_return(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (claim_id, str(order_id), aid, mlm, int(variation_id) if variation_id else None,
                 sku, qty, refund, status, reason,
                 json.dumps(c), json.dumps(o))
            )
            result = cur.fetchone()[0]
            processed.append({"sku": sku, "qty": qty, "result": result})
        except Exception as e:
            tg(f"⚠️ Devolución error: claim={claim_id} sku={sku}\n{str(e)[:200]}")
            cur.execute("ROLLBACK")
            cur.execute("UPDATE events SET processing_status='error', processing_error=%s WHERE id=%s",
                        (f"return_err:{sku}",eid))
            conn.commit(); sys.exit(2)

    cur.execute("UPDATE events SET processing_status='done', processed_at=NOW(), account_id=%s WHERE id=%s",(aid,eid))
    conn.commit()
    if processed:
        items_str = ", ".join(f"{p['sku']} ×{p['qty']}" for p in processed)
        tg(f"♻️ Devolución procesada `{nick}`: {items_str}\nClaim `{claim_id}` → +qty a *devolución*")
    print(f"✓ claim {claim_id} processed {len(processed)} returns")
elif etopic=="items":
    # MELI ack: item changed status. Refresh listings.last_sync etc.
    cur.execute("UPDATE events SET processing_status='done', processed_at=NOW(), account_id=%s WHERE id=%s",(aid,eid))
    conn.commit(); print("items event noted")
else:
    cur.execute("UPDATE events SET processing_status='skipped', processed_at=NOW(), processing_error=%s WHERE id=%s",(f"unsupported topic {etopic}",eid))
    conn.commit(); print(f"skipped topic {etopic}")
cur.close(); conn.close()
