-- =====================================================================
-- Sprint 1 — M1 Procurement + M2 Cost Layers — DDL (v2, verificado vs repo)
-- =====================================================================
-- Target file: inventory_platform/schema/02_procurement_cost_layers.sql
-- Se ejecuta DESPUÉS de 01_init.sql vía el mismo inv_migrate.yml existente
-- (migrate.py globbea *.sql en sorted order).
--
-- Verificado contra 01_init.sql real:
--   ✓ apply_stock_delta(p_sku,p_warehouse,p_delta,p_type,p_event_id,
--                       p_order_id,p_mlm_id,p_account_id,p_reason,p_author)
--   ✓ stock_movements.movement_type es TEXT con CHECK constraint
--   ✓ Warehouses reales: bodega_main, devolucion, transito, dañado
--   ✓ products.sku es PK TEXT; FK ON DELETE RESTRICT
--   ✓ accounts.id es SERIAL (int)
--   ✓ v_stock_current está pivoteada por warehouse — sanity check usa stock directo
--
-- Idempotente: rerun-safe. Soft-delete via archived. Tenant_id NULL = Elite Market.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 0. Extensiones
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------
-- 1. Expandir CHECK de stock_movements.movement_type
-- ---------------------------------------------------------------------
-- 01_init.sql original permite: sale,return_meli,manual_in,manual_out,
-- transfer,damage,reverse,initial_seed,backfill
-- Sprint 1 agrega: purchase, transfer_in, transfer_out, return_supplier
-- ---------------------------------------------------------------------
DO $$
DECLARE v_constraint text;
BEGIN
    SELECT conname INTO v_constraint
      FROM pg_constraint
     WHERE conrelid = 'stock_movements'::regclass
       AND contype = 'c'
       AND pg_get_constraintdef(oid) ILIKE '%movement_type%';
    IF v_constraint IS NOT NULL THEN
        EXECUTE format('ALTER TABLE stock_movements DROP CONSTRAINT %I', v_constraint);
    END IF;
END $$;

ALTER TABLE stock_movements
    ADD CONSTRAINT stock_movements_movement_type_check
    CHECK (movement_type IN (
        'sale','return_meli','manual_in','manual_out',
        'transfer','damage','reverse','initial_seed','backfill',
        'purchase','transfer_in','transfer_out','return_supplier'
    ));

-- ---------------------------------------------------------------------
-- 2. Enums Sprint 1
-- ---------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE po_status_enum AS ENUM (
        'draft','sent','in_transit','partially_received','received','cancelled'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE cost_method_enum AS ENUM ('weighted_avg','fifo');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE cost_layer_source_enum AS ENUM (
        'purchase','return_meli','adjustment','transfer_in','opening_balance'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------------------------------------------------------------------
-- 3. app_config (key/value global)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_config (
    key            text PRIMARY KEY,
    value          jsonb NOT NULL,
    description    text,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    updated_by     text
);

INSERT INTO app_config(key, value, description) VALUES
    ('cost_method_default',  '"weighted_avg"',   'Método de costeo default'),
    ('canonical_currency',   '"MXN"',            'Divisa canónica interna'),
    ('po_number_prefix',     '"PO"',             'Prefijo para po_number'),
    ('po_warehouse_default', '"bodega_main"',    'Warehouse default de recepción si no se especifica')
ON CONFLICT (key) DO NOTHING;

-- ---------------------------------------------------------------------
-- 4. schema_migrations (tracking de Sprint 1 aplicado)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    id           text PRIMARY KEY,
    applied_at   timestamptz NOT NULL DEFAULT now(),
    description  text
);

INSERT INTO schema_migrations(id, description)
VALUES ('sprint1_m1_m2_v1', 'M1 Procurement + M2 Cost Layers v1')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------
-- 5. suppliers
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           uuid,
    code                text NOT NULL UNIQUE,
    razon_social        text NOT NULL,
    rfc                 text,
    contacto_nombre     text,
    contacto_email      text,
    contacto_telefono   text,
    banco_nombre        text,
    banco_cuenta        text,
    banco_clabe         text,
    divisa_default      char(3) NOT NULL DEFAULT 'MXN',
    dias_credito        int NOT NULL DEFAULT 0 CHECK (dias_credito >= 0),
    pais                char(2) DEFAULT 'MX',
    notas               text,
    archived            boolean NOT NULL DEFAULT false,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_supplier_clabe CHECK (banco_clabe IS NULL OR banco_clabe ~ '^[0-9]{18}$'),
    CONSTRAINT chk_supplier_rfc   CHECK (rfc IS NULL OR rfc ~ '^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$')
);
CREATE INDEX IF NOT EXISTS idx_suppliers_active     ON suppliers(archived) WHERE archived = false;
CREATE INDEX IF NOT EXISTS idx_suppliers_razon_trgm ON suppliers USING gin(razon_social gin_trgm_ops);

