import duckdb as dd
from data.duck import sql_inventory

dd.sql(sql_inventory(entity_id_child="")).show()
dd.close()
