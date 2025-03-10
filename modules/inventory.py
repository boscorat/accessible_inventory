import logging
import sqlite3
from uuid import uuid4

import duckdb as dd
from duck import DuckConnect, sql_inventory
from exception import InventoryRemoveExcessiveError, InventoryRemoveZeroError
from sql import delete_inventory, insert_inventory, select_inventory, update_inventory

logger = logging.getLogger(__name__)
DuckConnect()


def configure_logging():
    logging.basicConfig(filename="event.log", level=logging.INFO)


configure_logging()


class Inventory:
    def __init__(
        self,
        entity_parent,
        entity_child,
        quantity,
        action="ADD",  # can be ADD or REMOVE
        position="IN",  # can be IN, ON, UNDER, BEHIND
        inventory_id=None,  # can be specified if the inventory already exists
        inventory_id_parent=None,  # can be specified if the parent inventory is known
    ):
        self.inventory_id = inventory_id
        self.inventory_id_parent = inventory_id_parent
        self.entity_parent = entity_parent
        self.entity_child = entity_child
        self.quantity = quantity
        self.action = action
        self.position = position
        self._initialize_current_inventory()
        self._initialize_inventory_parent()

        # removal errors
        if self.action == "REMOVE" and self.quantity_current == 0:
            raise InventoryRemoveZeroError(
                f"There are no {self.entity_child._plural} in {self.entity_parent.description} to remove"
            )
        if self.action == "REMOVE" and self.quantity > self.quantity_current:
            raise InventoryRemoveExcessiveError(
                f"There are not enough {self.entity_child._plural} in {self.entity_parent.description} to remove"
            )

        # set new quantity
        self._quantity_new = self.quantity_current + (
            quantity * (1 if action == "ADD" else -1)
        )

        # CREATE record if it doesn't exist
        if not self._exists:
            self.create_new()
        # UPDATE record if it exists and there's a positive quantity
        elif self._exists and self._quantity_new > 0:
            self.update_existing()
        # DELETE record if all quantity has been removed
        elif self._exists and self._quantity_new == 0:
            self.delete_existing()
        else:
            logger.info("No action required")
            print("No action required")

    def _initialize_current_inventory(self):
        if self.inventory_id:  # if an inventory_id is provided we set details from this
            inv = select_inventory(
                inventory_id=self.inventory_id,
                fields="[quantity],[inventory_id_parent]",
            )
            if inv:
                inv = dict(inv)
                self.quantity_current = inv["quantity"]
                self.inventory_id_parent = inv["inventory_id_parent"]
                self._exists = True
            else:
                raise ValueError("Invalid inventory_id provided")
        else:
            inv = select_inventory(  # if no inventory_id is provided we lookup the parent and child entities to get the current inventory
                entity_id_parent=self.entity_parent.entity_id,
                entity_id_child=self.entity_child.entity_id,
                position=self.position,
                fields="[inventory_id],[quantity],[inventory_id_parent]",
            )
            if inv:
                inv = dict(inv)
                self.inventory_id = inv["inventory_id"]
                self.quantity_current = inv["quantity"]
                self.inventory_id_parent = inv["inventory_id_parent"]
                self._exists = True
            else:
                self.inventory_id = uuid4()
                self.quantity_current = 0
                self._exists = False

    def _initialize_inventory_parent(self):
        if self.inventory_id_parent:
            inv = dd.execute(
                "select hierarchy_level from inventory_sql where inventory_id = ?",
                [self.inventory_id_parent],
            ).fetchone()
            dd.close()
            if inv:
                hierarchy_level = inv[0] + 1
                print(hierarchy_level)
            else:
                raise ValueError("Invalid inventory_id_parent provided")
        else:
            if self.entity_parent.base_hierarchy_level == 1:
                self.hierarchy_level = 1
                self.inventory_id_parent = self.inventory_id  # if the parent is a base entity, the parent inventory is the same as the child inventory
            else:
                inv = select_inventory(
                    entity_id_child=self.entity_parent.entity_id,
                    fields="[inventory_id],[hierarchy_level],[quantity]",
                )
                if inv and len(inv) == 1:
                    inv = dict(inv[0])
                    if inv["quantity"] == 1:
                        self.inventory_id_parent = inv["inventory_id"]
                        self.hierarchy_level = inv["hierarchy_level"] + 1
                    else:
                        raise ValueError("Parent inventory must have a quantity of 1")
                elif inv and len(inv) > 1:
                    dd.sql(
                        sql_inventory(entity_id_child=self.entity_parent.entity_id)
                    ).show()
                else:
                    raise ValueError("No parent inventory found")

    def __str__(self):
        if self._quantity_new > 0:
            return f"{self._quantity_new} {self.entity_child._plural if self._quantity_new > 1 else self.entity_child._singular} ({self.entity_child.entity_id}) {self.position.lower()} {self.entity_parent.description} ({self.entity_parent.entity_id})"
        else:
            return f"No {self.entity_child._plural} {self.position.lower()} {self.entity_parent.description}"

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        if value not in ["ADD", "REMOVE"]:
            raise ValueError("Action must be ADD or REMOVE")
        self._action = value

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if value not in ["IN", "ON", "UNDER", "BEHIND"]:
            raise ValueError("Position must be IN, ON, UNDER, BEHIND")
        self._position = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if not isinstance(value, int) or not value > 0:
            raise ValueError("Quantity must be an integer greater than 0")
        else:  # value is an integer greater than 0
            self._quantity = value

    def create_new(self):
        if not self._exists:
            try:
                insert_inventory(
                    inventory_id=self.inventory_id,
                    inventory_id_parent=self.inventory_id_parent,
                    entity_id_parent=self.entity_parent.entity_id,
                    entity_id_child=self.entity_child.entity_id,
                    quantity=self._quantity_new,
                    position=self.position,
                    hierarchy_level=self.hierarchy_level,
                )
                logger.info("Inventory created successfully")
                print("Inventory created successfully")
            except sqlite3.Error as e:
                logger.error(f"Error creating inventory: {e}")
                print(f"Error creating inventory: {e}")
        else:
            logger.info("Inventory already exists")
            print("Inventory already exists")

    def update_existing(self):
        if self._exists:
            try:
                update_inventory(
                    inventory_id=self.inventory_id,
                    quantity=self._quantity_new,
                )
                logger.info("Inventory updated successfully")
                print("Inventory updated successfully")
            except sqlite3.Error as e:
                logger.error(f"Error updating inventory: {e}")
                print(f"Error updating inventory: {e}")
        else:
            logger.info("Inventory does not exist")
            print("Inventory does not exist")

    def delete_existing(self):
        if self._exists:
            try:
                delete_inventory(inventory_id=self.inventory_id)
                logger.info("Inventory deleted successfully")
                print("Inventory deleted successfully")
            except sqlite3.Error as e:
                logger.error(f"Error deleting inventory: {e}")
                print(f"Error deleting inventory: {e}")
        else:
            logger.info("Inventory does not exist")
            print("Inventory does not exist")
