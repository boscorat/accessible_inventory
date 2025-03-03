# importing sqlite3 module
import sqlite3
from pathlib import Path

PATH = "/home/boscorat/repos/accessible_inventory/data/inventory.db"
DATABASE = Path(PATH).absolute().resolve()
# print(Path.home().absolute().resolve())
# print(PosixPath.cwd().absolute().resolve())
# print(f"{PosixPath.cwd()}/data/inventory.db")


def list_tables():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    connection.close()
    return tables


def list_columns(table_name):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute(f"SELECT name FROM PRAGMA_TABLE_INFO('{table_name}');")
    columns = cursor.fetchall()
    connection.close()
    return columns


def drop_table(table_name):
    connection = sqlite3.connect(DATABASE)
    connection.execute(f"DROP TABLE IF EXISTS {table_name}")
    connection.close()


def create_table_entity(
    query="CREATE TABLE IF NOT EXISTS entity_sql (entity_id varchar(60) NOT NULL, entity_id_parent varchar(60) NULL, entity_key VARCHAR(100) PRIMARY KEY NOT NULL, noun VARCHAR(50) NOT NULL, adjectives VARCHAR(255), description_singular VARCHAR(350) NOT NULL, description_plural VARCHAR(350) NOT NULL, base_hierarchy_level INT NULL, UNIQUE (entity_id))",
):
    connection = sqlite3.connect(DATABASE)
    connection.execute(query)
    connection.close()


def create_table_inventory(
    query="CREATE TABLE IF NOT EXISTS inventory_sql (inventory_id VARCHAR(60) NOT NULL, inventory_id_parent VARCHAR(60) NOT NULL REFERENCES inventory_sql(inventory_id), entity_id_parent VARCHAR(60) NOT NULL REFERENCES entity_sql(entity_id) ON DELETE CASCADE, entity_id_child VARCHAR(60) NOT NULL REFERENCES entity_sql(entity_id) ON DELETE CASCADE, quantity INTEGER NOT NULL DEFAULT(0), position VARCHAR(25) DEFAULT('IN'), hierarchy_level INT NULL, created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (entity_id_parent, entity_id_child, position), UNIQUE (inventory_id))",
):
    connection = sqlite3.connect(DATABASE)
    connection.execute(query)
    connection.close()


def insert_entity(
    entity_id,
    entity_key,
    noun,
    adjectives,
    description_singular,
    description_plural,
    base_hierarchy_level=0,
    entity_id_parent=None,
):
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        f"INSERT INTO entity_sql (entity_id, entity_id_parent, entity_key, noun, adjectives, description_singular, description_plural, base_hierarchy_level) VALUES ('{entity_id}', '{entity_id_parent}', '{entity_key}', '{noun}', '{adjectives}', '{description_singular}', '{description_plural}', '{base_hierarchy_level}')"
    )
    connection.commit()
    connection.close()


def insert_inventory(
    inventory_id,
    inventory_id_parent,
    entity_id_parent,
    entity_id_child,
    quantity,
    position="IN",
    hierarchy_level=0,
):
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        f"INSERT INTO inventory_sql (inventory_id, inventory_id_parent, entity_id_parent, entity_id_child, quantity, position, hierarchy_level) VALUES ('{inventory_id}', '{inventory_id_parent}', '{entity_id_parent}', '{entity_id_child}', {quantity}, '{position}', {hierarchy_level})"
    )
    connection.commit()
    connection.close()


def update_entity(
    entity_id,
    adjectives,
    description_singular,
    description_plural,
    base_hierarchy_level,
):
    sql = f"UPDATE entity_sql SET adjectives = '{adjectives}', description_singular = '{description_singular}', description_plural = '{description_plural}', base_hierarchy_level = '{base_hierarchy_level}' WHERE entity_id = '{entity_id}'"
    connection = sqlite3.connect(DATABASE)
    connection.execute(sql)
    connection.commit()
    connection.close()


def update_inventory(inventory_id, quantity):
    sql = f"UPDATE inventory_sql SET quantity = {quantity} WHERE inventory_id = '{inventory_id}'"
    connection = sqlite3.connect(DATABASE)
    connection.execute(sql)
    connection.commit()
    connection.close()


def update_inventory_hierarchy(inventory_id, hierarchy_level):
    sql = f"UPDATE inventory_sql SET hierarchy_level = {hierarchy_level} WHERE inventory_id = '{inventory_id}'"
    connection = sqlite3.connect(DATABASE)
    connection.execute(sql)
    connection.commit()
    connection.close()


def delete_entity(entity_id):
    sql = f"DELETE FROM entity_sql WHERE entity_id = '{entity_id}'"
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        "PRAGMA foreign_keys=ON"
    )  # enable foreign key constraints so that the delete operation cascades to the inventory table
    connection.execute(sql)
    connection.commit()
    connection.close()


def delete_inventory(inventory_id):
    sql = f"DELETE FROM inventory_sql WHERE inventory_id = '{inventory_id}'"
    connection = sqlite3.connect(DATABASE)
    connection.execute(
        "PRAGMA foreign_keys=ON"
    )  # enable foreign key constraints to prevent the deletion of a parent inventory item if it still has children
    connection.execute(sql)
    connection.commit()
    connection.close()


def select_entity(
    entity_id=None, entity_key=None, base_hierarchy_level=None, fields="*"
):
    if entity_id:
        sql = f"SELECT {fields} FROM entity_sql WHERE entity_id = '{entity_id}'"
    elif entity_key:
        sql = f"SELECT {fields} FROM entity_sql WHERE entity_key = '{entity_key}'"
    elif base_hierarchy_level:
        sql = f"SELECT {fields} FROM entity_sql WHERE base_hierarchy_level = '{base_hierarchy_level}'"
    else:
        sql = f"SELECT {fields} FROM entity_sql"
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor_obj = connection.cursor()
    cursor_obj.execute(sql)
    if entity_id or entity_key:
        output = cursor_obj.fetchone()
    else:
        output = cursor_obj.fetchall()
    connection.commit()
    connection.close()
    return output


def select_inventory(
    inventory_id=None,
    entity_id_parent=None,
    entity_id_child=None,
    position=None,
    fields="*",
):
    if (
        not inventory_id
        and not entity_id_parent
        and not entity_id_child
        and not position
    ):  # select all if no filters set
        sql = f"SELECT {fields} FROM inventory_sql"
    elif inventory_id:  # select by inventory_id as this is unique
        sql = (
            f"SELECT {fields} FROM inventory_sql WHERE inventory_id = '{inventory_id}'"
        )
    elif (
        entity_id_parent and entity_id_child and position
    ):  # select by parent, child and position
        sql = f"SELECT {fields} FROM inventory_sql WHERE entity_id_parent = '{entity_id_parent}' AND entity_id_child = '{entity_id_child}' AND position = '{position}'"
    elif entity_id_parent and entity_id_child:  # select by parent and child
        sql = f"SELECT {fields} FROM inventory_sql WHERE entity_id_parent = '{entity_id_parent}' AND entity_id_child = '{entity_id_child}'"
    elif entity_id_parent:  # select by parent
        sql = f"SELECT {fields} FROM inventory_sql WHERE entity_id_parent = '{entity_id_parent}'"
    elif entity_id_child:  # select by child
        sql = f"SELECT {fields} FROM inventory_sql WHERE entity_id_child = '{entity_id_child}'"
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor_obj = connection.cursor()
    cursor_obj.execute(sql)
    if inventory_id or (entity_id_parent and entity_id_child):
        output = cursor_obj.fetchone()
    else:
        output = cursor_obj.fetchall()
    connection.commit()
    connection.close()
    return output
