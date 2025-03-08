from entity import Entity
from inventory import Inventory

inventory = Inventory(
    entity_parent=Entity("stillwaters"), entity_child=Entity("lounge"), quantity=1
)
