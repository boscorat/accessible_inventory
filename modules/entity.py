import logging
import sqlite3
import uuid

from exception import EntityDeleteHasInventoryError, MasterGPOSError
from inflex import Noun  # type: ignore
from sql import (
    delete_entity,
    insert_entity,
    select_entity,
    select_inventory,
    update_entity,
)

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(filename="event.log", level=logging.INFO)


configure_logging()


class Entity:
    def __init__(
        self,
        description: str = "",
        base_hierarchy_level: int = 0,
        id: str = None,
        id_parent: str = None,
    ) -> None:
        self.description = description
        self.base_hierarchy_level = base_hierarchy_level
        self.id_parent = id_parent
        self._initialize_parts_of_speech()
        self._id_db = self.get_db_id()
        if id:  # if an id is provided, use it
            self.id = id
        elif (
            self._id_db
        ):  # if the entity already exists in the database, use the existing id
            self.id = self._id_db
        else:  # otherwise, generate a new id
            self.id = uuid.uuid4()
        self._exists = bool(self._id_db)
        self._initialize_forms()
        self._database_update()

    def __str__(self) -> str:
        return f"{self._singular_title} (total inventory: {self.inventory}) ({self.id})"

    def _initialize_parts_of_speech(self) -> None:
        self._noun = self.get_part_of_speech(speech_part="noun")
        self._adjectives = self.get_part_of_speech(speech_part="adjectives")
        self._key = "_".join(sorted(self._adjectives + [self._noun]))

    def _initialize_forms(self) -> None:
        self._plural = str(
            " ".join(self._adjectives) + " " + Noun(self._noun).plural()
        ).strip()
        self._singular = str(
            " ".join(self._adjectives) + " " + Noun(self._noun).singular()
        ).strip()
        self._plural_caps = self._plural.capitalize()
        self._singular_caps = self._singular.capitalize()
        self._plural_title = self._plural.title()
        self._singular_title = self._singular.title()
        # correction for fixed level entities, as they could be a fixed plural or singular and should reflect the description
        if self.base_hierarchy_level != 0:
            self._plural = self.description
            self._plural_caps = self.description.capitalize()
            self._plural_title = self.description.title()

    def _database_update(self) -> None:
        if not self._exists:
            if self.create_new():
                self._exists = True
        else:
            db_description = self.get_db_description()
            if self._singular != db_description:
                self.update_existing()

    @property
    def inventory(self) -> int:
        result = select_inventory(entity_id_child=self.id, fields="quantity")
        if result:
            qty = 0
            for row in result:
                qty += dict(row)["quantity"]
            return qty
        else:
            return 0

    def create_new(self) -> bool:
        """
        Create a new entity or location in the database.
        """
        if not self._exists:
            try:
                insert_entity(
                    entity_id=self.id,
                    entity_key=self._key,
                    noun=self._noun,
                    adjectives=" ".join(self._adjectives),
                    description_singular=self._singular,
                    description_plural=self._plural,
                    base_hierarchy_level=self.base_hierarchy_level,
                    entity_id_parent=self.id_parent,
                )
                logger.info("Entity created successfully")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error creating entity: {e}")
                return False
        else:
            logger.info("Entity already exists")
            return False

    def update_existing(self) -> bool:
        """
        Update an existing entity in the database.
        """
        if self._exists:
            try:
                update_entity(
                    entity_id=self.id,
                    adjectives=" ".join(self._adjectives),
                    description_singular=self._singular,
                    description_plural=self._plural,
                    base_hierarchy_level=self.base_hierarchy_level,
                )
                logger.info("Entity updated successfully")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error updating entity: {e}")
                return False
        else:
            logger.info("Entity does not exist")
            return False

    def select_existing(self) -> dict | None:
        """
        Select an existing entity from the database.
        """
        if self._exists:
            try:
                entity_sql_row = select_entity(entity_id=self.id)
                logger.info("Entity selected successfully")
                return entity_sql_row
            except sqlite3.Error as e:
                logger.error(f"Error selecting entity: {e}")
                return None
        else:
            logger.info("Entity does not exist")
            return None

    def delete_existing(self) -> bool:
        """
        Delete an existing entity from the database.
        """
        if self._exists and not self.inventory:
            try:
                delete_entity(entity_id=self.id)
                logger.info("Entity deleted successfully")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error deleting entity: {e}")
                return False
        elif self.inventory:
            logger.info("Cannot delete as entity has inventory")
            raise EntityDeleteHasInventoryError("Cannot delete as entity has inventory")
            return False
        else:
            logger.info("Entity does not exist")
            return False

    def get_db_id(self) -> str | None:
        result = select_entity(entity_key=self._key, fields="entity_id")
        if result:
            return dict(result)["entity_id"]
        else:
            return None  # if the entity does not exist, return None

    def get_db_description(self) -> str | None:
        result = select_entity(entity_id=self.id, fields="description_singular")
        if result:
            return dict(result)["description_singular"]
        else:
            return None

    @property
    def base_hierarchy_level(self):
        return self._base_hierarchy_level

    @base_hierarchy_level.setter
    def base_hierarchy_level(self, value):
        if not isinstance(value, int):
            raise ValueError(
                "Invalid hierarchy level. Hierarchy level must be an integer."
            )
        self._base_hierarchy_level = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        """
        Ensures consistency by lowering the case of the description.
        """
        if not value.strip():
            raise ValueError("Invalid description. Description cannot be empty.")
        else:
            self._description = value.strip().lower()

    def get_part_of_speech(self, speech_part) -> list[str] | str:
        excludes = ("a", "the", "my", "an")
        words = [word for word in self.description.split(" ") if word not in excludes]
        if not words:
            raise MasterGPOSError("Description is empty")
        noun = str(words[-1])
        if speech_part == "noun":
            return Noun(noun).singular()
        else:
            return [word for word in words if word != noun]
