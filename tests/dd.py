# coonect using duckdb and validate tables
import duckdb as dd

# Create an in-memory DuckDB connection
con = dd.connect(":memory:")

# connect to the inventory database
try:
    dd.sql(
        "ATTACH '/home/boscorat/repos/accessible_inventory/data/inventory.db' AS inventory (TYPE sqlite);"
    )
except dd.DuckDBError as e:
    print(e)

dd.sql("USE inventory")
tables = dd.sql("SHOW TABLES").fetchall()
for table in tables:
    tbl = table[0]
    print(tbl)
    sql = "DESCRIBE " + tbl
    res1 = dd.execute(sql).df()
    print(res1)

# res2 = dd.execute("DESCRIBE entity_sql").df()
# print(res2)


# lst = [1, 2, 3, 4]
# res = dd.execute(
#     "select * from ( VALUES (5),(3),(6),(2),(7) ) t(i) where i IN(SELECT UNNEST(?))",
#     [lst],
# ).fetchall()
# print(res)
# # [(3,), (2,)]

con.close()
