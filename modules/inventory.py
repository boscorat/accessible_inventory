import sqlite3
from uuid import uuid4
from venv import logger

from exception import InventoryRemoveExcessiveError, InventoryRemoveZeroError
from sql import delete_inventory, insert_inventory, select_inventory, update_inventory


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
        self.entity_parent = entity_parent
        self.entity_child = entity_child
        self.quantity = quantity
        self.action = action
        self.position = position

        def _initialize_current_inventory():
            if inventory_id:
                inv = select_inventory(
                    inventory_id=inventory_id, fields="[quantity],[inventory_id_parent]"
                )
                if inv:
                    self.id = inventory_id
                    self.new_quantity = inv[0]
                    self.inventory_id_parent = inv[1]
                    self._exists = True
                else:
                    raise ValueError("Invalid inventory_id provided")
            else:
                inv = select_inventory(
                    entity_id_parent=self.entity_parent,
                    entity_id_child=self.entity_child,
                    position=self.position,
                    fields="[quantity],[inventory_id_parent]",
                )

        if not self.exists:
            if self.quantity > 0:
                self.new_quantity = self.quantity
                self.id = uuid4()
                self.create_new()
            else:
                logger.info(
                    f"There are no {self.entity_child._plural} in {self.entity_parent.description} to remove"
                )
                raise InventoryRemoveZeroError(
                    f"There are no {self.entity_child._plural} in {self.entity_parent.description} to remove"
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
                    f"There are not enough {self.entity_child._plural} in {self.entity_parent.description} to remove"
                )
                raise InventoryRemoveExcessiveError(
                    f"There are not enough {self.entity_child._plural} in {self.entity_parent.description} to remove"
                )

    def __str__(self):
        if self.new_quantity > 0:
            return f"{self.new_quantity} {self.entity_child._plural if self.quantity > 1 else self.entity_child._singular} ({self.entity_child.id}) {self.position.lower()} {self.entity_parent.description} ({self.entity_parent.id})"
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
                if (
                    not self.entity_parent.base_hierarchy_level
                    or self.entity_parent.base_hierarchy_level != 1
                ):
                    inventory_id_parent, parent_hierarchy = self.get_parent()
                else:
                    inventory_id_parent = None
                    parent_hierarchy = 0
                insert_inventory(
                    inventory_id=self.id,
                    inventory_id_parent=inventory_id_parent,
                    entity_id_parent=self.entity_parent.id,
                    entity_id_child=self.entity_child.id,
                    quantity=self.quantity,
                    position=self.position,
                    hierarchy_level=parent_hierarchy + 1,
                )
                logger.info("Inventory created successfully")
            except sqlite3.Error as e:
                logger.error(f"Error creating inventory: {e}")
        else:
            logger.info("Inventory already exists")

    def get_parent(self):
        all_parents = select_inventory(
            entity_id_child=self.entity_parent.id,
            fields="inventory_id, position, quantity, hierarchy_level",
        )
        filtered_parents = [
            dict(parent)
            for parent in all_parents
            if dict(parent)["position"] == "IN" and dict(parent)["quantity"] == 1
        ]
        if len(filtered_parents) == 1:
            return (
                filtered_parents[0]["inventory_id"],
                filtered_parents[0]["hierarchy_level"],
            )
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


# inventory = Inventory(
#     entity_parent=Entity(description="Lounge"),
#     entity_child=Entity(description="Yellow Chair"),
#     quantity=4,
# )
# print(inventory)
