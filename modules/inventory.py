import logging
import sqlite3
from uuid import uuid4

from data.duck import dd
from data.sql import (
    delete_inventory,
    insert_inventory,
    update_entity_base_hierarchy_level,
    update_inventory,
)
from exception import InventoryRemoveExcessiveError, InventoryRemoveZeroError

logger = logging.getLogger(__name__)


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
        if (
            self.inventory_id
        ):  # if an inventory_id is provided we set details from this record
            inventory = (
                dd.execute(
                    "select quantity, inventory_id_parent from inventory_sql where inventory_id = ?",
                    [self.inventory_id],
                )
                .df()
                .to_dict("records")
            )
            if inventory:
                self.quantity_current = inventory[0]["quantity"]
                self.inventory_id_parent = inventory[0]["inventory_id_parent"]
                self._exists = True
            else:
                raise ValueError("Invalid inventory_id provided")
        else:  # if no inventory_id is provided we look up the inventory record from the entity_id_parent and entity_id_child
            inventory = (
                dd.execute(
                    "select inventory_id, quantity, inventory_id_parent from inventory_sql where entity_id_parent = ? and entity_id_child = ? and position = ?",
                    [
                        self.entity_parent.entity_id,
                        self.entity_child.entity_id,
                        self.position,
                    ],
                )
                .df()
                .to_dict("records")
            )
            if inventory:
                self.inventory_id = inventory[0]["inventory_id"]
                self.quantity_current = inventory[0]["quantity"]
                self.inventory_id_parent = inventory[0]["inventory_id_parent"]
                self._exists = True
            else:
                self.inventory_id = uuid4()
                self.quantity_current = 0
                self._exists = False

    def _initialize_inventory_parent(self):
        if self.inventory_id_parent:
            parent_record = dd.execute(
                "select hierarchy_level from inventory_sql where inventory_id = ?",
                [self.inventory_id_parent],
            ).fetchone()
            if parent_record:
                self.hierarchy_level = parent_record[0] + 1
            else:
                raise ValueError("Invalid inventory_id_parent provided")
        else:
            parent_records = (
                dd.execute(
                    "select * from inventory_sql where entity_id_child = ?",
                    [self.entity_parent.entity_id],
                )
                .df()
                .to_dict("records")
            )
            if not parent_records:  # if there are no parent inventories, this is the base level and hierarchy_level is 1
                self.inventory_id_parent = self.inventory_id
                self.hierarchy_level = 1
                # the parent entity is the base entity, so we set the base_hierarchy_level to 1
                update_entity_base_hierarchy_level(
                    entity_id=self.entity_parent.entity_id, base_hierarchy_level=1
                )
            elif len(parent_records) == 1:
                parent_record = parent_records[0]
                if parent_record["quantity"] == 1:
                    self.inventory_id_parent = parent_record["inventory_id"]
                    self.hierarchy_level = parent_record["hierarchy_level"] + 1
                else:
                    raise ValueError("Parent inventory must have a quantity of 1")
            elif len(parent_records) > 1:
                print("Multiple parent inventories found:")
                i = 1
                for rec in parent_records:
                    print(f"{i}) {rec['child']} in {rec['parent']}")
                    i += 1
                choice = input("Enter the number of the parent inventory to use: ")
                parent_record = dict(parent_records[int(choice) - 1])
                if parent_record["quantity"] == 1:
                    self.inventory_id_parent = parent_record["inventory_id"]
                    self.hierarchy_level = parent_record["hierarchy_level"] + 1
                else:
                    raise ValueError("Parent inventory must have a quantity of 1")
            else:
                raise ValueError(
                    "Something went wrong with the parent inventory lookup"
                )

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
