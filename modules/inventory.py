import sqlite3
from uuid import uuid4
from venv import logger

from exception import InventoryRemoveExcessiveError, InventoryRemoveZeroError
from sql import delete_inventory, insert_inventory, select_inventory, update_inventory


class Inventory:
    def __init__(self, entity_parent, entity_child, quantity, position="IN"):
        self.entity_parent = entity_parent
        self.entity_child = entity_child
        self.quantity = quantity
        self.position = position
        if not self.exists:
            if self.quantity > 0:
                self.new_quantity = self.quantity
                self.id = uuid4()
                self.create_new()
            else:
                logger.info(
                    f"There are no {self.entity_child.plural} in {self.entity_parent.description} to remove"
                )
                raise InventoryRemoveZeroError(
                    f"There are no {self.entity_child.plural} in {self.entity_parent.description} to remove"
                )
        else:
            self.id = self._get_inventory_id()
            db_quantity = self._get_db_quantity()
            self.new_quantity = db_quantity + self.quantity
            if self.new_quantity > 0:
                self.update_existing()
            elif self.new_quantity == 0:
                self.delete_existing()
                if (
                    not self.entity_child.inventory
                    and self.entity_child.base_hierarchy_level == 0
                ):
                    self.entity_child.delete_existing()
            else:  # new_quantity < 0
                logger.info(
                    f"There are not enough {self.entity_child.plural} in {self.entity_parent.description} to remove"
                )
                raise InventoryRemoveExcessiveError(
                    f"There are not enough {self.entity_child.plural} in {self.entity_parent.description} to remove"
                )

    def __str__(self):
        if self.new_quantity > 0:
            return f"{self.new_quantity} {self.entity_child.plural if self.quantity > 1 else self.entity_child.singular} {self.position.lower()} {self.entity_parent.description}"
        else:
            return f"No {self.entity_child.plural} {self.position.lower()} {self.entity_parent.description}"

    @property
    def entity_parent(self):
        return self._entity_parent

    @entity_parent.setter
    def entity_parent(self, value):
        self._entity_parent = value

    @property
    def entity_child(self):
        return self._entity_child

    @entity_child.setter
    def entity_child(self, value):
        self._entity_child = value

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
        self._quantity = value

    @staticmethod
    def show_all(anchor: str = "item"):  # can be item or class
        print(f"showing all {anchor} inventory")

    @property
    def exists(self) -> bool:
        result = select_inventory(
            entity_id_parent=self.entity_parent.id,
            entity_id_child=self.entity_child.id,
            position=self.position,
            fields="inventory_id",
        )
        return bool(result)

    def create_new(self):
        if not self.exists:
            try:
                id_parent = self.get_parent()
                insert_inventory(
                    inventory_id=self.id,
                    inventory_id_parent=id_parent,
                    entity_id_parent=self.entity_parent.id,
                    entity_id_child=self.entity_child.id,
                    quantity=self.quantity,
                    position=self.position,
                )
                logger.info("Inventory created successfully")
            except sqlite3.Error as e:
                logger.error(f"Error creating inventory: {e}")
        else:
            logger.info("Inventory already exists")

    def get_parent(self):
        all_parents = select_inventory(
            entity_id_child=self.entity_parent.id,
            fields="inventory_id, position, quantity",
        )
        filtered_parents = [
            dict(parent)
            for parent in all_parents
            if dict(parent)["position"] == "IN" and dict(parent)["quantity"] == 1
        ]
        if len(filtered_parents) == 1:
            return filtered_parents[0]["inventory_id"]
        else:
            choice = [parent for parent in filtered_parents]
            print(choice)
            return None

    def update_existing(self):
        if self.exists:
            try:
                update_inventory(
                    inventory_id=self.id,
                    quantity=self.new_quantity,
                )
                logger.info("Inventory updated successfully")
            except sqlite3.Error as e:
                logger.error(f"Error updating inventory: {e}")
        else:
            logger.info("Inventory does not exist")

    def delete_existing(self):
        if self.exists:
            try:
                delete_inventory(inventory_id=self.id)
                logger.info("Inventory deleted successfully")
            except sqlite3.Error as e:
                logger.error(f"Error deleting inventory: {e}")
        else:
            logger.info("Inventory does not exist")

    def _get_inventory_id(self) -> str:
        return select_inventory(
            entity_id_parent=self.entity_parent.id,
            entity_id_child=self.entity_child.id,
            fields="inventory_id",
        )[0]

    def _get_db_quantity(self) -> int:
        return select_inventory(
            entity_id_parent=self.entity_parent.id,
            entity_id_child=self.entity_child.id,
            fields="quantity",
        )[0]
