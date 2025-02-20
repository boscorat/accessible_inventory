from unittest.mock import patch

import pytest
from entity import Entity, EntityDeleteHasInventoryError


@pytest.fixture
def entity():
    return Entity(description="test entity", base_hierarchy_level=1)


def test_entity_initialization(entity):
    assert entity.description == "test entity"
    assert entity.base_hierarchy_level == 1
    assert entity.singular == "test entity"
    assert entity.plural == "test entities"


@patch("entity.select_inventory")
def test_inventory(mock_select_inventory, entity):
    mock_select_inventory.return_value = [(10,)]
    assert entity.inventory == 10


@patch("entity.select_entity")
def test_exists(mock_select_entity, entity):
    mock_select_entity.return_value = [1]
    assert entity.exists is True


@patch("entity.insert_entity")
@patch("entity.select_entity")
def test_create_new(mock_select_entity, mock_insert_entity, entity):
    mock_select_entity.return_value = []
    mock_insert_entity.return_value = None
    assert entity.create_new() is True


@patch("entity.update_entity")
@patch("entity.select_entity")
def test_update_existing(mock_select_entity, mock_update_entity, entity):
    mock_select_entity.return_value = [1]
    mock_update_entity.return_value = None
    assert entity.update_existing() is True


@patch("entity.select_entity")
def test_select_existing(mock_select_entity, entity):
    mock_select_entity.return_value = {"entity_id": 1}
    assert entity.select_existing() == {"entity_id": 1}


@patch("entity.delete_entity")
@patch("entity.select_inventory")
@patch("entity.select_entity")
def test_delete_existing(
    mock_select_entity, mock_select_inventory, mock_delete_entity, entity
):
    mock_select_entity.return_value = [1]
    mock_select_inventory.return_value = [(0,)]
    mock_delete_entity.return_value = None
    assert entity.delete_existing() is True


@patch("entity.select_inventory")
@patch("entity.select_entity")
def test_delete_existing_with_inventory(
    mock_select_entity, mock_select_inventory, entity
):
    mock_select_entity.return_value = [1]
    mock_select_inventory.return_value = [(10,)]
    with pytest.raises(EntityDeleteHasInventoryError):
        entity.delete_existing()


@patch("entity.select_entity")
def test_get_db_id(mock_select_entity, entity):
    mock_select_entity.return_value = [1]
    assert entity.get_db_id() == 1


@patch("entity.select_entity")
def test_get_db_description(mock_select_entity, entity):
    mock_select_entity.return_value = ["test entity"]
    assert entity.get_db_description() == "test entity"


def test_invalid_hierarchy_level():
    with pytest.raises(ValueError):
        Entity(description="test entity", base_hierarchy_level="invalid")


def test_empty_description():
    with pytest.raises(ValueError):
        Entity(description="")


def test_get_key(entity):
    assert entity.get_key() == "entity_test"


def test_get_part_of_speech(entity):
    assert entity.get_part_of_speech("noun") == "entity"
    assert entity.get_part_of_speech("adjectives") == ["test"]
