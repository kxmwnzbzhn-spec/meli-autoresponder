"""Procesa un evento MELI: fetch order details, decrement stock, register COGS, alert."""
import os,sys,json,requests,psycopg2
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
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()
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
        cur.execute("SELECT sku FROM listings WHERE mlm_id=%s",(mlm,))
        row=cur.fetchone()
        if not row:
            print(f"unmapped MLM {mlm}"); continue
        sku=row[0]
        try:
            cur.execute("SELECT apply_stock_delta(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (sku,'bodega_main',-qty,'sale',eid,str(o.get("id")),mlm,aid,f"order {o.get('id')}"))
            mid=cur.fetchone()[0]

            # --- Sprint 1: COGS registration ---
            # Llamar consume_cost después de stock OK. Si falla (no hay cost_layer),
            # NO abortar venta — capturar advertencia y seguir. Stock ya decrementó.
            cogs_total=None
            try:
                cur.execute("SELECT consume_cost(%s,%s,%s,%s,%s)",
                    (sku,'bodega_main',qty,str(o.get("id")),mid))
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
elif etopic=="items":
    # MELI ack: item changed status. Refresh listings.last_sync etc.
    cur.execute("UPDATE events SET processing_status='done', processed_at=NOW(), account_id=%s WHERE id=%s",(aid,eid))
    conn.commit(); print("items event noted")
else:
    cur.execute("UPDATE events SET processing_status='skipped', processed_at=NOW(), processing_error=%s WHERE id=%s",(f"unsupported topic {etopic}",eid))
    conn.commit(); print(f"skipped topic {etopic}")
cur.close(); conn.close()
