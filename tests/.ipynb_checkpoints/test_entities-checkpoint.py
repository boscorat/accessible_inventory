from unittest.mock import patch

import pytest
from entities import Entity, EntityDeleteHasInventoryError


@pytest.fixture
def mock_select_entity():
    with patch("entities.select_entity") as mock:
        yield mock


@pytest.fixture
def mock_insert_entity():
    with patch("entities.insert_entity") as mock:
        yield mock


@pytest.fixture
def mock_update_entity():
    with patch("entities.update_entity") as mock:
        yield mock


@pytest.fixture
def mock_delete_entity():
    with patch("entities.delete_entity") as mock:
        yield mock


@pytest.fixture
def mock_select_inventory():
    with patch("entities.select_inventory") as mock:
        yield mock


def test_entity_creation(mock_select_entity, mock_insert_entity):
    mock_select_entity.return_value = None
    entity = Entity("a plump lovely piglet")
    assert entity.singular == "plump lovely piglet"
    mock_insert_entity.assert_called_once()


def test_entity_exists(mock_select_entity):
    mock_select_entity.return_value = [1]
    entity = Entity("a plump lovely piglet")
    assert entity.exists is True


def test_entity_does_not_exist(mock_select_entity):
    mock_select_entity.return_value = None
    entity = Entity("a plump lovely piglet")
    assert entity.exists is False


def test_entity_update(mock_select_entity, mock_update_entity):
    mock_select_entity.side_effect = [[1], ["lovely piglet plump"]]
    entity = Entity("a plump lovely piglet")
    entity.update_existing()
    mock_update_entity.assert_called_once()


def test_entity_delete(mock_select_entity, mock_delete_entity, mock_select_inventory):
    mock_select_entity.return_value = 1
    mock_select_inventory.return_value = 0
    entity = Entity("a plump lovely piglet")
    entity.delete_existing()
    mock_delete_entity.assert_called_once()


def test_entity_delete_with_inventory(mock_select_entity, mock_select_inventory):
    mock_select_entity.return_value = 1
    mock_select_inventory.return_value = 10
    entity = Entity("a plump lovely piglet")
    with pytest.raises(EntityDeleteHasInventoryError):
        entity.delete_existing()


def test_get_key():
    entity = Entity("a plump lovely piglet")
    assert entity.get_key() == "lovely_piglet_plump"


def test_get_part_of_speech():
    entity = Entity("a plump lovely piglet")
    assert entity.get_part_of_speech("noun") == "piglet"
    assert entity.get_part_of_speech("adjectives") == ["plump", "lovely"]


def test_invalid_description():
    with pytest.raises(ValueError):
        Entity("")


def test_invalid_hierarchy_level():
    with pytest.raises(ValueError):
        Entity("a plump lovely piglet", base_hierarchy_level="invalid")
