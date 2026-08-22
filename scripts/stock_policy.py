"""Politica segura para mantener una pieza sin evadir pausas de Mercado Libre."""


def item_stock_action(status, sub_status, quantity):
    status=(status or "").lower()
    subs={str(x or "").lower() for x in (sub_status or []) if x}
    qty=int(quantity or 0)
    if status == "active":
        return "noop" if qty == 1 else "set_quantity"
    if status == "paused" and subs == {"out_of_stock"}:
        return "replenish_out_of_stock"
    return "skip_non_sellable"