-- ---------------------------------------------------------------------
-- 6. po_number_counter
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS po_number_counter (
    year      int PRIMARY KEY,
    last_seq  int NOT NULL DEFAULT 0
);

-- ---------------------------------------------------------------------
-- 7. purchase_orders
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_orders (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                uuid,
    po_number                text UNIQUE,                             -- generado por trigger si NULL
    supplier_id              uuid REFERENCES suppliers(id) ON DELETE RESTRICT,
    supplier_freetext        text,
    fecha_orden              date NOT NULL DEFAULT CURRENT_DATE,
    fecha_eta                date,
    fecha_received           date,
    estado                   po_status_enum NOT NULL DEFAULT 'draft',
    divisa                   char(3) NOT NULL DEFAULT 'MXN',
    tipo_cambio_mxn          numeric(12,4) NOT NULL DEFAULT 1.0000 CHECK (tipo_cambio_mxn > 0),
    warehouse_destino_code   text NOT NULL DEFAULT 'bodega_main',     -- alineado al 01_init.sql
    costo_flete_total_mxn    numeric(12,2) NOT NULL DEFAULT 0 CHECK (costo_flete_total_mxn >= 0),
    otros_costos_mxn         numeric(12,2) NOT NULL DEFAULT 0 CHECK (otros_costos_mxn >= 0),
    iva_acreditable_mxn      numeric(12,2) NOT NULL DEFAULT 0 CHECK (iva_acreditable_mxn >= 0),
    prorrateo_basis          text NOT NULL DEFAULT 'value' CHECK (prorrateo_basis IN ('value','weight','volume','qty')),
    notas                    text,
    archived                 boolean NOT NULL DEFAULT false,
    audit                    jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_by               text,
    created_at               timestamptz NOT NULL DEFAULT now(),
    updated_at               timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_supplier_or_freetext CHECK (supplier_id IS NOT NULL OR supplier_freetext IS NOT NULL),
    CONSTRAINT chk_eta_after_orden     CHECK (fecha_eta IS NULL OR fecha_eta >= fecha_orden),
    CONSTRAINT chk_received_state      CHECK (
        (estado = 'received' AND fecha_received IS NOT NULL)
        OR (estado <> 'received')
    )
);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_po_estado   ON purchase_orders(estado);
CREATE INDEX IF NOT EXISTS idx_po_eta_open ON purchase_orders(fecha_eta)
    WHERE estado NOT IN ('received','cancelled') AND archived = false;
CREATE INDEX IF NOT EXISTS idx_po_active   ON purchase_orders(archived) WHERE archived = false;

-- po_number trigger
CREATE OR REPLACE FUNCTION gen_po_number() RETURNS trigger AS $$
DECLARE
    v_year int;
    v_seq  int;
    v_prefix text;
