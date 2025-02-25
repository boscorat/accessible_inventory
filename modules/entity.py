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
    def __init__(self, description: str = "", base_hierarchy_level: int = 0) -> None:
        self.description = description
        self.base_hierarchy_level = base_hierarchy_level
        self._initialize_parts_of_speech()
        self._initialize_forms()
        self._database_update()
        self._exists = self.exists  # store the result of the exists check

    def __str__(self) -> str:
        return f"{self.singular_title} (total inventory: {self.inventory})"

    def _initialize_parts_of_speech(self) -> None:
        self._noun = self.get_part_of_speech(speech_part="noun")
        self._adjectives = self.get_part_of_speech(speech_part="adjectives")
        self._key = self.get_key()
        self._id = self.get_db_id()

    def _initialize_forms(self) -> None:
        self._plural = str(
            " ".join(self.adjectives) + " " + Noun(self.noun).plural()
        ).strip()
        self._singular = str(
            " ".join(self.adjectives) + " " + Noun(self.noun).singular()
        ).strip()
        self._plural_caps = self.plural.capitalize()
        self._singular_caps = self.singular.capitalize()
        self._plural_title = self.plural.title()
        self._singular_title = self.singular.title()

    def _database_update(self) -> None:
        if not self.exists:
            self.create_new()
        else:
            db_description = self.get_db_description()
            if self.singular != db_description:
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

    @property
    def exists(self) -> bool:
        """-> bool
        Check if the entity exists in the database.

        Returns:
            bool: True if the entity exists, False otherwise.
        """
        result = select_entity(entity_key=self.key, fields="entity_id")
        return bool(result)

    def create_new(self) -> bool:
        """
        Create a new entity or location in the database.
        """
        if not self.exists:
            try:
                insert_entity(
                    entity_id=uuid.uuid4(),
                    entity_key=self.key,
                    noun=self.noun,
                    adjectives=" ".join(self.adjectives),
                    description_singular=self.singular,
                    description_plural=self.plural,
                    base_hierarchy_level=self.base_hierarchy_level,
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
        if self.exists:
            try:
                update_entity(
                    entity_key=self.key,
                    adjectives=" ".join(self.adjectives),
                    description_singular=self.singular,
                    description_plural=self.plural,
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
        if self.exists:
            try:
                entity_sql_row = select_entity(entity_key=self.key)
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
                delete_entity(entity_key=self.key)
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
        result = select_entity(entity_key=self.key, fields="entity_id")
        if result:
            return result[0]
        else:
            return None

    def get_db_description(self) -> str | None:
        result = select_entity(entity_key=self.key, fields="description_singular")
        if result:
            return result[0]
        else:
            return None

    @property
    def noun(self):
        return self._noun

    @property
    def adjectives(self):
        return self._adjectives

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

    @property
    def key(self):
        return self._key

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def plural(self):
        return self._plural

    @property
    def singular(self):
        return self._singular

    @property
    def plural_caps(self):
        return self._plural_caps

    @property
    def singular_caps(self):
        return self._singular_caps

    @property
    def plural_title(self):
        return self._plural_title

    @property
    def singular_title(self):
        return self._singular_title

    def get_key(self) -> str:
        """
            Generate a unique key for the entity based on its adjectives and noun.
        def get_part_of_speech(self, speech_part: str) -> list[str] | str:
            Returns:
                str: The generated key.
        """
        return "_".join(sorted(self.adjectives + [self.noun]))

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
