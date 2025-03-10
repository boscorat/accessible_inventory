# coonect using duckdb and validate tables
import duckdb as dd


class DuckConnect:
    # Create an in-memory DuckDB connection
    con = dd.connect(":memory:")
    try:
        dd.sql(
            "ATTACH '/home/boscorat/repos/accessible_inventory/data/inventory.db' AS inventory (TYPE sqlite);"
        )
    except Exception as e:
        print(e)
    dd.sql("USE inventory")


def sql_inventory(
    inventory_id: str = None,
    inventory_id_parent: str = None,
    entity_id_child: str = None,
    entity_id_parent: str = None,
):
    sql = """
        select INV.hierarchy_level as lvl
            , INV.quantity as qty
            , CHI.description_singular as child
            , INV.position as pos
            , PAR.description_singular as parent
            , INV.inventory_id
            , INV.inventory_id_parent
            , PAR.entity_id as parent
            , CHI.entity_id as child
        from inventory_sql INV
        inner join entity_sql PAR on PAR.entity_id = INV.entity_id_parent
        inner join entity_sql CHI on CHI.entity_id = INV.entity_id_child
    """
    # WHERE clause if specified
    where: str = ""
    if inventory_id:
        where = f"WHERE INV.inventory_id = '{inventory_id}'"
    elif inventory_id_parent:
        where = f"WHERE INV.inventory_id_parent = '{inventory_id_parent}'"
    elif entity_id_child:
        where = f"WHERE CHI.entity_id = '{entity_id_child}'"
    elif entity_id_parent:
        where = f"WHERE PAR.entity_id = '{entity_id_parent}'"

    return sql + where
