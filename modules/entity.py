import logging
import sqlite3
from uuid import uuid4

from data.duck import dd
from data.sql import (
    delete_entity,
    insert_entity,
    update_entity,
)
from exception import EntityDeleteHasInventoryError, MasterGPOSError
from inflex import Noun  # type: ignore

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(filename="event.log", level=logging.INFO)


configure_logging()


class Entity:
    def __init__(
        self,
        description: str = "",
        base_hierarchy_level: int = 0,
        entity_id: str = None,
        entity_id_parent: str = None,
    ) -> None:
        self.description = description
        self.base_hierarchy_level = base_hierarchy_level
        self.entity_id = entity_id
        self.entity_id_parent = entity_id_parent
        self._initialize_parts_of_speech()
        self._initialize_current_entity()
        self._initialize_forms()
        self._database_update()

    def __str__(self) -> str:
        return f"{self._singular_title} (total inventory: {self.inventory}) ({self.entity_id})"

    def _initialize_parts_of_speech(self) -> None:
        self._noun = self.get_part_of_speech(speech_part="noun")
        self._adjectives = self.get_part_of_speech(speech_part="adjectives")
        self._key = "_".join(sorted(self._adjectives + [self._noun]))

    def _initialize_current_entity(self) -> None:
        if self.entity_id:
            ent = (
                dd.execute(
                    "select * from entity_sql where entity_id = ?", [self.entity_id]
                )
                .df()
                .to_dict("records")
            )
            if ent:
                # ent = dict(ent)
                self._key = ent[0]["entity_key"]
                self._db_description = ent[0]["description_singular"]
                self.base_hierarchy_level = ent[0]["base_hierarchy_level"]
                self.entity_id_parent = ent[0]["entity_id_parent"]
                self._exists = True
            else:
                self._exists = False
        else:
            ent = (
                dd.execute("select * from entity_sql where entity_key = ?", [self._key])
                .df()
                .to_dict("records")
            )
            if ent:
                # ent = dict(ent)
                self.entity_id = ent[0]["entity_id"]
                self._db_description = ent[0]["description_singular"]
                self.base_hierarchy_level = ent[0]["base_hierarchy_level"]
                self.entity_id_parent = ent[0]["entity_id_parent"]
                self._exists = True
            else:
                self.entity_id = uuid4()
                self._exists = False

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
            self._singular = self.description
            self._singular_caps = self.description.capitalize()
            self._singular_title = self.description.title()

    def _database_update(self) -> None:
        if not self._exists:
            if self.create_new():
                self._exists = True
        else:
            if self._singular != self._db_description:
                self.update_existing()

    @property
    def inventory(self) -> int:
        result = (
            dd.execute(
                "select quantity from inventory_sql where entity_id_child = ?",
                [self.entity_id],
            )
            .df()
            .to_dict("records")
        )
        if result:
            qty = 0
            for row in result:
                qty += (row)["quantity"]
            return qty
        else:
            return 0

    def create_new(self) -> bool:
        """
        Create a new entity in the database.
        """
        if not self._exists:
            try:
                insert_entity(
                    entity_id=self.entity_id,
                    entity_key=self._key,
                    noun=self._noun,
                    adjectives=" ".join(self._adjectives),
                    description_singular=self._singular,
                    description_plural=self._plural,
                    base_hierarchy_level=self.base_hierarchy_level,
                    entity_id_parent=self.entity_id_parent,
                )
                logger.info(f"Entity created successfully: {self}")
                print(f"Entity created successfully: {self}")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error creating entity: {e}")
                raise ValueError(f"Error creating entity: {e}")
        else:
            logger.error("Entity already exists but create_new called")
            raise ValueError("Entity already exists but create_new called")

    def update_existing(self) -> bool:
        """
        Update an existing entity in the database.
        """
        if self._exists:
            try:
                update_entity(
                    entity_id=self.entity_id,
                    adjectives=" ".join(self._adjectives),
                    description_singular=self._singular,
                    description_plural=self._plural,
                    base_hierarchy_level=self.base_hierarchy_level,
                )
                logger.info(f"Entity updated successfully: {self}")
                print(f"Entity updated successfully: {self}")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error updating entity: {e}")
                raise ValueError(f"Error updating entity: {e}")
        else:
            logger.error("Entity does not exist but update_existing called")
            print("Entity does not exist but update_existing called")
            return False

    def delete_existing(self) -> bool:
        """
        Delete an existing entity from the database.
        """
        if self._exists and not self.inventory:
            try:
                delete_entity(entity_id=self.entity_id)
                logger.info("Entity deleted successfully")
                print("Entity deleted successfully")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error deleting entity: {e}")
                raise ValueError(f"Error deleting entity: {e}")
        elif self.inventory:
            logger.info("Cannot delete as entity has inventory")
            raise EntityDeleteHasInventoryError("Cannot delete as entity has inventory")
        else:
            logger.error("Entity does not exist")
            raise ValueError("Entity does not exist but delete_existing called")

    @property
    def base_hierarchy_level(self):
        return self._base_hierarchy_level

    @base_hierarchy_level.setter
    def base_hierarchy_level(self, value):
        if not isinstance(value, int) and value > 0:
            raise ValueError(
                "Invalid hierarchy level. Hierarchy level must be a positive integer."
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
        excludes = ("a", "the", "my", "an", "this", "that", "these", "those")
        words = [word for word in self.description.split(" ") if word not in excludes]
        if not words:
            raise MasterGPOSError("Description is empty")
        noun = str(words[-1])
        if speech_part == "noun":
            return Noun(noun).singular()
        else:
            return [word for word in words if word != noun]
