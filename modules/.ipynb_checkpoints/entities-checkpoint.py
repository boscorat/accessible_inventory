import logging
import sqlite3
import uuid

from exceptions import ItemDeleteHasInventoryError, MasterGPOSError
from inflex import Noun  # type: ignore
from sql import (
    delete_entity,
    insert_entity,
    update_entity,
    select_entity,
)

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(filename="event.log", level=logging.INFO)


configure_logging()


class Entity:
    def __init__(self, description: str = "", entity_type: str = "") -> None:
        self.description = description
        self.entity_type = entity_type
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
    def inventory(self):
        if self.entity_type == "item":
            result = select_inventory(item_id=self.get_db_id(), fields="quantity")
            if result:
                return sum(result[0])
            else:
                return 0
        elif self.entity_type == "location":
            result = select_inventory(location_id=self.get_db_id(), fields="quantity")
            if result:
                return sum(result[0])
            else:
                return 0

    @property
    def exists(self) -> bool:
        """-> bool
        Check if the item exists in the database.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        if self.entity_type == "item":
            result = select_item(item_key=self.key, fields="item_id")
        elif self.entity_type == "location":
            result = select_location(location_key=self.key, fields="location_id")
        else:
            result = None
        return bool(result)

    def create_new(self):
        """
        Create a new item or location in the database.
        """
        if not self.exists:
            try:
                if self.entity_type == "item":
                    insert_item(
                        item_id=uuid.uuid4(),
                        item_key=self.key,
                        noun=self.noun,
                        adjectives=" ".join(self.adjectives),
                        description_singular=self.singular,
                        description_plural=self.plural,
                    )
                    logger.info("Item created successfully")
                elif self.entity_type == "location":
                    insert_location(
                        location_id=uuid.uuid4(),
                        location_key=self.key,
                        noun=self.noun,
                        adjectives=" ".join(self.adjectives),
                        description=self.singular,
                    )
                    logger.info("Location created successfully")
            except sqlite3.Error as e:
                logger.error(f"Error creating entity: {e}")
        else:
            logger.info("Entity already exists")

    def update_existing(self):
        """
        Update an existing item or location in the database.
        """
        if self._exists:
            try:
                if self.entity_type == "item":
                    update_item(
                        item_key=self.key,
                        adjectives=" ".join(self.adjectives),
                        description_singular=self.singular,
                        description_plural=self.plural,
                    )
                    logger.info("Item updated successfully")
                elif self.entity_type == "location":
                    update_location(
                        location_key=self.key,
                        adjectives=" ".join(self.adjectives),
                        description=self.singular,
                    )
                    logger.info("Location updated successfully")
            except sqlite3.Error as e:
                logger.error(f"Error updating entity: {e}")
        else:
            logger.info("Entity does not exist")

    def select_existing(self) -> dict | None:
        """
        Select an existing item or location from the database.
        """
        if self.exists:
            try:
                if self.entity_type == "item":
                    entity_sql_row = select_item(item_key=self.key)
                    logger.info("Item selected successfully")
                elif self.entity_type == "location":
                    entity_sql_row = select_location(location_key=self.key)
                    logger.info("Location selected successfully")
                return entity_sql_row
            except sqlite3.Error as e:
                logger.error(f"Error selecting entity: {e}")
        else:
            logger.info("Entity does not exist")

    def delete_existing(self):
        """
        Delete an existing item or location from the database.
        """
        if self._exists and not self.inventory:
            try:
                if self.entity_type == "item":
                    delete_item(item_key=self.key)
                    logger.info("Item deleted successfully")
                elif self.entity_type == "location":
                    delete_location(location_key=self.key)
                    logger.info("Location deleted successfully")
            except sqlite3.Error as e:
                logger.error(f"Error deleting entity: {e}")
        elif self.inventory:
            logger.info("Cannot delete as entity has inventory")
            raise ItemDeleteHasInventoryError("Cannot delete as entity has inventory")
        else:
            logger.info("Entity does not exist")

    def get_db_id(self) -> str | None:
        if self.entity_type == "item":
            result = select_item(item_key=self.key, fields="item_id")
        elif self.entity_type == "location":
            result = select_location(location_key=self.key, fields="location_id")
        else:
            result = None

        if result:
            return result[0]
        else:
            return None

    def get_db_description(self) -> str | None:
        """
        Retrieve the entity description from the database.
        """
        if self.entity_type == "item":
            return select_item(item_key=self.key, fields="description_singular")[0]
        elif self.entity_type == "location":
            return select_location(location_key=self.key, fields="description")[0]

    @property
    def noun(self):
        return self._noun

    @property
    def adjectives(self):
        return self._adjectives

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
    def entity_type(self):
        return self._entity_type

    @entity_type.setter
    def entity_type(self, value):
        if value.strip().lower() not in ["item", "location"]:
            raise ValueError(
                "Entity type cannot be empty and must be 'item' or 'location'."
            )
        else:
            self._entity_type = value.strip().lower()

    @property
    def key(self):
        return self._key

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