BEGIN
    IF NEW.po_number IS NOT NULL AND NEW.po_number <> '' THEN RETURN NEW; END IF;
    v_year   := EXTRACT(YEAR FROM NEW.fecha_orden)::int;
    v_prefix := (SELECT value #>> '{}' FROM app_config WHERE key = 'po_number_prefix');
    INSERT INTO po_number_counter(year, last_seq) VALUES (v_year, 0)
      ON CONFLICT (year) DO NOTHING;
    UPDATE po_number_counter SET last_seq = last_seq + 1
     WHERE year = v_year RETURNING last_seq INTO v_seq;
    NEW.po_number := v_prefix || '-' || v_year || '-' || lpad(v_seq::text, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_po_number ON purchase_orders;
CREATE TRIGGER trg_po_number BEFORE INSERT ON purchase_orders
    FOR EACH ROW EXECUTE FUNCTION gen_po_number();

-- updated_at genérico
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_suppliers_updated ON suppliers;
CREATE TRIGGER trg_suppliers_updated BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_po_updated ON purchase_orders;
CREATE TRIGGER trg_po_updated BEFORE UPDATE ON purchase_orders FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- 8. purchase_order_items
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id               uuid NOT NULL REFERENCES purchase_orders(id) ON DELETE RESTRICT,
    sku                 text NOT NULL REFERENCES products(sku) ON DELETE RESTRICT,
    qty_ordered         int  NOT NULL CHECK (qty_ordered > 0),
    qty_received        int  NOT NULL DEFAULT 0 CHECK (qty_received >= 0),
    unit_cost_origen    numeric(12,4) NOT NULL CHECK (unit_cost_origen >= 0),
    peso_kg_unit        numeric(8,3),
    volumen_m3_unit     numeric(8,4),
    notas               text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_recv_not_exceed CHECK (qty_received <= qty_ordered)
);
CREATE INDEX IF NOT EXISTS idx_poi_po   ON purchase_order_items(po_id);
CREATE INDEX IF NOT EXISTS idx_poi_sku  ON purchase_order_items(sku);
CREATE INDEX IF NOT EXISTS idx_poi_open ON purchase_order_items(po_id) WHERE qty_received < qty_ordered;

-- ---------------------------------------------------------------------
-- 9. cost_methods (override por SKU)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cost_methods (
    sku         text PRIMARY KEY REFERENCES products(sku) ON DELETE RESTRICT,
    method      cost_method_enum NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now(),
    updated_by  text
);
DROP TRIGGER IF EXISTS trg_cost_methods_updated ON cost_methods;
CREATE TRIGGER trg_cost_methods_updated BEFORE UPDATE ON cost_methods FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- 10. cost_layers
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cost_layers (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   uuid,
    sku                         text NOT NULL REFERENCES products(sku) ON DELETE RESTRICT,
    warehouse                   text NOT NULL,                          -- mismo nombre que stock.warehouse
    fecha                       timestamptz NOT NULL DEFAULT now(),
    source_type                 cost_layer_source_enum NOT NULL,
    source_id                   uuid,
    qty_recibida                int NOT NULL CHECK (qty_recibida > 0),
    qty_restante                int NOT NULL CHECK (qty_restante >= 0),
    costo_unitario_base_mxn     numeric(12,4) NOT NULL CHECK (costo_unitario_base_mxn >= 0),
    fletes_prorrateados_mxn     numeric(12,4) NOT NULL DEFAULT 0 CHECK (fletes_prorrateados_mxn >= 0),
    otros_prorrateados_mxn      numeric(12,4) NOT NULL DEFAULT 0 CHECK (otros_prorrateados_mxn >= 0),
    costo_landed_mxn            numeric(12,4) GENERATED ALWAYS AS
        (costo_unitario_base_mxn + fletes_prorrateados_mxn + otros_prorrateados_mxn) STORED,
    archived                    boolean NOT NULL DEFAULT false,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_qty_consistent CHECK (qty_restante <= qty_recibida)
);
CREATE INDEX IF NOT EXISTS idx_cl_sku_wh_fecha ON cost_layers(sku, warehouse, fecha);
CREATE INDEX IF NOT EXISTS idx_cl_active_fifo  ON cost_layers(sku, warehouse, fecha)
    WHERE qty_restante > 0 AND archived = false;
CREATE INDEX IF NOT EXISTS idx_cl_source       ON cost_layers(source_type, source_id);

-- ---------------------------------------------------------------------
-- 11. cogs_movements (audit COGS por venta)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cogs_movements (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           uuid,
    sku                 text NOT NULL REFERENCES products(sku),
    warehouse           text NOT NULL,
    qty                 int NOT NULL CHECK (qty > 0),
    cogs_total_mxn      numeric(14,4) NOT NULL CHECK (cogs_total_mxn >= 0),
    method_used         cost_method_enum NOT NULL,
    sale_order_id       text,            -- MELI order id
    stock_movement_id   bigint REFERENCES stock_movements(id),  -- liga al movimiento real
    cost_layer_ids      uuid[] NOT NULL,
    consumed_per_layer  jsonb NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cogs_sku_fecha ON cogs_movements(sku, created_at);
CREATE INDEX IF NOT EXISTS idx_cogs_order     ON cogs_movements(sale_order_id);
CREATE INDEX IF NOT EXISTS idx_cogs_movement  ON cogs_movements(stock_movement_id);

-- ---------------------------------------------------------------------
-- 12. purchase_order_receipts (idempotencia)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_order_receipts (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id               uuid NOT NULL REFERENCES purchase_orders(id),
    idempotency_key     text NOT NULL,
    payload             jsonb NOT NULL,
    received_by         text,
    received_at         timestamptz NOT NULL DEFAULT now(),
    UNIQUE (po_id, idempotency_key)
);

-- ---------------------------------------------------------------------
-- 13. Vistas
-- ---------------------------------------------------------------------

-- 13.1 v_po_open
CREATE OR REPLACE VIEW v_po_open AS
SELECT
    p.id, p.po_number, p.estado, p.fecha_orden, p.fecha_eta,
    (p.fecha_eta < CURRENT_DATE) AS eta_vencida,
    COALESCE(s.razon_social, p.supplier_freetext) AS proveedor,
    p.divisa, p.tipo_cambio_mxn,
    SUM(i.qty_ordered)                                              AS qty_total_ordered,
    SUM(i.qty_received)                                             AS qty_total_received,
    SUM(i.qty_ordered * i.unit_cost_origen)                         AS valor_origen,
    SUM(i.qty_ordered * i.unit_cost_origen) * p.tipo_cambio_mxn     AS valor_mxn
FROM purchase_orders p
LEFT JOIN suppliers s            ON s.id = p.supplier_id
LEFT JOIN purchase_order_items i ON i.po_id = p.id
WHERE p.archived = false AND p.estado NOT IN ('received','cancelled')
GROUP BY p.id, s.razon_social;

-- 13.2 v_cost_current
CREATE OR REPLACE VIEW v_cost_current AS
SELECT
    cl.sku,
    cl.warehouse,
    SUM(cl.qty_restante)                                            AS qty_disponible,
    SUM(cl.qty_restante * cl.costo_landed_mxn)                      AS valor_inventario_mxn,
    CASE WHEN SUM(cl.qty_restante) > 0
         THEN SUM(cl.qty_restante * cl.costo_landed_mxn) / SUM(cl.qty_restante)
         ELSE NULL
    END                                                             AS costo_promedio_mxn,
    MIN(cl.fecha) FILTER (WHERE cl.qty_restante > 0)                AS capa_mas_vieja_fecha,
    COUNT(*) FILTER (WHERE cl.qty_restante > 0)                     AS capas_activas
FROM cost_layers cl
WHERE cl.archived = false
GROUP BY cl.sku, cl.warehouse;

-- 13.3 v_cogs_history
CREATE OR REPLACE VIEW v_cogs_history AS
SELECT
    sku,
    date_trunc('day', created_at)::date AS fecha,
    SUM(qty)                            AS unidades_vendidas,
    SUM(cogs_total_mxn)                 AS cogs_dia_mxn,
    AVG(cogs_total_mxn / NULLIF(qty,0)) AS cogs_unit_promedio_mxn
FROM cogs_movements
GROUP BY sku, date_trunc('day', created_at);

-- 13.4 v_po_eta_overdue
CREATE OR REPLACE VIEW v_po_eta_overdue AS
SELECT
    p.id, p.po_number, p.fecha_eta,
    (CURRENT_DATE - p.fecha_eta) AS dias_atraso,
    COALESCE(s.razon_social, p.supplier_freetext) AS proveedor,
    p.estado
FROM purchase_orders p
LEFT JOIN suppliers s ON s.id = p.supplier_id
WHERE p.archived = false
  AND p.estado NOT IN ('received','cancelled')
  AND p.fecha_eta IS NOT NULL
  AND p.fecha_eta < CURRENT_DATE
ORDER BY dias_atraso DESC;

-- 13.5 v_inventory_valued (combina stock real + costo promedio para BS)
CREATE OR REPLACE VIEW v_inventory_valued AS
SELECT
    s.sku, s.warehouse, s.qty AS qty_stock,
    cc.qty_disponible AS qty_costed,
    cc.costo_promedio_mxn,
    (s.qty * COALESCE(cc.costo_promedio_mxn, 0)) AS valor_mxn,
    (s.qty - COALESCE(cc.qty_disponible, 0))     AS gap_costed
FROM stock s
LEFT JOIN v_cost_current cc ON cc.sku = s.sku AND cc.warehouse = s.warehouse;

-- ---------------------------------------------------------------------
-- 14. Comentarios
-- ---------------------------------------------------------------------
COMMENT ON TABLE  suppliers            IS 'Proveedores formales. Soft-delete via archived.';
COMMENT ON TABLE  purchase_orders      IS 'Cabecera PO. tipo_cambio_mxn snapshot inmutable.';
COMMENT ON TABLE  purchase_order_items IS 'Líneas PO. qty_received incrementa con receive_po().';
COMMENT ON TABLE  cost_layers          IS 'Capas FIFO/avg. qty_restante decrementa con consumos. Nunca DELETE.';
COMMENT ON TABLE  cogs_movements       IS 'Audit COGS. Liga venta (stock_movement) → capas consumidas.';
COMMENT ON VIEW   v_cost_current       IS 'Costo promedio actual y valor inventario por SKU+warehouse.';
COMMENT ON VIEW   v_inventory_valued   IS 'Stock físico + valor MXN para reportes contables.';

COMMIT;

-- =====================================================================
-- FIN DDL Sprint 1 (v2)
-- =====================================================================
