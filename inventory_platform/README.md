# Elite Market — Inventory Platform

Plataforma de inventario en tiempo real para Mercado Libre. Multi-tenant (9 cuentas, escalable a N), webhooks MELI, PostgreSQL transaccional, dashboard, audit trail completo.

## Arquitectura

```
MELI orders/shipments/items → Cloudflare Worker → Supabase PostgreSQL
                                       │
                                       └──→ GH Actions (process_event)
                                                  │
                                                  ├──→ Decrement stock (transactional)
                                                  ├──→ Telegram alerts
                                                  └──→ Email (Resend) si crítico
```

## Estructura

```
inventory_platform/
├── schema/
│   └── 01_init.sql           # Schema PostgreSQL (Supabase)
├── worker/
│   ├── src/index.js          # Cloudflare Worker (webhook receiver)
│   ├── wrangler.toml
│   └── package.json
├── scripts/
│   ├── migrate.py            # Aplica SQL a Supabase
│   ├── backfill_accounts.py  # Importa 9 cuentas MELI
│   ├── backfill_listings.py  # Importa MLM listings y mapea a SKUs
│   ├── process_event.py      # Procesa 1 evento (triggered by Worker)
│   ├── reprocess_events.py   # Re-corre fallidos
│   └── manual_adjust.py      # CLI ajustes manuales
└── README.md
```

## Setup completo (orden estricto)

### 1. Cuentas a crear (tú)
- [ ] Supabase project → anotar **SUPABASE_URL**, **SUPABASE_SERVICE_KEY**, **SUPABASE_DB_URL**
- [ ] Cloudflare account → anotar **CF_ACCOUNT_ID**, **CF_API_TOKEN**
- [ ] (Opcional) Resend account → **RESEND_API_KEY**

### 2. GitHub Secrets a setear (yo lo hago si me das los valores)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_DB_URL` (con password URL-encoded)
- `PAT_TOKEN` (PAT con scope `repo`)

### 3. Deploy en orden

```bash
# A. Migración Supabase
gh workflow run inv_migrate.yml

# B. Backfill cuentas (puebla tabla accounts)
gh workflow run inv_backfill_accounts.yml

# C. Backfill listings (puebla products + listings desde MLM)
gh workflow run inv_backfill_listings.yml

# D. Deploy Cloudflare Worker (local con wrangler)
cd inventory_platform/worker
npm install
wrangler login
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_SERVICE_KEY
wrangler secret put GH_TOKEN
wrangler secret put ADMIN_KEY
wrangler deploy
# Anotar URL devuelta: https://meli-webhook.<account>.workers.dev

# E. Registrar webhook en MELI
# Panel MELI → My applications → Notifications:
#   Callback URL: https://meli-webhook.<account>.workers.dev
#   Topics: orders_v2, shipments, items, claims

# F. Test: crear orden de prueba o reenviar evento manual
```

## Operaciones diarias

### Agregar producto nuevo (SKU)
```sql
INSERT INTO products (sku, modelo, color, brand, line)
VALUES ('JBL-FLIP8-NEGRO', 'JBL Flip 8', 'Negro', 'JBL', 'Bocinas');
INSERT INTO stock (sku, warehouse, qty) VALUES ('JBL-FLIP8-NEGRO', 'bodega_main', 100);
```

### Agregar cuenta MELI nueva
1. Crear secret `MELI_REFRESH_TOKEN_NUEVA` en GH
2. `INSERT INTO accounts (nickname, meli_user_id, refresh_token_secret) VALUES ('nueva', 123, 'MELI_REFRESH_TOKEN_NUEVA');`
3. Re-correr `inv_backfill_listings` (importa sus items)
4. Suscribir esa cuenta al callback MELI ya configurado (mismo Worker procesa todas)

### Ajuste manual de stock
```bash
SKU=JBL-GO4-AQUA WAREHOUSE=bodega_main DELTA=-3 REASON='merma agua' AUTHOR=luis \
  python inventory_platform/scripts/manual_adjust.py
```

### Vincular MLM listing a SKU (manual override)
```sql
UPDATE listings SET sku='JBL-GO4-ROJO' WHERE mlm_id='MLM2910806817';
```

## Reports SQL útiles

```sql
-- Stock actual
SELECT * FROM v_stock_current ORDER BY qty_bodega ASC LIMIT 20;

-- Ventas hoy
SELECT * FROM v_sales_daily WHERE day=CURRENT_DATE ORDER BY sold DESC;

-- Sobreventas (movimientos que rompieron stock)
SELECT * FROM stock_movements WHERE delta<0 AND after_qty=0 ORDER BY ts DESC LIMIT 50;

-- Audit trail de una orden
SELECT * FROM stock_movements WHERE order_id='2000016XXX';

-- Eventos sin procesar
SELECT id,topic,resource,processing_status,processing_error,attempts FROM events
WHERE processing_status IN ('pending','error') ORDER BY ts;
```

## Resiliencia

- **Worker → Supabase falla**: Worker devuelve 500 a MELI; MELI reintenta hasta 5x.
- **Supabase OK pero dispatch GH falla**: evento queda `pending`; `inv_reprocess_events` lo recoge cada 15min.
- **Process event falla**: status→`error`, attempts++; reprocesa hasta 5 attempts.
- **Oversell detectado**: transacción rollback, alerta Telegram, evento marcado `error`.
- **DB down**: Worker responde 503; MELI reintenta.

## Costos

| Servicio | Plan | Capacidad gratis | $0→$ |
|---|---|---|---|
| Cloudflare Workers | Free | 100k req/día | $5/mes a 10M req |
| Supabase | Free | 500MB, 50k MAU | $25/mes Pro |
| GitHub Actions | Free | 2000 min/mes privado, ∞ público | – |
| Telegram | Free | ∞ | – |
| Resend | Free | 100 emails/día | $20/mes 50k |

Total proyectado año 1: **$0**. Año 2 con crecimiento: ~$50/mes.

