import duckdb as dd
from duck import DuckConnect

DuckConnect()

inventory_id_parent = "4dbba35f-ef8f-4af1-9148-02f2a0e1cbd1"


if inventory_id_parent:
    inv = dd.execute(
        "select hierarchy_level from inventory_sql where inventory_id = ?",
        [inventory_id_parent],
    ).fetchone()
    dd.close()
    if inv:
        hierarchy_level = inv[0] + 1
        print(hierarchy_level)
    else:
        raise ValueError("Invalid inventory_id_parent provided")
